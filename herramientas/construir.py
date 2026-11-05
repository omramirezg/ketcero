"""Arma el sitio de Ket Cero en ../sitio: copia las animaciones del curso y genera las páginas.

Uso:  python herramientas/construir.py
Vuelve a correrlo cada vez que cambie una animación o se agregue una nueva al CATALOGO.
"""
import html, io, json, os, re, shutil
from datetime import date

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITIO = os.path.join(RAIZ, "sitio")
CURSO = r"C:\Users\USUARIO\Desktop\Maestria\2026-02\Monitoria de Deep Learning\Propuesta_2026"
DOMINIO = "https://ketcero.com"
AUTOR = "Omar Ramírez González"
LIMITE_MB = 25  # Cloudflare Pages no acepta archivos más grandes

# Cada tema: carpeta en /ia/, título, descripción y sus animaciones (ruta en el curso, título, descripción).
CATALOGO = [
    ("cnn", "Redes convolucionales", "Cómo una CNN mira una imagen: filtros que recorren la foto, mapas, pooling y la decisión final, con dígitos de MNIST.", [
        ("Semana_02/02_Clase_viernes_30_oct/1_Densa_vs_CNN_MNIST/Animacion_A4_la_CNN_completa.html", "La CNN completa, por dentro", "La red entera con un lote real: convoluciones, pooling, aplanado, capa densa y la vuelta del entrenamiento."),
    ]),
    ("deteccion", "Detección de objetos", "Encontrar y encerrar objetos en una imagen: cajas, puntajes y cómo aprende la red a ponerlas en el lugar correcto.", [
        ("Semana_03/02_Clase_viernes_6_nov/1_Mini_YOLO_digitos_en_la_calle/Animacion_B1_Mini_YOLO_por_dentro.html", "Mini YOLO por dentro: dígitos en la calle", "Una red pequeña al estilo YOLO aprende a encontrar dígitos sobre fotos de la calle: los datos, la red al nacer, la ida, la vuelta y la predicción."),
    ]),
]
PARTE_MB = 15  # tamaño de cada pedazo de datos cuando una animación pasa del límite

PRONTO = [
    ("Física", "Movimiento, energía, ondas y campos, con las ecuaciones animadas."),
    ("Matemática", "Cálculo, álgebra lineal y probabilidad: la base de todo lo demás."),
    ("Computación cuántica", "Qubits, superposición y compuertas, empezando por |0⟩."),
    ("Ingeniería", "Cómo se aplica todo esto en máquinas, estructuras y sistemas reales."),
]

LOGO = ('<svg viewBox="0 0 44 30" aria-hidden="true"><line x1="5" y1="3" x2="5" y2="27" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>'
        '<ellipse cx="19" cy="15" rx="6" ry="11" fill="none" stroke="#D85A30" stroke-width="3"/>'
        '<polyline points="31,3 39,15 31,27" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>')


