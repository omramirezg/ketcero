"""Arma un cuaderno .ipynb por ejercicio de práctica, para abrirlo en Colab, en vscode.dev o descargarlo.

Cada cuaderno trae: el enunciado, la celda con el código inicial y una celda «Comprobar» con el mismo arnés y las
mismas pruebas que corre el sitio en el navegador. Así el resultado es idéntico en los tres lugares.

Salida: apps/web/public/practica/<lección>/<ejercicio>.ipynb (se guardan en el repositorio, porque Colab y
vscode.dev los abren directo desde GitHub).

Uso:  python herramientas/cuadernos.py
"""
import glob, io, json, os, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "packages", "practica", "src"))
import ejercicios  # noqa: E402

ARNES = io.open(os.path.join(REPO, "packages", "practica", "src", "arnes.py"), encoding="utf-8").read()
SALIDA = os.path.join(REPO, "apps", "web", "public", "practica")


def lineas(texto):
    partes = texto.rstrip("\n").split("\n")
    return [l + "\n" for l in partes[:-1]] + [partes[-1]]


def md(texto):
    return {"cell_type": "markdown", "metadata": {}, "source": lineas(texto)}


def codigo(texto, **meta):
    return {"cell_type": "code", "execution_count": None, "metadata": meta, "outputs": [], "source": lineas(texto)}


def cuaderno(leccion, e):
    enunciado = "\n\n".join(e["enunciado"])
    celdas = [
        md(f"# {e['titulo']}\n\n{enunciado}\n\nEscribe tu código en la celda de abajo y después corre la celda "
           f"«Comprobar». Es el mismo ejercicio de https://ketcero.com/practica/{leccion}/"),
        codigo(e["inicial"]),
        md("## Comprobar\n\nCorre esta celda después de la tuya. Revisa tu función con las mismas pruebas del sitio."),
        codigo("#@title Comprobar (no hace falta leer este código)\n" + ARNES.rstrip() + "\n\n"
               + "PRUEBAS = " + repr(e["pruebas"]) + "\n\n"
               + "imprimir(correr_pruebas(globals(), PRUEBAS))\n", cellView="form"),
    ]
    return {"cells": celdas, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                                          "language_info": {"name": "python"}, "colab": {"provenance": []}},
            "nbformat": 4, "nbformat_minor": 5}


def main():
    hechos = 0
    for carpeta in sorted(d for d in glob.glob(os.path.join(REPO, "contenido", "practica", "*")) if os.path.isdir(d)):
        leccion = os.path.basename(carpeta)
        destino = os.path.join(SALIDA, leccion)
        os.makedirs(destino, exist_ok=True)
        for e in ejercicios.de_leccion(carpeta):
            with io.open(os.path.join(destino, e["id"] + ".ipynb"), "w", encoding="utf-8", newline="\n") as f:
                json.dump(cuaderno(leccion, e), f, ensure_ascii=False, indent=1)
                f.write("\n")
            hechos += 1
    print(f"{hechos} cuadernos en {os.path.relpath(SALIDA, REPO)}")


if __name__ == "__main__":
    main()
