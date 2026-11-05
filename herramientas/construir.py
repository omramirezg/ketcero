"""Arma el sitio de Ket Cero en ../sitio: copia las animaciones del curso y genera las páginas.

Uso:  python herramientas/construir.py
Vuelve a correrlo cada vez que cambie una animación o se agregue una lección al TEMARIO.
Para probarlo como en Cloudflare (encabezados, direcciones sin «.html»): python herramientas/servidor_local.py
"""
import hashlib, html, io, json, os, re, shutil
from datetime import date

from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITIO = os.path.join(RAIZ, "sitio")
MINIATURAS = os.path.join(RAIZ, "herramientas", "miniaturas")
CURSO = r"C:\Users\USUARIO\Desktop\Maestria\2026-02\Monitoria de Deep Learning\Propuesta_2026"
DOMINIO = "https://ketcero.com"
AUTOR = "Omar Ramírez González"
LIMITE_MB = 25  # Cloudflare no acepta archivos más grandes
PARTE_MB = 15  # tamaño de cada pedazo de datos cuando una animación pasa del límite
ACTUALIZADO = "5 de noviembre de 2026"
# Cloudflare Web Analytics: pega aquí el token que da el panel (ver notas/PASOS_GOOGLE_Y_ANALITICA.md); vacío = sin analítica
ANALITICA = ""

# Temario de machine learning. Cada tema: (carpeta en /ia/, título, descripción, lecciones).
# Lección publicada: dict con fuente (ruta en el curso), slug de su página, miniatura, descripción, datos,
# qué se aprende, requisitos y minutos aproximados. Lección pendiente: solo el título.
TEMARIO = [
    ("redes-profundas", "Redes neuronales profundas", "Qué es una red, cuándo le gana al machine learning clásico y cómo aprende con descenso de gradiente.", [
        {"titulo": "¿Machine learning o deep learning? Depende de cuántos datos hay"},
        {"titulo": "Una red que pinta un mapa de cultivos"},
    ]),
    ("cnn", "Redes convolucionales", "Cómo una red lee una imagen.", [
        {"titulo": "La CNN completa, por dentro",
         "slug": "la-cnn-completa",
         "fuente": "Semana_02/02_Clase_viernes_30_oct/1_Densa_vs_CNN_MNIST/Animacion_A4_la_CNN_completa.html",
         "miniatura": "cnn-completa.jpg",
         "alt": "La pérdida de cada imagen del lote en la CNN completa",
         "desc": "Una LeNet-5 aprende a leer dígitos de MNIST: lotes reales, la pérdida de cada imagen, el backward capa por capa y el paso de AdamW.",
         "datos": "86 pasos entrenar · 43 predecir · 5 épocas", "pasos": 86 + 43, "minutos": 30,
         "aprender": [
             "Cómo se reparten las imágenes de MNIST: 55.000 para entrenar, 5.000 para validar y 10.000 de prueba, en lotes de 128.",
             "Cómo nace la LeNet-5 con pesos al azar y cuáles de sus capas aprenden: 44.426 parámetros.",
             "La ida de un lote real, capa por capa: convoluciones, ReLU, pooling, aplanar y capas densas.",
             "La pérdida de cada imagen y del lote, y la vuelta (backward) capa por capa hasta el paso de AdamW.",
             "Cómo se valida cada época y cómo la red ya entrenada reconoce un 3 que nunca vio.",
         ],
         "requisitos": "Saber qué es una neurona y una capa densa ayuda, pero no es indispensable: cada operación se muestra con sus números."},
        {"titulo": "Transfer learning: hojas de café sanas o enfermas"},
        {"titulo": "Clasificar sin entrenar: CLIP contra una CNN"},
    ]),
    ("deteccion", "Detección de objetos", "Encontrar y encerrar objetos: cajas, puntajes, IoU y NMS.", [
        {"titulo": "Mini-YOLO por dentro: dígitos en la calle",
         "slug": "mini-yolo-digitos-en-la-calle",
         "fuente": "Semana_03/02_Clase_viernes_6_nov/1_Mini_YOLO_digitos_en_la_calle/Animacion_B1_Mini_YOLO_por_dentro.html",
         "miniatura": "mini-yolo.jpg", "fotos": True,
         "alt": "El NMS del Mini-YOLO borra las cajas que se solapan",
         "desc": "Una red pequeña al estilo YOLO aprende a encontrar dígitos sobre fotos reales de la calle, desde la red recién nacida hasta las cajas finales.",
         "datos": "186 pasos entrenar · 66 predecir · 30 épocas", "pasos": 186 + 66, "minutos": 60,
         "aprender": [
             "Cómo se arman las escenas: dígitos de MNIST pegados sobre fotos reales de la calle.",
             "La red al nacer: nueve convoluciones con su BatchNorm, cinco pool y dos capas densas que terminan en una rejilla de 7 × 7.",
             "La ida de un lote real y la pérdida de YOLO, término por término.",
             "La vuelta con la regla de la cadena y el paso de AdamW, lote tras lote y época tras época.",
             "Al predecir: decodificar las 98 cajas, el puntaje, el umbral, el IoU y el NMS hasta las cajas finales.",
         ],
         "requisitos": "Haber visto «La CNN completa, por dentro»: aquí se usan las mismas piezas (convoluciones, pooling, capas densas)."},
        {"titulo": "YOLO11 encuentra huecos en la calle"},
    ]),
    ("segmentacion", "Segmentación de imágenes", "Etiquetar cada píxel de una imagen, no solo encerrar el objeto en una caja.", [
        {"titulo": "Cómo se etiquetan las imágenes para entrenar"},
        {"titulo": "Segmentación semántica, píxel por píxel"},
    ]),
    ("generativos-secuencias", "Modelos generativos y secuencias", "Redes que inventan imágenes y redes que leen datos en orden.", [
        {"titulo": "GANs: dos redes que compiten"},
        {"titulo": "RNNs: una red con memoria"},
    ]),
    ("transformers-grafos", "Transformers y redes de grafos", "La atención, base de los modelos de lenguaje, y las redes que aprenden sobre conexiones.", [
        {"titulo": "Transformers: la atención, número por número"},
        {"titulo": "Redes neuronales de grafos"},
    ]),
]

