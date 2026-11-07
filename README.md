# Ket Cero · Ciencia desde cero

Sitio de [ketcero.com](https://ketcero.com): animaciones que muestran la ciencia por dentro y ejercicios que se
comprueban en el navegador. Un proyecto de Omar Ramírez González.

## Carpetas

- `apps/web/`: el sitio en Astro (páginas estáticas). `npm run build` deja todo en `apps/web/dist/`, que es lo que
  se publica.
- `apps/api/`: Worker con D1 para cuentas, progreso y cursos de pago. **Apagado**: no se despliega (ver su README).
- `contenido/`: el temario (`cursos/*.json`), una página `.mdx` por lección, las rutas (`rutas.json`) y la
  práctica (`practica/<lección>.mdx` + un `.py` por ejercicio con enunciado, código inicial, solución y pruebas).
- `packages/motor/`: la portada («El cero que aprende»), el contrato con las animaciones del curso y el motor v2
  de escenas (`ESCENA.md`).
- `packages/practica/`: editor CodeMirror y Pyodide en un Web Worker para los ejercicios.
- `packages/ketcero-py/`: el paquete de pip `ketcero` (listar, descargar y comprobar ejercicios) y el arnés de
  corrección que usan el sitio, los cuadernos y la terminal.
- `herramientas/`: scripts de Python que corren **en el computador** (no en Cloudflare).
- `sitio/` y `herramientas/construir.py`: el generador anterior, de referencia. Lo publicado ya no sale de aquí.

## Actualizar el sitio

1. Animaciones nuevas o cambiadas: agrega la lección en `contenido/` (o corre `python herramientas/migrar_temario.py`
   si cambió el TEMARIO de `construir.py`) y después `npm run recursos`. Ese paso lee la carpeta del curso, copia
   las animaciones a `apps/web/public/ia/`, hace miniaturas y cuadernos, y se sube a GitHub con lo demás
   (Cloudflare no ve la carpeta del curso).
2. `npm run build` y `python herramientas/servidor_local.py 8890` para mirarlo en http://localhost:8890.
3. `npm test` corre todas las pruebas (TypeScript y Python).
4. Sube los cambios a GitHub: Cloudflare construye y publica solo.

Ningún archivo puede pasar de 25 MB (límite de Cloudflare). Si una animación pesa más, `recursos.py` saca sus datos
grandes a `<animación>_datos/*.js` en pedazos de 15 MB, que la página carga antes de su código.

## Publicar en Cloudflare

El sitio es un **Worker con archivos estáticos**: `wrangler.jsonc` le dice a Cloudflare que sirva `apps/web/dist/`.

- Build command: `npm ci && npm run build`
- Deploy command: `npx wrangler deploy`
- Versión de Node: la de `.node-version`.

Dominio: en el Worker, **Settings → Domains & Routes → Add → Custom domain → `ketcero.com`** (y `www.ketcero.com`).
