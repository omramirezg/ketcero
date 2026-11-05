# Ket Cero · Ciencia desde cero

Sitio de [ketcero.com](https://ketcero.com): animaciones que muestran la ciencia por dentro. Un proyecto de Omar Ramírez González.

## Carpetas

- `sitio/`: lo que se publica en Cloudflare Pages (páginas, estilo, ícono y animaciones).
- `herramientas/construir.py`: copia las animaciones desde la carpeta del curso y genera las páginas, el `sitemap.xml` y el `robots.txt`.

## Actualizar el sitio

1. Agrega o cambia animaciones en `CATALOGO`, dentro de `herramientas/construir.py`.
2. Corre `python herramientas/construir.py`.
3. Sube los cambios a GitHub: Cloudflare Pages publica solo.

Ningún archivo puede pasar de 25 MB (límite de Cloudflare). Si una animación pesa más, el script saca sus datos grandes a `<animación>_datos/*.js` en pedazos de 15 MB, que la página carga antes de su código.

## Publicar en Cloudflare (una sola vez)

El sitio se publica como **Worker con archivos estáticos**: `wrangler.jsonc` le dice a Cloudflare que sirva la carpeta `sitio/`.

1. En Cloudflare: **Compute → Workers & Pages → Create → Import a repository** y elige `omramirezg/ketcero`.
2. Configuración:
   - Build command: *(vacío)*
   - Deploy command: `npx wrangler deploy`
3. Cuando termine, en el Worker: **Settings → Domains & Routes → Add → Custom domain → `ketcero.com`** (y también `www.ketcero.com`).
