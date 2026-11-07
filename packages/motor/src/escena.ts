// Motor v2 de Ket Cero: una escena es DATOS (JSON) y este runtime la dibuja en SVG, paso a paso.
// Python (o cualquier lenguaje) escribe la escena; el sitio solo la muestra. Especificación: packages/motor/ESCENA.md
//
// Reglas de dibujo que vienen del curso:
//  - los números van en casillas: coral si es positivo, verde azulado si es negativo, blanco si es 0, con la
//    intensidad relativa al mayor de su mismo signo y la tinta siempre oscura (la casilla es «papel» también en
//    modo oscuro);
//  - las fórmulas llegan ya compiladas por LaTeX como trazos SVG (sin fuentes) y toman el color del texto;
//  - todo lo demás usa los colores del sitio (variables CSS), así el modo oscuro sale solo.

export const FORMATO = "ketcero-escena";
export const VERSION = 1;

export type Valor = number | null; // null: casilla vacía (todavía no calculada)

export interface Matriz {
  id: string; tipo: "matriz"; x: number; y: number;
  valores: Valor[][];
  celda?: number;          // lado de cada casilla (por omisión 28)
  decimales?: number;      // por omisión 2
  numeros?: boolean;       // escribir el número dentro (por omisión true)
  etiqueta?: string;       // texto encima de la matriz
  visible?: boolean;
}
export interface Marco {
  id: string; tipo: "marco"; sobre: string;  // id de la matriz
  fila: number; col: number; filas: number; cols: number;
  visible?: boolean;
}
export interface Texto {
  id: string; tipo: "texto"; x: number; y: number; texto: string;
  tam?: number; peso?: 400 | 500 | 600; ancla?: "start" | "middle" | "end"; tono?: "tinta" | "gris"; mono?: boolean;
  visible?: boolean;
}
export interface Formula {
  id: string; tipo: "formula"; x: number; y: number;  // (x, y) = inicio de la línea base
  tex: string;                                        // la fuente, para leer y para buscar
  svg: { vb: string; cuerpo: string; ancho: number; alto: number; base: number }; // compilada por LaTeX
  visible?: boolean;
}
export interface Flecha { id: string; tipo: "flecha"; de: [number, number]; a: [number, number]; visible?: boolean }

export type Objeto = Matriz | Marco | Texto | Formula | Flecha;

/** Un cambio cambia campos de un objeto. `celdas` cambia casillas sueltas de una matriz: [fila, col, valor]. */
export type Cambio = { id: string; celdas?: [number, number, Valor][] } & Partial<Record<string, unknown>>;

export interface Paso { titulo: string; texto?: string; cambios: Cambio[] }

export interface Escena {
  formato: typeof FORMATO; version: number;
  titulo: string; credito?: string;
  lienzo: { ancho: number; alto: number };
  objetos: Objeto[];
  pasos: Paso[];
}

// ---------------------------------------------------------------- validación y estado (sin DOM, se prueba en Node)

export function validarEscena(e: any): string[] {
  const p: string[] = [];
  if (e?.formato !== FORMATO) p.push(`formato debe ser «${FORMATO}»`);
  if (e?.version !== VERSION) p.push(`versión ${e?.version} no soportada (este runtime lee la ${VERSION})`);
  if (!(e?.lienzo?.ancho > 0 && e?.lienzo?.alto > 0)) p.push("lienzo.ancho y lienzo.alto deben ser positivos");
  const ids = new Set<string>();
  for (const o of e?.objetos ?? []) {
    if (!o?.id) p.push("un objeto no tiene id");
    else if (ids.has(o.id)) p.push(`id repetido: ${o.id}`);
    ids.add(o?.id);
    if (!["matriz", "marco", "texto", "formula", "flecha"].includes(o?.tipo)) p.push(`${o?.id}: tipo desconocido «${o?.tipo}»`);
    if (o?.tipo === "matriz" && (!Array.isArray(o.valores) || o.valores.some((f: unknown) => !Array.isArray(f) || (f as unknown[]).length !== o.valores[0].length)))
      p.push(`${o.id}: valores debe ser una matriz rectangular`);
  }
  for (const o of e?.objetos ?? []) if (o?.tipo === "marco" && !ids.has(o.sobre)) p.push(`${o.id}: la matriz «${o.sobre}» no existe`);
  if (!Array.isArray(e?.pasos) || e.pasos.length === 0) p.push("la escena necesita al menos un paso");
  (e?.pasos ?? []).forEach((paso: Paso, i: number) => {
    if (!paso?.titulo) p.push(`paso ${i + 1}: falta el título`);
    for (const c of paso?.cambios ?? []) if (!ids.has(c.id)) p.push(`paso ${i + 1}: cambia «${c.id}», que no existe`);
  });
  return p;
}

