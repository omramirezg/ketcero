// Progreso en el navegador. Siempre se guarda primero aquí (localStorage), con o sin cuenta y con o sin red.
// Si la API está prendida (PUBLIC_API_ACTIVA=si al construir) y el estudiante entró con su correo, se sincroniza
// con /api/progreso: cada entrada lleva la hora en que cambió y gana la más reciente.

export interface Entrada { clave: string; valor: unknown; actualizado: number }

const LLAVE = "ketcero:progreso";
export const API_ACTIVA = import.meta.env.PUBLIC_API_ACTIVA === "si";

export function leerLocal(): Record<string, Entrada> {
  try { return JSON.parse(localStorage.getItem(LLAVE) ?? "{}"); } catch { return {}; }
}

function escribirLocal(todo: Record<string, Entrada>) {
  try { localStorage.setItem(LLAVE, JSON.stringify(todo)); } catch { /* sin almacenamiento: no pasa nada */ }
}

export function guardar(clave: string, valor: unknown, cuando = Date.now()) {
  const todo = leerLocal();
  todo[clave] = { clave, valor, actualizado: cuando };
  escribirLocal(todo);
  void sincronizar();
}

export function mezclar(local: Record<string, Entrada>, remotas: Entrada[]): Record<string, Entrada> {
  const r = { ...local };
  for (const e of remotas) if (!r[e.clave] || r[e.clave].actualizado < e.actualizado) r[e.clave] = e;
  return r;
}

let enCurso: Promise<void> | null = null;

/** Sube lo local y baja lo remoto. Sin API o sin sesión no hace nada. */
export function sincronizar(): Promise<void> {
  if (!API_ACTIVA) return Promise.resolve();
  if (enCurso) return enCurso;
  enCurso = (async () => {
    try {
      const r = await fetch("/api/progreso", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ entradas: Object.values(leerLocal()).slice(-200) }),
      });
      if (!r.ok) return; // 401: no ha entrado; sigue todo en local
      const { entradas } = (await r.json()) as { entradas: Entrada[] };
      escribirLocal(mezclar(leerLocal(), entradas));
      document.dispatchEvent(new CustomEvent("ketcero:progreso"));
    } catch { /* sin red: se intenta la próxima vez */ } finally { enCurso = null; }
  })();
  return enCurso;
}

export async function quienSoy(): Promise<string | null> {
  if (!API_ACTIVA) return null;
  try {
    const r = await fetch("/api/yo");
    return r.ok ? ((await r.json()) as { correo: string }).correo : null;
  } catch { return null; }
}

export async function pedirEnlace(correo: string): Promise<{ ok: boolean; mensaje: string; enlace?: string }> {
  try {
    const r = await fetch("/api/acceso/enlace", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ correo, volver: location.pathname }),
    });
    const j = (await r.json()) as { error?: string; enlace_de_prueba?: string };
    if (!r.ok) return { ok: false, mensaje: j.error ?? "No se pudo mandar el enlace" };
    return { ok: true, mensaje: `Te mandamos un enlace a ${correo}. Ábrelo en este mismo navegador.`, enlace: j.enlace_de_prueba };
  } catch {
    return { ok: false, mensaje: "Sin conexión. Tu progreso sigue guardado en este navegador." };
  }
}

export async function salir() {
  try { await fetch("/api/acceso/salir", { method: "POST" }); } catch { /* nada */ }
}