def pagina(titulo, descripcion, ruta, cuerpo, actual="", extra_head=""):
    """Plantilla común: cabecera con la marca, menú, contenido y pie con la firma."""
    menu = [("/", "Inicio"), ("/ia/", "Inteligencia artificial"), ("/omar/", "Quién soy")]
    marca = ' aria-current="page"'
    enlaces = "".join(f'<a href="{u}"{marca if u == actual else ""}>{t}</a>' for u, t in menu)
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(titulo)}</title>
<meta name="description" content="{html.escape(descripcion)}">
<meta name="author" content="{AUTOR}">
<link rel="canonical" href="{DOMINIO}{ruta}">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Ket Cero">
<meta property="og:title" content="{html.escape(titulo)}">
<meta property="og:description" content="{html.escape(descripcion)}">
<meta property="og:url" content="{DOMINIO}{ruta}">
<meta property="og:locale" content="es_CO">
<link rel="stylesheet" href="/estilo.css">
{extra_head}</head>
<body>
<header class="barra"><div class="ancho">
<a class="marca" href="/">{LOGO}<b>Ket Cero</b></a>
<nav class="menu">{enlaces}</nav>
</div></header>
<main>
{cuerpo}
</main>
<footer class="pie"><div class="ancho">
<span>Ket Cero · Ciencia desde cero · un proyecto de <a href="/omar/">{AUTOR}</a></span>
<span>© {date.today().year}</span>
</div></footer>
</body>
</html>
"""


def mb(ruta):
    return os.path.getsize(ruta) / 1e6


def partir(origen, destino):
    """Para animaciones de más de LIMITE_MB: saca los datos grandes (const X = {...JSON...};) a archivos .js aparte.

    Cada dato se guarda como texto JSON en pedazos de PARTE_MB, en <nombre>_datos/X_k.js; la página los carga
    en orden antes de su código y los vuelve a armar con JSON.parse. El código de la animación no cambia.
    """
    s = io.open(origen, encoding="utf-8").read()
    ini = s.index("<script>") + len("<script>")
    fin = s.index("</script>", ini)
    js = s[ini:fin]
    carpeta = os.path.splitext(os.path.basename(destino))[0] + "_datos"
    os.makedirs(os.path.join(os.path.dirname(destino), carpeta), exist_ok=True)
    lector = json.JSONDecoder()
    etiquetas, partes_js, cursor = [], [], 0
    for m in re.finditer(r"(?m)^const (\w+) = ", js):
        a = m.end()
        try:
            _, b = lector.raw_decode(js, a)
        except ValueError:
            continue
        if (b - a) / 1e6 < 1:
            continue
        nombre, texto, paso = m.group(1), js[a:b], int(PARTE_MB * 1e6)
        for k in range(0, len(texto), paso):
            archivo = f"{nombre}_{k // paso}.js"
            io.open(os.path.join(os.path.dirname(destino), carpeta, archivo), "w", encoding="utf-8").write(
                "(window.__D = window.__D || {});\n"
                f"(__D.{nombre} = __D.{nombre} || []).push({json.dumps(texto[k:k + paso], ensure_ascii=False)});\n")
            etiquetas.append(f'<script src="{carpeta}/{archivo}"></script>')
        partes_js += [js[cursor:a], f"JSON.parse(__D.{nombre}.join(''))"]
        cursor = b
    partes_js.append(js[cursor:])
    nuevo = s[:ini - len("<script>")] + "\n".join(etiquetas) + "\n<script>" + "".join(partes_js) + s[fin:]
    io.open(destino, "w", encoding="utf-8").write(nuevo)
    pesos = [mb(destino)] + [mb(os.path.join(os.path.dirname(destino), carpeta, f)) for f in os.listdir(os.path.join(os.path.dirname(destino), carpeta))]
    if max(pesos) > LIMITE_MB:
        raise SystemExit(f"{os.path.basename(destino)}: un pedazo quedó de {max(pesos):.1f} MB; baja PARTE_MB")


def copiar_animaciones():
    """Copia cada animación a /ia/<tema>/ con su nombre original (así siguen funcionando los enlaces entre ellas)."""
    shutil.rmtree(os.path.join(SITIO, "ia"), ignore_errors=True)
    filas = []
    for clave, _, _, anims in CATALOGO:
        destino = os.path.join(SITIO, "ia", clave)
        os.makedirs(destino, exist_ok=True)
        for fuente, titulo, desc in anims:
            origen = os.path.join(CURSO, fuente)
            nombre = os.path.basename(fuente)
            peso = mb(origen)
            if peso > LIMITE_MB:
                partir(origen, os.path.join(destino, nombre))
            else:
                shutil.copy2(origen, os.path.join(destino, nombre))
            filas.append((clave, nombre, titulo, peso))
    return filas


def tarjeta_animacion(clave, fuente, titulo, desc):
    nombre = os.path.basename(fuente)
    peso = mb(os.path.join(CURSO, fuente))
    aviso = "  ·  conviene abrirla con wifi" if peso > 8 else ""
    return (f'<li><a class="tarjeta" href="/ia/{clave}/{nombre}"><h3>{html.escape(titulo)}</h3>'
            f'<p>{html.escape(desc)}</p><span class="dato">Animación · {peso:.1f} MB{aviso}</span></a></li>')


def construir_inicio():
    temas = "".join(
        f'<a class="tarjeta" href="/ia/#{c}"><span class="etiqueta">{len(a)} {"animaciones" if len(a) > 1 else "animación"}</span>'
        f'<h3>{t}</h3><p>{html.escape(d)}</p></a>' for c, t, d, a in CATALOGO)
    pronto = "".join(f'<div class="tarjeta pronto"><span class="etiqueta">Próximamente</span><h3>{t}</h3><p>{d}</p></div>' for t, d in PRONTO)
    cuerpo = f"""<div class="ancho portada">
