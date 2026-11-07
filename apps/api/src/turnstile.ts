// Cloudflare Turnstile (el «no soy un robot» sin acertijos). Está listo pero apagado: con TURNSTILE_ACTIVO = «no»
// se acepta cualquier pedido; con «si» el formulario debe mandar el token y aquí se verifica con Cloudflare.
import { activo, type Entorno } from "./config";

export async function verificarTurnstile(env: Entorno, token: string | undefined, ip: string): Promise<boolean> {
  if (!activo(env.TURNSTILE_ACTIVO)) return true;
  if (!token || !env.TURNSTILE_SECRETO) return false;
  const datos = new FormData();
  datos.append("secret", env.TURNSTILE_SECRETO);
  datos.append("response", token);
  if (ip) datos.append("remoteip", ip);
  const r = await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify", { method: "POST", body: datos });
  const j = (await r.json()) as { success?: boolean };
  return j.success === true;
}
