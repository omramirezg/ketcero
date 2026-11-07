// Pruebas de los ejercicios de práctica:
//  1. el lector de TypeScript (el que usa el sitio) entiende cada ejercicio igual que el de Python;
//  2. en cada ejercicio la solución de referencia pasa todas las pruebas, el código inicial no,
//     y cada error típico («# === error: … ===») lo atrapa al menos una prueba con un mensaje claro.
// Python corre las pruebas con el mismo arnes.py que usa Pyodide en el navegador.
import { describe, expect, it } from "vitest";
import { execFileSync } from "node:child_process";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, resolve } from "node:path";
import { ejerciciosDeLeccion } from "../src/cargar";
import { enunciadoHtml } from "../src/ejercicios";

const RAIZ = resolve(__dirname, "../../..");
const PRACTICA = join(RAIZ, "contenido", "practica");
const PYTHON = process.env.PYTHON ?? (process.platform === "win32" ? "python" : "python3");
const lecciones = readdirSync(PRACTICA).filter((d) => statSync(join(PRACTICA, d)).isDirectory());

function python(args: string[], entrada?: string): string {
  try {
    return execFileSync(PYTHON, args, { cwd: RAIZ, input: entrada, encoding: "utf-8", env: { ...process.env, PYTHONIOENCODING: "utf-8" } });
  } catch (e: any) {
    if (e.stdout) return e.stdout; // probar_ejercicios sale con 1 si algo falla: igual queremos el informe
    throw e;
  }
}

describe("lector de ejercicios", () => {
  it("hay al menos una lección con ejercicios", () => {
    expect(lecciones.length).toBeGreaterThan(0);
  });

  for (const leccion of lecciones) {
    it(`${leccion}: TypeScript y Python leen lo mismo`, () => {
      const ts = ejerciciosDeLeccion(join(PRACTICA, leccion));
      const py = JSON.parse(python(["-c",
        "import json,sys; sys.path.insert(0,'packages/practica/src'); import ejercicios; " +
        `print(json.dumps(ejercicios.de_leccion(sys.argv[1]), ensure_ascii=False))`, join(PRACTICA, leccion)]));
      expect(ts).toEqual(py);
    });
  }

  it("el enunciado escapa HTML y convierte `código`", () => {
    expect(enunciadoHtml("usa `a < b` y <b>")).toBe("usa <code>a &lt; b</code> y &lt;b&gt;");
  });
});

describe("pruebas ocultas de cada ejercicio", () => {
  const informe: any[] = JSON.parse(python(["packages/practica/probar_ejercicios.py"]));

  for (const fila of informe) {
    describe(fila.ejercicio, () => {
      it("la solución de referencia pasa todas las pruebas", () => {
        expect(fila.pruebas).toBeGreaterThan(0);
        expect(fila.solucion_pasa).toBe(true);
      });
      it("el código inicial todavía no pasa", () => {
        expect(fila.inicial_falla).toBe(true);
      });
      it("tiene al menos un error típico", () => {
        expect(Object.keys(fila.errores).length).toBeGreaterThan(0);
      });
      for (const [nombre, r] of Object.entries<any>(fila.errores)) {
        it(`atrapa el error «${nombre}» con un mensaje`, () => {
          expect(r.atrapado).toBe(true);
          expect(r.mensaje.length).toBeGreaterThan(10);
        });
      }
    });
  }
});

describe("cuadernos para Colab y vscode.dev", () => {
  for (const leccion of lecciones) {
    for (const e of ejerciciosDeLeccion(join(PRACTICA, leccion))) {
      it(`${leccion}/${e.id}.ipynb existe y está al día (si falla: python herramientas/cuadernos.py)`, () => {
        const ruta = join(RAIZ, "apps", "web", "public", "practica", leccion, `${e.id}.ipynb`);
        const nb = JSON.parse(readFileSync(ruta, "utf-8"));
        expect(nb.cells[1].source.join("")).toBe(e.inicial.replace(/\n$/, ""));
        const comprobar = nb.cells[3].source.join("");
        expect(comprobar).toContain("PRUEBAS = ");
        expect(comprobar).not.toContain(e.solucion.trim()); // la solución nunca sale
      });
    }
  }
});

describe("arnés", () => {
  const correr = (codigo: string, pruebas: string) =>
    JSON.parse(python(["-c", "import sys,json; sys.path.insert(0,'packages/practica/src'); import arnes; " +
      "d=json.load(sys.stdin); print(arnes.corregir_json(d['c'], d['p']))"], JSON.stringify({ c: codigo, p: pruebas })));

  it("explica cuando el código ni siquiera corre", () => {
    const r = correr("def f(:\n  pass", "def prueba_x(ns):\n    funcion(ns, 'f')");
    expect(r).toHaveLength(1);
    expect(r[0].ok).toBe(false);
    expect(r[0].mensaje).toMatch(/Python se detuvo: SyntaxError/);
  });

  it("avisa si falta el return", () => {
    const r = correr("def f(x):\n    x * 2", "def prueba_x(ns):\n    \"\"\"Duplica\"\"\"\n    cerca(funcion(ns, 'f')(2), 4, 'f(2)')");
    expect(r[0]).toMatchObject({ nombre: "Duplica", ok: false });
    expect(r[0].mensaje).toMatch(/return/);
  });

  it("avisa si la función no existe", () => {
    const r = correr("def g(x):\n    return x", "def prueba_x(ns):\n    funcion(ns, 'f')");
    expect(r[0].mensaje).toMatch(/No encuentro la función «f»/);
  });

  it("compara arreglos por forma y por valores", () => {
    const pr = "def prueba_x(ns):\n    cerca(funcion(ns, 'f')(), np.array([1.0, 2.0]), 'v')";
    expect(correr("import numpy as np\ndef f():\n    return np.array([1.0, 2.0])", pr)[0].ok).toBe(true);
    expect(correr("import numpy as np\ndef f():\n    return np.array([1.0, 2.0, 3.0])", pr)[0].mensaje).toMatch(/forma/);
    expect(correr("import numpy as np\ndef f():\n    return np.array([1.0, 2.5])", pr)[0].mensaje).toMatch(/números no coinciden/);
  });
});
