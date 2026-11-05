"""Arma el sitio de Ket Cero en ../sitio: copia las animaciones del curso y genera las páginas.

Uso:  python herramientas/construir.py
Vuelve a correrlo cada vez que cambie una animación o se agregue una lección al TEMARIO.
"""
import html, io, json, os, re, shutil
from datetime import date

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITIO = os.path.join(RAIZ, "sitio")
MINIATURAS = os.path.join(RAIZ, "herramientas", "miniaturas")
CURSO = r"C:\Users\USUARIO\Desktop\Maestria\2026-02\Monitoria de Deep Learning\Propuesta_2026"
DOMINIO = "https://ketcero.com"
AUTOR = "Omar Ramírez González"
LIMITE_MB = 25  # Cloudflare no acepta archivos más grandes
PARTE_MB = 15  # tamaño de cada pedazo de datos cuando una animación pasa del límite
ACTUALIZADO = "5 de noviembre de 2026"

# Temario de machine learning. Cada tema: (carpeta en /ia/, título, descripción, lecciones).
# Lección publicada: dict con fuente (ruta en el curso), miniatura, descripción y datos.
# Lección pendiente: solo el título.
TEMARIO = [
    ("fundamentos", "Fundamentos", "Lo que hace falta antes de cualquier red.", [
        {"titulo": "Regresión lineal: ajustar una recta"},
        {"titulo": "La pérdida y el descenso de gradiente"},
    ]),
    ("redes-neuronales", "Redes neuronales", "De una neurona a una red densa que aprende.", [
        {"titulo": "Una neurona, número por número"},
        {"titulo": "El backward con la regla de la cadena"},
    ]),
    ("cnn", "Redes convolucionales", "Cómo una red lee una imagen.", [
        {"titulo": "La CNN completa, por dentro",
         "fuente": "Semana_02/02_Clase_viernes_30_oct/1_Densa_vs_CNN_MNIST/Animacion_A4_la_CNN_completa.html",
         "miniatura": "cnn-completa.jpg",
         "alt": "La pérdida de cada imagen del lote en la CNN completa",
         "desc": "Una LeNet-5 aprende a leer dígitos de MNIST: lotes reales, la pérdida de cada imagen, el backward capa por capa y el paso de AdamW.",
         "datos": "86 pasos entrenar · 43 predecir · 5 épocas", "pasos": 86 + 43},
    ]),
    ("deteccion", "Detección de objetos", "Encontrar y encerrar objetos: cajas, puntajes, IoU y NMS.", [
        {"titulo": "Mini-YOLO por dentro: dígitos en la calle",
         "fuente": "Semana_03/02_Clase_viernes_6_nov/1_Mini_YOLO_digitos_en_la_calle/Animacion_B1_Mini_YOLO_por_dentro.html",
         "miniatura": "mini-yolo.jpg",
         "alt": "El NMS del Mini-YOLO borra las cajas que se solapan",
         "desc": "Una red pequeña al estilo YOLO aprende a encontrar dígitos sobre fotos reales de la calle, desde la red recién nacida hasta las cajas finales.",
         "datos": "186 pasos entrenar · 66 predecir · 30 épocas", "pasos": 186 + 66},
    ]),
    ("lenguaje", "Modelos de lenguaje", "Del bigrama a los transformers.", [
        {"titulo": "El bigrama de letras"},
    ]),
]

LOGO = ('<svg width="34" height="24" viewBox="0 0 44 30" aria-hidden="true"><line x1="5" y1="3" x2="5" y2="27" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>'
        '<ellipse cx="19" cy="15" rx="6" ry="11" fill="none" stroke="#C8502A" stroke-width="3"/>'
        '<polyline points="31,3 39,15 31,27" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>')