const copiar = <T>(x: T): T => JSON.parse(JSON.stringify(x));

/** Estado de todos los objetos después de aplicar los pasos 0 … k (los cambios se acumulan). */
export function estadoEn(e: Escena, k: number): Map<string, Objeto> {
  const estado = new Map(copiar(e.objetos).map((o) => [o.id, o]));
  for (let i = 0; i <= k && i < e.pasos.length; i++) {
    for (const c of e.pasos[i].cambios) {
      const o = estado.get(c.id) as any;
      const { id: _id, celdas, ...resto } = c;
      Object.assign(o, copiar(resto));
      if (celdas) for (const [f, col, v] of celdas) o.valores[f][col] = v;
    }
  }
  return estado;
}

/** Color de una casilla con la regla del curso: escala por signo, coral (+) y verde azulado (−). */
export function colorCasilla(v: Valor, maxPos: number, maxNeg: number): string {
  if (v === null) return "none";
  const CORAL = [216, 90, 48], TEAL = [29, 158, 117];
  const t = v > 0 ? (maxPos ? v / maxPos : 0) : v < 0 ? (maxNeg ? -v / maxNeg : 0) : 0;
  const base = v >= 0 ? CORAL : TEAL;
  const k = 0.08 + 0.72 * Math.min(1, t); // nunca del todo saturado: el número tiene que leerse
  const c = base.map((b) => Math.round(255 + (b - 255) * (v === 0 ? 0 : k)));
  return `rgb(${c[0]},${c[1]},${c[2]})`;
}

export function numero(v: number, d = 2): string {
  const t = Math.abs(v).toFixed(d);
  return (v < 0 && +t !== 0 ? "−" : "") + t.replace(".", ",");
}

// ---------------------------------------------------------------- dibujo

const NS = "http://www.w3.org/2000/svg";
function el<K extends keyof SVGElementTagNameMap>(padre: Element, tag: K, attrs: Record<string, string | number> = {}, texto?: string) {
  const e = document.createElementNS(NS, tag);
  for (const k in attrs) e.setAttribute(k, String(attrs[k]));
  if (texto != null) e.textContent = texto;
  padre.appendChild(e);
  return e;
}

export interface Control { ir(k: number): void; paso(): number; total: number; destruir(): void }

