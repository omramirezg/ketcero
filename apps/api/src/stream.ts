// Videos con Cloudflare Stream (apagado: STREAM_ACTIVO = «no»). Los videos de un curso de pago se suben con
// «requireSignedURLs»; para verlos, la página pide aquí un token firmado que vale una hora y solo se entrega a
// quien tiene acceso al curso. El token es un JWT RS256 firmado con una clave de Stream (POST /stream/keys).
import { usuarioDe } from "./acceso";
import { activo, type Entorno } from "./config";
import { tieneAcceso } from "./pagos";
import { error, json } from "./util";

const b64url = (b: ArrayBuffer | Uint8Array) =>
  btoa(String.fromCharCode(...new Uint8Array(b))).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
const texto64 = (o: unknown) => b64url(new TextEncoder().encode(JSON.stringify(o)));

export async function firmarToken(env: Entorno, video: string, ahora = Date.now(), segundos = 3600): Promise<string> {
  if (!env.STREAM_CLAVE_ID || !env.STREAM_CLAVE_JWK) throw new Error("Falta STREAM_CLAVE_ID o STREAM_CLAVE_JWK");
  const jwk = JSON.parse(atob(env.STREAM_CLAVE_JWK));
  const clave = await crypto.subtle.importKey("jwk", jwk, { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" }, false, ["sign"]);
  const cabeza = texto64({ alg: "RS256", kid: env.STREAM_CLAVE_ID });
  const datos = texto64({ sub: video, kid: env.STREAM_CLAVE_ID, exp: Math.floor(ahora / 1000) + segundos });
  const firma = await crypto.subtle.sign("RSASSA-PKCS1-v1_5", clave, new TextEncoder().encode(`${cabeza}.${datos}`));
  return `${cabeza}.${datos}.${b64url(firma)}`;
}

export async function tokenDeVideo(req: Request, env: Entorno, curso: string, video: string): Promise<Response> {
  if (!activo(env.STREAM_ACTIVO)) return error(404, "No existe");
  if (!/^[0-9a-f]{32}$/.test(video)) return error(400, "Video inválido");
  const u = await usuarioDe(req, env);
  if (!(await tieneAcceso(env, u?.id ?? null, curso))) return error(u ? 403 : 401, u ? "Este video es del curso de pago" : "No has entrado");
  return json({ token: await firmarToken(env, video) });
}
