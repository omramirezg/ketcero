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
    ("redes-profundas", "Redes neuronales profundas", "Qué es una red, cuándo le gana al machine learning clásico y cómo aprende con descenso de gradiente.", [
        {"titulo": "¿Machine learning o deep learning? Depende de cuántos datos hay"},
        {"titulo": "Una red que pinta un mapa de cultivos"},
    ]),
    ("cnn", "Redes convolucionales", "Cómo una red lee una imagen.", [
        {"titulo": "La CNN completa, por dentro",
         "fuente": "Semana_02/02_Clase_viernes_30_oct/1_Densa_vs_CNN_MNIST/Animacion_A4_la_CNN_completa.html",
         "miniatura": "cnn-completa.jpg",
         "alt": "La pérdida de cada imagen del lote en la CNN completa",
         "desc": "Una LeNet-5 aprende a leer dígitos de MNIST: lotes reales, la pérdida de cada imagen, el backward capa por capa y el paso de AdamW.",
         "datos": "86 pasos entrenar · 43 predecir · 5 épocas", "pasos": 86 + 43},
        {"titulo": "Transfer learning: hojas de café sanas o enfermas"},
        {"titulo": "Clasificar sin entrenar: CLIP contra una CNN"},
    ]),
    ("deteccion", "Detección de objetos", "Encontrar y encerrar objetos: cajas, puntajes, IoU y NMS.", [
        {"titulo": "Mini-YOLO por dentro: dígitos en la calle",
         "fuente": "Semana_03/02_Clase_viernes_6_nov/1_Mini_YOLO_digitos_en_la_calle/Animacion_B1_Mini_YOLO_por_dentro.html",
         "miniatura": "mini-yolo.jpg", "fotos": True,
         "alt": "El NMS del Mini-YOLO borra las cajas que se solapan",
         "desc": "Una red pequeña al estilo YOLO aprende a encontrar dígitos sobre fotos reales de la calle, desde la red recién nacida hasta las cajas finales.",
         "datos": "186 pasos entrenar · 66 predecir · 30 épocas", "pasos": 186 + 66},
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

LOGO = ('<svg width="34" height="24" viewBox="0 0 44 30" aria-hidden="true"><line x1="5" y1="3" x2="5" y2="27" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>'
        '<ellipse cx="19" cy="15" rx="6" ry="11" fill="none" stroke="#C8502A" stroke-width="3"/>'
        '<polyline points="31,3 39,15 31,27" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>')
# Aplica el tema guardado antes de pintar (sin parpadeo) y maneja el botón Oscuro / Claro.
TEMA_JS = '<script>try{var t=localStorage.getItem("tema");if(t)document.documentElement.dataset.tema=t}catch(e){}</script>\n'
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
</script>"""
FUENTES = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
           '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
           '<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono&display=swap" rel="stylesheet">\n')


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
<div class="izq"><button id="menu" class="hamb" type="button" aria-expanded="false" aria-controls="cajon" aria-label="Abrir los cursos"><span></span><span></span><span></span></button>
<a class="marca" href="/">{LOGO}Ket Cero<small>Machine learning desde cero</small></a></div>
<nav>{enlaces}<button id="tema" type="button" role="switch" aria-checked="true"><span>Modo oscuro</span><span class="pista"><span class="perilla"></span></span></button></nav>
</div></header>
<div id="velo" class="velo" hidden></div>
<aside id="cajon" class="cajon" aria-label="Cursos">
{cajon}
</aside>
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


# Capa que el sitio agrega a cada animación publicada (los originales del curso no se tocan):
# - la misma cabecera del sitio (marca, Cursos, Quién soy, interruptor de modo oscuro) y el aviso de versión preliminar;
# - la animación se escala en el alto que queda debajo de la cabecera (se ajusta su función escalar());
# - la interfaz con la letra y el estilo sobrio del sitio, sin cursivas;
# - modo oscuro por inversión de colores (invert .93 deja el blanco en #121212, como el fondo del sitio); la cabecera
#   y las fotos llevan colores «pre-invertidos» para verse igual que en el resto del sitio.
KC_ALTO = 65
CAPA_TEMPRANA = """<script>var KC_ALTO = %d;try{if(localStorage.getItem("tema")!=="claro")document.documentElement.classList.add("kc-oscuro")}catch(e){document.documentElement.classList.add("kc-oscuro")}</script>
""" % KC_ALTO
CAPA_HEAD = """<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono&display=swap" rel="stylesheet">
<style>
/* --- cabecera del sitio --- */
#kc-cab { --f:#FFFFFF; --t:#161616; --g:#6B6B6B; --l:#E2E2E2; --cero:#C8502A;
  position:fixed; top:0; left:0; right:0; height:%(alto)dpx; box-sizing:border-box; z-index:50; display:flex; align-items:center; justify-content:space-between;
  padding:0 24px; background:var(--f); border-bottom:1px solid var(--l); font:14px "IBM Plex Sans", system-ui, sans-serif; color:var(--t); }
html.kc-oscuro #kc-cab { --f:#FFFFFF; --t:#000000; --g:#616161; --l:#E3E3E3; --cero:#FF8255; }   /* tras invertir: #121212, #EDEDED, #9A9A9A, #2A2A2A, coral */
#kc-cab a { color:inherit; text-decoration:none; }
#kc-cab .kc-marca { display:flex; align-items:center; gap:10px; font-weight:600; font-size:18px; color:var(--t); }
#kc-cab .kc-marca small { font-weight:400; color:var(--g); font-size:14px; margin-left:8px; padding-left:12px; border-left:1px solid var(--l); }
#kc-cab nav { display:flex; align-items:center; gap:28px; }
#kc-cab nav a, #kc-cab nav button { color:var(--g); font:14px "IBM Plex Sans", system-ui, sans-serif; }
#kc-cab nav a:hover, #kc-cab nav button:hover { color:var(--t); }
#kc-cab .kc-aviso { font:12px "IBM Plex Mono", monospace; color:var(--g); }
#kc-cab .kc-volver { color:var(--t) !important; }
#kc-tema { display:inline-flex; align-items:center; gap:10px; background:none; border:0; padding:0; cursor:pointer; }
.kc-pista { position:relative; width:34px; height:18px; box-sizing:border-box; border:1px solid var(--g); border-radius:9px; }
.kc-perilla { position:absolute; top:2px; left:2px; width:12px; height:12px; border-radius:50%%; background:var(--g); transition:transform .15s; }
#kc-tema[aria-checked="true"] .kc-pista { background:var(--t); border-color:var(--t); }
#kc-tema[aria-checked="true"] .kc-perilla { transform:translateX(16px); background:var(--f); }
/* --- la animación debajo de la cabecera --- */
#codigo { top:%(alto)dpx !important; }
#codbtn { top:%(boton)dpx !important; }
/* --- estilo del sitio en la interfaz de la animación --- */
* { font-style:normal !important; }
#modos button, #cabeza, #cabeza button, #texto, #inicio, #inicio h1, #inicio h2, #inicio p, #estado, #barra, #pie, #codcab, #codbtn, #velS, #vctl, #pestBanda {
  font-family:"IBM Plex Sans", system-ui, sans-serif !important; }