# Cursos del sitio: (carpeta en /cursos/, nombre, descripción, temario). Por ahora solo Deep Learning.
CURSOS = [
    ("deep-learning", "Deep Learning",
     "Redes neuronales profundas en el orden de las sesiones del curso: de las redes densas a los transformers. Cada lección es una animación paso a paso con los datos reales del entrenamiento.",
     TEMARIO),
]
CURSO_DL = "/cursos/deep-learning/"

LOGO = ('<svg width="34" height="24" viewBox="0 0 44 30" aria-hidden="true"><line x1="5" y1="3" x2="5" y2="27" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>'
        '<ellipse cx="19" cy="15" rx="6" ry="11" fill="none" stroke="#C8502A" stroke-width="3"/>'
        '<polyline points="31,3 39,15 31,27" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>')


def version(ruta_publica):
    """Dirección con ?v=<huella del archivo>: así el navegador puede guardarlo un año y aun así ve los cambios."""
    contenido = open(os.path.join(SITIO, ruta_publica.lstrip("/")), "rb").read()
    return f"{ruta_publica}?v={hashlib.sha1(contenido).hexdigest()[:10]}"


def beacon():
    if not ANALITICA:
        return ""
    return ('<script defer src="https://static.cloudflareinsights.com/beacon.min.js" '
            f'data-cf-beacon=\'{{"token": "{ANALITICA}"}}\'></script>\n')


