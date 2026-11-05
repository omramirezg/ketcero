"""Genera herramientas/miniaturas/compartir.png (1200 × 630): la imagen que sale al compartir ketcero.com.

Usa los datos reales de la animación de portada (el 0 de prueba y el mapa de su filtro) y las fuentes del sitio.
Uso:  python herramientas/imagen_compartir.py
"""
import io, json, os
from playwright.sync_api import sync_playwright

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = json.load(open(os.path.join(RAIZ, "herramientas", "animacion_cero", "datos_cero.json"), encoding="utf-8"))
f = D["filtro_principal"]
X, M = D["entrada"], D["mapas"][f]
pos = max([v for fila in M for v in fila if v > 0] + [1e-6])
neg = max([-v for fila in M for v in fila if v < 0] + [1e-6])


def color(v):
    if v == 0:
        return "transparent"
    r, g, b = (216, 90, 48) if v > 0 else (29, 158, 117)
    a = min(1, abs(v) / (pos if v > 0 else neg)) ** 0.9
    return f"rgba({r},{g},{b},{a:.3f})"


c = 13
celdas = []
for i in range(28):
    for j in range(28):
        celdas.append(f'<rect x="{j*c}" y="{i*c}" width="{c-1}" height="{c-1}" fill="#2A2A2A" fill-opacity=".35"/>')
        if X[i][j] > 0:
            celdas.append(f'<rect x="{j*c}" y="{i*c}" width="{c-1}" height="{c-1}" fill="#EDEDED" fill-opacity="{X[i][j]*0.92:.3f}"/>')
xm, ym = 28 * c + 34, 2 * c
for i in range(24):
    for j in range(24):
        celdas.append(f'<rect x="{xm+j*c}" y="{ym+i*c}" width="{c-1}" height="{c-1}" fill="{color(M[i][j])}" stroke="#2A2A2A" stroke-width=".5"/>')
ancho_svg, alto_svg = xm + 24 * c, 28 * c
fuentes = os.path.join(RAIZ, "sitio", "fuentes").replace("\\", "/")
pagina = f"""<!doctype html><html><head><meta charset="utf-8"><style>
@font-face {{ font-family:'Plex'; font-weight:400 600; src:url(file:///{fuentes}/IBMPlexSans-latin.woff2) format('woff2'); }}
@font-face {{ font-family:'PlexMono'; src:url(file:///{fuentes}/IBMPlexMono-latin.woff2) format('woff2'); }}
body {{ margin:0; width:1200px; height:630px; background:#111111; color:#EDEDED; font-family:'Plex'; display:flex; align-items:center; justify-content:space-between; padding:0 70px; box-sizing:border-box; }}
.marca {{ display:flex; align-items:center; gap:16px; font-weight:600; font-size:40px; }}
h1 {{ font-weight:600; font-size:44px; line-height:1.12; letter-spacing:-.8px; margin:34px 0 18px; max-width:460px; }}
p {{ font-family:'PlexMono'; font-size:19px; color:#9A9A9A; margin:0; }}
</style></head><body>
<div><div class="marca"><svg width="62" height="44" viewBox="0 0 44 30"><line x1="5" y1="3" x2="5" y2="27" stroke="#EDEDED" stroke-width="3" stroke-linecap="round"/>
<ellipse cx="19" cy="15" rx="6" ry="11" fill="none" stroke="#D85A30" stroke-width="3"/>
<polyline points="31,3 39,15 31,27" fill="none" stroke="#EDEDED" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>Ket Cero</div>
<h1>Machine learning desde cero, con cada operación a la vista.</h1>
<p>ketcero.com</p></div>
<svg width="{ancho_svg}" height="{alto_svg}" viewBox="0 0 {ancho_svg} {alto_svg}" style="width:{ancho_svg*0.86:.0f}px">{''.join(celdas)}</svg>
</body></html>"""
salida = os.path.join(RAIZ, "herramientas", "miniaturas", "compartir.png")
with sync_playwright() as p:
    nav = p.chromium.launch(channel="chrome")
    pag = nav.new_page(viewport={"width": 1200, "height": 630})
    temporal = os.path.join(RAIZ, "herramientas", "miniaturas", "_compartir.html")
    io.open(temporal, "w", encoding="utf-8").write(pagina)
    pag.goto("file:///" + temporal.replace("\\", "/"))
    pag.evaluate("document.fonts.ready")
    pag.wait_for_timeout(300)
    pag.screenshot(path=salida)
    nav.close()
    os.remove(temporal)
print("listo:", salida)
