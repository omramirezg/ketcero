// Pruebas de los cursos de pago (webhooks firmados de Lemon Squeezy y Paddle) y de los tokens de Cloudflare Stream.
// Ninguna llama a un servicio de verdad: las firmas se hacen aquí con secretos de prueba.
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createHmac, generateKeyPairSync, createVerify } from "node:crypto";
import { atender } from "../src/index";
import type { Entorno } from "../src/config";
import { d1EnMemoria } from "./d1-en-memoria";

const ORIGEN = "http://localhost:8787";
const SECRETO_LS = "secreto-de-prueba-ls";
const SECRETO_PADDLE = "pdl_ntfset_prueba";
let env: Entorno;

beforeEach(() => {
  env = {
    DB: d1EnMemoria(), ORIGEN, ENTORNO: "local", CORREO_PROVEEDOR: "consola", TURNSTILE_ACTIVO: "no",
    PAGOS_ACTIVOS: "si", CURSOS_DE_PAGO: "vision-avanzada", LEMONSQUEEZY_SECRETO: SECRETO_LS, PADDLE_SECRETO: SECRETO_PADDLE,
  };
  vi.spyOn(console, "log").mockImplementation(() => {});
});

const pedir = (ruta: string, init: RequestInit = {}) =>
  atender(new Request(ORIGEN + ruta, { ...init, headers: { Origin: ORIGEN, ...(init.headers ?? {}) } }), env);

const hmac = (s: string, m: string) => createHmac("sha256", s).update(m).digest("hex");

function avisoLS(evento: string, pedido: number, curso = "vision-avanzada", correo = "ana@ejemplo.com") {
  return JSON.stringify({ meta: { event_name: evento, custom_data: { curso, correo } }, data: { id: String(pedido), attributes: { status: evento === "order_refunded" ? "refunded" : "paid", user_email: correo } } });
}

const mandarLS = (cuerpo: string, firma = hmac(SECRETO_LS, cuerpo)) =>
  atender(new Request(ORIGEN + "/api/pagos/webhook/lemonsqueezy", { method: "POST", headers: { "X-Signature": firma }, body: cuerpo }), env);

function mandarPaddle(datos: object, ts = Math.floor(Date.now() / 1000), secreto = SECRETO_PADDLE) {
  const cuerpo = JSON.stringify(datos);
  return atender(new Request(ORIGEN + "/api/pagos/webhook/paddle", {
    method: "POST", headers: { "Paddle-Signature": `ts=${ts};h1=${hmac(secreto, `${ts}:${cuerpo}`)}` }, body: cuerpo,
  }), env);
}

async function sesion(correo: string) {
  const r = await pedir("/api/acceso/enlace", { method: "POST", body: JSON.stringify({ correo }) });
  const enlace = new URL(((await r.json()) as any).enlace_de_prueba);
  const f = new FormData();
  f.append("t", enlace.searchParams.get("t")!);
  const e = await pedir("/api/acceso/entrar", { method: "POST", body: f });
  return e.headers.get("Set-Cookie")!.split(";")[0];
}

const acceso = async (c?: string) =>
  (await (await pedir("/api/cursos/vision-avanzada/acceso", { headers: c ? { Cookie: c } : {} })).json()) as any;

describe("apagado", () => {
  it("con PAGOS_ACTIVOS = no, el webhook no existe y todos los cursos son gratis", async () => {
    env.PAGOS_ACTIVOS = "no";
    expect((await mandarLS(avisoLS("order_created", 1))).status).toBe(404);
    expect(await acceso()).toMatchObject({ tipo: "gratis", acceso: true });
  });

  it("un curso que no está en CURSOS_DE_PAGO es gratis", async () => {
    const r = (await (await pedir("/api/cursos/deep-learning/acceso")).json()) as any;
    expect(r).toMatchObject({ tipo: "gratis", acceso: true });
  });
});