export function montarEscena(caja: HTMLElement, escena: Escena, inicio = 0): Control {
  const problemas = validarEscena(escena);
  if (problemas.length) throw new Error("Escena inválida:\n- " + problemas.join("\n- "));
  const { ancho, alto } = escena.lienzo;
  caja.classList.add("kc-escena");
  caja.replaceChildren();

  const svg = el(caja as unknown as Element, "svg", { viewBox: `0 0 ${ancho} ${alto}`, role: "img", "aria-label": escena.titulo, class: "kc-lienzo" }) as SVGSVGElement;
  const capa = el(svg, "g");
  const panel = document.createElement("div");
  panel.className = "kc-panel";
  panel.innerHTML = `<div class="kc-nav"><button type="button" data-ant>← Anterior</button><span class="kc-cuenta" aria-live="polite"></span><button type="button" data-sig>Siguiente →</button></div>
<h2 class="kc-titulo"></h2><p class="kc-texto"></p>${escena.credito ? `<p class="kc-credito"></p>` : ""}`;
  caja.appendChild(panel);
  if (escena.credito) panel.querySelector(".kc-credito")!.textContent = escena.credito;

  // un <g> por objeto, creado una vez; cada paso solo actualiza atributos (así las transiciones CSS se ven)
  const nodos = new Map<string, SVGGElement>();
  const orden = [...escena.objetos].sort((a, b) => Number(a.tipo === "marco") - Number(b.tipo === "marco"));
  for (const o of orden) nodos.set(o.id, el(capa, "g", { "data-id": o.id, class: `kc-${o.tipo}` }));

  let actual = -1;
  const ir = (k: number) => {
    k = Math.max(0, Math.min(escena.pasos.length - 1, k));
    const estado = estadoEn(escena, k);
    for (const o of estado.values()) pintar(nodos.get(o.id)!, o, estado);
    actual = k;
    const p = escena.pasos[k];
    panel.querySelector(".kc-titulo")!.textContent = p.titulo;
    panel.querySelector(".kc-texto")!.textContent = p.texto ?? "";
    panel.querySelector(".kc-cuenta")!.textContent = `Paso ${k + 1} de ${escena.pasos.length}`;
    (panel.querySelector("[data-ant]") as HTMLButtonElement).disabled = k === 0;
    (panel.querySelector("[data-sig]") as HTMLButtonElement).disabled = k === escena.pasos.length - 1;
    caja.dataset.paso = String(k);
  };

  panel.querySelector("[data-ant]")!.addEventListener("click", () => ir(actual - 1));
  panel.querySelector("[data-sig]")!.addEventListener("click", () => ir(actual + 1));
  const teclas = (ev: KeyboardEvent) => {
    if ((ev.target as HTMLElement)?.closest?.("input, textarea, [contenteditable]")) return;
    if (ev.key === "ArrowRight") { ir(actual + 1); ev.preventDefault(); }
    else if (ev.key === "ArrowLeft") { ir(actual - 1); ev.preventDefault(); }
    else if (ev.key === "0" && (ev.ctrlKey || ev.metaKey)) { zoom = { x: 0, y: 0, w: ancho, h: alto }; ponerZoom(); ev.preventDefault(); }
  };
  document.addEventListener("keydown", teclas);

  // Ctrl + rueda acerca el dibujo alrededor del cursor; doble clic vuelve al tamaño normal.
  let zoom = { x: 0, y: 0, w: ancho, h: alto };
  const ponerZoom = () => svg.setAttribute("viewBox", `${zoom.x} ${zoom.y} ${zoom.w} ${zoom.h}`);
  svg.addEventListener("wheel", (ev) => {
    if (!ev.ctrlKey) return;
    ev.preventDefault();
    const r = svg.getBoundingClientRect();
    const px = zoom.x + ((ev.clientX - r.left) / r.width) * zoom.w;
    const py = zoom.y + ((ev.clientY - r.top) / r.height) * zoom.h;
    const f = Math.exp(ev.deltaY * 0.0015);
    const w = Math.min(ancho, Math.max(ancho / 12, zoom.w * f));
    const h = (w / ancho) * alto;
    zoom = { x: px - ((px - zoom.x) / zoom.w) * w, y: py - ((py - zoom.y) / zoom.h) * h, w, h };
    zoom.x = Math.max(0, Math.min(ancho - w, zoom.x));
    zoom.y = Math.max(0, Math.min(alto - h, zoom.y));
    ponerZoom();
  }, { passive: false });
  svg.addEventListener("dblclick", () => { zoom = { x: 0, y: 0, w: ancho, h: alto }; ponerZoom(); });

  ir(inicio);
  return { ir, paso: () => actual, total: escena.pasos.length, destruir: () => { document.removeEventListener("keydown", teclas); caja.replaceChildren(); } };
}

