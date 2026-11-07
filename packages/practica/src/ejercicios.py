"""Lee los ejercicios de Ket Cero (un .py por ejercicio, con secciones «# === nombre ===»).

Secciones: titulo, enunciado (líneas con «# »), inicial (código que ve el estudiante), solucion (de referencia,
nunca se publica), «error: …» (respuestas equivocadas típicas, para probar que las pruebas las atrapan) y
pruebas (funciones prueba_* que corre el arnés).
"""
import glob, io, os, re

SECCION = re.compile(r"^# === (.+?) ===\s*$")


def leer(ruta):
    secciones, actual, lineas = {}, None, []
    for linea in io.open(ruta, encoding="utf-8").read().split("\n"):
        m = SECCION.match(linea)
        if m:
            if actual:
                secciones[actual] = "\n".join(lineas).strip("\n") + "\n"
            actual, lineas = m.group(1), []
        else:
            lineas.append(linea)
    if actual:
        secciones[actual] = "\n".join(lineas).strip("\n") + "\n"
    texto = lambda s: [l[2:] if l.startswith("# ") else l.lstrip("#") for l in s.strip().split("\n")]
    nombre = os.path.splitext(os.path.basename(ruta))[0]
    return {
        "id": nombre,
        "titulo": " ".join(texto(secciones["titulo"])).strip(),
        "enunciado": [p for p in texto(secciones["enunciado"]) if p.strip()],
        "inicial": secciones["inicial"],
        "solucion": secciones["solucion"],
        "errores": {k[len("error: "):]: v for k, v in secciones.items() if k.startswith("error: ")},
        "pruebas": secciones["pruebas"],
    }


def de_leccion(carpeta):
    return [leer(r) for r in sorted(glob.glob(os.path.join(carpeta, "*.py")))]
