"""Prueba de punta a punta de la práctica en Chrome: Pyodide carga con la CSP de /practica/*, la solución de
referencia pasa, el código inicial falla, un ciclo infinito se corta y la página no tiene errores de consola.

Uso:  python herramientas/servidor_local.py 8890   (en otra terminal)
      python herramientas/probar_practica_navegador.py [puerto]
Guarda capturas en notas/capturas/astro/practica-*.png
"""
import os, sys
from playwright.sync_api import sync_playwright

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "packages", "practica", "src"))
import ejercicios  # noqa: E402

PUERTO = sys.argv[1] if len(sys.argv) > 1 else "8890"
LECCION = "la-derivada-que-usa-una-red"
URL = f"http://localhost:{PUERTO}/practica/{LECCION}/"
CAPTURAS = os.path.join(REPO, "notas", "capturas", "astro")


def poner_codigo(pagina, caja, codigo):
    # se selecciona todo y se inserta de un golpe (escribir tecla por tecla haría que el editor reindente)
    pagina.click(f"#{caja} .cm-content")
    pagina.keyboard.press("Control+A")
    pagina.keyboard.insert_text(codigo)
    puesto = pagina.evaluate(f"document.querySelector('#{caja} .cm-content').innerText")
    if puesto.strip().split() != codigo.strip().split():
        raise SystemExit(f"No se pudo poner el código en {caja}: " + repr(puesto))


def comprobar(pagina, caja, espera=120_000):
    pagina.click(f"#{caja} [data-comprobar]")
    # (wait_for_function usa eval y la CSP de la página lo prohíbe, así que se espera el botón desde aquí)
    pagina.locator(f"#{caja} [data-comprobar]:not([disabled])").wait_for(timeout=espera)
    return pagina.inner_text(f"#{caja} .estado")


def main():
    os.makedirs(CAPTURAS, exist_ok=True)
    fallas = []
    with sync_playwright() as p:
        nav = p.chromium.launch(channel="chrome")
        for tema in ("oscuro", "claro"):
            pagina = nav.new_page(viewport={"width": 1280, "height": 900})
            consola, csp = [], []
            pagina.on("console", lambda m: consola.append(m.text) if m.type == "error" else None)
            pagina.on("pageerror", lambda e: consola.append(str(e)))
            if tema == "claro":
                pagina.add_init_script("localStorage.setItem('tema','claro')")
            pagina.goto(URL)
            pagina.evaluate("document.addEventListener('securitypolicyviolation', e => console.error('CSP ' + e.violatedDirective))")
            todos = ejercicios.de_leccion(os.path.join(REPO, "contenido", "practica", LECCION))
            for n, e in enumerate(todos):
                e["caja"] = f"ejercicio-{n + 1}"
            if tema == "oscuro":
                for e in todos:
                    poner_codigo(pagina, e["caja"], e["solucion"])
                    r = comprobar(pagina, e["caja"])
                    print(f"{e['id']:28s} solución   → {r}")
                    if not r.startswith("Pasa las"):
                        fallas.append(f"{e['id']}: la solución no pasa en el navegador ({r})")
                    for nombre, cod in e["errores"].items():
                        poner_codigo(pagina, e["caja"], cod)
                        r = comprobar(pagina, e["caja"])
                        print(f"{'':28s} error      → {r}  ({nombre})")
                        if r.startswith("Pasa las"):
                            fallas.append(f"{e['id']}: el error «{nombre}» pasa en el navegador")
                # ciclo infinito: el trabajador se mata a los 10 s y la página sigue viva
                primero = todos[0]["caja"]
                poner_codigo(pagina, primero, "def derivada(f, x, h=1e-5):\n    while True:\n        pass\n")
                r = comprobar(pagina, primero, espera=30_000)
                print(f"{primero:28s} ciclo      → {r[:70]}…")
                if "segundos" not in r:
                    fallas.append("el ciclo infinito no se cortó")
                poner_codigo(pagina, primero, todos[0]["solucion"])
                r = comprobar(pagina, primero)
                print(f"{primero:28s} de nuevo   → {r}")
                if not r.startswith("Pasa las"):
                    fallas.append("después de cortar el ciclo, Python no volvió a cargar")
                # deja el ejercicio 2 con un error a la vista para la captura
                seg = todos[1]
                poner_codigo(pagina, seg["caja"], list(seg["errores"].values())[0])
                comprobar(pagina, seg["caja"])
                pagina.locator(f"#{seg['caja']}").scroll_into_view_if_needed()
            else:
                poner_codigo(pagina, todos[0]["caja"], todos[0]["inicial"])
                r = comprobar(pagina, todos[0]["caja"])
                print(f"{todos[0]['id']:28s} inicial    → {r}  (tema claro)")
                pagina.locator(f"#{todos[0]['caja']}").scroll_into_view_if_needed()
            pagina.screenshot(path=os.path.join(CAPTURAS, f"practica-{tema}.png"))
            pagina.screenshot(path=os.path.join(CAPTURAS, f"practica-{tema}-completa.png"), full_page=True)
            if consola:
                fallas.append(f"errores de consola ({tema}): {consola}")
            pagina.close()
        movil = nav.new_page(viewport={"width": 390, "height": 844})
        movil.goto(URL)
        ancho = movil.evaluate("document.documentElement.scrollWidth")
        movil.screenshot(path=os.path.join(CAPTURAS, "practica-movil.png"), full_page=True)
        if ancho > 390:
            fallas.append(f"en el celular la página se desborda ({ancho}px)")
        nav.close()
    print("\n" + ("Todo bien." if not fallas else "FALLAS:\n- " + "\n- ".join(fallas)))
    sys.exit(1 if fallas else 0)


if __name__ == "__main__":
    main()
