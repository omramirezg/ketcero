// Progreso del estudiante. El navegador siempre guarda primero en localStorage (funciona sin cuenta y sin red);
// si hay sesión, sincroniza aquí. Cada entrada lleva la hora en que cambió y gana la más reciente.
import { usuarioDe } from "./acceso";
import type { Entorno } from "./config";
import { error, json } from "./util";

export interface Entrada { clave: string; valor: unknown; actualizado: number }

const MAX_ENTRADAS = 200;
const MAX_CLAVE = 200;
const MAX_VALOR = 2000;

export async function leerProgreso(req: Request, env: Entorno): Promise<Response> {
  const u = await usuarioDe(req, env);
  if (!u) return error(401, "No has entrado");
  return json({ entradas: await todas(env, u.id) });
}

export async function sincronizar(req: Request, env: Entorno, ahora = Date.now()): Promise<Response> {
  const u = await usuarioDe(req, env);
  if (!u) return error(401, "No has entrado");
  let cuerpo: { entradas?: Entrada[] };
  try { cuerpo = await req.json(); } catch { return error(400, "Se esperaba JSON"); }
  const entradas = Array.isArray(cuerpo.entradas) ? cuerpo.entradas : null;
  if (!entradas || entradas.length > MAX_ENTRADAS) return error(400, `Se esperaban hasta ${MAX_ENTRADAS} entradas`);
  const consultas = [];
  for (const e of entradas) {
    const valor = JSON.stringify(e?.valor ?? null);
    if (typeof e?.clave !== "string" || !e.clave || e.clave.length > MAX_CLAVE || valor.length > MAX_VALOR)
      return error(400, "Entrada inválida");
    const cuando = Math.min(Number(e.actualizado) || 0, ahora); // un reloj adelantado no puede ganar para siempre
    consultas.push(env.DB.prepare(
      `INSERT INTO progreso (usuario_id, clave, valor, actualizado) VALUES (?, ?, ?, ?)
       ON CONFLICT (usuario_id, clave) DO UPDATE SET valor = excluded.valor, actualizado = excluded.actualizado
       WHERE excluded.actualizado > progreso.actualizado`,
    ).bind(u.id, e.clave, valor, cuando));
  }
  if (consultas.length) await env.DB.batch(consultas);
  return json({ entradas: await todas(env, u.id) });
}

async function todas(env: Entorno, usuario: number): Promise<Entrada[]> {
  const r = await env.DB.prepare("SELECT clave, valor, actualizado FROM progreso WHERE usuario_id = ? ORDER BY clave")
    .bind(usuario).all<{ clave: string; valor: string; actualizado: number }>();
  return r.results.map((f) => ({ clave: f.clave, valor: JSON.parse(f.valor), actualizado: f.actualizado }));
}