function pintar(g: SVGGElement, o: Objeto, estado: Map<string, Objeto>) {
  g.style.opacity = o.visible === false ? "0" : "1";
  g.setAttribute("aria-hidden", String(o.visible === false));
  switch (o.tipo) {
    case "matriz": return pintarMatriz(g, o);
    case "marco": {
      const m = estado.get(o.sobre) as Matriz;
      const c = m.celda ?? 28;
      g.style.transform = `translate(${m.x + o.col * c}px, ${m.y + o.fila * c}px)`;
      // dos bordes: un halo del color del texto (se ve sobre el fondo) y uno oscuro (se ve sobre las casillas claras)
      if (!g.querySelector("rect")) { el(g, "rect", { class: "kc-marco-halo" }); el(g, "rect", { class: "kc-marco-borde" }); }
      for (const r of g.querySelectorAll("rect")) { r.setAttribute("width", String(o.cols * c)); r.setAttribute("height", String(o.filas * c)); }
      return;
    }
    case "texto": {
      let t = g.querySelector("text");
      if (!t) t = el(g, "text");
      t.setAttribute("x", String(o.x));
      t.setAttribute("y", String(o.y));
      t.setAttribute("font-size", String(o.tam ?? 18));
      t.setAttribute("font-weight", String(o.peso ?? 400));
      t.setAttribute("text-anchor", o.ancla ?? "start");
      t.setAttribute("class", `kc-t-${o.tono ?? "tinta"}${o.mono ? " kc-mono" : ""}`);
      t.textContent = o.texto;
      return;
    }
    case "formula": {
      if (g.dataset.tex !== o.tex) {
        g.replaceChildren();
        const s = el(g, "svg", { viewBox: o.svg.vb, width: o.svg.ancho, height: o.svg.alto, overflow: "visible" });
        s.innerHTML = o.svg.cuerpo; // trazos generados por LaTeX en la exportación (no viene del usuario)
        const titulo = el(g, "title", {}, o.tex);
        g.insertBefore(titulo, s);
        g.dataset.tex = o.tex;
      }
      g.style.transform = `translate(${o.x}px, ${o.y - o.svg.base}px)`;
      return;
    }
    case "flecha": {
      let l = g.querySelector("line");
      if (!l) l = el(g, "line", { class: "kc-flecha-linea", "marker-end": "url(#kc-punta)" });
      asegurarPunta(g.ownerSVGElement!);
      l.setAttribute("x1", String(o.de[0])); l.setAttribute("y1", String(o.de[1]));
      l.setAttribute("x2", String(o.a[0])); l.setAttribute("y2", String(o.a[1]));
      return;
    }
  }
}

function asegurarPunta(svg: SVGSVGElement) {
  if (svg.querySelector("#kc-punta")) return;
  const defs = el(svg, "defs");
  const m = el(defs, "marker", { id: "kc-punta", viewBox: "0 0 10 10", refX: 9, refY: 5, markerWidth: 7, markerHeight: 7, orient: "auto-start-reverse" });
  el(m, "path", { d: "M0,0 L10,5 L0,10 z", class: "kc-flecha-punta" });
}

