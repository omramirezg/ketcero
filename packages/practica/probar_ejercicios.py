"""Prueba los ejercicios: la solución de referencia pasa todas las pruebas y cada error típico falla al menos una.

Uso:  python packages/practica/probar_ejercicios.py [carpeta_de_ejercicios …]   (sin carpetas: todo contenido/practica)
Escribe un JSON con el resultado (lo lee vitest) y sale con código 1 si algo no cuadra.
"""
import glob, json, os, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), "ketcero-py", "src"))
from ketcero import arnes, ejercicios  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(AQUI))


def main():
    carpetas = sys.argv[1:] or sorted(d for d in glob.glob(os.path.join(RAIZ, "contenido", "practica", "*")) if os.path.isdir(d))
    informe, bien = [], True
    for carpeta in carpetas:
        for e in ejercicios.de_leccion(carpeta):
            sol = arnes.corregir(e["solucion"], e["pruebas"])
            ini = arnes.corregir(e["inicial"], e["pruebas"])
            fila = {"ejercicio": f"{os.path.basename(carpeta)}/{e['id']}", "pruebas": len(sol),
                    "solucion_pasa": all(r["ok"] for r in sol) and len(sol) > 0,
                    "inicial_falla": not all(r["ok"] for r in ini),
                    "errores": {}}
            for nombre, codigo in e["errores"].items():
                res = arnes.corregir(codigo, e["pruebas"])
                fallas = [r for r in res if not r["ok"]]
                fila["errores"][nombre] = {"atrapado": bool(fallas), "mensaje": fallas[0]["mensaje"] if fallas else "",
                                           "esperado": fallas[0]["esperado"] if fallas else None,
                                           "obtenido": fallas[0]["obtenido"] if fallas else None}
            ok = fila["solucion_pasa"] and fila["inicial_falla"] and all(x["atrapado"] for x in fila["errores"].values())
            bien &= ok
            informe.append(fila)
    print(json.dumps(informe, ensure_ascii=False, indent=1))
    sys.exit(0 if bien else 1)


if __name__ == "__main__":
    main()