<div class="ket" aria-hidden="true">|<span class="cero">0</span>⟩</div>
<h1>Ket Cero</h1>
<p class="lema">Ciencia desde cero</p>
<p>Animaciones que abren la caja negra: cada número, cada multiplicación y cada paso, para entender de verdad cómo funcionan la inteligencia artificial, la física, la matemática y la ingeniería.</p>
<p class="firma">Por <a href="/omar/">{AUTOR}</a></p>
</div>
<section><div class="ancho">
<h2>¿Por qué |0⟩?</h2>
<p class="intro">En computación cuántica, |0⟩ («ket cero») es el estado del que arranca todo cálculo. Aquí es lo mismo: no se da nada por sabido, todo empieza desde cero.</p>
</div></section>
<section><div class="ancho">
<h2>Inteligencia artificial</h2>
<p class="intro">Redes neuronales por dentro, con datos reales y cada operación a la vista.</p>
<div class="rejilla">{temas}</div>
</div></section>
<section><div class="ancho">
<h2>Lo que viene</h2>
<div class="rejilla">{pronto}</div>
</div></section>"""
    return pagina("Ket Cero · Ciencia desde cero",
                  "Animaciones que muestran la ciencia por dentro: inteligencia artificial, física, matemática e ingeniería explicadas desde cero, en español.",
                  "/", cuerpo, "/")


def construir_ia():
    bloques = []
    for clave, titulo, desc, anims in CATALOGO:
        items = "".join(tarjeta_animacion(clave, *a) for a in anims)
        bloques.append(f'<section class="tema" id="{clave}"><div class="ancho"><h2>{titulo}</h2>'
                       f'<p class="intro">{html.escape(desc)}</p><ul class="lista rejilla">{items}</ul></div></section>')
    cuerpo = ('<div class="ancho portada"><h1>Inteligencia artificial, por dentro</h1>'
              '<p class="lema">Cada animación avanza paso a paso: usa los botones o las flechas del teclado.</p></div>'
              + "".join(bloques))
    return pagina("Inteligencia artificial por dentro · Ket Cero",
                  "Animaciones de redes neuronales paso a paso: CNN, transfer learning, CLIP, detección de objetos y modelos de lenguaje, en español.",
                  "/ia/", cuerpo, "/ia/")


def construir_omar():
    persona = f"""<script type="application/ld+json">
{{"@context": "https://schema.org", "@type": "Person", "name": "{AUTOR}",
 "url": "{DOMINIO}/omar/", "jobTitle": "Monitor de Deep Learning",
 "sameAs": ["https://github.com/omramirezg"],
 "worksFor": {{"@type": "Organization", "name": "Ket Cero", "url": "{DOMINIO}"}}}}
</script>
"""
    cuerpo = f"""<div class="ancho portada">
<div class="persona">
<div class="foto">Tu foto<br>(la misma de LinkedIn)</div>
<div>
<h1>{AUTOR}</h1>
<p class="lema">Creador de Ket Cero</p>
<p>Soy monitor del curso de Deep Learning de la maestría <span class="completar">[universidad y programa]</span>. Hago animaciones que muestran las redes neuronales por dentro, con los números reales, porque así es como yo aprendí a entenderlas.</p>
<p><span class="completar">[Tu formación: pregrado, maestría, experiencia]</span></p>
<p><span class="completar">[Qué buscas: por ejemplo, roles de ML Engineer]</span></p>
<p><a href="https://github.com/omramirezg">GitHub</a> · <span class="completar">[LinkedIn]</span> · <span class="completar">[correo de contacto]</span></p>
</div>
</div>
</div>"""
    return pagina(f"{AUTOR} · Ket Cero",
                  f"{AUTOR}, creador de Ket Cero: animaciones de inteligencia artificial y ciencia explicadas desde cero.",
                  "/omar/", cuerpo, "/omar/", persona)


def construir_404():
    cuerpo = ('<div class="ancho portada"><div class="ket" aria-hidden="true">|<span class="cero">?</span>⟩</div>'
              '<h1>Esta página no existe</h1><p>Puede que el enlace haya cambiado. <a href="/">Volver al inicio</a>.</p></div>')
    return pagina("Página no encontrada · Ket Cero", "La página que buscas no existe.", "/404", cuerpo)


def escribir(ruta, texto):
    ruta = os.path.join(SITIO, ruta)
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    io.open(ruta, "w", encoding="utf-8", newline="\n").write(texto)


def main():
    filas = copiar_animaciones()
    escribir("index.html", construir_inicio())
    escribir("ia/index.html", construir_ia())
    escribir("omar/index.html", construir_omar())
    escribir("404.html", construir_404())
    urls = ["/", "/ia/", "/omar/"] + [f"/ia/{c}/{n}" for c, n, _, _ in filas]
    hoy = date.today().isoformat()
    escribir("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
             + "".join(f"<url><loc>{DOMINIO}{u}</loc><lastmod>{hoy}</lastmod></url>\n" for u in urls) + "</urlset>\n")
    escribir("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {DOMINIO}/sitemap.xml\n")
    total = sum(p for *_, p in filas)
    print(f"{len(filas)} animaciones copiadas ({total:.1f} MB). Sitio listo en {SITIO}")
    for c, n, _, p in filas:
        print(f"  {p:6.1f} MB  /ia/{c}/{n}")


if __name__ == "__main__":
    main()
