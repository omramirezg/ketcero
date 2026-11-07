/// <reference lib="webworker" />
// Web Worker que corre Python en el navegador con Pyodide. Se carga solo cuando el estudiante pulsa «Comprobar»
// por primera vez; si una corrección se pasa del tiempo, la página mata este trabajador y crea otro.
import arnes from "../../ketcero-py/src/ketcero/arnes.py?raw"; // la misma fuente que el paquete de pip

export const PYODIDE = "https://cdn.jsdelivr.net/pyodide/v0.29.4/full/";

type Pedido = { tipo: "corregir"; id: number; codigo: string; pruebas: string };

let listo: Promise<any> | null = null;

function cargar() {
  if (!listo)
    listo = (async () => {
      const { loadPyodide } = await import(/* @vite-ignore */ PYODIDE + "pyodide.mjs");
      const py = await loadPyodide({ indexURL: PYODIDE });
      await py.loadPackage("numpy");
      py.FS.writeFile("/home/pyodide/arnes.py", arnes);
      py.runPython("import sys; sys.path.insert(0, '/home/pyodide'); import arnes");
      return py;
    })();
  return listo;
}

self.onmessage = async (ev: MessageEvent<Pedido | { tipo: "cargar" }>) => {
  const d = ev.data;
  try {
    const py = await cargar();
    if (d.tipo === "cargar") return postMessage({ tipo: "listo" });
    py.globals.set("_codigo", d.codigo);
    py.globals.set("_pruebas", d.pruebas);
    const texto = py.runPython("arnes.corregir_json(_codigo, _pruebas)");
    postMessage({ tipo: "resultado", id: d.id, resultados: JSON.parse(texto) });
  } catch (e) {
    postMessage({ tipo: "error", id: (d as Pedido).id, mensaje: String((e as Error)?.message ?? e) });
  }
};
