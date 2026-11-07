"""Arnés de corrección de Ket Cero: corre el código del estudiante y las pruebas ocultas de un ejercicio.

Corre igual en el navegador (Pyodide, dentro de un Web Worker) y en un computador (CPython), así las pruebas
locales (`ketcero comprobar`, vitest) dan exactamente lo mismo que el sitio.

Las pruebas de cada ejercicio son funciones `prueba_*(ns)` que reciben el espacio de nombres del estudiante y,
si algo no cuadra, lanzan `Falla(mensaje, esperado=…, obtenido=…)`. La primera línea del docstring es el nombre
que ve el estudiante.
"""
import json, math, traceback

try:
    import numpy as np
except ImportError:  # el arnés funciona sin NumPy para ejercicios que no lo usan
    np = None


class Falla(Exception):
    def __init__(self, mensaje, esperado=None, obtenido=None):
        super().__init__(mensaje)
        self.mensaje, self.esperado, self.obtenido = mensaje, esperado, obtenido


def mostrar(v):
    if np is not None and isinstance(v, np.ndarray):
        return np.array2string(np.round(v, 4), separator=", ")
    if isinstance(v, float):
        return f"{v:.6g}"
    return repr(v)


def cerca(obtenido, esperado, que, tol=1e-4):
    """Falla si `obtenido` no está a menos de `tol` (relativa) de `esperado`. Sirve para números y arreglos."""
    if obtenido is None:
        raise Falla(f"{que}: tu función devolvió None. ¿Te faltó el return?", mostrar(esperado), "None")
    if np is not None and (isinstance(esperado, np.ndarray) or isinstance(obtenido, np.ndarray)):
        o, e = np.asarray(obtenido, dtype=float), np.asarray(esperado, dtype=float)
        if o.shape != e.shape:
            raise Falla(f"{que}: la forma no coincide", str(e.shape), str(o.shape))
        if not np.allclose(o, e, rtol=tol, atol=tol):
            raise Falla(f"{que}: los números no coinciden", mostrar(e), mostrar(o))
        return
    try:
        o = float(obtenido)
    except (TypeError, ValueError):
        raise Falla(f"{que}: se esperaba un número", mostrar(esperado), mostrar(obtenido))
    if math.isnan(o) or not math.isclose(o, float(esperado), rel_tol=tol, abs_tol=tol):
        raise Falla(f"{que}: el número no coincide", mostrar(float(esperado)), mostrar(o))


def funcion(ns, nombre):
    f = ns.get(nombre)
    if not callable(f):
        raise Falla(f"No encuentro la función «{nombre}». Revisa que la definas con ese nombre exacto.")
    return f


def ultima_linea_error(e):
    pila = traceback.format_exception_only(type(e), e)
    return pila[-1].strip()


def corregir(codigo, pruebas):
    """Devuelve una lista de resultados: {nombre, ok, mensaje, esperado, obtenido}."""
    ns = {"__name__": "estudiante"}
    try:
        exec(compile(codigo, "tu_codigo.py", "exec"), ns)
    except Exception as e:  # el código ni siquiera corre
        return [{"nombre": "Tu código corre sin errores", "ok": False,
                 "mensaje": "Python se detuvo: " + ultima_linea_error(e), "esperado": None, "obtenido": None}]
    return correr_pruebas(ns, pruebas)


def correr_pruebas(ns, pruebas):
    """Corre las pruebas contra un espacio de nombres que ya existe (en un cuaderno: globals())."""
    entorno = {"np": np, "Falla": Falla, "cerca": cerca, "funcion": funcion, "math": math}
    exec(compile(pruebas, "pruebas.py", "exec"), entorno)
    resultados = []
    for nombre, f in entorno.items():
        if not (nombre.startswith("prueba_") and callable(f)):
            continue
        titulo = (f.__doc__ or nombre).strip().split("\n")[0]
        try:
            f(ns)
            resultados.append({"nombre": titulo, "ok": True, "mensaje": "", "esperado": None, "obtenido": None})
        except Falla as falla:
            resultados.append({"nombre": titulo, "ok": False, "mensaje": falla.mensaje,
                               "esperado": falla.esperado, "obtenido": falla.obtenido})
        except Exception as e:
            resultados.append({"nombre": titulo, "ok": False, "mensaje": "Tu función lanzó un error: " + ultima_linea_error(e),
                               "esperado": None, "obtenido": None})
    return resultados


def corregir_json(codigo, pruebas):
    return json.dumps(corregir(codigo, pruebas), ensure_ascii=False)


def imprimir(resultados):
    """Muestra los resultados como texto (para Colab, VS Code y la terminal)."""
    bien = sum(r["ok"] for r in resultados)
    for r in resultados:
        print(("Pasa     " if r["ok"] else "No pasa  ") + r["nombre"])
        if not r["ok"]:
            print("         " + r["mensaje"])
            if r["esperado"] is not None:
                print("         Esperado:      " + str(r["esperado"]))
            if r["obtenido"] is not None:
                print("         Tu código dio: " + str(r["obtenido"]))
    print()
    print(f"Pasa {bien} de {len(resultados)} pruebas.")
    return bien == len(resultados)
