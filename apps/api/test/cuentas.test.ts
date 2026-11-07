// Pruebas de la API de cuentas y progreso, con una D1 en memoria. No sale ningún correo: el proveedor es «consola».
import { beforeEach, describe, expect, it, vi } from "vitest";
import { atender } from "../src/index";
import type { Entorno } from "../src/config";
import { d1EnMemoria } from "./d1-en-memoria";

const ORIGEN = "http://localhost:8787";
let env: Entorno;

beforeEach(() => {
  env = { DB: d1EnMemoria(), ORIGEN, ENTORNO: "local", CORREO_PROVEEDOR: "consola", TURNSTILE_ACTIVO: "no", PAGOS_ACTIVOS: "no" };
  vi.spyOn(console, "log").mockImplementation(() => {});
});

const pedir = (ruta: string, init: RequestInit = {}) =>
  atender(new Request(ORIGEN + ruta, { ...init, headers: { Origin: ORIGEN, ...(init.headers ?? {}) } }), env);

async function pedirEnlace(correo: string) {
  const r = await pedir("/api/acceso/enlace", { method: "POST", body: JSON.stringify({ correo, volver: "/practica/x/" }) });
  return { r, j: (await r.json()) as any };
}

async function entrarCon(enlace: string) {
  const u = new URL(enlace);
  const form = new FormData();
  form.append("t", u.searchParams.get("t")!);
  form.append("volver", u.searchParams.get("volver") ?? "/");
  return pedir("/api/acceso/entrar", { method: "POST", body: form });
}

async function sesion(correo = "Ana@Ejemplo.com ") {
  const { j } = await pedirEnlace(correo);
  const r = await entrarCon(j.enlace_de_prueba);
  return r.headers.get("Set-Cookie")!.split(";")[0];
}

describe("enlace mágico", () => {
  it("rechaza un correo inválido", async () => {
    const { r } = await pedirEnlace("no-es-correo");
    expect(r.status).toBe(400);
  });

  it("en local devuelve el enlace y no manda correos", async () => {
    const { r, j } = await pedirEnlace("ana@ejemplo.com");
    expect(r.status).toBe(200);
    expect(j.enlace_de_prueba).toMatch(/^http:\/\/localhost:8787\/api\/acceso\/entrar\?t=[\w-]{40,}&volver=%2Fpractica%2Fx%2F$/);
    expect(console.log).toHaveBeenCalledWith(expect.stringContaining("[correo de prueba] para ana@ejemplo.com"));
  });

  it("en producción NO devuelve el enlace en la respuesta", async () => {
    env.ENTORNO = "produccion";
    const { j } = await pedirEnlace("ana@ejemplo.com");
    expect(j).toEqual({ ok: true });
  });

  it("guarda solo el hash del token", async () => {
    const { j } = await pedirEnlace("ana@ejemplo.com");
    const token = new URL(j.enlace_de_prueba).searchParams.get("t")!;
    const filas = (env.DB as any).sqlite.prepare("SELECT token_hash FROM enlaces").all();
    expect(filas).toHaveLength(1);
    expect(filas[0].token_hash).not.toBe(token);
    expect(filas[0].token_hash).toMatch(/^[0-9a-f]{64}$/);
  });

  it("GET muestra un botón y no gasta el token (los antivirus de correo abren enlaces)", async () => {
    // con «no-referrer» el navegador mandaría Origin: null y el POST se rechazaría
    const { j } = await pedirEnlace("ana@ejemplo.com");
    const r = await pedir(new URL(j.enlace_de_prueba).pathname + new URL(j.enlace_de_prueba).search);
    expect(await r.text()).toContain('<form method="post" action="/api/acceso/entrar">');
    expect(r.headers.get("Referrer-Policy")).toBe("same-origin");
    expect((await entrarCon(j.enlace_de_prueba)).status).toBe(303);
  });

  it("entrar crea la sesión, redirige a donde estaba y el enlace sirve una sola vez", async () => {
    const { j } = await pedirEnlace("ana@ejemplo.com");
    const r = await entrarCon(j.enlace_de_prueba);
    expect(r.status).toBe(303);
    expect(r.headers.get("Location")).toBe("/practica/x/");
    expect(r.headers.get("Set-Cookie")).toMatch(/^kc_sesion=[\w-]+; Path=\/; HttpOnly; Secure; SameSite=Lax; Max-Age=2592000$/);
    expect((await entrarCon(j.enlace_de_prueba)).status).toBe(400);
  });

  it("un enlace vencido no sirve", async () => {
    const { j } = await pedirEnlace("ana@ejemplo.com");
    (env.DB as any).sqlite.exec("UPDATE enlaces SET expira = 0");
    expect((await entrarCon(j.enlace_de_prueba)).status).toBe(400);
  });

  it("no deja redirigir a otro sitio", async () => {
    const { j } = await pedirEnlace("ana@ejemplo.com");
    const u = new URL(j.enlace_de_prueba);
    const form = new FormData();
    form.append("t", u.searchParams.get("t")!);
    form.append("volver", "//malo.com/");
    const r = await pedir("/api/acceso/entrar", { method: "POST", body: form });
    expect(r.headers.get("Location")).toBe("/");
  });

  it("limita cuántos enlaces se piden por hora", async () => {
    for (let i = 0; i < 5; i++) expect((await pedirEnlace("ana@ejemplo.com")).r.status).toBe(200);
    expect((await pedirEnlace("ana@ejemplo.com")).r.status).toBe(429);
  });

  it("rechaza pedidos que vienen de otro sitio (CSRF)", async () => {
    const r = await pedir("/api/acceso/enlace", { method: "POST", headers: { Origin: "https://malo.com" }, body: "{}" });
    expect(r.status).toBe(403);
  });

  it("con Turnstile prendido y sin token, no manda el enlace", async () => {
    env.TURNSTILE_ACTIVO = "si";
    env.TURNSTILE_SECRETO = "x";
    expect((await pedirEnlace("ana@ejemplo.com")).r.status).toBe(403);
  });
});