#cont, #inicio .sub, #inicio .op .n, #inicio .pie, #estado .txt { font-family:"IBM Plex Mono", monospace !important; }
#modos button { background:transparent !important; color:#6B6B6B !important; border-color:#D6D6D6 !important; font-size:15px !important; }
#modos button.on { color:#161616 !important; border-color:#161616 !important; font-weight:500; }
#modos button:not(.on):hover { color:#161616 !important; background:transparent !important; }
#cabeza .sec { color:#6B6B6B !important; font-weight:400 !important; }
#cabeza .sec.hecho { color:#3A3A3A !important; }
#cabeza .sec.act { color:#161616 !important; font-weight:500 !important; border-color:#161616 !important; border-bottom-color:#161616 !important; }
#cabeza .sec:hover { color:#161616 !important; }
#regla { border-top:1px solid #161616 !important; }
#regla2 { border-top:1px solid #D6D6D6 !important; }
#inicio h1 { text-align:left !important; left:200px !important; font-weight:600 !important; font-size:34px !important; letter-spacing:-.5px; }
#inicio .sub { text-align:left !important; left:200px !important; font-size:14px !important; color:#6B6B6B !important; }
#inicio .op { border:1px solid #E2E2E2 !important; box-shadow:none !important; background:transparent !important; }
#inicio .op:hover { border-color:#161616 !important; }
#inicio .op h2 { text-align:left !important; margin:34px 36px 0 !important; font-weight:600 !important; font-size:28px !important; }
#inicio .op p { text-align:left !important; margin:16px 36px 0 !important; font-size:18px !important; line-height:1.55 !important; color:#3A3A3A; }
#inicio .op .n { text-align:left !important; left:36px !important; right:36px !important; font-size:13px !important; color:#6B6B6B !important; }
#inicio .pie { text-align:left !important; left:200px !important; font-size:13px !important; }
#estado { background:transparent !important; border-color:#E2E2E2 !important; }
#codbtn { font-size:14px !important; }
#codbtn:not(.on) { border-color:#D6D6D6 !important; }
#codbtn.on { background:transparent !important; border-color:#161616 !important; color:#161616 !important; }
/* --- modo oscuro --- */
html.kc-oscuro { filter:invert(.93) hue-rotate(180deg); }
/* en las lecciones con fotos reales (data-kc-fotos) las imágenes se vuelven a invertir para conservar sus colores;
   en las demás (dígitos y mapas) las imágenes se oscurecen igual que los dibujos */