function pintarMatriz(g: SVGGElement, m: Matriz) {
  const c = m.celda ?? 28, d = m.decimales ?? 2, conNumeros = m.numeros !== false;
  const filas = m.valores.length, cols = m.valores[0]?.length ?? 0;
  g.style.transform = `translate(${m.x}px, ${m.y}px)`;
  // el número más largo tiene que caber en la casilla: la letra se achica si hace falta
  let largo = 1;
  for (const fila of m.valores) for (const v of fila) if (v !== null) largo = Math.max(largo, numero(v, d).length);
  const letra = Math.min(c * 0.34, (c * 0.9) / (largo * 0.6));
  if (g.dataset.forma !== `${filas}x${cols}x${c}`) {
    g.replaceChildren();
    if (m.etiqueta) el(g, "text", { x: 0, y: -10, class: "kc-t-gris kc-mono", "font-size": 14 }, m.etiqueta);
    for (let f = 0; f < filas; f++)
      for (let k = 0; k < cols; k++) {
        const r = el(g, "rect", { x: k * c, y: f * c, width: c, height: c, class: "kc-casilla" });
        r.dataset.f = String(f); r.dataset.c = String(k);
        if (conNumeros) el(g, "text", { x: k * c + c / 2, "text-anchor": "middle", "dominant-baseline": "central", class: "kc-num" });
      }
    el(g, "rect", { x: 0, y: 0, width: cols * c, height: filas * c, class: "kc-borde" });
    g.dataset.forma = `${filas}x${cols}x${c}`;
  }
  let maxPos = 0, maxNeg = 0;
  for (const fila of m.valores) for (const v of fila) if (v !== null) { if (v > maxPos) maxPos = v; if (-v > maxNeg) maxNeg = -v; }
  const casillas = g.querySelectorAll<SVGRectElement>("rect.kc-casilla");
  const textos = g.querySelectorAll<SVGTextElement>("text.kc-num");
  let i = 0;
  for (let f = 0; f < filas; f++)
    for (let k = 0; k < cols; k++, i++) {
      const v = m.valores[f][k];
      casillas[i].setAttribute("fill", v === null ? "none" : colorCasilla(v, maxPos, maxNeg));
      casillas[i].classList.toggle("kc-vacia", v === null);
      if (conNumeros) {
        textos[i].textContent = v === null ? "" : numero(v, d);
        textos[i].setAttribute("font-size", letra.toFixed(1));
        textos[i].setAttribute("y", String(f * c + c / 2));
      }
    }
}

/** Estilos del runtime: usan las variables del sitio (--tinta, --gris, --linea, --fondo), así sirve en claro y oscuro. */
export const ESTILOS = `
.kc-escena { display:block; }
.kc-escena .kc-lienzo { width:100%; height:auto; display:block; border:1px solid var(--linea); background:var(--fondo); touch-action:pan-y; }
.kc-escena g { transition:transform .45s ease, opacity .35s ease; }
.kc-escena .kc-casilla { stroke:rgba(0,0,0,.12); stroke-width:.6; transition:fill .35s ease; }
.kc-escena .kc-casilla.kc-vacia { stroke:var(--linea); stroke-dasharray:2 2; }
.kc-escena .kc-borde { fill:none; stroke:var(--gris); stroke-width:1; }
.kc-escena .kc-num { fill:#1A1A1A; font-family:"IBM Plex Mono", monospace; }
.kc-escena .kc-marco-halo { fill:none; stroke:var(--tinta); stroke-width:6; }
.kc-escena .kc-marco-borde { fill:none; stroke:#1A1A1A; stroke-width:2.5; }
.kc-escena .kc-t-tinta { fill:var(--tinta); font-family:"IBM Plex Sans", sans-serif; }
.kc-escena .kc-t-gris { fill:var(--gris); font-family:"IBM Plex Sans", sans-serif; }
.kc-escena .kc-mono { font-family:"IBM Plex Mono", monospace; }
.kc-escena .kc-formula { color:var(--tinta); }
.kc-escena .kc-flecha-linea { stroke:var(--gris); stroke-width:1.5; }
.kc-escena .kc-flecha-punta { fill:var(--gris); }
.kc-escena .kc-panel { margin-top:14px; }
.kc-escena .kc-nav { display:flex; align-items:center; gap:18px; font:13px "IBM Plex Mono", monospace; color:var(--gris); }
.kc-escena .kc-nav button { font:14px "IBM Plex Sans", sans-serif; color:var(--tinta); background:none; border:1px solid var(--linea); padding:7px 14px; cursor:pointer; }
.kc-escena .kc-nav button:hover:not(:disabled) { border-color:var(--tinta); }
.kc-escena .kc-nav button:disabled { opacity:.4; cursor:default; }
.kc-escena .kc-titulo { font:600 19px "IBM Plex Sans", sans-serif; margin:16px 0 6px; color:var(--tinta); }
.kc-escena .kc-texto { margin:0; color:var(--texto); max-width:760px; }
.kc-escena .kc-credito { margin:16px 0 0; font:12px "IBM Plex Mono", monospace; color:var(--gris); }
@media (prefers-reduced-motion: reduce) { .kc-escena g, .kc-escena .kc-casilla { transition:none; } }
`;