describe("sesión", () => {
  it("/api/yo sin sesión es 401 y con sesión devuelve el correo normalizado", async () => {
    expect((await pedir("/api/yo")).status).toBe(401);
    const c = await sesion();
    const r = await pedir("/api/yo", { headers: { Cookie: c } });
    expect(await r.json()).toEqual({ correo: "ana@ejemplo.com" });
  });

  it("dos entradas con el mismo correo son el mismo usuario", async () => {
    await sesion("ana@ejemplo.com");
    await sesion("ANA@ejemplo.com");
    expect((env.DB as any).sqlite.prepare("SELECT COUNT(*) AS n FROM usuarios").get().n).toBe(1);
  });

  it("salir borra la sesión", async () => {
    const c = await sesion();
    await pedir("/api/acceso/salir", { method: "POST", headers: { Cookie: c } });
    expect((await pedir("/api/yo", { headers: { Cookie: c } })).status).toBe(401);
  });
});

describe("progreso", () => {
  const poner = (c: string, entradas: unknown[]) =>
    pedir("/api/progreso", { method: "PUT", headers: { Cookie: c }, body: JSON.stringify({ entradas }) });

  it("sin sesión no se puede leer ni escribir", async () => {
    expect((await pedir("/api/progreso")).status).toBe(401);
  });

  it("guarda y devuelve el progreso", async () => {
    const c = await sesion();
    const r = await poner(c, [{ clave: "practica:l/01", valor: { resuelto: true, bien: 3, total: 3 }, actualizado: 1000 }]);
    expect((await r.json() as any).entradas).toEqual([{ clave: "practica:l/01", valor: { resuelto: true, bien: 3, total: 3 }, actualizado: 1000 }]);
  });

  it("gana el cambio más reciente, venga del dispositivo que venga", async () => {
    const c = await sesion();
    await poner(c, [{ clave: "k", valor: "nuevo", actualizado: 2000 }]);
    await poner(c, [{ clave: "k", valor: "viejo", actualizado: 1000 }]);
    const j = (await (await pedir("/api/progreso", { headers: { Cookie: c } })).json()) as any;
    expect(j.entradas[0].valor).toBe("nuevo");
  });

  it("un reloj adelantado no gana para siempre", async () => {
    const c = await sesion();
    await poner(c, [{ clave: "k", valor: "futuro", actualizado: Date.now() + 1e12 }]);
    const j = (await (await pedir("/api/progreso", { headers: { Cookie: c } })).json()) as any;
    expect(j.entradas[0].actualizado).toBeLessThanOrEqual(Date.now());
  });

  it("cada usuario ve solo lo suyo", async () => {
    const a = await sesion("ana@ejemplo.com");
    const b = await sesion("beto@ejemplo.com");
    await poner(a, [{ clave: "k", valor: 1, actualizado: 1 }]);
    const j = (await (await pedir("/api/progreso", { headers: { Cookie: b } })).json()) as any;
    expect(j.entradas).toEqual([]);
  });

  it("rechaza entradas demasiado grandes", async () => {
    const c = await sesion();
    expect((await poner(c, [{ clave: "k", valor: "x".repeat(3000), actualizado: 1 }])).status).toBe(400);
    expect((await poner(c, Array.from({ length: 201 }, (_, i) => ({ clave: "k" + i, valor: 1, actualizado: 1 })))).status).toBe(400);
  });
});

describe("todo lo demás", () => {
  it("una ruta de la API que no existe es 404", async () => {
    expect((await pedir("/api/nada")).status).toBe(404);
  });
});
