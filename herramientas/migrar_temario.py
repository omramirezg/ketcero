"""Pasa el TEMARIO de construir.py a contenido/ (formato del sitio nuevo en Astro).

Uso:  python herramientas/migrar_temario.py
Escribe contenido/cursos/deep-learning.json (temas, orden y lecciones en preparación) y una lección .mdx por cada
lección publicada. Si la lección ya existe, actualiza sus metadatos y conserva el texto que tenga debajo.
Mientras el sitio publicado siga saliendo de construir.py, corre esto después de cambiar su TEMARIO.
"""
import io, json, os, re, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "herramientas"))
import construir as c  # noqa: E402

CONTENIDO = os.path.join(RAIZ, "contenido")
# Qué hay que haber visto antes de cada lección (el sitio arma con esto «Antes de esta lección»).
PRERREQUISITOS = {
    "la-cnn-completa": [],
    "mini-yolo-digitos-en-la-calle": ["la-cnn-completa"],
    "tipos-de-segmentacion": [],
    "unet-edificios-en-fotos-satelitales": ["la-cnn-completa", "tipos-de-segmentacion"],
}


def frontmatter(d):
    # YAML con valores en JSON: Astro lo lee como YAML y Python lo lee línea por línea con json.loads
    return "---\n" + "".join(f"{k}: {json.dumps(v, ensure_ascii=False)}\n" for k, v in d.items()) + "---\n"


def main():
    os.makedirs(os.path.join(CONTENIDO, "cursos"), exist_ok=True)
    os.makedirs(os.path.join(CONTENIDO, "lecciones"), exist_ok=True)
    for clave_curso, nombre, desc, temario in c.CURSOS:
        temas = []
        for t, (clave, titulo, desc_tema, lecciones) in enumerate(temario, 1):
            items = []
            for l, lec in enumerate(lecciones, 1):
                if "fuente" not in lec:
                    items.append({"titulo": lec["titulo"], "estado": "preparacion"})
                    continue
                items.append({"slug": lec["slug"]})
                meta = {
                    "titulo": lec["titulo"], "slug": lec["slug"], "curso": clave_curso, "tema": clave,
                    "numero": f"{t}.{l}", "descripcion": lec["desc"], "aprender": lec["aprender"],
                    "requisitos": lec["requisitos"], "prerrequisitos": PRERREQUISITOS.get(lec["slug"], []),
                    "minutos": lec["minutos"], "pasos": lec["pasos"], "datos": lec["datos"],
                    "miniatura": lec["miniatura"], "alt": lec["alt"],
                    "animacion": {"fuente": lec["fuente"],
                                  "fotos": lec["fotos"] if isinstance(lec.get("fotos"), str) else bool(lec.get("fotos"))},
                    "estado": "publicada",
                }
                ruta = os.path.join(CONTENIDO, "lecciones", lec["slug"] + ".mdx")
                cuerpo = ""
                if os.path.exists(ruta):
                    viejo = io.open(ruta, encoding="utf-8").read()
                    m = re.match(r"---\n.*?\n---\n(.*)", viejo, re.S)
                    cuerpo = m.group(1) if m else ""
                io.open(ruta, "w", encoding="utf-8", newline="\n").write(frontmatter(meta) + cuerpo)
            temas.append({"clave": clave, "titulo": titulo, "descripcion": desc_tema, "lecciones": items})
        curso = {"slug": clave_curso, "nombre": nombre, "descripcion": desc, "actualizado": c.ACTUALIZADO,
                 "ruta": "deep-learning", "temas": temas}
        io.open(os.path.join(CONTENIDO, "cursos", clave_curso + ".json"), "w", encoding="utf-8", newline="\n").write(
            json.dumps(curso, ensure_ascii=False, indent=2) + "\n")
    print("contenido/ actualizado desde el TEMARIO de construir.py")


if __name__ == "__main__":
    main()
