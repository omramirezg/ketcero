"""Arma el clip de cada lección: una secuencia de los pasos más vistosos de su animación (modo oscuro), cada uno
recortado a su contenido y llenando el cuadro, con fundidos suaves entre uno y otro.

Uso:  python herramientas/grabar_clips.py [https://ketcero.com] [--candidatos]
  --candidatos  captura muchos pasos y arma hojas de contacto en notas/capturas/ para elegir cuáles usar.
Deja en herramientas/miniaturas/: <clave>.webm, <clave>.mp4 y <clave>.jpg (la imagen fija es el primer paso).
Necesita ffmpeg en el PATH, Pillow y la librería playwright de Python.
"""
import os, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
BASE = ARGS[0] if ARGS else "https://ketcero.com"
CANDIDATOS = "--candidatos" in sys.argv
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA = os.path.join(RAIZ, "herramientas", "miniaturas")
A4 = "/ia/cnn/Animacion_A4_la_CNN_completa#"
B1 = "/ia/deteccion/Animacion_B1_Mini_YOLO_por_dentro#"
# clave de la lección: pasos elegidos (en orden) para su clip
CLIPS = {
    "cnn-completa": [A4 + "entrenar/12", A4 + "entrenar/7", A4 + "entrenar/14", A4 + "entrenar/15", A4 + "entrenar/30", A4 + "predecir/16"],
    "mini-yolo": [B1 + "entrenar/10", B1 + "predecir/7", B1 + "entrenar/21", B1 + "predecir/55", B1 + "predecir/61"],
}
OCULTAR = "#kc-zoom, #kc-seguir, #kc-movil, #kc-ayuda { display:none !important; }"
W, H = 1600, 900          # cuadro del clip (16:9)
FONDO = (17, 17, 17)      # el gris casi negro del sitio
SEG, FUNDIDO = 2.6, 0.7   # segundos de cada paso y del fundido


def capturar(rutas, carpeta):
    rutas_png = []
    with sync_playwright() as p:
        nav = p.chromium.launch(channel="chrome")
        ctx = nav.new_context(viewport={"width": 1600, "height": 900}, device_scale_factor=2)
        ctx.add_init_script("try{localStorage.setItem('tema','oscuro')}catch(e){}")
        pag = ctx.new_page()
        for k, ruta in enumerate(rutas):
            pag.goto(BASE + ruta, wait_until="load")
            pag.add_style_tag(content=OCULTAR)
            pag.wait_for_timeout(2600)
            # la barra del zoom (−, 1×, +, ⟲, Ampliar) se crea después: se esconde buscando su botón «Ampliar»
            pag.evaluate("""() => { for (const b of document.querySelectorAll('button')) if (/Ampliar/.test(b.textContent)) b.parentElement.style.display = 'none'; }""")
            pag.wait_for_timeout(200)
            png = os.path.join(carpeta, f"{k:02d}.png")
            pag.query_selector("#dibujo").screenshot(path=png)
            rutas_png.append(png)
        ctx.close(); nav.close()
    return rutas_png


def encuadrar(png):
    """Recorta al contenido (lo que no es fondo) y lo centra en un cuadro de 16:9 con margen."""
    im = Image.open(png).convert("RGB")
    fondo = Image.new("RGB", im.size, im.getpixel((im.width // 2, 4)))
    hay = np.array(ImageChops.difference(im, fondo).convert("L")) > 24
    # filas y columnas con contenido de verdad: se ignoran las líneas finas (bordes, separadores de una línea)
    def utiles(cuenta, minimo):
        con = cuenta > minimo
        # una fila/columna cuenta solo si al menos 12 de sus 31 vecinas también tienen contenido (las líneas sueltas no)
        vecinas = np.convolve(con.astype(int), np.ones(31, int), mode="same")
        return np.where(con & (vecinas >= 12))[0]
    filas = utiles(hay.sum(1), max(6, im.width * 0.004))
    cols = utiles(hay.sum(0), max(6, im.height * 0.004))
    if len(filas) and len(cols):
        m = 24
        im = im.crop((max(0, cols[0] - m), max(0, filas[0] - m), min(im.width, cols[-1] + m), min(im.height, filas[-1] + m)))
    escala = min((W * 0.92) / im.width, (H * 0.88) / im.height)
    im = im.resize((max(1, int(im.width * escala)), max(1, int(im.height * escala))), Image.LANCZOS)
    lienzo = Image.new("RGB", (W, H), FONDO)
    lienzo.paste(im, ((W - im.width) // 2, (H - im.height) // 2))
    lienzo.save(png)
    return png


def video(cuadros, base):
    entradas, filtros, n = [], [], len(cuadros)
    for c in cuadros:
        entradas += ["-loop", "1", "-t", f"{SEG + FUNDIDO:.2f}", "-i", c]
    previo, t = "0:v", SEG
    for k in range(1, n):
        filtros.append(f"[{previo}][{k}:v]xfade=transition=fade:duration={FUNDIDO}:offset={t:.2f}[v{k}]")
        previo, t = f"v{k}", t + SEG
    filtros.append(f"[{previo}]scale=1280:-2,fps=24,format=yuv420p[sal]")
    comun = ["ffmpeg", "-y", "-loglevel", "error", *entradas, "-filter_complex", ";".join(filtros), "-map", "[sal]", "-an"]
    subprocess.run(comun + ["-c:v", "libvpx-vp9", "-b:v", "0", "-crf", "36", "-row-mt", "1", base + ".webm"], check=True)
    subprocess.run(comun + ["-c:v", "libx264", "-crf", "26", "-preset", "slow", "-movflags", "+faststart", base + ".mp4"], check=True)
    Image.open(cuadros[0]).resize((1280, 720), Image.LANCZOS).save(base + ".jpg", quality=88)


def main():
    if CANDIDATOS:
        destino = os.path.join(RAIZ, "notas", "capturas", "candidatos")
        os.makedirs(destino, exist_ok=True)
        grupos = {"a4": [A4 + f"entrenar/{k}" for k in range(5, 40)] + [A4 + f"predecir/{k}" for k in range(1, 44, 3)],
                  "b1": [B1 + f"predecir/{k}" for k in range(1, 67, 2)] + [B1 + f"entrenar/{k}" for k in range(5, 60, 3)]}
        for nombre, rutas in grupos.items():
            tmp = tempfile.mkdtemp()
            for k, png in enumerate(capturar(rutas, tmp)):
                Image.open(encuadrar(png)).resize((480, 270)).save(os.path.join(destino, f"{nombre}_{k:02d}_{rutas[k].split('#')[1].replace('/', '_')}.jpg"))
        print("candidatos en", destino)
        return
    os.makedirs(SALIDA, exist_ok=True)
    for clave, rutas in CLIPS.items():
        tmp = tempfile.mkdtemp()
        cuadros = [encuadrar(png) for png in capturar(rutas, tmp)]
        base = os.path.join(SALIDA, clave)
        video(cuadros, base)
        print(clave, {e: f"{os.path.getsize(base + e) / 1e6:.2f} MB" for e in (".webm", ".mp4", ".jpg")})


if __name__ == "__main__":
    main()
