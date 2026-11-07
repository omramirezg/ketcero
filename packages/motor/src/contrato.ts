// Contrato entre el sitio y las animaciones.
//
// 1) Animaciones del curso (A4, B1, U0, U1…): son páginas HTML completas que genera Python en la carpeta del curso.
//    El sitio NO las modifica por dentro; en la preconstrucción (herramientas/recursos.py) les agrega unas pocas
//    líneas fijas y las publica en /ia/<tema>/<archivo sin .html>:
//      - <html data-kc-leccion="<slug>" [data-kc-fotos | data-kc-fotos="jpeg"]>
//      - <script src="/kc/temprano.js"> al comienzo del <head> (alto de la cabecera, tema, «Cargando…»)
//      - meta de la lección (título, descripción, canonical, og) y /kc/fuentes.css + /kc/capa.css
//      - <script src="/kc/capa.js"> al final del <body> (cabecera, modo oscuro, zoom, seguir donde quedaste)
//      - todo `innerHeight` del motor pasa a `(innerHeight - KC_ALTO)`, y el marco baja KC_ALTO píxeles
//    Requisito para el motor del curso: usar `innerHeight` exactamente 3 veces y mover el marco con
//    `m.style.top = ((innerHeight …`. Si el motor cambia eso, recursos.py lo avisa y no publica.
//    Si una animación pesa más de 25 MB, sus datos grandes (`const X = {…};`) salen a <archivo>_datos/X_k.js.
//
// 2) Escenas del motor v2 (ver escena.ts): datos declarativos que dibuja el runtime de este paquete.

/** Cómo se trata una animación del curso al publicarla. */
export interface AnimacionDelCurso {
  /** Ruta dentro de la carpeta del curso (Propuesta_2026/…/Animacion_X.html). */
  fuente: string;
  /** Fotos reales: true = toda imagen conserva sus colores en modo oscuro; "jpeg" = solo las JPEG. */
  fotos: boolean | "jpeg";
}

/** Lo que la capa (/kc/capa.js) sabe de cada lección: va en KC_LECCIONES. */
export interface LeccionEnCapa {
  titulo: string;
  numero: string;
  pagina: string;
  animacion: string;
  anterior: { titulo: string; pagina: string } | null;
  siguiente: { titulo: string; pagina: string } | null;
}

/** Datos reales de la animación de portada «El cero que aprende» (los escribe entrenar_cero.py). */
export interface DatosCero {
  indice_prueba: number;
  etiqueta: number;
  filtro_principal: number;
  /** Imagen 28 × 28 con valores entre 0 y 1. */
  entrada: number[][];
  /** Los 6 filtros 5 × 5 de la primera capa. */
  filtros: number[][][];
  sesgos: number[];
  /** Los 6 mapas 24 × 24 (antes de ReLU). */
  mapas: number[][][];
  /** Salida softmax de las 10 clases. */
  probabilidades: number[];
}

export interface OpcionesCero {
  /** Contenedor del panel de código en vivo (en celular no se pasa). */
  codigo?: HTMLElement | null;
}
