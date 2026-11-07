"""Exporta «El cero que aprende» como escena del motor v2 (formato ketcero-escena, versión 1).

Lee los datos reales de la portada (apps/web/public/js/cero_datos.js: el 0 de MNIST, el filtro principal de conv1,
su sesgo y su mapa) y arma una escena paso a paso: la imagen, el filtro, la ventana que recorre la imagen con la
cuenta de cada casilla en LaTeX, y el mapa que se llena fila por fila. Antes de escribir, comprueba que cada
casilla calculada aquí coincide con el mapa que guardó el entrenamiento.

Salida: apps/web/public/escenas/el-cero-que-aprende.json
Uso:    python herramientas/exportar_escena_cero.py
"""
import io, json, os, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "packages", "ketcero-py", "src"))
from ketcero.escena import Escena  # noqa: E402

DATOS = os.path.join(REPO, "apps", "web", "public", "js", "cero_datos.js")
SALIDA = os.path.join(REPO, "apps", "web", "public", "escenas", "el-cero-que-aprende.json")
CREDITO = "Animación hecha por Omar Ramírez González para el curso de Deep Learning"


def leer_datos():
    texto = io.open(DATOS, encoding="utf-8").read()
    return json.loads(texto[texto.index("{"):texto.rindex("}") + 1])


def conv(x, w, b, i, j):
    k = len(w)
    return sum(x[i + a][j + c] * w[a][c] for a in range(k) for c in range(k)) + b


def tex_num(v, d=3):
    t = f"{abs(v):.{d}f}".replace(".", "{,}")
    return ("-" if v < 0 and float(f"{abs(v):.{d}f}") else "") + t


def armar():
    D = leer_datos()
    f = D["filtro_principal"]
    x, w, b, mapa = D["entrada"], D["filtros"][f], D["sesgos"][f], D["mapas"][f]
    n, k = len(x), len(w)
    m = n - k + 1

    calculado = [[conv(x, w, b, i, j) for j in range(m)] for i in range(m)]
    peor = max(abs(calculado[i][j] - mapa[i][j]) for i in range(m) for j in range(m))
    if peor > 0.01:
        raise SystemExit(f"La cuenta no coincide con el mapa del entrenamiento (diferencia {peor:.4f}).")

    e = Escena("El cero que aprende: un filtro recorre la imagen", ancho=1600, alto=900, credito=CREDITO)
    e.matriz("x", 40, 80, x, celda=22, decimales=1, etiqueta=f"x · el 0 escrito a mano · {n} × {n}")
    e.matriz("w", 720, 120, w, celda=46, decimales=2, etiqueta=f"w · filtro {f + 1} de conv1 · {k} × {k}")
    e.texto("sesgo", 720, 400, f"b = {tex_num(b).replace('{,}', ',')}", tam=18, mono=True)
    e.matriz("z", 1036, 80, [[None] * m for _ in range(m)], celda=22, decimales=1, etiqueta=f"z · mapa de salida · {m} × {m}")
    e.marco("ventana", "x", 0, 0, k, k)
    e.marco("casilla", "z", 0, 0, 1, 1)
    e.formula("regla", 40, 780, r"z_{i,j} = \sum_{a=0}^{4}\sum_{c=0}^{4} x_{i+a,\,j+c}\; w_{a,c} \;+\; b", tam=24)
    e.formula("cuenta", 40, 850, r"z_{0,0} = 0", tam=24)

    e.paso("Un cero escrito a mano",
           f"Es la imagen {D['indice_prueba']} del conjunto de prueba de MNIST: {n} × {n} píxeles, cada uno entre 0 (negro) "
           "y 1 (blanco). Con Ctrl + rueda del mouse puedes acercarte para leer los números.",
           e.mostrar("x"))
    e.paso("El filtro que aprendió la red",
           f"La primera capa tiene 6 filtros de {k} × {k}. Este es el {f + 1}: 25 pesos y un sesgo b, todos aprendidos "
           "durante el entrenamiento. Coral es positivo, verde azulado es negativo.",
           e.mostrar("w", "sesgo"))
    e.paso("La salida empieza vacía",
           f"El filtro cabe en {m} posiciones por fila y {m} por columna, así que la salida es de {m} × {m}. "
           "Cada casilla sale de una sola cuenta.",
           e.mostrar("z", "regla"))

    # tres casillas en cámara lenta: la primera, la más positiva y la más negativa
    todas = [(i, j) for i in range(m) for j in range(m)]
    elegidas = [(0, 0), max(todas, key=lambda p: calculado[p[0]][p[1]]), min(todas, key=lambda p: calculado[p[0]][p[1]])]
    llenas = set()
    for n_caso, (i, j) in enumerate(elegidas):
        suma = calculado[i][j] - b
        e.paso(f"La ventana en la fila {i}, columna {j}",
               "Se pone el filtro encima de la imagen, se multiplica cada píxel por el peso que le queda encima "
               "y se suman los 25 productos.",
               e.mostrar("ventana", "cuenta"),
               e.cambiar("ventana", fila=i, col=j),
               e.nueva_formula("cuenta", rf"z_{{{i},{j}}} = \underbrace{{{tex_num(suma)}}}_{{\text{{suma de 25 productos}}}} \;+\; ({tex_num(b)})", tam=24))
        texto = ("El resultado va a la misma posición en la salida." if n_caso == 0 else
                 "Es la casilla más alta del mapa: aquí la imagen se parece mucho al patrón del filtro." if n_caso == 1 else
                 "Es la casilla más baja: aquí la imagen es lo contrario del patrón del filtro.")
        e.paso(f"z[{i}, {j}] = {calculado[i][j]:.3f}".replace(".", ","), texto,
               e.mostrar("casilla"),
               e.cambiar("casilla", fila=i, col=j),
               e.nueva_formula("cuenta", rf"z_{{{i},{j}}} = {tex_num(suma)} + ({tex_num(b)}) = {tex_num(calculado[i][j])}", tam=24),
               e.celdas("z", [(i, j, calculado[i][j])]))
        llenas.add((i, j))

    # fila por fila: primero la fila 0 completa, después bloques de filas
    bloques = [range(0, 1), range(1, 6), range(6, 12), range(12, 18), range(18, m)]
    for r in bloques:
        nuevas = [(i, j, calculado[i][j]) for i in r for j in range(m) if (i, j) not in llenas]
        ultima = r[-1]
        e.paso(f"Filas {r[0]} a {ultima}" if len(r) > 1 else f"La fila {r[0]} completa",
               "La ventana avanza una casilla a la derecha; al llegar al borde baja una fila y vuelve a empezar. "
               "Es el doble for de la convolución.",
               e.cambiar("ventana", fila=ultima, col=m - 1),
               e.cambiar("casilla", fila=ultima, col=m - 1),
               e.nueva_formula("cuenta", rf"z_{{{ultima},{m - 1}}} = {tex_num(calculado[ultima][m - 1])}", tam=24),
               e.celdas("z", nuevas))
        llenas.update((i, j) for i, j, _ in nuevas)

    e.paso("El mapa completo",
           f"Las {m * m} casillas, cada una con la misma cuenta. Donde el mapa es coral, la imagen tiene el patrón que "
           "busca el filtro; donde es verde azulado, tiene el contrario. La red mira estos mapas, no los píxeles.",
           e.ocultar("ventana", "casilla", "cuenta"))
    return e


def main():
    e = armar()
    e.guardar(SALIDA)
    print(f"{len(e.datos['pasos'])} pasos → {os.path.relpath(SALIDA, REPO)} ({os.path.getsize(SALIDA) / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
