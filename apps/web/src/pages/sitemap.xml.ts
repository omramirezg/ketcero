import { DOMINIO, cursos, todasPublicadas } from "../lib/sitio";

export async function GET() {
  const lista = await cursos();
  const lecciones = todasPublicadas(lista);
  const urls = ["/", "/cursos/", ...lista.map((c) => `/cursos/${c.slug}/`), ...lecciones.map((l) => l.pagina), "/rutas/", "/omar/",
    ...lecciones.map((l) => l.url)];
  const hoy = new Date().toISOString().slice(0, 10);
  const xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + urls.map((u) => `<url><loc>${DOMINIO}${u}</loc><lastmod>${hoy}</lastmod></url>\n`).join("") + "</urlset>\n";
  return new Response(xml, { headers: { "Content-Type": "application/xml; charset=utf-8" } });
}
