// Datos que comparten todas las páginas: cursos con sus temas numerados, lecciones publicadas en orden y
// direcciones con huella (?v=) de los archivos que arma herramientas/recursos.py.
import { getCollection, type CollectionEntry } from "astro:content";
import recursos from "../generado/recursos.json";

export const DOMINIO = "https://ketcero.com";
export const AUTOR = "Omar Ramírez González";
// Cloudflare Web Analytics: el token del panel (ver notas/PASOS_GOOGLE_Y_ANALITICA.md); vacío = sin analítica
export const ANALITICA = "";

type Recursos = {
  lecciones: Record<string, { url: string; pagina: string; peso_mb: number; miniatura: string; clip: string | null }>;
  versiones: Record<string, string>;
};
const R = recursos as Recursos;

/** Dirección pública con ?v=<huella>, para que el navegador la guarde un año y aun así vea los cambios. */
export function v(ruta: string): string {
  const h = R.versiones[ruta];
  if (!h) throw new Error(`Falta ${ruta} en recursos.json: corre python herramientas/recursos.py`);
  return `${ruta}?v=${h}`;
}

export type Leccion = CollectionEntry<"lecciones">["data"] & {
  url: string;
  pagina: string;
  miniaturaUrl: string;
  clipBase: string | null;
};
export type Item = { numero: string; titulo: string; leccion?: Leccion };
export type Tema = { clave: string; titulo: string; descripcion: string; t: number; items: Item[]; publicadas: number };
export type Curso = CollectionEntry<"cursos">["data"] & { temasNum: Tema[]; publicadas: Leccion[] };

let cache: Curso[] | null = null;

export async function cursos(): Promise<Curso[]> {
  if (cache) return cache;
  const lecciones = new Map((await getCollection("lecciones")).map((e) => [e.data.slug, e.data]));
  const lista = (await getCollection("cursos")).map((e) => e.data);
  cache = lista.map((c) => {
    const publicadas: Leccion[] = [];
    const temasNum = c.temas.map((tema, i) => {
      const t = i + 1;
      const items: Item[] = tema.lecciones.map((l, j) => {
        const numero = `${t}.${j + 1}`;
        if ("slug" in l) {
          const d = lecciones.get(l.slug);
          if (!d) throw new Error(`La lección ${l.slug} del curso ${c.slug} no existe en contenido/lecciones`);
          const r = R.lecciones[l.slug];
          if (!r) throw new Error(`La lección ${l.slug} no está armada: corre python herramientas/recursos.py`);
          const leccion: Leccion = { ...d, numero, url: r.url, pagina: r.pagina, miniaturaUrl: r.miniatura, clipBase: r.clip };
          publicadas.push(leccion);
          return { numero, titulo: d.titulo, leccion };
        }
        return { numero, titulo: l.titulo };
      });
      return { clave: tema.clave, titulo: tema.titulo, descripcion: tema.descripcion, t, items, publicadas: items.filter((x) => x.leccion).length };
    });
    return { ...c, temasNum, publicadas };
  });
  return cache;
}

export function todasPublicadas(lista: Curso[]): Leccion[] {
  return lista.flatMap((c) => c.publicadas);
}

export function ld(objeto: unknown): string {
  return '<script type="application/ld+json">\n' + JSON.stringify(objeto, null, 1) + "\n</script>\n";
}
