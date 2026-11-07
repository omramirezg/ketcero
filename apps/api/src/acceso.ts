// Entrar sin contraseña: el estudiante escribe su correo, le llega un enlace de un solo uso y al abrirlo queda
// con una sesión de 30 días en una cookie HttpOnly. El enlace abre una página con un botón «Entrar» (POST),
// así los antivirus de correo que visitan los enlaces no gastan el token.
import { DIAS_SESION, ENLACES_POR_CORREO_HORA, ENLACES_POR_IP_HORA, MINUTOS_ENLACE, type Entorno } from "./config";
import { enviar, mensajeDeEntrada } from "./correo";
import { verificarTurnstile } from "./turnstile";
import { azar, cookie, correoValido, error, escapar, json, leerCookie, sha256 } from "./util";

export const COOKIE = "kc_sesion";
const HORA = 3600_000;

export interface Usuario { id: number; correo: string }

const ipDe = (req: Request) => req.headers.get("CF-Connecting-IP") ?? "";

export async function pedirEnlace(req: Request, env: Entorno, ahora = Date.now()): Promise<Response> {
  let cuerpo: { correo?: string; turnstile?: string; volver?: string };
  try { cuerpo = await req.json(); } catch { return error(400, "Se esperaba JSON"); }
  const correo = (cuerpo.correo ?? "").trim().toLowerCase();
  if (!correoValido(correo)) return error(400, "Ese correo no parece válido");
  const ip = ipDe(req);
  if (!(await verificarTurnstile(env, cuerpo.turnstile, ip))) return error(403, "No pudimos comprobar que no eres un robot");

  const ipHash = await sha256("ip:" + ip);
  const desde = ahora - HORA;
  const porCorreo = await env.DB.prepare("SELECT COUNT(*) AS n FROM enlaces WHERE correo = ? AND creado > ?").bind(correo, desde).first<{ n: number }>();
  const porIp = await env.DB.prepare("SELECT COUNT(*) AS n FROM enlaces WHERE ip_hash = ? AND creado > ?").bind(ipHash, desde).first<{ n: number }>();
  if ((porCorreo?.n ?? 0) >= ENLACES_POR_CORREO_HORA || (porIp?.n ?? 0) >= ENLACES_POR_IP_HORA)
    return error(429, "Pediste muchos enlaces seguidos. Espera un rato y vuelve a intentarlo.");

  const token = azar();
  await env.DB.prepare("INSERT INTO enlaces (token_hash, correo, ip_hash, creado, expira) VALUES (?, ?, ?, ?, ?)")
    .bind(await sha256(token), correo, ipHash, ahora, ahora + MINUTOS_ENLACE * 60_000).run();
  const volver = seguro(cuerpo.volver);
  const enlace = `${env.ORIGEN}/api/acceso/entrar?t=${token}${volver !== "/" ? "&volver=" + encodeURIComponent(volver) : ""}`;
  await enviar(env, { para: correo, ...mensajeDeEntrada(enlace) });
  // En local (correo por consola) se devuelve el enlace para poder probar sin buzón.
  const local = env.ENTORNO === "local" && (env.CORREO_PROVEEDOR || "consola") === "consola";
  return json({ ok: true, ...(local ? { enlace_de_prueba: enlace } : {}) });
}

/** Solo rutas internas: evita que el enlace mande a otro sitio. */
function seguro(volver: string | undefined | null): string {
  return volver && /^\/(?!\/)[\w\-./#?=&%]*$/.test(volver) ? volver : "/";
}

export function paginaEntrar(req: Request): Response {
  const url = new URL(req.url);
  const t = url.searchParams.get("t") ?? "";
  const volver = seguro(url.searchParams.get("volver"));
  const html = `<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex"><title>Entrar · Ket Cero</title><link rel="stylesheet" href="/estilo.css"></head>
<body><div class="cuerpo solo"><main id="contenido" class="texto"><section class="cabeza"><div class="mono">Ket Cero</div>
<h1>Entrar</h1><p>Pulsa el botón para terminar de entrar en este navegador.</p>
<form method="post" action="/api/acceso/entrar"><input type="hidden" name="t" value="${escapar(t)}"><input type="hidden" name="volver" value="${escapar(volver)}">
<p><button class="boton" type="submit">Entrar</button></p></form></section></main></div></body></html>`;
  return new Response(html, { headers: { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store", "Referrer-Policy": "same-origin" } });
}

export async function entrar(req: Request, env: Entorno, ahora = Date.now()): Promise<Response> {
  const datos = await req.formData();
  const token = String(datos.get("t") ?? "");
  const volver = seguro(String(datos.get("volver") ?? "/"));
  if (!token) return error(400, "Falta el enlace");
  const hash = await sha256(token);
  // Se marca usado en la misma consulta que lo valida: dos clics seguidos no crean dos sesiones.
  const fila = await env.DB.prepare("UPDATE enlaces SET usado = ? WHERE token_hash = ? AND usado IS NULL AND expira > ? RETURNING correo")
    .bind(ahora, hash, ahora).first<{ correo: string }>();
  if (!fila) return new Response("Este enlace ya se usó o venció. Pide otro desde la página.", { status: 400, headers: { "Content-Type": "text/plain; charset=utf-8" } });

  await env.DB.prepare("INSERT INTO usuarios (correo, creado) VALUES (?, ?) ON CONFLICT (correo) DO NOTHING").bind(fila.correo, ahora).run();
  const u = await env.DB.prepare("SELECT id FROM usuarios WHERE correo = ?").bind(fila.correo).first<{ id: number }>();
  const sesion = azar();
  await env.DB.prepare("INSERT INTO sesiones (id_hash, usuario_id, creado, expira) VALUES (?, ?, ?, ?)")
    .bind(await sha256(sesion), u!.id, ahora, ahora + DIAS_SESION * 86400_000).run();
  return new Response(null, { status: 303, headers: { Location: volver, "Set-Cookie": cookie(COOKIE, sesion, DIAS_SESION * 86400) } });
}

export async function usuarioDe(req: Request, env: Entorno, ahora = Date.now()): Promise<Usuario | null> {
  const s = leerCookie(req, COOKIE);
  if (!s) return null;
  return await env.DB.prepare(
    "SELECT u.id, u.correo FROM sesiones s JOIN usuarios u ON u.id = s.usuario_id WHERE s.id_hash = ? AND s.expira > ?",
  ).bind(await sha256(s), ahora).first<Usuario>();
}

export async function salir(req: Request, env: Entorno): Promise<Response> {
  const s = leerCookie(req, COOKIE);
  if (s) await env.DB.prepare("DELETE FROM sesiones WHERE id_hash = ?").bind(await sha256(s)).run();
  return json({ ok: true }, 200, { "Set-Cookie": cookie(COOKIE, "", 0) });
}

export async function yo(req: Request, env: Entorno): Promise<Response> {
  const u = await usuarioDe(req, env);
  if (!u) return error(401, "No has entrado");
  return json({ correo: u.correo });
}
