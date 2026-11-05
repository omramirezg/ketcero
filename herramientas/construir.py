"""Arma el sitio de Ket Cero en ../sitio: copia las animaciones del curso y genera las páginas.

Uso:  python herramientas/construir.py
Vuelve a correrlo cada vez que cambie una animación o se agregue una nueva al CATALOGO.
"""
import html, io, os, shutil
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
        ("Semana_02/02_Clase_viernes_30_oct/1_Densa_vs_CNN_MNIST/Animacion_A1_la_ventana.html", "La ventana de 3 × 3", "Un filtro recorre el dígito y en cada posición multiplica y suma: así nace un mapa de características."),
        ("Semana_02/02_Clase_viernes_30_oct/1_Densa_vs_CNN_MNIST/Animacion_A2_filtro_RGB.html", "Un filtro sobre una foto a color", "Con tres canales (rojo, verde y azul) el filtro también tiene tres capas, y sus resultados se suman."),
        ("Semana_02/02_Clase_viernes_30_oct/1_Densa_vs_CNN_MNIST/Animacion_A3_de_la_imagen_a_la_prediccion.html", "De la imagen a la predicción", "El recorrido de una imagen por toda la red, hasta los puntajes de cada dígito."),
        ("Semana_02/02_Clase_viernes_30_oct/1_Densa_vs_CNN_MNIST/Animacion_A4_la_CNN_completa.html", "La CNN completa, por dentro", "La red entera con un lote real: convoluciones, pooling, aplanado, capa densa y la vuelta del entrenamiento."),
        ("Semana_02/02_Clase_viernes_30_oct/1_Densa_vs_CNN_MNIST/Animacion_A5_canales_en_3D.html", "Los canales, en 3D", "Los mapas de cada filtro apilados en profundidad, para ver qué es un «canal»."),
        ("Semana_02/02_Clase_viernes_30_oct/1_Densa_vs_CNN_MNIST/Animacion_A6_la_red_en_3D.html", "La red en 3D", "La arquitectura completa en tres dimensiones, capa por capa."),
        ("Semana_02/02_Clase_viernes_30_oct/1_Densa_vs_CNN_MNIST/Animacion_A7_aplanar_a_densa_a_escala.html", "De aplanar a la densa, a escala", "Cómo los mapas se vuelven un vector largo y entran a la capa densa, con los tamaños reales."),
    ]),
    ("transfer-learning", "Transfer learning", "Reutilizar una red que ya aprendió de millones de fotos para resolver un problema nuevo con pocos datos.", [
        ("Semana_02/02_Clase_viernes_30_oct/2_Transfer_Hojas_de_cafe/Animacion_T_tres_competidores.html", "Los tres competidores", "Desde cero, red congelada o ajuste fino: la misma foto de una hoja de café y tres formas de aprender."),
        ("Semana_02/02_Clase_viernes_30_oct/2_Transfer_Hojas_de_cafe/Animacion_T_transfer_learning_por_dentro.html", "Transfer learning por dentro: hojas de café", "ResNet18 preentrenada decidiendo si una hoja de café está sana o enferma, paso a paso."),
        ("Semana_02/04_Complementarios/Transfer_Perros_vs_gatos/Animacion_T_transfer_learning_A.html", "Perros y gatos", "El caso clásico: una red de ImageNet adaptada para distinguir perros de gatos."),
        ("Semana_02/04_Complementarios/Transfer_EuroSAT/Animacion_T_transfer_learning_C.html", "Imágenes de satélite (EuroSAT)", "Transfer learning cuando las fotos se parecen poco a las de ImageNet."),
    ]),
    ("zero-shot", "Zero-shot con CLIP", "Clasificar sin entrenar: un modelo que entiende imágenes y texto a la vez.", [
        ("Semana_02/03_Asesoria_miercoles_4_nov/3_Zero_shot_GTSRB/Animacion_Z_CLIP_vs_CNN.html", "CLIP zero-shot contra una CNN entrenada", "Señales de tránsito: CLIP solo con descripciones en texto, frente a una CNN entrenada con miles de fotos."),
    ]),
    ("deteccion", "Detección de objetos", "Encontrar y encerrar objetos en una imagen: cajas, puntajes y cómo se mide si el detector es bueno.", [
        ("Semana_03/02_Clase_viernes_6_nov/2_YOLO11_huecos/Animacion_B2_del_monton_de_cajas_al_mAP.html", "Del montón de cajas al mAP", "De miles de cajas candidatas a la métrica que resume qué tan bueno es un detector."),
        ("Semana_03/02_Clase_viernes_6_nov/2_YOLO11_huecos/Animacion_B4_la_trampa_de_las_copias.html", "La trampa de las copias", "Por qué fotos casi repetidas entre entrenamiento y prueba inflan los resultados."),
    ]),
    ("llm", "Modelos de lenguaje", "Construir un modelo de lenguaje desde la idea más simple.", [
        ("Temas_de_estudio_extra/04_Construir_mi_LLM/Animacion_Clase_01_el_bigrama.html", "El bigrama de letras", "El modelo de lenguaje más pequeño posible: predecir la siguiente letra contando parejas."),
    ]),
    ("aprendizaje-automatico", "Aprendizaje automático", "Los modelos clásicos, entendidos número por número.", [
        ("Temas_de_estudio_extra/03_Ruta_ML_Engineer/Semana_01_Regresion_lineal/Animacion_regresion_lineal.html", "La regresión lineal: ¿cuánto vale una casa?", "Ajustar una recta a los datos con descenso de gradiente, paso a paso."),
    ]),
]

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


def copiar_animaciones():
    """Copia cada animación a /ia/<tema>/ con su nombre original (así siguen funcionando los enlaces entre ellas)."""
    filas = []
    for clave, _, _, anims in CATALOGO:
        destino = os.path.join(SITIO, "ia", clave)
        os.makedirs(destino, exist_ok=True)
        for fuente, titulo, desc in anims:
            origen = os.path.join(CURSO, fuente)
            nombre = os.path.basename(fuente)
            peso = mb(origen)
            if peso > LIMITE_MB:
                raise SystemExit(f"{nombre} pesa {peso:.1f} MB: pasa el límite de {LIMITE_MB} MB de Cloudflare Pages")
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