describe("Lemon Squeezy", () => {
  it("rechaza una firma falsa o ausente", async () => {
    expect((await mandarLS(avisoLS("order_created", 1), "00".repeat(32))).status).toBe(401);
    expect((await mandarLS(avisoLS("order_created", 1), "")).status).toBe(401);
  });

  it("rechaza un cuerpo cambiado después de firmar", async () => {
    const original = avisoLS("order_created", 1);
    expect((await mandarLS(original.replace("ana@", "eva@"), hmac(SECRETO_LS, original))).status).toBe(401);
  });

  it("una compra da acceso al correo del checkout, aunque todavía no tenga cuenta", async () => {
    expect(((await (await mandarLS(avisoLS("order_created", 7))).json()) as any).efecto).toBe("dar");
    const c = await sesion("ana@ejemplo.com");
    expect(await acceso(c)).toMatchObject({ tipo: "pago", acceso: true, entraste: true });
    expect(await acceso(await sesion("beto@ejemplo.com"))).toMatchObject({ acceso: false });
    expect(await acceso()).toMatchObject({ acceso: false, entraste: false });
  });

  it("el mismo aviso dos veces cuenta una sola", async () => {
    await mandarLS(avisoLS("order_created", 7));
    expect(((await (await mandarLS(avisoLS("order_created", 7))).json()) as any).repetido).toBe(true);
    expect((env.DB as any).sqlite.prepare("SELECT COUNT(*) AS n FROM pedidos").get().n).toBe(1);
  });

  it("un reembolso quita el acceso", async () => {
    await mandarLS(avisoLS("order_created", 7));
    await mandarLS(avisoLS("order_refunded", 7));
    expect(await acceso(await sesion("ana@ejemplo.com"))).toMatchObject({ acceso: false });
  });

  it("un curso que no es de pago se registra pero no da nada", async () => {
    const r = (await (await mandarLS(avisoLS("order_created", 8, "inventado"))).json()) as any;
    expect(r.efecto).toBe("ignorado");
  });

  it("/api/yo lista los cursos comprados", async () => {
    await mandarLS(avisoLS("order_created", 7));
    const c = await sesion("ana@ejemplo.com");
    expect(await (await pedir("/api/yo", { headers: { Cookie: c } })).json()).toEqual({ correo: "ana@ejemplo.com", cursos: ["vision-avanzada"] });
  });
});

describe("Paddle", () => {
  const compra = (id: string) => ({ event_id: id, event_type: "transaction.completed", data: { id: "txn_1", custom_data: { curso: "vision-avanzada", correo: "Ana@Ejemplo.com" } } });

  it("una compra con firma válida da acceso", async () => {
    expect(((await (await mandarPaddle(compra("evt_1"))).json()) as any).efecto).toBe("dar");
    expect(await acceso(await sesion("ana@ejemplo.com"))).toMatchObject({ acceso: true });
  });

  it("rechaza un secreto equivocado", async () => {
    expect((await mandarPaddle(compra("evt_1"), undefined, "otro")).status).toBe(401);
  });

  it("rechaza un aviso de hace más de 5 minutos (reenvío)", async () => {
    expect((await mandarPaddle(compra("evt_1"), Math.floor(Date.now() / 1000) - 600)).status).toBe(401);
  });

  it("un reembolso aprobado quita el acceso", async () => {
    await mandarPaddle(compra("evt_1"));
    await mandarPaddle({ event_id: "evt_2", event_type: "adjustment.updated", data: { id: "txn_1", action: "refund", status: "approved", custom_data: { curso: "vision-avanzada", correo: "ana@ejemplo.com" } } });
    expect(await acceso(await sesion("ana@ejemplo.com"))).toMatchObject({ acceso: false });
  });
});

describe("Cloudflare Stream", () => {
  const VIDEO = "a".repeat(32);
  const { privateKey, publicKey } = generateKeyPairSync("rsa", { modulusLength: 2048 });

  beforeEach(() => {
    env.STREAM_ACTIVO = "si";
    env.STREAM_CLAVE_ID = "clave-de-prueba";
    env.STREAM_CLAVE_JWK = Buffer.from(JSON.stringify(privateKey.export({ format: "jwk" }))).toString("base64");
  });

  const token = (c?: string) => pedir(`/api/cursos/vision-avanzada/videos/${VIDEO}/token`, { headers: c ? { Cookie: c } : {} });

  it("apagado: no existe", async () => {
    env.STREAM_ACTIVO = "no";
    expect((await token()).status).toBe(404);
  });

  it("sin cuenta 401, sin compra 403", async () => {
    expect((await token()).status).toBe(401);
    expect((await token(await sesion("beto@ejemplo.com"))).status).toBe(403);
  });

  it("con compra entrega un JWT RS256 válido para ese video, que vence en una hora", async () => {
    await mandarLS(avisoLS("order_created", 7));
    const r = (await (await token(await sesion("ana@ejemplo.com"))).json()) as any;
    const [cabeza, datos, firma] = r.token.split(".");
    const v = createVerify("RSA-SHA256");
    v.update(`${cabeza}.${datos}`);
    expect(v.verify(publicKey, Buffer.from(firma, "base64url"))).toBe(true);
    expect(JSON.parse(Buffer.from(cabeza, "base64url").toString())).toEqual({ alg: "RS256", kid: "clave-de-prueba" });
    const d = JSON.parse(Buffer.from(datos, "base64url").toString());
    expect(d.sub).toBe(VIDEO);
    expect(d.exp - Date.now() / 1000).toBeGreaterThan(3500);
  });
});
