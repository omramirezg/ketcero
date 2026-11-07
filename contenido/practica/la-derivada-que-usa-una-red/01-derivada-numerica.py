# === titulo ===
# La derivada, con números
# === enunciado ===
# Escribe `derivada(f, x, h)`: la pendiente de `f` en el punto `x`, calculada solo con dos evaluaciones de `f`.
# Usa la diferencia centrada: evalúa un poquito a la derecha, `f(x + h)`, un poquito a la izquierda, `f(x - h)`, resta y divide por la distancia entre los dos puntos, que es `2 * h`.
# Para comprobar a mano: con `f(x) = x²` y `x = 3`, la pendiente debe dar 6.
# === inicial ===
def derivada(f, x, h=1e-5):
    # f(x + h) es la altura un poquito a la derecha; f(x - h), un poquito a la izquierda
    return 0.0
# === solucion ===
def derivada(f, x, h=1e-5):
    return (f(x + h) - f(x - h)) / (2 * h)
# === error: dividir por h en vez de 2h ===
def derivada(f, x, h=1e-5):
    return (f(x + h) - f(x - h)) / h
# === error: no dividir ===
def derivada(f, x, h=1e-5):
    return f(x + h) - f(x - h)
# === pruebas ===
def prueba_cuadrado(ns):
    """La pendiente de x² en x = 3 es 6"""
    d = funcion(ns, "derivada")
    cerca(d(lambda x: x * x, 3.0), 6.0, "derivada(x², 3)")


def prueba_seno(ns):
    """La pendiente de sen(x) en x = 0 es cos(0) = 1"""
    d = funcion(ns, "derivada")
    cerca(d(math.sin, 0.0), 1.0, "derivada(sen, 0)")


def prueba_otro_punto(ns):
    """Funciona en cualquier punto: x³ en x = −2 da 12"""
    d = funcion(ns, "derivada")
    cerca(d(lambda x: x ** 3, -2.0), 12.0, "derivada(x³, −2)")