# Aplica el tema guardado antes de pintar (sin parpadeo) y maneja el botón Oscuro / Claro.
TEMA_JS = '<script>try{var t=localStorage.getItem("tema");if(t)document.documentElement.dataset.tema=t}catch(e){}</script>\n'
CLIP_JS = """<script>
(function () {
  var quieto = matchMedia("(prefers-reduced-motion: reduce)").matches;
  document.querySelectorAll("video.clip").forEach(function (v) {
    if (quieto) { v.removeAttribute("autoplay"); v.pause(); return; }
    if (!v.hasAttribute("data-al-pasar")) return;
    var fila = v.closest("a") || v;
    fila.addEventListener("mouseenter", function () { v.play().catch(function () {}); });
    fila.addEventListener("mouseleave", function () { v.pause(); });
  });
})();
</script>"""
BOTON_JS = """<script>
(function () {
  var b = document.getElementById("tema"), r = document.documentElement;
  function oscuro() { return r.dataset.tema !== "claro"; }  // oscuro por defecto
  function rotulo() { b.setAttribute("aria-checked", oscuro() ? "true" : "false"); }
  b.addEventListener("click", function () {
    r.dataset.tema = oscuro() ? "claro" : "oscuro";
    try { localStorage.setItem("tema", r.dataset.tema); } catch (e) {}
    rotulo();
  });
  rotulo();
})();
(function () {
  var m = document.getElementById("menu"), c = document.getElementById("cajon"), v = document.getElementById("velo");
  function medir() {
    var raya = document.querySelector(".marca small");
    var x = raya && raya.offsetParent ? raya.getBoundingClientRect().left : 0;
    document.documentElement.style.setProperty("--ancho-cajon", x > 200 ? x + "px" : "86vw");
  }
  medir();
  addEventListener("resize", medir);
  function poner(abierto) {
    m.setAttribute("aria-expanded", abierto ? "true" : "false");
    c.classList.toggle("abierto", abierto);
    v.hidden = !abierto;
    if (abierto) c.querySelector("a").focus();
  }
  m.addEventListener("click", function () { poner(m.getAttribute("aria-expanded") !== "true"); });
  v.addEventListener("click", function () { poner(false); });
  c.addEventListener("click", function (e) { if (e.target.closest("a")) poner(false); });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape" && !v.hidden) { poner(false); m.focus(); } });
})();
(function () {
  var b = document.getElementById("cursos"), l = document.getElementById("lista-cursos");
  function poner(abierto) { b.setAttribute("aria-expanded", abierto ? "true" : "false"); l.hidden = !abierto; }
  b.addEventListener("click", function (e) { e.stopPropagation(); poner(l.hidden); });
  document.addEventListener("click", function (e) { if (!l.hidden && !l.contains(e.target)) poner(false); });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape" && !l.hidden) { poner(false); b.focus(); } });
})();
(function () {
  // lecciones ya abiertas (las marca la capa de las animaciones) y «seguir donde quedaste»
  var vistas = [];
  try { vistas = JSON.parse(localStorage.getItem("kc-vistas") || "[]"); } catch (e) {}
  [].forEach.call(document.querySelectorAll("[data-leccion]"), function (el) {
    if (vistas.indexOf(el.getAttribute("data-leccion")) < 0 || el.id === "seguir") return;
    var s = document.createElement("span"); s.className = "vista"; s.textContent = "vista";
    (el.querySelector(".d") || el).appendChild(s);
  });
  var seguir = document.getElementById("seguir");
  if (seguir) try {
    var h = localStorage.getItem("kc-paso-" + seguir.getAttribute("data-leccion"));
    if (h && /^#[a-z_0-9]+\\/\\d+$/.test(h)) {
      var p = h.slice(1).split("/");
      seguir.href = seguir.getAttribute("data-animacion") + h;
      seguir.textContent = "Seguir donde quedaste: " + p[0] + ", paso " + p[1] + " →";
      seguir.hidden = false;
    }
  } catch (e) {}
})();
(function () {
  // «Cargando la animación…» mientras el navegador trae una animación pesada
  var c = document.getElementById("cargando");
  document.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest("a[data-abre-animacion]");
    if (a && c && e.button === 0 && !e.ctrlKey && !e.metaKey && !e.shiftKey) c.hidden = false;
  });
  addEventListener("pageshow", function () { if (c) c.hidden = true; });
})();
</script>"""


