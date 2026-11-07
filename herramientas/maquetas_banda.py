"""Maquetas de color para la banda de la red (CSS inyectado; no cambia el sitio).
Uso: python herramientas/maquetas_banda.py http://localhost:PUERTO  -> notas/capturas/banda/
Los colores se escriben en modo claro: el modo oscuro invierte (invert + hue-rotate), así que
un relleno pastel claro se ve como un tinte oscuro y un borde medio se ve como un acento claro."""
import os, sys
from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8895"
SALIDA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "notas", "capturas", "banda")
FIG = ":is(rect,path,polygon,circle,ellipse):not(.hit)"
FAM = {  # familia -> selector de grupos
    "entrada": '[data-capa="entrada"]',
    "bajada": '[data-capa^="b"]',
    "pool": '[data-capa^="p"]',
    "fondo": '[data-capa="f"]',
    "subir": '[data-capa^="u"]',
    "pegar": '[data-capa^="c"]',
    "subida": '[data-capa^="s"]:not([data-capa="sal"])',
    "salida": ':is([data-capa="sal"],[data-capa="f1"],[data-capa="f2"])',
}

def regla(fam, relleno=None, borde=None, grosor=None):
    s = f"#dibujo g{FAM[fam]}"
    css = ""
    if relleno:
        css += f'{s} {FIG}[fill="#FFFFFF"],{s} {FIG}[fill="#fff"],{s} {FIG}[fill="white"]{{fill:{relleno}!important}}'
    if borde:
        css += f'{s} {FIG}:not([stroke="none"]){{stroke:{borde}!important' + (f";stroke-width:{grosor}" if grosor else "") + "}"
    return css

def paleta(d, grosor=None):
    return "".join(regla(f, *v, grosor) for f, v in d.items())

# colores en modo claro (en oscuro se invierten): relleno pastel -> tinte oscuro, borde -> acento claro
OPCIONES = [
    ("0_actual", "Actual (sin color)", ""),
    ("A_familias", "A · Por familia, suave (codificador azul, fondo violeta, decodificador verde, uniones coral)",
     paleta({"entrada": ("#ECECEC", "#5A5A5A"), "bajada": ("#DCE7F3", "#2F5F8F"), "pool": (None, "#2F5F8F"),
             "fondo": ("#E7E0F3", "#5B3F8F"), "subir": (None, "#2F7A5C"), "pegar": ("#F8E1D8", "#B4532C"),
             "subida": ("#DCEFE6", "#2F7A5C"), "salida": ("#F8E1D8", "#B4532C")})),
    ("B_solo_borde", "B · Solo el borde de color (cajas oscuras, contorno de la familia)",
     paleta({"entrada": (None, "#5A5A5A"), "bajada": (None, "#2F5F8F"), "pool": (None, "#2F5F8F"),
             "fondo": (None, "#5B3F8F"), "subir": (None, "#2F7A5C"), "pegar": (None, "#B4532C"),
             "subida": (None, "#2F7A5C"), "salida": (None, "#B4532C")}, grosor=1.3)),
    ("C_un_acento", "C · Un solo acento coral: solo las operaciones (pool, subir, pegar, pérdida)",
     paleta({"pool": (None, "#B4532C"), "subir": (None, "#B4532C"), "pegar": ("#F8E1D8", "#B4532C"),
             "salida": ("#F8E1D8", "#B4532C")})),
    ("D_la_U", "D · La forma de la U: azul al bajar, se calienta en el fondo, coral al subir",
     paleta({"entrada": ("#ECECEC", "#5A5A5A"), "bajada": ("#DCE7F3", "#2F5F8F"), "pool": (None, "#4A5F8F"),
             "fondo": ("#EADCF0", "#6E3F8F"), "subir": (None, "#A2483A"), "pegar": ("#F6E2D6", "#A85A2C"),
             "subida": ("#F8E1D8", "#B4532C"), "salida": ("#F3E6C8", "#8F6A1F")})),
    ("E_calido", "E · Tonos cálidos tierra (arena, oliva, coral), sin azules",
     paleta({"entrada": ("#EEE9E0", "#6E665A"), "bajada": ("#EFE6D2", "#8A6A2F"), "pool": (None, "#8A6A2F"),
             "fondo": ("#E6E9D6", "#5E6A2F"), "subir": (None, "#5E6A2F"), "pegar": ("#F8E1D8", "#B4532C"),
             "subida": ("#E2EAD9", "#4F6E3A"), "salida": ("#F8E1D8", "#B4532C")})),
]
BASE_CSS = "html.kc-oscuro{filter:invert(.92) hue-rotate(180deg) sepia(.14)!important}"

def main():
    os.makedirs(SALIDA, exist_ok=True)
    with sync_playwright() as p:
        nav = p.chromium.launch(channel="chrome")
        ctx = nav.new_context(viewport={"width": 1700, "height": 760}, device_scale_factor=1.5)
        ctx.add_init_script("try{localStorage.setItem('tema','oscuro')}catch(e){}")
        pag = ctx.new_page()
        pag.goto(BASE + "/ia/segmentacion/Animacion_U1_UNet_por_dentro#entrenar/1", wait_until="load", timeout=120000)
        pag.wait_for_timeout(2500)
        pag.click("#codbtn"); pag.wait_for_timeout(900)
        pag.add_style_tag(content=BASE_CSS)
        caja = pag.evaluate("(()=>{const g=[...document.querySelectorAll('#dibujo g[data-capa]')].map(e=>e.getBoundingClientRect());"
                            "return [Math.min(...g.map(r=>r.left))-14, Math.min(...g.map(r=>r.top))-10, Math.max(...g.map(r=>r.right))+14, Math.max(...g.map(r=>r.bottom))+10]})()")
        clip = {"x": caja[0], "y": caja[1], "width": caja[2] - caja[0], "height": caja[3] - caja[1]}
        for clave, _, css in OPCIONES:
            pag.evaluate("(c)=>{let s=document.getElementById('maqueta');if(!s){s=document.createElement('style');s.id='maqueta';document.head.appendChild(s)}s.textContent=c}", css)
            pag.wait_for_timeout(300)
            pag.screenshot(path=os.path.join(SALIDA, f"{clave}.png"), clip=clip)
        nav.close()
    fuente = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 30)
    ims = [Image.open(os.path.join(SALIDA, f"{c}.png")) for c, _, _ in OPCIONES]
    w = max(i.width for i in ims); h = sum(i.height + 60 for i in ims) + 10
    hoja = Image.new("RGB", (w + 20, h), (40, 40, 40)); d = ImageDraw.Draw(hoja); y = 10
    for (c, nombre, _), im in zip(OPCIONES, ims):
        d.text((10, y), nombre, fill=(240, 240, 240), font=fuente); hoja.paste(im, (10, y + 48)); y += im.height + 60
    hoja.save(os.path.join(SALIDA, "comparar_banda.jpg"), quality=90)
    print("listo")

if __name__ == "__main__":
    main()
