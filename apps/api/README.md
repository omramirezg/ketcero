# API de Ket Cero (Worker + D1)

Un Worker de Cloudflare que atiende `/api/*` y deja todo lo demás a los archivos de Astro (`apps/web/dist`).
**No está desplegado.** El sitio publicado usa el `wrangler.jsonc` de la raíz, que solo sirve archivos.

## Qué hace hoy

| Ruta | Para qué |
|---|---|
| `POST /api/acceso/enlace` | `{correo, volver?, turnstile?}` → manda un enlace para entrar (vence en 15 min, un solo uso) |
| `GET /api/acceso/entrar?t=…` | página con un botón «Entrar» (así los antivirus de correo que abren enlaces no lo gastan) |
| `POST /api/acceso/entrar` | valida el enlace, crea la sesión (cookie `kc_sesion`, HttpOnly, 30 días) y vuelve a la página |
| `POST /api/acceso/salir` | borra la sesión |
| `GET /api/yo` | `{correo}` o 401 |
| `GET /api/progreso` · `PUT /api/progreso` | lee o sincroniza `{entradas: [{clave, valor, actualizado}]}`; gana el cambio más reciente |

Seguridad: en D1 solo se guardan hashes SHA-256 de los enlaces y de las sesiones; límite de 5 enlaces por correo
y 20 por IP cada hora; lo que cambia datos solo se acepta desde el mismo origen; `volver` solo admite rutas internas.

## Interruptores (`vars` en `wrangler.jsonc`)

| Variable | Valores | Hoy |
|---|---|---|
| `CORREO_PROVEEDOR` | `consola` (no manda nada, lo escribe en el registro) · `resend` | `consola` |
| `TURNSTILE_ACTIVO` | `si` · `no` | `no` |
| `PAGOS_ACTIVOS` | `si` · `no` | `no` |
| `STREAM_ACTIVO` | `si` · `no` | `no` |

En el sitio, la caja «Guardar tu progreso» solo aparece si se construye con `PUBLIC_API_ACTIVA=si`.
Sin eso, el progreso igual se guarda en el navegador (localStorage).

## Probarlo en el computador

```bash
npm test -w @ketcero/api                       # pruebas con una D1 en memoria (node:sqlite)
cd apps/web && PUBLIC_API_ACTIVA=si npm run build && cd ../api
npx wrangler d1 migrations apply ketcero --local --env local
npx wrangler dev --env local                   # http://localhost:8787 con el sitio y la API
python ../../herramientas/probar_cuentas_navegador.py 8787
```

En local el correo no sale: la API devuelve `enlace_de_prueba` y la página lo muestra como enlace.
