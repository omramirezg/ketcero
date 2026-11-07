// Lee un ejercicio de Ket Cero (un .py con secciones «# === nombre ===»). Es la misma lectura que ejercicios.py,
// para que el sitio, las pruebas locales y el paquete de Python vean exactamente el mismo ejercicio.

export interface Ejercicio {
  id: string;
  titulo: string;
  enunciado: string[];
  inicial: string;
  solucion: string;
  errores: Record<string, string>;
  pruebas: string;
}

const SECCION = /^# === (.+?) ===\s*$/;

export function leerEjercicio(texto: string, id: string): Ejercicio {
  const secciones: Record<string, string> = {};
  let actual: string | null = null;
  let lineas: string[] = [];
  const cerrar = () => {
    if (actual) secciones[actual] = lineas.join("\n").replace(/^\n+|\n+$/g, "") + "\n";
  };
  for (const linea of texto.replace(/\r\n/g, "\n").split("\n")) {
    const m = SECCION.exec(linea);
    if (m) {
      cerrar();
      actual = m[1];
      lineas = [];
    } else lineas.push(linea);
  }
  cerrar();
  for (const s of ["titulo", "enunciado", "inicial", "solucion", "pruebas"])
    if (!(s in secciones)) throw new Error(`El ejercicio ${id} no tiene la sección «${s}»`);
  const comentario = (s: string) =>
    s.trim().split("\n").map((l) => (l.startsWith("# ") ? l.slice(2) : l.replace(/^#+/, "")));
  const errores: Record<string, string> = {};
  for (const [k, v] of Object.entries(secciones)) if (k.startsWith("error: ")) errores[k.slice(7)] = v;
  return {
    id,
    titulo: comentario(secciones.titulo).join(" ").trim(),
    enunciado: comentario(secciones.enunciado).filter((p) => p.trim()),
    inicial: secciones.inicial,
    solucion: secciones.solucion,
    errores,
    pruebas: secciones.pruebas,
  };
}

/** Texto del enunciado con `código` → <code>código</code>, escapando todo lo demás. */
export function enunciadoHtml(parrafo: string): string {
  const esc = (s: string) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  return parrafo
    .split("`")
    .map((trozo, i) => (i % 2 ? `<code>${esc(trozo)}</code>` : esc(trozo)))
    .join("");
}
