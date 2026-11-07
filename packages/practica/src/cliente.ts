// En el navegador: monta cada <section class="ejercicio"> de la página con un editor CodeMirror 6 y el botón
// «Comprobar», que corre el código del estudiante y las pruebas en Pyodide dentro de un Web Worker.
import { EditorState } from "@codemirror/state";
import { EditorView, keymap, lineNumbers, highlightActiveLine, drawSelection } from "@codemirror/view";
import { defaultKeymap, history, historyKeymap, indentWithTab } from "@codemirror/commands";
import { indentUnit, syntaxHighlighting, HighlightStyle, bracketMatching } from "@codemirror/language";
import { python } from "@codemirror/lang-python";
import { tags as t } from "@lezer/highlight";

export interface Resultado { nombre: string; ok: boolean; mensaje: string; esperado: string | null; obtenido: string | null }

const CARGA_MS = 90_000; // la primera vez se baja Pyodide y NumPy (unos 15 MB)
const CORRER_MS = 10_000; // un ciclo infinito no puede colgar la página

// Colores de VS Code (Dark+ / Light+) tomados de variables CSS, así cambian con el interruptor de tema.
const colores = HighlightStyle.define([
  { tag: [t.keyword, t.controlKeyword, t.operatorKeyword, t.definitionKeyword, t.moduleKeyword], color: "var(--c-clave)" },
  { tag: [t.function(t.variableName), t.function(t.propertyName), t.function(t.definition(t.variableName))], color: "var(--c-funcion)" },
  { tag: [t.className, t.namespace], color: "var(--c-modulo)" },
  { tag: [t.variableName, t.propertyName, t.definition(t.variableName)], color: "var(--c-var)" },
  { tag: [t.number, t.bool, t.null], color: "var(--c-num)" },
  { tag: [t.string, t.special(t.string)], color: "var(--c-cadena)" },
  { tag: t.comment, color: "var(--c-com)" },
]);

const aspecto = EditorView.theme({
  "&": { fontSize: "13.5px", border: "1px solid var(--linea)", backgroundColor: "var(--fondo)", color: "var(--c-texto)" },
  "&.cm-focused": { outline: "1px solid var(--gris)" },
  ".cm-content": { fontFamily: '"IBM Plex Mono", monospace', padding: "10px 0", caretColor: "var(--tinta)" },
  ".cm-gutters": { backgroundColor: "var(--fondo)", color: "var(--gris)", border: "0", fontFamily: '"IBM Plex Mono", monospace' },
  ".cm-activeLine, .cm-activeLineGutter": { backgroundColor: "var(--marca)" },
  "&.cm-focused .cm-selectionBackground, .cm-selectionBackground": { backgroundColor: "var(--seleccion) !important" },
  ".cm-cursor": { borderLeftColor: "var(--tinta)" },
});

// ---------- el trabajador (uno por página, se crea al primer «Comprobar») ----------
let trabajador: Worker | null = null;
let listo: Promise<void> | null = null;
let siguiente = 1;

function matar() { trabajador?.terminate(); trabajador = null; listo = null; }

function nuevoTrabajador(): Promise<void> {
  trabajador = new Worker(new URL("./trabajador.ts", import.meta.url), { type: "module" });
  const w = trabajador;
  return new Promise<void>((resolver, rechazar) => {
    const reloj = setTimeout(() => { matar(); rechazar(new Error("Python tardó demasiado en cargar. Revisa tu conexión y vuelve a intentarlo.")); }, CARGA_MS);
    w.onmessage = (e) => {
      if (e.data.tipo === "listo") { clearTimeout(reloj); resolver(); }
      else if (e.data.tipo === "error") { clearTimeout(reloj); matar(); rechazar(new Error("No se pudo cargar Python: " + e.data.mensaje)); }
    };
    w.onerror = (e) => { clearTimeout(reloj); matar(); rechazar(new Error("No se pudo cargar Python: " + e.message)); };
    w.postMessage({ tipo: "cargar" });
  });
}

export async function corregir(codigo: string, pruebas: string): Promise<Resultado[]> {
  if (!listo) listo = nuevoTrabajador();
  await listo;
  const w = trabajador!;
  const id = siguiente++;
  return new Promise((resolver, rechazar) => {
    const reloj = setTimeout(() => {
      matar();
      rechazar(new Error(`Tu código lleva más de ${CORRER_MS / 1000} segundos corriendo. ¿Hay un ciclo que nunca termina? Lo detuve; corrígelo y vuelve a comprobar.`));
    }, CORRER_MS);
    w.onmessage = (e) => {
      if (e.data.id !== id) return;
      clearTimeout(reloj);
      if (e.data.tipo === "resultado") resolver(e.data.resultados);
      else rechazar(new Error(e.data.mensaje));
    };
    w.postMessage({ tipo: "corregir", id, codigo, pruebas });
  });
}

