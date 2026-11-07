"""Preconstrucción del sitio en Astro: arma en apps/web/public/ lo que viene del curso y de Python.

Uso:  python herramientas/recursos.py        (lo corre `npm run build` antes de Astro)

- Lee las lecciones publicadas de contenido/lecciones/*.mdx (sus metadatos).
- Copia cada animación del curso a public/ia/<tema>/, la parte en pedazos si pasa de 25 MB y le agrega la capa
  (mismas funciones que construir.py: partir, agregar_capa, escribir_capa), así las animaciones se vuelven a armar
  desde el curso cada vez.
- Copia la capa (/kc/), la animación de portada (/js/cero_datos.js), miniaturas en WebP, clips y la imagen para compartir.
- Escribe apps/web/src/generado/recursos.json: dirección y peso de cada animación, si tiene clip, y la huella (?v=)
  de cada archivo para que el navegador lo guarde un año sin perder los cambios.
"""
import glob, hashlib, io, json, os, shutil, sys

from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "herramientas"))
import construir as c  # noqa: E402

PUBLICO = os.path.join(RAIZ, "apps", "web", "public")
GENERADO = os.path.join(RAIZ, "apps", "web", "src", "generado")
c.SITIO = PUBLICO  # las funciones de construir.py escriben aquí
CARPETAS_GENERADAS = ("ia", "img", "kc", "js")


def leer_frontmatter(ruta):
    lineas = io.open(ruta, encoding="utf-8").read().split("\n")
    assert lineas[0] == "---", ruta
    meta = {}
    for linea in lineas[1:]:
        if linea == "---":
            break
        clave, valor = linea.split(": ", 1)
        meta[clave] = json.loads(valor)
    return meta


def huella(ruta_publica):
    contenido = open(os.path.join(PUBLICO, ruta_publica.lstrip("/")), "rb").read()
    return hashlib.sha1(contenido).hexdigest()[:10]


def main():
    lecciones = sorted((leer_frontmatter(r) for r in glob.glob(os.path.join(RAIZ, "contenido", "lecciones", "*.mdx"))),
                       key=lambda m: [int(x) for x in m["numero"].split(".")])
    publicadas = [m for m in lecciones if m["estado"] == "publicada"]
    for carpeta in CARPETAS_GENERADAS:
        shutil.rmtree(os.path.join(PUBLICO, carpeta), ignore_errors=True)
    os.makedirs(os.path.join(PUBLICO, "img"))
    os.makedirs(os.path.join(PUBLICO, "js"))
    shutil.copy2(os.path.join(RAIZ, "herramientas", "animacion_cero", "cero_datos.js"), os.path.join(PUBLICO, "js", "cero_datos.js"))
    shutil.copy2(os.path.join(c.MINIATURAS, "compartir.png"), os.path.join(PUBLICO, "img", "compartir.png"))

    orden, salida = [], {"lecciones": {}, "versiones": {}}
    for m in publicadas:
        fuente = m["animacion"]["fuente"]
        nombre = os.path.basename(fuente)
        destino = os.path.join(PUBLICO, "ia", m["tema"])
        os.makedirs(destino, exist_ok=True)
        origen = os.path.join(c.CURSO, fuente)
        peso = c.mb(origen)
        if peso > c.LIMITE_MB:
            c.partir(origen, os.path.join(destino, nombre))
        else:
            shutil.copy2(origen, os.path.join(destino, nombre))
        Image.open(os.path.join(c.MINIATURAS, m["miniatura"])).save(
            os.path.join(PUBLICO, "img", c.webp(m["miniatura"])), "WEBP", quality=82, method=6)
        base = os.path.splitext(m["miniatura"])[0]
        tiene_clip = all(os.path.exists(os.path.join(c.MINIATURAS, base + ext)) for ext in (".webm", ".mp4"))
        if tiene_clip:
            for ext in (".webm", ".mp4"):
                shutil.copy2(os.path.join(c.MINIATURAS, base + ext), os.path.join(PUBLICO, "img", base + ext))
        url = f"/ia/{m['tema']}/{nombre[:-5]}"
        pagina = f"/cursos/{m['curso']}/{m['slug']}/"
        lec = {"slug": m["slug"], "titulo": m["titulo"], "desc": m["descripcion"], "url": url, "pagina": pagina,
               "fotos": m["animacion"]["fotos"]}
        c.agregar_capa(os.path.join(destino, nombre), lec)
        orden.append((m["tema"], m["numero"], lec))
        salida["lecciones"][m["slug"]] = {"url": url, "pagina": pagina, "peso_mb": round(peso, 1),
                                          "miniatura": "/img/" + c.webp(m["miniatura"]), "clip": "/img/" + base if tiene_clip else None}
    c.escribir_capa(orden)

    for raiz, _, archivos in os.walk(PUBLICO):
        for a in archivos:
            rel = "/" + os.path.relpath(os.path.join(raiz, a), PUBLICO).replace(os.sep, "/")
            if rel.startswith("/ia/"):
                continue
            salida["versiones"][rel] = huella(rel)
    os.makedirs(GENERADO, exist_ok=True)
    io.open(os.path.join(GENERADO, "recursos.json"), "w", encoding="utf-8", newline="\n").write(
        json.dumps(salida, ensure_ascii=False, indent=1) + "\n")
    print(f"{len(publicadas)} animaciones armadas en {PUBLICO}")
    for slug, d in salida["lecciones"].items():
        print(f"  {d['peso_mb']:6.1f} MB  {d['url']}")


if __name__ == "__main__":
    main()