def pagina(titulo, descripcion, ruta, cuerpo, actual="", extra_head=""):
    """Plantilla común: cabecera con la marca, menú, contenido y pie con la firma."""
    marca = ' aria-current="page"'
    lista = "".join(f'<a href="/cursos/{c}/">{nombre}<small>{len(tem)} temas · {publicadas_en(tem)} lecciones</small></a>'
                    for c, nombre, _, tem in CURSOS)
    enlaces = (f'<div class="desplegable"><button id="cursos" type="button" aria-expanded="false" aria-controls="lista-cursos"'
               f'{marca if actual.startswith("/cursos/") else ""}>Cursos</button>'
               f'<div id="lista-cursos" class="lista" hidden>{lista}</div></div>'
               f'<a href="/omar/"{marca if actual == "/omar/" else ""}>Quién soy</a>')
    cajon = "".join(f'<p class="t">{nombre}</p><ol>'
                    + "".join(f'<li><a href="/cursos/{c}/#{clave}"><em>{t}</em>{titulo}<span>{sum("fuente" in l for l in lecciones)}</span></a></li>'
                              for t, (clave, titulo, _, lecciones) in enumerate(tem, 1)) + '</ol>'
                    for c, nombre, _, tem in CURSOS)
    cuerpo = cuerpo.replace("<main", '<main id="contenido"', 1)
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
<meta property="og:image" content="{DOMINIO}/img/compartir.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Ket Cero: un 0 escrito a mano y lo que ve un filtro de la red">
<meta property="og:locale" content="es_CO">
<meta name="twitter:card" content="summary_large_image">
<link rel="preload" href="/fuentes/IBMPlexSans-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{version('/kc/fuentes.css')}">
<link rel="stylesheet" href="{version('/estilo.css')}">
{beacon()}{extra_head}</head>
<body>
<a class="saltar" href="#contenido">Saltar al contenido</a>
<header><div class="in">
<div class="izq"><button id="menu" class="hamb" type="button" aria-expanded="false" aria-controls="cajon" aria-label="Abrir los cursos"><span></span><span></span><span></span></button>
<a class="marca" href="/" aria-label="Ket Cero, inicio">{LOGO}Ket Cero<small>Machine learning desde cero</small></a></div>
<nav aria-label="Principal">{enlaces}<button id="tema" type="button" role="switch" aria-checked="true"><span>Modo oscuro</span><span class="pista"><span class="perilla"></span></span></button></nav>
</div></header>
<div id="velo" class="velo" hidden></div>
<aside id="cajon" class="cajon" aria-label="Cursos">
{cajon}
</aside>
{cuerpo}
<div id="cargando" class="cargando" role="status" hidden><div>{LOGO}<p>Cargando la animación…</p><small>Trae los datos reales de cada paso: la primera vez tarda unos segundos.</small></div></div>
<footer><div class="in"><span>Ket Cero · un proyecto de <a href="/omar/">{AUTOR}</a></span><span>ketcero.com</span></div></footer>
{BOTON_JS}
{CLIP_JS}
</body>
</html>
"""


def ld(objeto):
    return '<script type="application/ld+json">\n' + json.dumps(objeto, ensure_ascii=False, indent=1) + "\n</script>\n"


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


# ------------------------------------------------------------------------------------------------------------
# Capa del sitio sobre cada animación publicada (los originales del curso no se tocan).
# Los archivos grandes solo llevan unas pocas líneas FIJAS (agregar_capa); todo lo que la capa hace vive en
# archivos pequeños de /kc/ (temprano.js, capa.css, capa.js). Así, mejorar la capa no cambia los archivos grandes
# y el repositorio no crece cada vez.
# ------------------------------------------------------------------------------------------------------------
KC_ALTO = 65
CAPA_DIR = os.path.join(RAIZ, "herramientas", "capa")  # temprano.js, capa.css y capa.js: la capa de las animaciones


def agregar_capa(ruta, lec):
    """Las líneas fijas que se agregan a una animación grande. No deben cambiar cuando se mejora la capa."""
    s = io.open(ruta, encoding="utf-8").read()
    atributos = f' data-kc-leccion="{lec["slug"]}"' + (" data-kc-fotos" if lec.get("fotos") else "")
    s = s.replace("<html", "<html" + atributos, 1)
    # la animación se escala en el alto que deja la cabecera y se baja esa misma altura
    assert s.count("innerHeight") == 3 and "m.style.top = ((innerHeight" in s, ruta
    s = s.replace("m.style.top = ((innerHeight", "m.style.top = KC_ALTO + ((innerHeight")
    s = s.replace("innerHeight", "(innerHeight - KC_ALTO)")
    titulo = html.escape(lec["titulo"]) + " · Ket Cero"
    s = re.sub(r"<title>.*?</title>", lambda m: f"<title>{titulo}</title>", s, count=1, flags=re.S)
    i = s.index("<head>") + len("<head>")
    s = s[:i] + '\n<script src="/kc/temprano.js"></script>' + s[i:]
    url = DOMINIO + lec["url"]
    cabeza = (f'<meta name="description" content="{html.escape(lec["desc"])}">\n'
              f'<link rel="canonical" href="{url}">\n'
              f'<meta property="og:type" content="article">\n<meta property="og:site_name" content="Ket Cero">\n'
              f'<meta property="og:title" content="{titulo}">\n<meta property="og:description" content="{html.escape(lec["desc"])}">\n'
              f'<meta property="og:url" content="{url}">\n<meta property="og:image" content="{DOMINIO}/img/compartir.png">\n'
              '<meta name="twitter:card" content="summary_large_image">\n'
              '<link rel="icon" href="/favicon.svg" type="image/svg+xml">\n'
              '<link rel="stylesheet" href="/kc/fuentes.css">\n<link rel="stylesheet" href="/kc/capa.css">\n')
    j = s.index("</head>")
    s = s[:j] + cabeza + s[j:]
    k = s.rindex("</body>")
    s = s[:k] + '<script src="/kc/capa.js"></script>\n' + s[k:]
    io.open(ruta, "w", encoding="utf-8", newline="").write(s)


def escribir_capa(publicadas_orden):
    """Copia la capa a /kc/ con los datos de las lecciones (título, página, anterior, siguiente) y la analítica."""
    os.makedirs(os.path.join(SITIO, "kc"), exist_ok=True)
    lecciones = {}
    for n, (clave, num, lec) in enumerate(publicadas_orden):
        def ref(otra):
            return {"titulo": otra[2]["titulo"], "pagina": otra[2]["pagina"]} if otra else None
        lecciones[lec["slug"]] = {"titulo": lec["titulo"], "numero": num, "pagina": lec["pagina"], "animacion": lec["url"],
                                  "anterior": ref(publicadas_orden[n - 1] if n > 0 else None),
                                  "siguiente": ref(publicadas_orden[n + 1] if n + 1 < len(publicadas_orden) else None)}
    datos = ("var KC_LECCIONES = " + json.dumps(lecciones, ensure_ascii=False) + ";\n"
             + "var KC_ANALITICA = " + json.dumps(ANALITICA) + ";\n")
    for archivo in ("temprano.js", "capa.css"):
        shutil.copy2(os.path.join(CAPA_DIR, archivo), os.path.join(SITIO, "kc", archivo))
    capa = io.open(os.path.join(CAPA_DIR, "capa.js"), encoding="utf-8").read()
    io.open(os.path.join(SITIO, "kc", "capa.js"), "w", encoding="utf-8", newline="\n").write(datos + capa)
    shutil.copy2(os.path.join(CAPA_DIR, "fuentes.css"), os.path.join(SITIO, "kc", "fuentes.css"))


def publicadas():
    """Las lecciones con animación, con su tema y su número (2.1, 3.1…)."""
    for t, (clave, _, _, lecciones) in enumerate(TEMARIO, 1):
        for l, lec in enumerate(lecciones, 1):
            if "fuente" in lec:
                yield clave, f"{t}.{l}", lec


def webp(nombre_jpg):
    return os.path.splitext(nombre_jpg)[0] + ".webp"


def copiar_animaciones():
    """Copia cada animación a /ia/<tema>/ con su nombre original (así siguen funcionando los enlaces entre ellas)."""
    shutil.rmtree(os.path.join(SITIO, "ia"), ignore_errors=True)
    shutil.rmtree(os.path.join(SITIO, "img"), ignore_errors=True)
    os.makedirs(os.path.join(SITIO, "img"))
    os.makedirs(os.path.join(SITIO, "js"), exist_ok=True)
    for archivo in ("cero.js", "cero_datos.js"):  # animación de portada «El cero que aprende»
        shutil.copy2(os.path.join(RAIZ, "herramientas", "animacion_cero", archivo), os.path.join(SITIO, "js", archivo))
    shutil.copy2(os.path.join(MINIATURAS, "compartir.png"), os.path.join(SITIO, "img", "compartir.png"))
    filas = []
    for clave, num, lec in publicadas():
        destino = os.path.join(SITIO, "ia", clave)
        os.makedirs(destino, exist_ok=True)
        origen = os.path.join(CURSO, lec["fuente"])
        nombre = os.path.basename(lec["fuente"])
        peso = mb(origen)
        if peso > LIMITE_MB:
            partir(origen, os.path.join(destino, nombre))
        else:
            shutil.copy2(origen, os.path.join(destino, nombre))
        Image.open(os.path.join(MINIATURAS, lec["miniatura"])).save(os.path.join(SITIO, "img", webp(lec["miniatura"])), "WEBP", quality=82, method=6)
        for ext in (".webm", ".mp4"):  # clip de la animación corriendo (lo graba herramientas/grabar_clips.py)
            clip = os.path.splitext(lec["miniatura"])[0] + ext
            if os.path.exists(os.path.join(MINIATURAS, clip)):
                shutil.copy2(os.path.join(MINIATURAS, clip), os.path.join(SITIO, "img", clip))
        lec["url"] = f"/ia/{clave}/{nombre[:-5]}"  # sin «.html»: Cloudflare sirve la página directo, sin la redirección 307
        lec["pagina"] = f"{CURSO_DL}{lec['slug']}/"
        agregar_capa(os.path.join(destino, nombre), lec)
        filas.append((lec["url"], peso))
    escribir_capa(list(publicadas()))
    return filas


def publicadas_en(temario):
    return sum("fuente" in l for _, _, _, lecciones in temario for l in lecciones)


def filas_cursos():
    return "".join(f'<a class="fila curso" href="/cursos/{c}/"><div class="n">{k:02d}</div><div><b>{nombre}</b><p>{html.escape(desc)}</p>'
                   f'<div class="d">{len(tem)} temas · {publicadas_en(tem)} lecciones publicadas</div></div></a>'
                   for k, (c, nombre, desc, tem) in enumerate(CURSOS, 1))


def miniatura(lec, clase="", carga="lazy"):
    ruta = version("/img/" + webp(lec["miniatura"]))
    return f'<img{clase} src="{ruta}" alt="{html.escape(lec["alt"])}" width="940" height="587" loading="{carga}">'


def clip(lec, solo_al_pasar=False):
    """La animación corriendo, en un video corto sin sonido. En el temario se anima al pasar el mouse;
    en la página de la lección se reproduce sola en bucle. Si no hay clip, queda la imagen fija."""
    base = os.path.splitext(lec["miniatura"])[0]
    if not os.path.exists(os.path.join(SITIO, "img", base + ".webm")):
        return miniatura(lec)
    poster = version("/img/" + webp(lec["miniatura"]))
    fuentes = "".join(f'<source src="{version("/img/" + base + ext)}" type="video/{ext[1:]}">' for ext in (".webm", ".mp4"))
    modo = 'preload="none" data-al-pasar' if solo_al_pasar else 'autoplay preload="auto"'
    return (f'<video class="clip" muted loop playsinline {modo} poster="{poster}" aria-label="{html.escape(lec["alt"])}">'
            f'{fuentes}</video>')


def construir_curso(clave_curso, nombre, desc_curso, temario):
    temas = []
    for t, (clave, titulo, desc, lecciones) in enumerate(temario, 1):
        filas = []
        for l, lec in enumerate(lecciones, 1):
            num = f"{t}.{l}"
            if "fuente" in lec:
                filas.append(f'<a class="fila pub" data-leccion="{lec["slug"]}" href="{lec["pagina"]}"><div class="n">{num}</div><div><b>{html.escape(lec["titulo"])}</b>'
                             f'<p>{html.escape(lec["desc"])}</p><div class="d">{lec["datos"]} · versión preliminar</div></div>'
                             f'{clip(lec, solo_al_pasar=True)}</a>')
            else:
                filas.append(f'<div class="fila pend"><div class="n">{num}</div><div><b>{html.escape(lec["titulo"])}</b></div><div class="d">en preparación</div></div>')
        temas.append(f'<section class="tema" id="{clave}"><h2>{titulo} <span>Tema {t}</span></h2><p>{html.escape(desc)}</p>{"".join(filas)}</section>')
    cuerpo = f"""<div class="cuerpo">
