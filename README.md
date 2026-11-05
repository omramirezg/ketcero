# Ket Cero · Ciencia desde cero

Sitio de [ketcero.com](https://ketcero.com): animaciones que muestran la ciencia por dentro. Un proyecto de Omar Ramírez González.

## Carpetas

- `sitio/`: lo que se publica en Cloudflare Pages (páginas, estilo, ícono y animaciones).
- `herramientas/construir.py`: copia las animaciones desde la carpeta del curso y genera las páginas, el `sitemap.xml` y el `robots.txt`.

## Actualizar el sitio

1. Agrega o cambia animaciones en `CATALOGO`, dentro de `herramientas/construir.py`.
2. Corre `python herramientas/construir.py`.
3. Sube los cambios a GitHub: Cloudflare Pages publica solo.

Ningún archivo puede pasar de 25 MB (límite de Cloudflare Pages); el script avisa si alguno se pasa.

## Publicar en Cloudflare Pages (una sola vez)

1. Crea un repositorio **público** en GitHub, por ejemplo `ketcero`, y sube esta carpeta.
2. En Cloudflare: **Compute → Workers & Pages → Create → Pages → Connect to Git** y elige el repositorio.
3. Configuración de compilación:
   - Framework preset: **None**
   - Build command: *(vacío)*
   - Build output directory: **`sitio`**
4. Cuando termine, en el proyecto: **Custom domains → Set up a custom domain → `ketcero.com`** (y también `www.ketcero.com`).
