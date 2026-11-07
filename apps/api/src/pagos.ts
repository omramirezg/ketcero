// Cursos de pago con una pasarela que es «comerciante registrado» (Lemon Squeezy o Paddle): ellas cobran, facturan
// al cliente y pagan los impuestos del país del comprador; aquí solo llega un aviso firmado (webhook) y se da o se
// quita el acceso al curso. Todo apagado mientras PAGOS_ACTIVOS no sea «si».
//
// Firmas:
//  - Lemon Squeezy: encabezado X-Signature = HMAC-SHA256(secreto, cuerpo) en hexadecimal.
//  - Paddle Billing: encabezado Paddle-Signature = «ts=…;h1=…», con h1 = HMAC-SHA256(secreto, ts + ":" + cuerpo);
//    se rechaza si ts tiene más de 5 minutos (evita que reenvíen un aviso viejo).
// El checkout manda en custom_data el curso y el correo con que el estudiante entró a Ket Cero.
import { usuarioDe } from "./acceso";
import { activo, type Entorno } from "./config";
import { error, hmacSha256, iguales, json } from "./util";

type Proveedor = "lemonsqueezy" | "paddle";
const TOLERANCIA_S = 300;

export function cursosDePago(env: Entorno): string[] {
  return (env.CURSOS_DE_PAGO ?? "").split(",").map((s) => s.trim()).filter(Boolean);
}

export async function firmaValida(proveedor: Proveedor, env: Entorno, req: Request, cuerpo: string, ahora = Date.now()): Promise<boolean> {
  if (proveedor === "lemonsqueezy") {
    const secreto = env.LEMONSQUEEZY_SECRETO;
    const firma = req.headers.get("X-Signature") ?? "";
    return !!secreto && !!firma && iguales(await hmacSha256(secreto, cuerpo), firma.toLowerCase());
  }
  const secreto = env.PADDLE_SECRETO;
  const partes = Object.fromEntries((req.headers.get("Paddle-Signature") ?? "").split(";").map((p) => p.split("=") as [string, string]));
  const ts = Number(partes.ts);
  if (!secreto || !partes.h1 || !ts || Math.abs(ahora / 1000 - ts) > TOLERANCIA_S) return false;
  return iguales(await hmacSha256(secreto, `${partes.ts}:${cuerpo}`), partes.h1.toLowerCase());
}

interface Aviso { id: string; evento: string; pedido: string | null; correo: string | null; curso: string | null; efecto: "dar" | "quitar" | "ignorado" }

export function leerAviso(proveedor: Proveedor, d: any): Aviso {
  if (proveedor === "lemonsqueezy") {
    const evento = String(d?.meta?.event_name ?? "");
    const extra = d?.meta?.custom_data ?? {};
    const pagado = d?.data?.attributes?.status === "paid";
    return {
      id: `lemonsqueezy:${evento}:${d?.data?.id}`,
      evento,
      pedido: d?.data?.id != null ? String(d.data.id) : null,
      correo: (extra.correo ?? d?.data?.attributes?.user_email ?? null)?.toLowerCase() ?? null,
      curso: extra.curso ?? null,
      efecto: evento === "order_created" && pagado ? "dar" : evento === "order_refunded" ? "quitar" : "ignorado",
    };
  }
  const evento = String(d?.event_type ?? "");
  const extra = d?.data?.custom_data ?? {};
  return {
    id: `paddle:${d?.event_id}`,
    evento,
    pedido: d?.data?.id ?? null,
    correo: extra.correo?.toLowerCase() ?? null,
    curso: extra.curso ?? null,
    // un reembolso en Paddle llega como un ajuste aprobado sobre la transacción
    efecto: evento === "transaction.completed" ? "dar"
      : evento === "adjustment.updated" && d?.data?.action === "refund" && d?.data?.status === "approved" ? "quitar" : "ignorado",
  };
}

export async function webhookPagos(req: Request, env: Entorno, proveedor: Proveedor, ahora = Date.now()): Promise<Response> {
  if (!activo(env.PAGOS_ACTIVOS)) return error(404, "No existe");
  const cuerpo = await req.text();
  if (!(await firmaValida(proveedor, env, req, cuerpo, ahora))) return error(401, "Firma inválida");
  let datos: unknown;
  try { datos = JSON.parse(cuerpo); } catch { return error(400, "JSON inválido"); }
  const a = leerAviso(proveedor, datos);
  if (a.efecto !== "ignorado" && (!a.correo || !a.curso || !cursosDePago(env).includes(a.curso))) a.efecto = "ignorado";

  // El mismo aviso puede llegar dos veces (la pasarela reintenta): se registra una sola.
  const nuevo = await env.DB.prepare(
    "INSERT INTO pedidos (id, proveedor, evento, pedido, correo, curso, efecto, recibido, datos) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT (id) DO NOTHING",
  ).bind(a.id, proveedor, a.evento, a.pedido, a.correo, a.curso, a.efecto, ahora, cuerpo).run();
  if (!nuevo.meta.changes) return json({ ok: true, repetido: true });

  if (a.efecto === "dar") {
    await env.DB.prepare("INSERT INTO usuarios (correo, creado) VALUES (?, ?) ON CONFLICT (correo) DO NOTHING").bind(a.correo, ahora).run();
    await env.DB.prepare(
      `INSERT INTO acceso_cursos (usuario_id, curso, origen, pedido_id, desde, hasta)
       SELECT id, ?, 'pago', ?, ?, NULL FROM usuarios WHERE correo = ?
       ON CONFLICT (usuario_id, curso) DO UPDATE SET origen = 'pago', pedido_id = excluded.pedido_id, hasta = NULL`,
    ).bind(a.curso, a.pedido, ahora, a.correo).run();
  } else if (a.efecto === "quitar") {
    await env.DB.prepare(
      "UPDATE acceso_cursos SET hasta = ? WHERE curso = ? AND pedido_id = ? AND usuario_id = (SELECT id FROM usuarios WHERE correo = ?)",
    ).bind(ahora, a.curso, a.pedido, a.correo).run();
  }
  return json({ ok: true, efecto: a.efecto });
}

export async function tieneAcceso(env: Entorno, usuario: number | null, curso: string, ahora = Date.now()): Promise<boolean> {
  if (!activo(env.PAGOS_ACTIVOS) || !cursosDePago(env).includes(curso)) return true; // curso gratis
  if (usuario === null) return false;
  const f = await env.DB.prepare("SELECT 1 AS si FROM acceso_cursos WHERE usuario_id = ? AND curso = ? AND (hasta IS NULL OR hasta > ?)")
    .bind(usuario, curso, ahora).first();
  return !!f;
}

export async function accesoACurso(req: Request, env: Entorno, curso: string): Promise<Response> {
  const u = await usuarioDe(req, env);
  const pago = activo(env.PAGOS_ACTIVOS) && cursosDePago(env).includes(curso);
  return json({ curso, tipo: pago ? "pago" : "gratis", acceso: await tieneAcceso(env, u?.id ?? null, curso), entraste: !!u });
}
