"""Maquetas de estilo: la misma página con distintas paletas, inyectadas como CSS (no cambia el sitio).
Uso: python herramientas/maquetas_estilo.py http://localhost:PUERTO   → notas/capturas/maquetas/
"""
import os, sys
from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8893"
SALIDA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "notas", "capturas", "maquetas")
CORAL = "#D85A30"


def sitio(fondo, tinta, gris, linea, texto, coral=False):
    css = f":root,:root[data-tema=claro]{{--fondo:{fondo};--tinta:{tinta};--gris:{gris};--linea:{linea};--texto:{texto};--texto2:{texto};--marca:{linea}}}"
    if coral:
        css += (f".ir{{border-bottom-color:{CORAL}!important;border-bottom-width:2px!important}}"
                f".hamb{{border-color:{CORAL}!important}}"
                f".fila.pub{{border-left:2px solid transparent;padding-left:10px}}.fila.pub:hover{{border-left-color:{CORAL}}}"
                f".fila.pub .clip,.fila.pub img{{border-color:{CORAL}55!important}}"
                f"nav a[aria-current=page]{{border-bottom:2px solid {CORAL};padding-bottom:3px}}"
                f".tema h2{{border-left:3px solid {CORAL};padding-left:12px}}"
                f".franja{{border-top-color:{CORAL}88!important}}")
    return css


def animacion(filtro, coral=False, contraste=False):
    css = f"html.kc-oscuro{{filter:{filtro}!important}}"
    if coral:  # antes de invertir: el coral sobrevive (la inversión + hue-rotate deja el tono y aclara)
        css += ("#cabeza .sec.act{border-bottom-color:#8E2E0E!important;color:#000!important}"
                "#modos button.on{background:#8E2E0E!important;border-color:#8E2E0E!important}"
                "#progv{background:#8E2E0E!important}#prog{height:6px!important}")
    if contraste:
        css += ("#cabeza .sec{color:#5A5A5A!important}#estado button.b{font-size:15px!important;height:30px!important}"
                "#estado .txt{color:#3A3A3A!important}")
    return css


VARIANTES = [
    ("0_actual", "Actual", "", ""),
    ("1_calido", "1 · Oscuro cálido",
     sitio("#16130F", "#F1EBE0", "#A59E92", "#2F2A23", "#D9D2C6"),
     animacion("invert(.92) hue-rotate(180deg) sepia(.14)")),
    ("2_calido_coral", "2 · Cálido + acento coral",
     sitio("#16130F", "#F1EBE0", "#A59E92", "#2F2A23", "#D9D2C6", coral=True),
     animacion("invert(.92) hue-rotate(180deg) sepia(.14)", coral=True)),
    ("3_calido_coral_contraste", "3 · Cálido + coral + más contraste",
     sitio("#16130F", "#FFFFFF", "#C2BBAF", "#38322A", "#E6DFD3", coral=True),
     animacion("invert(.92) hue-rotate(180deg) sepia(.14)", coral=True, contraste=True)),
    ("4_tinta_azul", "4 · Azul tinta + coral",
     sitio("#0F1720", "#EEF3F8", "#9AA8B8", "#22303F", "#D3DCE6", coral=True),
     animacion("invert(.92) hue-rotate(180deg) sepia(.3) hue-rotate(175deg) saturate(1.4)", coral=True)),
    ("5_papel_claro", "5 · Claro papel (claro por defecto)",
     sitio("#F7F3EC", "#1B1A17", "#6E685E", "#E2DBCF", "#3A362F", coral=True),
     "html.kc-oscuro{filter:sepia(.12)!important}" + animacion("sepia(.12)", coral=False)),
]
PAGINAS = [("portada", "/", False), ("temario", "/cursos/deep-learning/#segmentacion", False),
           ("animacion", "/ia/segmentacion/Animacion_U1_UNet_por_dentro#entrenar/1", True)]


def main():
    os.makedirs(SALIDA, exist_ok=True)
    with sync_playwright() as p:
        nav = p.chromium.launch(channel="chrome")
        for clave, nombre, css_sitio, css_anim in VARIANTES:
            ctx = nav.new_context(viewport={"width": 1600, "height": 900})
            ctx.add_init_script("try{localStorage.setItem('tema','oscuro')}catch(e){}")
            for pnom, ruta, es_anim in PAGINAS:
                pag = ctx.new_page()
                pag.goto(BASE + ruta, wait_until="load", timeout=120000)
                css = css_anim if es_anim else css_sitio
                if clave == "5_papel_claro" and not es_anim:
                    pag.evaluate("document.documentElement.setAttribute('data-tema','claro')")
                if css:
                    pag.add_style_tag(content=css)
                pag.wait_for_timeout(3500 if pnom == "portada" else 1800)
                pag.screenshot(path=os.path.join(SALIDA, f"{pnom}_{clave}.png"))
                pag.close()
            ctx.close()
        nav.close()
    # hojas de comparación por página: 2 columnas × 3 filas, con el nombre de cada variante
    try:
        fuente = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 28)
    except OSError:
        fuente = ImageFont.load_default()
    for pnom, _, _ in PAGINAS:
        w, h = 800, 450
        hoja = Image.new("RGB", (2 * w + 30, 3 * (h + 50) + 10), (40, 40, 40))
        d = ImageDraw.Draw(hoja)
        for k, (clave, nombre, _, _) in enumerate(VARIANTES):
            im = Image.open(os.path.join(SALIDA, f"{pnom}_{clave}.png")).resize((w, h), Image.LANCZOS)
            x, y = 10 + (k % 2) * (w + 10), 10 + (k // 2) * (h + 50)
            d.text((x, y), nombre, fill=(240, 240, 240), font=fuente)
            hoja.paste(im, (x, y + 40))
        hoja.save(os.path.join(SALIDA, f"comparar_{pnom}.jpg"), quality=88)
    print("listo:", SALIDA)


if __name__ == "__main__":
    main()
