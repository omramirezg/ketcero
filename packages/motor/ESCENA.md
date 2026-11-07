# Escenas de Ket Cero (motor v2) · formato `ketcero-escena`, versión 1

Una escena es **solo datos** (JSON). Python la escribe (`ketcero.escena`), el sitio la dibuja en SVG con
`montarEscena()` de `src/escena.ts`. Las animaciones del curso que ya existen (A4, B1, U0, U1) siguen siendo
páginas completas generadas en la carpeta del curso; este formato es para las nuevas, y para poder probarlas,
validarlas y versionarlas como datos.

## Forma

```jsonc
{
  "formato": "ketcero-escena",
  "version": 1,
  "titulo": "El cero que aprende: un filtro recorre la imagen",
  "credito": "Animación hecha por Omar Ramírez González para el curso de Deep Learning",
  "lienzo": { "ancho": 1600, "alto": 900 },      // unidades del dibujo (el SVG se escala al ancho de la página)
  "objetos": [ /* todo lo que aparece en algún momento, con su estado inicial */ ],
  "pasos":   [ /* cada paso cambia campos de algunos objetos */ ]
}
```

### Objetos

Todos llevan `id` (único) y `visible` (por omisión `true`; el exportador de Python los crea ocultos).

| tipo | campos | se dibuja como |
|---|---|---|
| `matriz` | `x, y, valores` (filas × columnas, `null` = casilla vacía), `celda` (28), `decimales` (2), `numeros` (true), `etiqueta` | casillas con el número adentro; coral si es positivo, verde azulado si es negativo, blanco si es 0, con intensidad relativa al mayor **de su mismo signo**; tinta siempre oscura |
| `marco` | `sobre` (id de una matriz), `fila, col, filas, cols` | un rectángulo sobre esas casillas (la ventana de una convolución, la casilla que se llena) |
| `texto` | `x, y, texto`, `tam` (18), `peso`, `ancla`, `tono` (`tinta`·`gris`), `mono` | texto con la letra del sitio |
| `formula` | `x, y` (inicio de la línea base), `tex` (fuente LaTeX), `svg: {vb, cuerpo, ancho, alto, base}` | trazos compilados por LaTeX (sin fuentes) que toman el color del texto |
| `flecha` | `de: [x, y]`, `a: [x, y]` | una línea con punta |

### Pasos

```jsonc
{ "titulo": "La ventana en la fila 11, columna 20",
  "texto": "Se pone el filtro encima de la imagen…",
  "cambios": [
    { "id": "ventana", "visible": true, "fila": 11, "col": 20 },   // cualquier campo del objeto
    { "id": "z", "celdas": [[11, 20, 1.772]] }                       // casillas sueltas de una matriz: [fila, col, valor]
  ] }
```

Los cambios **se acumulan**: el estado en el paso *k* es el estado inicial más los cambios de los pasos 0 … *k*
(`estadoEn(escena, k)`). Por eso se puede saltar a cualquier paso y volver atrás sin efectos raros.

## Reglas (vienen del curso)

- Una operación por paso. Cuando hay una cuenta, la cuenta se ve con sus números reales.
- Fórmulas y cuentas en LaTeX de verdad (`Escena.formula`, `Escena.nueva_formula`), nunca texto plano.
- Coma decimal y signo menos tipográfico en los números de las casillas.
- Nada de colores en el texto: solo las casillas (por signo) llevan color.
- Datos reales: el exportador del cero comprueba que cada casilla calculada coincide con el mapa del entrenamiento.

## Lo que hace el runtime

- Dibuja en un `<svg>` con `viewBox` = lienzo; cada objeto es un `<g>` que se crea una vez y se actualiza en
  cada paso (los movimientos y apariciones tienen transición; se apagan con `prefers-reduced-motion`).
- Navegación: botones «Anterior / Siguiente», flechas del teclado, `?paso=N` en la dirección de la página.
- Zoom: Ctrl + rueda acerca alrededor del cursor; doble clic o Ctrl + 0 vuelve al tamaño normal.
- Modo oscuro sin código aparte: todo usa `--tinta`, `--gris`, `--linea`, `--fondo` del sitio; las casillas son
  «papel» (claras con tinta oscura) en los dos modos.
- `validarEscena()` (TypeScript) y `ketcero.escena.validar()` (Python) aplican las mismas reglas; las pruebas
  comprueban que los dos aceptan la escena exportada.

## Ejemplo

```bash
python herramientas/exportar_escena_cero.py      # → apps/web/public/escenas/el-cero-que-aprende.json
npm run build && python herramientas/servidor_local.py 8890
# http://localhost:8890/escenas/el-cero-que-aprende/   (borrador, sin enlazar, noindex)
```

## Lo que falta para la versión 2 del formato

- Pilas de mapas (las hojas oblicuas de las animaciones de convolución) como tipo propio.
- Reacomodos animados (flatten / reshape: los números vuelan uno por uno).
- Panel de código sincronizado con los pasos (como el de la portada).