# Aplica el tema guardado antes de pintar (sin parpadeo) y maneja el botón Oscuro / Claro.
TEMA_JS = '<script>try{var t=localStorage.getItem("tema");if(t)document.documentElement.dataset.tema=t}catch(e){}</script>\n'
BOTON_JS = """<script>
(function () {
  var b = document.getElementById("tema"), r = document.documentElement;
  function oscuro() { return r.dataset.tema ? r.dataset.tema === "oscuro" : matchMedia("(prefers-color-scheme: dark)").matches; }
  function rotulo() { b.setAttribute("aria-checked", oscuro() ? "true" : "false"); }
  b.addEventListener("click", function () {
    r.dataset.tema = oscuro() ? "claro" : "oscuro";
    try { localStorage.setItem("tema", r.dataset.tema); } catch (e) {}
    rotulo();
  });
  rotulo();
})();
</script>"""
FUENTES = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
           '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
           '<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono&display=swap" rel="stylesheet">\n')


def pagina(titulo, descripcion, ruta, cuerpo, actual="", extra_head=""):
    """Plantilla común: cabecera con la marca, menú, contenido y pie con la firma."""
    menu = [("/", "Temario"), ("/omar/", "Quién soy")]
    marca = ' aria-current="page"'
    enlaces = "".join(f'<a href="{u}"{marca if u == actual else ""}>{t}</a>' for u, t in menu)
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{TEMA_JS}<title>{html.escape(titulo)}</title>
<meta name="description" content="{html.escape(descripcion)}">
<meta name="author" content="{AUTOR}">
<link rel="canonical" href="{DOMINIO}{ruta}">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="alternate icon" href="/favicon.ico">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Ket Cero">
<meta property="og:title" content="{html.escape(titulo)}">
<meta property="og:description" content="{html.escape(descripcion)}">
<meta property="og:url" content="{DOMINIO}{ruta}">
<meta property="og:locale" content="es_CO">
{FUENTES}<link rel="stylesheet" href="/estilo.css">
{extra_head}</head>
<body>
<header><div class="in">
<a class="marca" href="/">{LOGO}Ket Cero<small>Machine learning desde cero</small></a>
<nav>{enlaces}<button id="tema" type="button" role="switch" aria-checked="false"><span>Modo oscuro</span><span class="pista"><span class="perilla"></span></span></button></nav>
</div></header>
{cuerpo}
<footer><div class="in"><span>Ket Cero · un proyecto de <a href="/omar/">{AUTOR}</a></span><span>ketcero.com</span></div></footer>
{BOTON_JS}
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


def publicadas():
    """Las lecciones con animación, con su tema y su número (3.1, 4.1…)."""
    for t, (clave, _, _, lecciones) in enumerate(TEMARIO, 1):
        for l, lec in enumerate(lecciones, 1):
            if "fuente" in lec:
                yield clave, f"{t}.{l}", lec


def copiar_animaciones():
    """Copia cada animación a /ia/<tema>/ con su nombre original (así siguen funcionando los enlaces entre ellas)."""
    shutil.rmtree(os.path.join(SITIO, "ia"), ignore_errors=True)
    shutil.rmtree(os.path.join(SITIO, "img"), ignore_errors=True)
    os.makedirs(os.path.join(SITIO, "img"))
    filas = []
    for clave, _, lec in publicadas():
        destino = os.path.join(SITIO, "ia", clave)
        os.makedirs(destino, exist_ok=True)
        origen = os.path.join(CURSO, lec["fuente"])
        nombre = os.path.basename(lec["fuente"])
        peso = mb(origen)
        if peso > LIMITE_MB:
            partir(origen, os.path.join(destino, nombre))
        else:
            shutil.copy2(origen, os.path.join(destino, nombre))
        shutil.copy2(os.path.join(MINIATURAS, lec["miniatura"]), os.path.join(SITIO, "img", lec["miniatura"]))
        lec["url"] = f"/ia/{clave}/{nombre}"
        filas.append((lec["url"], peso))
    return filas


