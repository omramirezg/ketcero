# === titulo ===
# La regla de la cadena en una neurona
# === enunciado ===
# Una neurona con un solo peso: `z = w · x + b`, después `a = σ(z)` (la sigmoide) y la pérdida `L = (a − y)²`.
# Escribe `gradiente(w, b, x, y)` que devuelva la pareja `(∂L/∂w, ∂L/∂b)`, eslabón por eslabón:
# `∂L/∂a = 2 · (a − y)`, `∂a/∂z = a · (1 − a)`, `∂z/∂w = x` y `∂z/∂b = 1`. Multiplica los eslabones que van de L hasta cada peso.
# === inicial ===
import math

def sigmoide(z):
    return 1 / (1 + math.exp(-z))

def gradiente(w, b, x, y):
    z = w * x + b
    a = sigmoide(z)
    # ∂L/∂a, ∂a/∂z, y luego ∂L/∂w y ∂L/∂b
    return 0.0, 0.0
# === solucion ===
import math

def sigmoide(z):
    return 1 / (1 + math.exp(-z))

def gradiente(w, b, x, y):
    z = w * x + b
    a = sigmoide(z)
    dL_da = 2 * (a - y)
    da_dz = a * (1 - a)
    return dL_da * da_dz * x, dL_da * da_dz
# === error: olvidar la derivada de la sigmoide ===
import math

def sigmoide(z):
    return 1 / (1 + math.exp(-z))

def gradiente(w, b, x, y):
    a = sigmoide(w * x + b)
    return 2 * (a - y) * x, 2 * (a - y)
# === error: olvidar multiplicar por x ===
import math

def sigmoide(z):
    return 1 / (1 + math.exp(-z))

def gradiente(w, b, x, y):
    a = sigmoide(w * x + b)
    g = 2 * (a - y) * a * (1 - a)
    return g, g
# === pruebas ===
def _referencia(w, b, x, y):
    a = 1 / (1 + math.exp(-(w * x + b)))
    g = 2 * (a - y) * a * (1 - a)
    return g * x, g


def _par(ns, w, b, x, y):
    r = funcion(ns, "gradiente")(w, b, x, y)
    if not isinstance(r, (tuple, list)) or len(r) != 2:
        raise Falla("gradiente debe devolver una pareja (∂L/∂w, ∂L/∂b)", "(número, número)", repr(r))
    return r


def prueba_dw(ns):
    """∂L/∂w en w = 0,5, b = −0,2, x = 2, y = 1"""
    cerca(_par(ns, 0.5, -0.2, 2.0, 1.0)[0], _referencia(0.5, -0.2, 2.0, 1.0)[0], "∂L/∂w")


def prueba_db(ns):
    """∂L/∂b en el mismo punto"""
    cerca(_par(ns, 0.5, -0.2, 2.0, 1.0)[1], _referencia(0.5, -0.2, 2.0, 1.0)[1], "∂L/∂b")


def prueba_otro_ejemplo(ns):
    """Otro ejemplo: w = −1, b = 0,3, x = −1,5, y = 0"""
    r = _par(ns, -1.0, 0.3, -1.5, 0.0)
    e = _referencia(-1.0, 0.3, -1.5, 0.0)
    cerca(r[0], e[0], "∂L/∂w")
    cerca(r[1], e[1], "∂L/∂b")