<main>
<section class="cabeza">
<div class="mono"><a href="/cursos/">Cursos</a> / {nombre} · actualizado el {ACTUALIZADO}</div>
<h1>{nombre}</h1>
<p>{html.escape(desc_curso)}</p>
<p class="aviso">Las animaciones publicadas son versiones preliminares: todavía están en revisión y pueden tener errores.</p>
</section>
{"".join(temas)}
</main>
</div>"""
    curso_ld = {"@context": "https://schema.org", "@type": "Course", "name": nombre, "description": desc_curso,
                "url": f"{DOMINIO}/cursos/{clave_curso}/", "inLanguage": "es",
                "provider": {"@type": "Organization", "name": "Ket Cero", "url": DOMINIO},
                "author": {"@type": "Person", "name": AUTOR, "url": f"{DOMINIO}/omar/"},
                "hasPart": [{"@type": "LearningResource", "name": lec["titulo"], "url": DOMINIO + lec["pagina"],
                             "description": lec["desc"]} for _, _, lec in publicadas()]}
    return pagina(f"{nombre} · Ket Cero", f"Curso de {nombre} desde cero, en español. {desc_curso}",
                  f"/cursos/{clave_curso}/", cuerpo, f"/cursos/{clave_curso}/", ld(curso_ld))


def construir_leccion(n, orden):
    """La página de una lección: qué vas a aprender, requisitos, cuánto dura y el botón para abrir la animación."""
    clave, num, lec = orden[n]
    tema = next(titulo for c, titulo, _, _ in TEMARIO if c == clave)
    ant = orden[n - 1][2] if n > 0 else None
    sig = orden[n + 1][2] if n + 1 < len(orden) else None
    vecinas = (f'<nav class="vecinas" aria-label="Lecciones">'
               + (f'<a href="{ant["pagina"]}">← {html.escape(ant["titulo"])}</a>' if ant else "<span></span>")
               + (f'<a href="{sig["pagina"]}">{html.escape(sig["titulo"])} →</a>' if sig else "<span></span>") + "</nav>")
    puntos = "".join(f"<li>{html.escape(p)}</li>" for p in lec["aprender"])
    cuerpo = f"""<div class="cuerpo solo leccion">