def construir_inicio():
    lados, temas = [], []
    for t, (clave, titulo, desc, lecciones) in enumerate(TEMARIO, 1):
        n_pub = sum("fuente" in l for l in lecciones)
        lados.append(f'<li><a href="#{clave}">{t} · {titulo} <span>{n_pub}</span></a></li>')
        filas = []
        for l, lec in enumerate(lecciones, 1):
            num = f"{t}.{l}"
            if "fuente" in lec:
                filas.append(f'<a class="fila pub" href="{lec["url"]}"><div class="n">{num}</div><div><b>{html.escape(lec["titulo"])}</b>'
                             f'<p>{html.escape(lec["desc"])}</p><div class="d">{lec["datos"]}</div></div>'
                             f'<img src="/img/{lec["miniatura"]}" alt="{html.escape(lec["alt"])}" loading="lazy"></a>')
            else:
                filas.append(f'<div class="fila pend"><div class="n">{num}</div><div><b>{html.escape(lec["titulo"])}</b></div><div class="d">en preparación</div></div>')
        temas.append(f'<section class="tema" id="{clave}"><h2>{titulo} <span>Tema {t}</span></h2><p>{html.escape(desc)}</p>{"".join(filas)}</section>')
    cuerpo = f"""<div class="cuerpo">
<aside>
<p class="t">Temario</p>
<ol>{"".join(lados)}</ol>
<p class="t">Autor</p>
<p><a href="/omar/">{AUTOR}</a></p>
</aside>
<main>
<section class="cabeza">
<div class="mono">Temario · actualizado el {ACTUALIZADO}</div>
<h1>Machine learning desde cero, con cada operación a la vista.</h1>
<p>Un recorrido ordenado: de la regresión lineal a la detección de objetos. Cada lección es una animación paso a paso hecha con los datos reales del entrenamiento.</p>
</section>
{"".join(temas)}
</main>
</div>"""
    return pagina("Ket Cero · Machine learning desde cero",
                  "Machine learning desde cero, en español: lecciones animadas paso a paso con los datos reales del entrenamiento. Redes convolucionales, detección de objetos y más.",
                  "/", cuerpo, "/")


def construir_omar():
    persona = f"""<script type="application/ld+json">
{{"@context": "https://schema.org", "@type": "Person", "name": "{AUTOR}",
 "url": "{DOMINIO}/omar/", "jobTitle": "Monitor de Deep Learning",
 "sameAs": ["https://github.com/omramirezg"],
 "worksFor": {{"@type": "Organization", "name": "Ket Cero", "url": "{DOMINIO}"}}}}
</script>
"""
    cuerpo = f"""<div class="cuerpo solo">
<main class="texto">
<section class="cabeza">
<div class="mono">Quién soy</div>
<h1>{AUTOR}</h1>
<p>Creador de Ket Cero.</p>
</section>
</main>
</div>"""
    return pagina(f"{AUTOR} · Ket Cero",
                  f"{AUTOR}, creador de Ket Cero: machine learning desde cero, con animaciones paso a paso.",
                  "/omar/", cuerpo, "/omar/", persona)


def construir_404():
    cuerpo = ('<div class="cuerpo solo"><main class="texto"><section class="cabeza"><div class="mono">Error 404</div>'
              '<h1>Esta página no existe</h1><p>Puede que el enlace haya cambiado. <a href="/">Volver al temario</a>.</p></section></main></div>')
    return pagina("Página no encontrada · Ket Cero", "La página que buscas no existe.", "/404", cuerpo)


def escribir(ruta, texto):
    ruta = os.path.join(SITIO, ruta)
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    io.open(ruta, "w", encoding="utf-8", newline="\n").write(texto)


def main():
    filas = copiar_animaciones()
    escribir("index.html", construir_inicio())
    escribir("omar/index.html", construir_omar())
    escribir("404.html", construir_404())
    urls = ["/", "/omar/"] + [u for u, _ in filas]
    hoy = date.today().isoformat()
    escribir("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
             + "".join(f"<url><loc>{DOMINIO}{u}</loc><lastmod>{hoy}</lastmod></url>\n" for u in urls) + "</urlset>\n")
    escribir("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {DOMINIO}/sitemap.xml\n")
    print(f"{len(filas)} animaciones copiadas ({sum(p for _, p in filas):.1f} MB). Sitio listo en {SITIO}")
    for u, p in filas:
        print(f"  {p:6.1f} MB  {u}")


if __name__ == "__main__":
    main()
