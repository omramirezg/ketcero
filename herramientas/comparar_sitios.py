"""Compara el sitio nuevo (local) con el publicado: capturas lado a lado, errores de consola, CSP y desborde.

Uso:  python herramientas/comparar_sitios.py http://localhost:8890 [carpeta_capturas]
"""
import json, os, sys
from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

LOCAL = sys.argv[1]
PUBLICADO = "https://ketcero.com"
DESTINO = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "notas", "capturas", "astro")
PAGINAS = ["/", "/cursos/", "/cursos/deep-learning/", "/cursos/deep-learning/la-cnn-completa/",
           "/cursos/deep-learning/mini-yolo-digitos-en-la-calle/", "/cursos/deep-learning/tipos-de-segmentacion/",
           "/cursos/deep-learning/unet-edificios-en-fotos-satelitales/", "/omar/", "/no-existe"]
SOLO_LOCAL = ["/rutas/"]
os.makedirs(DESTINO, exist_ok=True)
VIGILA = """() => { window.__csp = []; document.addEventListener('securitypolicyviolation', e => window.__csp.push(e.violatedDirective + ' ' + e.blockedURI)); }"""


def captura(nav, base, ruta, ancho, tema, nombre):
    ctx = nav.new_context(viewport={"width": ancho, "height": 900 if ancho > 900 else 844})
    ctx.add_init_script(f"try{{localStorage.setItem('tema','{tema}')}}catch(e){{}}")
    ctx.add_init_script(f"({VIGILA})()")
    pag = ctx.new_page()
    errores = []
    pag.on("console", lambda m: errores.append(m.text[:160]) if m.type == "error" else None)
    pag.on("pageerror", lambda e: errores.append(str(e)[:160]))
    pag.goto(base + ruta, wait_until="load", timeout=90000)
    pag.wait_for_timeout(1200)
    info = pag.evaluate("() => ({ancho: document.documentElement.scrollWidth, cliente: document.documentElement.clientWidth, csp: window.__csp || []})")
    pag.screenshot(path=nombre, full_page=True)
    ctx.close()
    errores = [e for e in errores if "404" not in e or ruta != "/no-existe"]
    return {"errores": errores, "desborde": info["ancho"] > info["cliente"] + 1, "csp": info["csp"]}


def diferencia(a, b):
    ia, ib = Image.open(a).convert("RGB"), Image.open(b).convert("RGB")
    if ia.size != ib.size:
        return f"tamaño distinto {ia.size} vs {ib.size}"
    caja = ImageChops.difference(ia, ib).point(lambda v: 255 if v > 24 else 0).convert("L")
    return round(sum(1 for p in caja.getdata() if p) / (ia.width * ia.height) * 100, 2)


def main():
    informe = []
    with sync_playwright() as p:
        nav = p.chromium.launch(channel="chrome")
        for ruta in PAGINAS + SOLO_LOCAL:
            for ancho in (1600, 390):
                for tema in ("oscuro", "claro"):
                    clave = (ruta.strip("/").replace("/", "_") or "portada") + f"_{ancho}_{tema}"
                    nuevo = os.path.join(DESTINO, clave + "_nuevo.png")
                    r = captura(nav, LOCAL, ruta, ancho, tema, nuevo)
                    fila = {"pagina": ruta, "ancho": ancho, "tema": tema, **r}
                    if ruta not in SOLO_LOCAL:
                        viejo = os.path.join(DESTINO, clave + "_publicado.png")
                        captura(nav, PUBLICADO, ruta, ancho, tema, viejo)
                        fila["diferencia_%"] = diferencia(nuevo, viejo)
                    informe.append(fila)
                    print(json.dumps(fila, ensure_ascii=False), flush=True)
        nav.close()
    json.dump(informe, open(os.path.join(DESTINO, "informe.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