<main>
<section class="cabeza">
<div class="mono"><a href="/cursos/">Cursos</a> / <a href="{CURSO_DL}">Deep Learning</a> / <a href="{CURSO_DL}#{clave}">{html.escape(tema)}</a> · lección {num}</div>
<h1>{html.escape(lec["titulo"])}</h1>
<p>{html.escape(lec["desc"])}</p>
<div class="acciones"><a class="boton" href="{lec["url"]}" data-abre-animacion>Abrir la animación →</a>
<a id="seguir" class="ir" hidden data-leccion="{lec["slug"]}" data-animacion="{lec["url"]}" data-abre-animacion href="{lec["url"]}"></a></div>
<p class="aviso">Versión preliminar: todavía está en revisión y puede tener errores.</p>
</section>
<a class="figura" href="{lec["url"]}" data-abre-animacion>{clip(lec)}</a>
<section class="ficha">
<h2>Qué vas a aprender</h2>
<ul>{puntos}</ul>
<h2>Antes de empezar</h2>
<p>{html.escape(lec["requisitos"])}</p>
<h2>Cuánto dura</h2>
<p>{lec["datos"]}. A tu ritmo, unos {lec["minutos"]} minutos. Avanza con las flechas del teclado o con los botones de abajo; Ctrl + rueda del mouse acerca el dibujo.</p>
</section>
{vecinas}
</main>
</div>"""
    recurso = {"@context": "https://schema.org", "@type": "LearningResource", "name": lec["titulo"], "description": lec["desc"],
               "url": DOMINIO + lec["pagina"], "inLanguage": "es", "learningResourceType": "Animación interactiva",
               "educationalLevel": "Universitario", "timeRequired": f"PT{lec['minutos']}M",
               "teaches": lec["aprender"], "image": f"{DOMINIO}/img/{webp(lec['miniatura'])}",
               "author": {"@type": "Person", "name": AUTOR, "url": f"{DOMINIO}/omar/"},
               "isPartOf": {"@type": "Course", "name": "Deep Learning", "url": DOMINIO + CURSO_DL}}
    return pagina(f"{lec['titulo']} · Ket Cero", lec["desc"], lec["pagina"], cuerpo, lec["pagina"], ld(recurso))


def construir_cursos():
    cuerpo = f"""<div class="cuerpo">