html.kc-oscuro[data-kc-fotos] img, html.kc-oscuro[data-kc-fotos] image, html.kc-oscuro video { filter:hue-rotate(180deg) invert(1) contrast(1.163); }
html.kc-oscuro #kc-cab .kc-cero { stroke:#FF8255; }
</style>
""" % {"alto": KC_ALTO, "boton": KC_ALTO + 10}
LOGO_KC = ('<svg width="34" height="24" viewBox="0 0 44 30" aria-hidden="true"><line x1="5" y1="3" x2="5" y2="27" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>'
           '<ellipse class="kc-cero" cx="19" cy="15" rx="6" ry="11" fill="none" stroke="#C8502A" stroke-width="3"/>'
           '<polyline points="31,3 39,15 31,27" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>')
CAPA_BODY = """<header id="kc-cab"><a class="kc-marca" href="/">""" + LOGO_KC + """Ket Cero<small>Machine learning desde cero</small></a>
<nav><span class="kc-aviso">Versión preliminar: en revisión, puede tener errores</span><a class="kc-volver" href="{curso}">← Volver al curso</a><a href="/cursos/">Cursos</a><a href="/omar/">Quién soy</a>
<button id="kc-tema" type="button" role="switch" aria-checked="true">Modo oscuro<span class="kc-pista"><span class="kc-perilla"></span></span></button></nav></header>
<script>
(function () {
  var r = document.documentElement, b = document.getElementById("kc-tema");
  function poner() { b.setAttribute("aria-checked", r.classList.contains("kc-oscuro") ? "true" : "false"); }
  b.addEventListener("click", function () {
    r.classList.toggle("kc-oscuro");
    try { localStorage.setItem("tema", r.classList.contains("kc-oscuro") ? "oscuro" : "claro"); } catch (e) {}
    poner();
  });
  poner();
})();
</script>
"""


# Zoom del dibujo (svg#dibujo): se acerca cambiando su viewBox, así solo se mueve lo de adentro del cuadro
# (el SVG recorta lo que sale de su caja) y el texto vectorial queda nítido. «Ampliar» deja solo el dibujo en pantalla completa.
# Al cambiar de paso (cambia el #hash) o si el motor pone otro viewBox, vuelve a la vista completa.
CAPA_ZOOM = """<div id="kc-zoom" role="toolbar" aria-label="Zoom del dibujo"><button type="button" data-z="menos" title="Alejar">−</button><span class="kc-nivel">1×</span><button type="button" data-z="mas" title="Acercar (también Ctrl + rueda del mouse o pellizcar)">+</button><button type="button" data-z="cero" title="Vista completa">⟲</button><button type="button" data-z="ampliar" title="Ver solo el dibujo en pantalla completa (Esc para salir)">Ampliar</button></div>
<style>
#kc-zoom { position:fixed; z-index:45; display:none; align-items:center; background:#FFFFFF; border:1px solid #D6D6D6; font:13px "IBM Plex Sans", system-ui, sans-serif; color:#3A3A3A; user-select:none; }
#kc-zoom button { background:none; border:0; border-left:1px solid #E2E2E2; padding:5px 11px; color:#3A3A3A; font:inherit; cursor:pointer; line-height:1.2; }
#kc-zoom button:first-child { border-left:0; }
#kc-zoom button:hover { color:#161616; }
#kc-zoom .kc-nivel { min-width:34px; padding:0 4px; text-align:center; font:12px "IBM Plex Mono", monospace; color:#6B6B6B; border-left:1px solid #E2E2E2; }
html.kc-zoom-activo #dibujo { cursor:grab; overflow:hidden !important; }
html.kc-arrastrando #dibujo { cursor:grabbing; }
#dibujo { touch-action:pan-x pan-y; }
html.kc-zoom-activo #dibujo { touch-action:none; }
html.kc-ampliado #kc-cab, html.kc-ampliado #codigo, html.kc-ampliado #codbtn, html.kc-ampliado #marco > :not(#dibujo) { visibility:hidden !important; }
html.kc-ampliado #marco { transform:none !important; left:0 !important; top:0 !important; width:100vw !important; height:100vh !important; }
html.kc-ampliado #dibujo { visibility:visible !important; position:fixed !important; left:24px !important; top:20px !important; width:calc(100vw - 48px) !important; height:calc(100vh - 76px) !important; }
html.kc-ampliado body { background:#FFFFFF; }
</style>
<script>
(function () {
  var svg = document.getElementById("dibujo"), caja = document.getElementById("kc-zoom"), r = document.documentElement;
  if (!svg || !caja) return;
  var nivel = caja.querySelector(".kc-nivel"), botonAmpliar = caja.querySelector('[data-z="ampliar"]');
  var z = 1, base = null, propio = null, hash = location.hash, MAX = 6;
  function leer() { var v = (svg.getAttribute("viewBox") || "").trim().split(/[\\s,]+/).map(Number); return v.length === 4 && v.every(isFinite) ? v : null; }
  function texto(v) { return v.map(function (n) { return +n.toFixed(3); }).join(" "); }
  // pone el zoom nz manteniendo fijo el punto (px, py) del dibujo; sin punto, acerca hacia el centro de lo que se ve
  function poner(nz, px, py) {
    if (!base) { base = leer(); if (!base) return; }
    nz = Math.max(1, Math.min(MAX, nz));
    var c = leer() || base, w = base[2] / nz, h = base[3] / nz, x, y;
    if (px == null) { x = c[0] + c[2] / 2 - w / 2; y = c[1] + c[3] / 2 - h / 2; }
    else { x = px - (px - c[0]) * (w / c[2]); y = py - (py - c[1]) * (h / c[3]); }
    x = Math.max(base[0], Math.min(base[0] + base[2] - w, x));
    y = Math.max(base[1], Math.min(base[1] + base[3] - h, y));
    z = nz;
    if (z <= 1.001) { z = 1; propio = null; svg.setAttribute("viewBox", texto(base)); }
    else { propio = texto([x, y, w, h]); svg.setAttribute("viewBox", propio); }
    r.classList.toggle("kc-zoom-activo", z > 1);
    nivel.textContent = (Math.round(z * 10) / 10).toString().replace(".", ",") + "×";
  }
  function reiniciar() { if (z > 1 && base) poner(1); base = null; z = 1; propio = null; r.classList.remove("kc-zoom-activo"); nivel.textContent = "1×"; }
  // si el motor cambia el viewBox (un paso nuevo, un paso ancho), esa pasa a ser la vista completa
  new MutationObserver(function () {
    var v = svg.getAttribute("viewBox");
    if (v === propio || (z === 1 && base && v === texto(base))) return;
    base = null; z = 1; propio = null; r.classList.remove("kc-zoom-activo"); nivel.textContent = "1×";
  }).observe(svg, { attributes: true, attributeFilter: ["viewBox"] });
  setInterval(function () { if (location.hash !== hash) { hash = location.hash; reiniciar(); } ubicar(); }, 250);
  function punto(ev) { var p = svg.createSVGPoint(); p.x = ev.clientX; p.y = ev.clientY; return p.matrixTransform(svg.getScreenCTM().inverse()); }
  caja.addEventListener("click", function (ev) {
    var b = ev.target.closest("button"); if (!b) return;
    var q = b.getAttribute("data-z");
    if (q === "mas") poner(z * 1.5); else if (q === "menos") poner(z / 1.5); else if (q === "cero") poner(1); else if (q === "ampliar") ampliar(!r.classList.contains("kc-ampliado"));
  });
  // Ctrl + rueda: acerca alrededor del puntero (la rueda sola sigue siendo de la página)
  svg.addEventListener("wheel", function (ev) {
    if (!ev.ctrlKey) return;
    ev.preventDefault(); ev.stopPropagation();
    var p = punto(ev); poner(z * Math.exp(-Math.max(-120, Math.min(120, ev.deltaY)) * 0.0015), p.x, p.y);
  }, { passive: false, capture: true });
  // arrastrar para moverse (solo con zoom) y pellizcar con dos dedos
  var dedos = {}, arrastre = null, pellizco = null, movido = false;
  svg.addEventListener("pointerdown", function (ev) {
    dedos[ev.pointerId] = { x: ev.clientX, y: ev.clientY };
    var ids = Object.keys(dedos);
    if (ids.length === 2) {
      var a = dedos[ids[0]], b = dedos[ids[1]];
      pellizco = { d: Math.hypot(a.x - b.x, a.y - b.y), z: z }; arrastre = null; return;
    }
    if (z > 1 && ev.button === 0) { arrastre = { x: ev.clientX, y: ev.clientY, v: leer() }; movido = false; svg.setPointerCapture(ev.pointerId); }
  });
  svg.addEventListener("pointermove", function (ev) {
    if (!dedos[ev.pointerId]) return;
    dedos[ev.pointerId] = { x: ev.clientX, y: ev.clientY };
    var ids = Object.keys(dedos);
    if (pellizco && ids.length === 2) {
      var a = dedos[ids[0]], b = dedos[ids[1]], m = punto({ clientX: (a.x + b.x) / 2, clientY: (a.y + b.y) / 2 });
      poner(pellizco.z * Math.hypot(a.x - b.x, a.y - b.y) / pellizco.d, m.x, m.y); ev.preventDefault(); return;
    }
    if (!arrastre || !base) return;
    var dx = ev.clientX - arrastre.x, dy = ev.clientY - arrastre.y;
    if (Math.abs(dx) + Math.abs(dy) > 3) { movido = true; r.classList.add("kc-arrastrando"); }
    var k = svg.getScreenCTM().a, v = arrastre.v;
    var x = Math.max(base[0], Math.min(base[0] + base[2] - v[2], v[0] - dx / k));
    var y = Math.max(base[1], Math.min(base[1] + base[3] - v[3], v[1] - dy / k));
    propio = texto([x, y, v[2], v[3]]); svg.setAttribute("viewBox", propio);
  });
  function soltar(ev) {
    delete dedos[ev.pointerId];
    if (Object.keys(dedos).length < 2) pellizco = null;
    arrastre = null; r.classList.remove("kc-arrastrando");
  }
  svg.addEventListener("pointerup", soltar); svg.addEventListener("pointercancel", soltar);
  // un arrastre no cuenta como clic sobre el dibujo
  svg.addEventListener("click", function (ev) { if (movido) { ev.stopPropagation(); ev.preventDefault(); movido = false; } }, true);
  function ampliar(si) {
    r.classList.toggle("kc-ampliado", si);
    botonAmpliar.textContent = si ? "Cerrar" : "Ampliar";
    try {
      if (si && r.requestFullscreen && !document.fullscreenElement) r.requestFullscreen().catch(function () {});
      if (!si && document.fullscreenElement) document.exitFullscreen().catch(function () {});
    } catch (e) {}
    ubicar();
  }
  document.addEventListener("fullscreenchange", function () { if (!document.fullscreenElement && r.classList.contains("kc-ampliado")) ampliar(false); });
  document.addEventListener("keydown", function (ev) { if (ev.key === "Escape" && r.classList.contains("kc-ampliado")) ampliar(false); });
  // los controles van en la esquina inferior derecha del cuadro del dibujo, solo cuando hay dibujo a la vista
  function ubicar() {
    if (r.classList.contains("kc-ampliado")) {
      caja.style.display = "flex"; caja.style.left = "auto"; caja.style.top = "auto"; caja.style.right = "24px"; caja.style.bottom = "14px"; return;
    }
    var b = svg.getBoundingClientRect(), inicio = document.getElementById("inicio");
    var hay = b.width > 120 && b.height > 80 && getComputedStyle(svg).display !== "none" && getComputedStyle(svg).visibility !== "hidden"
      && svg.childElementCount > 1 && !(inicio && inicio.offsetParent !== null && getComputedStyle(inicio).display !== "none");
    caja.style.display = hay ? "flex" : "none";
    if (!hay) return;
    caja.style.right = "auto"; caja.style.bottom = "auto";
    caja.style.left = Math.max(8, b.right - caja.offsetWidth - 8) + "px";
    caja.style.top = Math.max(8, b.bottom - caja.offsetHeight - 8) + "px";
  }
  addEventListener("resize", ubicar);
  ubicar();
})();
</script>
"""


def agregar_capa(ruta, curso, fotos=False):
    s = io.open(ruta, encoding="utf-8").read()
    if fotos:
        s = s.replace("<html", "<html data-kc-fotos", 1)
    # la animación se escala en el alto que deja la cabecera y se baja esa misma altura
    assert s.count("innerHeight") == 3 and "m.style.top = ((innerHeight" in s, ruta
    s = s.replace("m.style.top = ((innerHeight", "m.style.top = KC_ALTO + ((innerHeight")
    s = s.replace("innerHeight", "(innerHeight - KC_ALTO)")
    i = s.index("<head>") + len("<head>")
    s = s[:i] + "\n" + CAPA_TEMPRANA + s[i:]
    j = s.index("</head>")
    s = s[:j] + CAPA_HEAD + s[j:]
    k = s.rindex("</body>")
    s = s[:k] + CAPA_BODY.replace("{curso}", curso) + CAPA_ZOOM + s[k:]
    io.open(ruta, "w", encoding="utf-8").write(s)


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
    os.makedirs(os.path.join(SITIO, "js"), exist_ok=True)
    for archivo in ("cero.js", "cero_datos.js"):  # animación de portada «El cero que aprende»
        shutil.copy2(os.path.join(RAIZ, "herramientas", "animacion_cero", archivo), os.path.join(SITIO, "js", archivo))
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
        agregar_capa(os.path.join(destino, nombre), f"/cursos/deep-learning/#{clave}", lec.get("fotos", False))
        lec["url"] = f"/ia/{clave}/{nombre[:-5]}"  # sin «.html»: Cloudflare sirve la página directo, sin la redirección 307
        filas.append((lec["url"], peso))
    return filas


def publicadas_en(temario):
    return sum("fuente" in l for _, _, _, lecciones in temario for l in lecciones)


def filas_cursos():
    return "".join(f'<a class="fila curso" href="/cursos/{c}/"><div class="n">{k:02d}</div><div><b>{nombre}</b><p>{html.escape(desc)}</p>'
                   f'<div class="d">{len(tem)} temas · {publicadas_en(tem)} lecciones publicadas</div></div></a>'
                   for k, (c, nombre, desc, tem) in enumerate(CURSOS, 1))


def construir_curso(clave_curso, nombre, desc_curso, temario):
    temas = []
    for t, (clave, titulo, desc, lecciones) in enumerate(temario, 1):
        filas = []
        for l, lec in enumerate(lecciones, 1):
            num = f"{t}.{l}"
            if "fuente" in lec:
                filas.append(f'<a class="fila pub" href="{lec["url"]}"><div class="n">{num}</div><div><b>{html.escape(lec["titulo"])}</b>'
                             f'<p>{html.escape(lec["desc"])}</p><div class="d">{lec["datos"]} · versión preliminar</div></div>'
                             f'<img src="/img/{lec["miniatura"]}" alt="{html.escape(lec["alt"])}" loading="lazy"></a>')
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
    return pagina(f"{nombre} · Ket Cero", f"Curso de {nombre} desde cero, en español. {desc_curso}",
                  f"/cursos/{clave_curso}/", cuerpo, f"/cursos/{clave_curso}/")


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
    return (f'<div class="franja"><a href="{ultima["url"]}">Última lección: {html.escape(corto(ultima["titulo"]))} →</a>'
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
<script src="/js/cero_datos.js"></script>
<script src="/js/cero.js"></script>
<script>montarCero(document.getElementById("cero"), window.DATOS_CERO, {{ codigo: document.getElementById("codigo") }});</script>"""
    return pagina("Ket Cero · Machine learning desde cero",
                  "Machine learning desde cero, en español: cursos con lecciones animadas paso a paso hechas con los datos reales del entrenamiento.",
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
              '<h1>Esta página no existe</h1><p>Puede que el enlace haya cambiado. <a href="/">Volver al inicio</a>.</p></section></main></div>')
    return pagina("Página no encontrada · Ket Cero", "La página que buscas no existe.", "/404", cuerpo)


def escribir(ruta, texto):
    ruta = os.path.join(SITIO, ruta)
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    io.open(ruta, "w", encoding="utf-8", newline="\n").write(texto)


def main():
    filas = copiar_animaciones()
    escribir("index.html", construir_inicio())
    escribir("cursos/index.html", construir_cursos())
    for c in CURSOS:
        escribir(f"cursos/{c[0]}/index.html", construir_curso(*c))
    escribir("omar/index.html", construir_omar())
    escribir("404.html", construir_404())
    urls = ["/", "/cursos/"] + [f"/cursos/{c[0]}/" for c in CURSOS] + ["/omar/"] + [u for u, _ in filas]
    hoy = date.today().isoformat()
    escribir("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
             + "".join(f"<url><loc>{DOMINIO}{u}</loc><lastmod>{hoy}</lastmod></url>\n" for u in urls) + "</urlset>\n")
    escribir("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {DOMINIO}/sitemap.xml\n")
    print(f"{len(filas)} animaciones copiadas ({sum(p for _, p in filas):.1f} MB). Sitio listo en {SITIO}")
    for u, p in filas:
        print(f"  {p:6.1f} MB  {u}")


if __name__ == "__main__":
    main()
