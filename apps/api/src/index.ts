// Worker de Ket Cero: atiende /api/* y deja todo lo demás a los archivos estáticos de Astro.
// Hoy el sitio publicado NO usa este Worker (wrangler.jsonc de la raíz solo sirve archivos). Para prenderlo
// se despliega apps/api/wrangler.jsonc, que sirve los mismos archivos más la API. Ver notas/COMO_PUBLICAR_ASTRO.md.
import { entrar, paginaEntrar, pedirEnlace, salir, yo } from "./acceso";
import type { Entorno } from "./config";
import { leerProgreso, sincronizar } from "./progreso";
import { error } from "./util";

type Ruta = [método: string, patrón: RegExp, (req: Request, env: Entorno, m: RegExpMatchArray) => Promise<Response> | Response];

const RUTAS: Ruta[] = [
  ["POST", /^\/api\/acceso\/enlace$/, (r, e) => pedirEnlace(r, e)],
  ["GET", /^\/api\/acceso\/entrar$/, (r) => paginaEntrar(r)],
  ["POST", /^\/api\/acceso\/entrar$/, (r, e) => entrar(r, e)],
  ["POST", /^\/api\/acceso\/salir$/, (r, e) => salir(r, e)],
  ["GET", /^\/api\/yo$/, (r, e) => yo(r, e)],
  ["GET", /^\/api\/progreso$/, (r, e) => leerProgreso(r, e)],
  ["PUT", /^\/api\/progreso$/, (r, e) => sincronizar(r, e)],
];

export async function atender(req: Request, env: Entorno): Promise<Response> {
  const url = new URL(req.url);
  if (!url.pathname.startsWith("/api/")) return env.ASSETS ? env.ASSETS.fetch(req) : error(404, "No existe");
  // Defensa contra CSRF: lo que cambia datos solo se acepta desde el mismo sitio (los webhooks vienen firmados).
  if (req.method !== "GET" && !url.pathname.startsWith("/api/pagos/webhook/")) {
    const origen = req.headers.get("Origin");
    if (origen && origen !== env.ORIGEN && origen !== url.origin) return error(403, "Origen no permitido");
  }
  for (const [metodo, patron, f] of RUTAS) {
    const m = url.pathname.match(patron);
    if (m && req.method === metodo) {
      try { return await f(req, env, m); } catch (e) { console.error(e); return error(500, "Algo falló de nuestro lado"); }
    }
  }
  return error(404, "No existe");
}

export default { fetch: atender } satisfies ExportedHandler<Entorno>;