<main>
<section class="cabeza">
<div class="mono">{len(CURSOS)} {"curso" if len(CURSOS) == 1 else "cursos"}</div>
<h1>Cursos</h1>
<p>Cada curso es un temario completo, con sus lecciones animadas paso a paso.</p>
</section>
<section class="tema">{filas_cursos()}</section>
</main>
</div>"""
    return pagina("Cursos · Ket Cero", "Cursos de machine learning desde cero, en español, con animaciones paso a paso.", "/cursos/", cuerpo, "/cursos/")


def franja_portada():
    """Pie de la primera pantalla: la última lección publicada, la señal para bajar y la siguiente en el orden del curso."""
    orden = [(clave, lec) for clave, _, _, lecciones in TEMARIO for lec in lecciones]
    k = max(i for i, (_, lec) in enumerate(orden) if "fuente" in lec)
    ultima = orden[k][1]
    proxima = next((lec for _, lec in orden[k + 1:] if "fuente" not in lec), None)
    derecha = f'<span>Próxima: {html.escape(proxima["titulo"].split(":")[0])}</span>' if proxima else "<span></span>"
    corto = lambda titulo: titulo.split(":")[0]
    return (f'<div class="franja"><a href="{ultima["pagina"]}">Última lección: {html.escape(corto(ultima["titulo"]))} →</a>'
            f'<a class="bajar" href="#lista-de-cursos">Cursos ↓</a>{derecha}</div>')


def construir_inicio():
    cuerpo = f"""<div class="cuerpo">
