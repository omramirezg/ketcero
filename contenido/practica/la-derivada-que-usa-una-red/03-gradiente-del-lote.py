# === titulo ===
# El gradiente de un lote entero
# === enunciado ===
# Ahora sin sigmoide y con muchos ejemplos a la vez: la predicción es `p = w · X + b` (X es un arreglo de NumPy) y la pérdida es el promedio `L = mean((p − Y)²)`.
# Escribe `gradiente_lote(w, b, X, Y)` que devuelva `(∂L/∂w, ∂L/∂b)` para todo el lote, sin un solo `for`: `∂L/∂w = mean(2 · (p − Y) · X)` y `∂L/∂b = mean(2 · (p − Y))`.
# Ojo: es el promedio, no la suma. Con la suma, el gradiente crece con el tamaño del lote.
# === inicial ===
import numpy as np

def gradiente_lote(w, b, X, Y):
    p = w * X + b
    return 0.0, 0.0
# === solucion ===
import numpy as np

def gradiente_lote(w, b, X, Y):
    p = w * X + b
    r = p - Y
    return np.mean(2 * r * X), np.mean(2 * r)
# === error: sumar en vez de promediar ===
import numpy as np

def gradiente_lote(w, b, X, Y):
    r = w * X + b - Y
    return np.sum(2 * r * X), np.sum(2 * r)
# === error: restar al revés ===
import numpy as np

def gradiente_lote(w, b, X, Y):
    r = Y - (w * X + b)
    return np.mean(2 * r * X), np.mean(2 * r)
# === pruebas ===
X = np.array([0.0, 1.0, 2.0, 3.0])
Y = np.array([1.0, 3.0, 5.0, 7.0])


def _ref(w, b, X, Y):
    r = w * X + b - Y
    return float(np.mean(2 * r * X)), float(np.mean(2 * r))


def prueba_dw(ns):
    """∂L/∂w con w = 0,5 y b = 0 sobre 4 ejemplos"""
    r = funcion(ns, "gradiente_lote")(0.5, 0.0, X, Y)
    cerca(r[0], _ref(0.5, 0.0, X, Y)[0], "∂L/∂w")


def prueba_db(ns):
    """∂L/∂b en el mismo punto"""
    r = funcion(ns, "gradiente_lote")(0.5, 0.0, X, Y)
    cerca(r[1], _ref(0.5, 0.0, X, Y)[1], "∂L/∂b")


def prueba_en_el_minimo(ns):
    """En la recta perfecta (w = 2, b = 1) el gradiente es cero"""
    r = funcion(ns, "gradiente_lote")(2.0, 1.0, X, Y)
    cerca(r[0], 0.0, "∂L/∂w en el mínimo")
    cerca(r[1], 0.0, "∂L/∂b en el mínimo")


def prueba_lote_grande(ns):
    """No cambia de escala si el lote se repite 10 veces"""
    XX, YY = np.tile(X, 10), np.tile(Y, 10)
    r = funcion(ns, "gradiente_lote")(0.5, 0.0, XX, YY)
    cerca(r[0], _ref(0.5, 0.0, X, Y)[0], "∂L/∂w con 40 ejemplos")
