# === titulo ===
# Un paso de descenso de gradiente
# === enunciado ===
# El gradiente apunta hacia donde la pérdida SUBE más rápido. Para aprender, la red da un paso pequeño en la dirección contraria: `w ← w − lr · ∂L/∂w` y `b ← b − lr · ∂L/∂b`.
# Escribe `paso(w, b, X, Y, lr)` que devuelva el nuevo `(w, b)`. Ya tienes `gradiente_lote` del ejercicio anterior.
# Para comprobarlo: después de 500 pasos con `lr = 0,05`, la recta debe quedar en `w ≈ 2` y `b ≈ 1`.
# === inicial ===
import numpy as np

def gradiente_lote(w, b, X, Y):
    r = w * X + b - Y
    return np.mean(2 * r * X), np.mean(2 * r)

def paso(w, b, X, Y, lr):
    dL_dw, dL_db = gradiente_lote(w, b, X, Y)
    return w, b
# === solucion ===
import numpy as np

def gradiente_lote(w, b, X, Y):
    r = w * X + b - Y
    return np.mean(2 * r * X), np.mean(2 * r)

def paso(w, b, X, Y, lr):
    dL_dw, dL_db = gradiente_lote(w, b, X, Y)
    return w - lr * dL_dw, b - lr * dL_db
# === error: sumar el gradiente en vez de restarlo ===
import numpy as np

def gradiente_lote(w, b, X, Y):
    r = w * X + b - Y
    return np.mean(2 * r * X), np.mean(2 * r)

def paso(w, b, X, Y, lr):
    dL_dw, dL_db = gradiente_lote(w, b, X, Y)
    return w + lr * dL_dw, b + lr * dL_db
# === pruebas ===
X = np.array([0.0, 1.0, 2.0, 3.0])
Y = np.array([1.0, 3.0, 5.0, 7.0])


def prueba_un_paso(ns):
    """Un paso desde w = 0, b = 0 con lr = 0,1"""
    r = funcion(ns, "paso")(0.0, 0.0, X, Y, 0.1)
    cerca(r[0], 0.0 - 0.1 * float(np.mean(-2 * Y * X)), "w nuevo")
    cerca(r[1], 0.0 - 0.1 * float(np.mean(-2 * Y)), "b nuevo")


def prueba_baja_la_perdida(ns):
    """Después de un paso, la pérdida es más pequeña"""
    w, b = funcion(ns, "paso")(0.0, 0.0, X, Y, 0.05)
    antes = float(np.mean((0.0 * X - Y) ** 2))
    despues = float(np.mean((w * X + b - Y) ** 2))
    if not despues < antes:
        raise Falla("La pérdida subió: el paso va hacia arriba de la colina", f"menor que {antes:.4g}", f"{despues:.4g}")


def prueba_converge(ns):
    """Con 500 pasos llega a la recta w = 2, b = 1"""
    p = funcion(ns, "paso")
    w, b = 0.0, 0.0
    for _ in range(500):
        w, b = p(w, b, X, Y, 0.05)
    cerca(w, 2.0, "w después de 500 pasos", tol=1e-2)
    cerca(b, 1.0, "b después de 500 pasos", tol=1e-2)
