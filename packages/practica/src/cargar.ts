// Solo en el servidor (Astro, vitest, el generador de cuadernos): lee los ejercicios de una lección del disco.
import { readFileSync, readdirSync } from "node:fs";
import { join, basename } from "node:path";
import { leerEjercicio, type Ejercicio } from "./ejercicios";

export function ejerciciosDeLeccion(carpeta: string): Ejercicio[] {
  return readdirSync(carpeta)
    .filter((f) => f.endsWith(".py"))
    .sort()
    .map((f) => leerEjercicio(readFileSync(join(carpeta, f), "utf-8"), basename(f, ".py")));
}