// ---------- cada ejercicio ----------
function guardado(clave: string): string | null { try { return localStorage.getItem(clave); } catch { return null; } }
function guardar(clave: string, v: string | null) {
  try { if (v === null) localStorage.removeItem(clave); else localStorage.setItem(clave, v); } catch { /* sin almacenamiento */ }
}

function pintar(lista: HTMLOListElement, resultados: Resultado[]) {
  lista.replaceChildren();
  for (const r of resultados) {
    const li = document.createElement("li");
    li.className = r.ok ? "pasa" : "falla";
    const marca = document.createElement("span");
    marca.className = "marca-prueba";
    marca.textContent = r.ok ? "Pasa" : "No pasa";
    const nombre = document.createElement("span");
    nombre.textContent = r.nombre;
    li.append(marca, nombre);
    if (!r.ok) {
      const det = document.createElement("div");
      det.className = "detalle";
      det.textContent = r.mensaje;
      if (r.esperado !== null || r.obtenido !== null) {
        const tabla = document.createElement("dl");
        for (const [k, v] of [["Esperado", r.esperado], ["Tu código dio", r.obtenido]] as const) {
          if (v === null) continue;
          const dt = document.createElement("dt"); dt.textContent = k;
          const dd = document.createElement("dd"); dd.textContent = v;
          tabla.append(dt, dd);
        }
        det.append(tabla);
      }
      li.append(det);
    }
    lista.append(li);
  }
}

export function montarEjercicio(caja: HTMLElement) {
  const datos = JSON.parse(caja.querySelector<HTMLScriptElement>("script[type='application/json']")!.textContent!);
  const clave = `ketcero:practica:${datos.leccion}/${datos.id}`;
  const lugar = caja.querySelector<HTMLElement>(".editor")!;
  const estado = caja.querySelector<HTMLElement>(".estado")!;
  const lista = caja.querySelector<HTMLOListElement>(".resultados")!;
  const boton = caja.querySelector<HTMLButtonElement>("[data-comprobar]")!;
  const reiniciar = caja.querySelector<HTMLButtonElement>("[data-reiniciar]")!;

  lugar.replaceChildren(); // quita el <pre> que se ve sin JavaScript
  const vista = new EditorView({
    parent: lugar,
    state: EditorState.create({
      doc: guardado(clave) ?? datos.inicial,
      extensions: [
        lineNumbers(), history(), drawSelection(), highlightActiveLine(), bracketMatching(),
        indentUnit.of("    "), python(), syntaxHighlighting(colores), aspecto,
        keymap.of([...defaultKeymap, ...historyKeymap, indentWithTab,
          { key: "Mod-Enter", run: () => { boton.click(); return true; } }]),
        EditorView.contentAttributes.of({ "aria-label": `Editor de Python: ${datos.titulo}` }),
        EditorView.updateListener.of((u) => { if (u.docChanged) guardar(clave, u.state.doc.toString()); }),
      ],
    }),
  });
  boton.disabled = false;
  reiniciar.disabled = false;

  boton.addEventListener("click", async () => {
    boton.disabled = true;
    estado.textContent = trabajador ? "Corriendo las pruebas…" : "Cargando Python en tu navegador (solo la primera vez, unos segundos)…";
    try {
      const res = await corregir(vista.state.doc.toString(), datos.pruebas);
      pintar(lista, res);
      const bien = res.filter((r) => r.ok).length;
      estado.textContent = bien === res.length ? `Pasa las ${res.length} pruebas.` : `Pasa ${bien} de ${res.length} pruebas.`;
      caja.dataset.resuelto = String(bien === res.length);
      caja.dispatchEvent(new CustomEvent("ketcero:comprobado", { bubbles: true, detail: { leccion: datos.leccion, id: datos.id, bien, total: res.length } }));
    } catch (e) {
      lista.replaceChildren();
      estado.textContent = (e as Error).message;
    } finally {
      boton.disabled = false;
    }
  });

  reiniciar.addEventListener("click", () => {
    if (!confirm("¿Borrar tu código y volver al inicial?")) return;
    vista.dispatch({ changes: { from: 0, to: vista.state.doc.length, insert: datos.inicial } });
    guardar(clave, null);
    lista.replaceChildren();
    estado.textContent = "";
    delete caja.dataset.resuelto;
  });
}

export function montarTodos(raiz: ParentNode = document) {
  raiz.querySelectorAll<HTMLElement>("section.ejercicio").forEach(montarEjercicio);
}