<main>
<section class="cabeza portada">
<div>
<div class="mono">Actualizado el {ACTUALIZADO}</div>
<h1>Machine learning desde cero, con cada operación a la vista.</h1>
<p>Deja de imaginarte cómo funciona una red neuronal. Míralo. Lecciones animadas, número por número.</p>
<a class="ir" href="/cursos/deep-learning/">Empezar el curso de Deep Learning →</a>
<div id="codigo" class="panel-codigo"></div>
</div>
<div class="lado">
<p class="explica">Una red ya entrenada mira un 0: su primer filtro busca bordes, casilla por casilla.</p>
<div id="cero" class="cero"></div>
</div>
{franja_portada()}
</section>
<section class="tema" id="lista-de-cursos"><h2>Cursos</h2><p>Empieza por aquí.</p>{filas_cursos()}</section>
</main>
</div>
<script src="{version('/js/cero_datos.js')}"></script>
<script src="{version('/js/cero.js')}"></script>
<script>montarCero(document.getElementById("cero"), window.DATOS_CERO, {{ codigo: document.getElementById("codigo") }});</script>"""
    sitio_ld = [{"@context": "https://schema.org", "@type": "WebSite", "name": "Ket Cero", "url": DOMINIO + "/", "inLanguage": "es",
                 "description": "Machine learning desde cero, en español: lecciones animadas paso a paso con los datos reales del entrenamiento."},
                {"@context": "https://schema.org", "@type": "Organization", "name": "Ket Cero", "url": DOMINIO + "/",
                 "logo": DOMINIO + "/favicon.svg", "founder": {"@type": "Person", "name": AUTOR, "url": f"{DOMINIO}/omar/"},
                 "sameAs": ["https://github.com/omramirezg/ketcero"]}]
    return pagina("Ket Cero · Machine learning desde cero",
                  "Machine learning desde cero, en español: cursos con lecciones animadas paso a paso hechas con los datos reales del entrenamiento.",
                  "/", cuerpo, "/", "".join(ld(o) for o in sitio_ld))


def construir_omar():
    persona = ld({"@context": "https://schema.org", "@type": "Person", "name": AUTOR,
                  "url": f"{DOMINIO}/omar/", "jobTitle": "Monitor de Deep Learning",
                  "sameAs": ["https://github.com/omramirezg"],
                  "worksFor": {"@type": "Organization", "name": "Ket Cero", "url": DOMINIO}})
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
              '<h1>Esta página no existe</h1><p>Puede que el enlace haya cambiado. <a href="/">Volver al inicio</a>.</p></section></main></div>')
    return pagina("Página no encontrada · Ket Cero", "La página que buscas no existe.", "/404", cuerpo)


# Encabezados que Cloudflare agrega a cada respuesta. Caché larga solo para archivos con ?v=huella o que nunca cambian;
# las páginas y la capa de /kc/ se revalidan en cada visita (respuesta 304, casi gratis).
CSP = ("default-src 'self'; script-src 'self' 'unsafe-inline' https://static.cloudflareinsights.com; "
       "style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self'; "
       "connect-src 'self' https://cloudflareinsights.com; object-src 'none'; base-uri 'self'; form-action 'self'; "
       "frame-ancestors 'self'; upgrade-insecure-requests")
LARGA = "public, max-age=31536000, immutable"
HEADERS = f"""/*
  Strict-Transport-Security: max-age=31536000; includeSubDomains
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=(), usb=()
  X-Frame-Options: SAMEORIGIN
  Cross-Origin-Opener-Policy: same-origin
  Content-Security-Policy: {CSP}

/fuentes/*
  Cache-Control: {LARGA}

/js/*
  Cache-Control: {LARGA}

/img/*
  Cache-Control: public, max-age=86400

/estilo.css
  Cache-Control: {LARGA}
"""


def escribir(ruta, texto):
    ruta = os.path.join(SITIO, ruta)
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    io.open(ruta, "w", encoding="utf-8", newline="\n").write(texto)


def main():
    filas = copiar_animaciones()
    orden = list(publicadas())
    escribir("index.html", construir_inicio())
    escribir("cursos/index.html", construir_cursos())
    for c in CURSOS:
        escribir(f"cursos/{c[0]}/index.html", construir_curso(*c))
    for n, (_, _, lec) in enumerate(orden):
        escribir(lec["pagina"].strip("/") + "/index.html", construir_leccion(n, orden))
    escribir("omar/index.html", construir_omar())
    escribir("404.html", construir_404())
    escribir("_headers", HEADERS)
    urls = (["/", "/cursos/"] + [f"/cursos/{c[0]}/" for c in CURSOS] + [lec["pagina"] for _, _, lec in orden]
            + ["/omar/"] + [u for u, _ in filas])
    hoy = date.today().isoformat()
    escribir("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
             + "".join(f"<url><loc>{DOMINIO}{u}</loc><lastmod>{hoy}</lastmod></url>\n" for u in urls) + "</urlset>\n")
    escribir("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {DOMINIO}/sitemap.xml\n")
    print(f"{len(filas)} animaciones copiadas ({sum(p for _, p in filas):.1f} MB). Sitio listo en {SITIO}")
    for u, p in filas:
        print(f"  {p:6.1f} MB  {u}")


if __name__ == "__main__":
    main()
