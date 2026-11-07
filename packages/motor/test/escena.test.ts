// Pruebas del motor v2 sin navegador: validación, estado acumulado de los pasos, colores por signo, y que la
// escena exportada desde Python sea válida para este runtime y para el validador de Python a la vez.
import { describe, expect, it } from "vitest";
import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { colorCasilla, estadoEn, numero, validarEscena, type Escena, type Matriz } from "../src/escena";

const RAIZ = resolve(__dirname, "../../..");
const PYTHON = process.env.PYTHON ?? (process.platform === "win32" ? "python" : "python3");

const base = (): Escena => ({
  formato: "ketcero-escena", version: 1, titulo: "prueba", lienzo: { ancho: 100, alto: 100 },
  objetos: [
    { id: "m", tipo: "matriz", x: 0, y: 0, valores: [[1, -2], [null, 0]], visible: false },
    { id: "v", tipo: "marco", sobre: "m", fila: 0, col: 0, filas: 1, cols: 1, visible: false },
  ],
  pasos: [
    { titulo: "uno", cambios: [{ id: "m", visible: true }] },
    { titulo: "dos", cambios: [{ id: "v", visible: true, col: 1 }, { id: "m", celdas: [[1, 0, 5]] }] },
    { titulo: "tres", cambios: [{ id: "v", fila: 1 }] },
  ],
});

describe("validarEscena", () => {
  it("una escena bien hecha no tiene problemas", () => expect(validarEscena(base())).toEqual([]));

  it("encuentra los errores típicos", () => {
    const e: any = base();
    e.version = 2;
    e.objetos.push({ id: "m", tipo: "círculo" });
    e.objetos[1].sobre = "nada";
    e.pasos[0].cambios.push({ id: "fantasma" });
    e.pasos[1].titulo = "";
    const p = validarEscena(e).join("\n");
    expect(p).toMatch(/versión 2/);
    expect(p).toMatch(/id repetido: m/);
    expect(p).toMatch(/tipo desconocido «círculo»/);
    expect(p).toMatch(/la matriz «nada» no existe/);
    expect(p).toMatch(/cambia «fantasma», que no existe/);
    expect(p).toMatch(/paso 2: falta el título/);
  });

  it("rechaza una matriz que no es rectangular", () => {
    const e: any = base();
    e.objetos[0].valores = [[1, 2], [3]];
    expect(validarEscena(e).join()).toMatch(/rectangular/);
  });
});

describe("estadoEn: los cambios se acumulan paso a paso", () => {
  it("paso 0", () => {
    const s = estadoEn(base(), 0);
    expect(s.get("m")!.visible).toBe(true);
    expect(s.get("v")!.visible).toBe(false);
  });
  it("paso 1 cambia campos y casillas sueltas", () => {
    const s = estadoEn(base(), 1);
    expect(s.get("v")).toMatchObject({ visible: true, fila: 0, col: 1 });
    expect((s.get("m") as Matriz).valores).toEqual([[1, -2], [5, 0]]);
  });
  it("paso 2 conserva lo anterior", () => {
    expect(estadoEn(base(), 2).get("v")).toMatchObject({ visible: true, fila: 1, col: 1 });
  });
  it("no cambia la escena original (se puede volver atrás)", () => {
    const e = base();
    estadoEn(e, 2);
    expect((e.objetos[0] as Matriz).valores[1][0]).toBeNull();
  });
});

describe("colores y números", () => {
  it("positivo coral, negativo verde azulado, cero blanco, vacío sin relleno", () => {
    expect(colorCasilla(2, 2, 1)).toBe("rgb(224,123,89)");  // el más alto: 80 % de coral (el número se sigue leyendo)
    expect(colorCasilla(-1, 2, 1)).toBe("rgb(74,177,145)"); // el más negativo: 80 % de verde azulado
    expect(colorCasilla(0, 2, 1)).toBe("rgb(255,255,255)");
    expect(colorCasilla(null, 2, 1)).toBe("none");
  });
  it("cada signo tiene su propia escala", () => {
    // −1 es el más negativo aunque 100 sea mucho más grande: igual sale con el color fuerte
    expect(colorCasilla(-1, 100, 1)).toBe(colorCasilla(-5, 2, 5));
  });
  it("coma decimal y signo menos tipográfico", () => {
    expect(numero(-0.256, 2)).toBe("−0,26");
    expect(numero(-0.001, 2)).toBe("0,00");
    expect(numero(3, 1)).toBe("3,0");
  });
});

describe("la escena exportada desde Python", () => {
  const ruta = join(RAIZ, "apps", "web", "public", "escenas", "el-cero-que-aprende.json");
  const e: Escena = JSON.parse(readFileSync(ruta, "utf-8"));

  it("es válida para el runtime", () => expect(validarEscena(e)).toEqual([]));

  it("Python también la da por válida (los dos validadores dicen lo mismo)", () => {
    const salida = execFileSync(PYTHON, ["-c",
      "import json,sys; sys.path.insert(0,'packages/ketcero-py/src'); from ketcero.escena import validar; " +
      "print(json.dumps(validar(json.load(open(sys.argv[1], encoding='utf-8')))))", ruta], { cwd: RAIZ, encoding: "utf-8" });
    expect(JSON.parse(salida)).toEqual([]);
  });

  it("al final el mapa está completo y sin casillas vacías", () => {
    const z = estadoEn(e, e.pasos.length - 1).get("z") as Matriz;
    expect(z.valores.flat().every((v) => v !== null)).toBe(true);
    expect(z.valores.length).toBe(24);
  });

  it("las fórmulas vienen compiladas y toman el color del texto", () => {
    const f = e.objetos.find((o) => o.tipo === "formula") as any;
    expect(f.svg.cuerpo).toMatch(/currentColor/);
    expect(f.svg.cuerpo).not.toMatch(/#010203/i);
  });
});
