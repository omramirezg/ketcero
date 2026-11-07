"""Arma un cuaderno .ipynb por ejercicio de práctica, para abrirlo en Colab, en vscode.dev o descargarlo.

Cada cuaderno trae: el enunciado, la celda con el código inicial y una celda «Comprobar» con el mismo arnés y las
mismas pruebas que corre el sitio en el navegador. Así el resultado es idéntico en los tres lugares.

Salida (se guardan en el repositorio, porque Colab y vscode.dev los abren directo desde GitHub):
  apps/web/public/practica/<lección>/<ejercicio>.ipynb
  apps/web/public/practica/<lección>/<ejercicio>.json   (enunciado, código inicial y pruebas: lo usa «ketcero descargar»)
  apps/web/public/practica/indice.json                 (lecciones y ejercicios: lo usa «ketcero listar»)

Uso:  python herramientas/cuadernos.py
"""
import glob, io, json, os, re, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "packages", "ketcero-py", "src"))
from ketcero import ejercicios  # noqa: E402

ARNES = io.open(os.path.join(REPO, "packages", "ketcero-py", "src", "ketcero", "arnes.py"), encoding="utf-8").read()
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


def frontmatter(ruta):
    """Lee «clave: valor» del frontmatter de la página .mdx de la lección."""
    if not os.path.exists(ruta):
        return {}
    texto = io.open(ruta, encoding="utf-8").read().split("---")[1]
    return {m.group(1): json.loads(m.group(2)) if m.group(2).startswith('"') else m.group(2)
            for m in re.finditer(r"^(\w+):\s*(.+?)\s*$", texto, re.M)}


def escribir(ruta, datos):
    with io.open(ruta, "w", encoding="utf-8", newline="\n") as f:
        json.dump(datos, f, ensure_ascii=False, indent=1)
        f.write("\n")


def main():
    hechos, indice = 0, []
    for carpeta in sorted(d for d in glob.glob(os.path.join(REPO, "contenido", "practica", "*")) if os.path.isdir(d)):
        leccion = os.path.basename(carpeta)
        fm = frontmatter(carpeta + ".mdx")
        destino = os.path.join(SALIDA, leccion)
        os.makedirs(destino, exist_ok=True)
        lista = []
        for e in ejercicios.de_leccion(carpeta):
            escribir(os.path.join(destino, e["id"] + ".ipynb"), cuaderno(leccion, e))
            escribir(os.path.join(destino, e["id"] + ".json"), {
                "leccion": leccion, "id": e["id"], "titulo": e["titulo"], "enunciado": e["enunciado"],
                "inicial": e["inicial"], "pruebas": e["pruebas"]})  # la solución nunca sale
            lista.append({"id": e["id"], "titulo": e["titulo"]})
            hechos += 1
        indice.append({"slug": leccion, "titulo": fm.get("titulo", leccion), "estado": fm.get("estado", "borrador"),
                       "pagina": f"/practica/{leccion}/", "ejercicios": lista})
    escribir(os.path.join(SALIDA, "indice.json"), {"formato": "ketcero-practica", "version": 1, "lecciones": indice})
    print(f"{hechos} ejercicios (cuaderno + json) e indice.json en {os.path.relpath(SALIDA, REPO)}")


if __name__ == "__main__":
    main()
