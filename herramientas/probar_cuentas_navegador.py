"""Prueba de punta a punta de cuentas y progreso, todo en el computador (wrangler dev + D1 local, sin correos).

1. Sin cuenta: resolver el ejercicio 1 lo guarda en el navegador.
2. Pedir el enlace (en local la API lo devuelve), abrirlo, pulsar «Entrar»: queda la sesión y el progreso sube.
3. Otro navegador limpio entra con el mismo correo y ve el ejercicio como resuelto.

Uso:  (cd apps/web && PUBLIC_API_ACTIVA=si npm run build)
      (cd apps/api && npx wrangler d1 migrations apply ketcero --local --env local && npx wrangler dev --env local)
      python herramientas/probar_cuentas_navegador.py [puerto]
"""
import json, os, sys, time
from playwright.sync_api import sync_playwright

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "packages", "practica", "src"))
import ejercicios  # noqa: E402

PUERTO = sys.argv[1] if len(sys.argv) > 1 else "8787"
BASE = f"http://localhost:{PUERTO}"
LECCION = "la-derivada-que-usa-una-red"
URL = f"{BASE}/practica/{LECCION}/"
CORREO = f"prueba{int(time.time())}@ejemplo.com"
CAPTURAS = os.path.join(REPO, "notas", "capturas", "astro")


def resolver(pagina, codigo):
    pagina.click("#ejercicio-1 .cm-content")
    pagina.keyboard.press("Control+A")
    pagina.keyboard.insert_text(codigo)
    pagina.click("#ejercicio-1 [data-comprobar]")
    pagina.locator("#ejercicio-1 [data-comprobar]:not([disabled])").wait_for(timeout=120_000)
    return pagina.inner_text("#ejercicio-1 .estado")


def entrar(pagina):
    pagina.fill("#correo", CORREO)
    pagina.click("[data-entrar] button")
    pagina.locator("[data-enlace-prueba]").wait_for(timeout=10_000)
    enlace = pagina.get_attribute("[data-enlace-prueba]", "href")
    pagina.goto(enlace)
    pagina.click("button[type=submit]")
    pagina.wait_for_url(URL, timeout=10_000)
    pagina.locator("[data-con-sesion]:not([hidden])").wait_for(timeout=10_000)


def main():
    e1 = ejercicios.de_leccion(os.path.join(REPO, "contenido", "practica", LECCION))[0]
    fallas = []
    with sync_playwright() as p:
        nav = p.chromium.launch(channel="chrome")
        a = nav.new_context(viewport={"width": 1280, "height": 900}).new_page()
        errores = []
        a.on("pageerror", lambda e: errores.append(str(e)))
        a.goto(URL)
        r = resolver(a, e1["solucion"])
        print("sin cuenta:", r)
        local = a.evaluate("localStorage.getItem('ketcero:progreso')")
        print("localStorage:", local)
        if "practica:" + LECCION + "/" + e1["id"] not in (local or ""):
            fallas.append("el progreso no quedó en localStorage")
        entrar(a)
        print("entró como:", a.inner_text("[data-correo]"))
        a.screenshot(path=os.path.join(CAPTURAS, "cuentas-con-sesion.png"))
        a.wait_for_timeout(1500)  # la sincronización corre al cargar
        remoto = a.evaluate("fetch('/api/progreso').then(r => r.json())")
        print("en D1:", json.dumps(remoto, ensure_ascii=False))
        if not any(x["clave"].endswith(e1["id"]) and x["valor"]["resuelto"] for x in remoto.get("entradas", [])):
            fallas.append("el progreso no llegó a D1")

        b = nav.new_context(viewport={"width": 1280, "height": 900}).new_page()
        b.goto(URL)
        if "Ya lo resolviste" in b.inner_text("#ejercicio-1 .estado"):
            fallas.append("un navegador limpio ya decía resuelto antes de entrar")
        b.screenshot(path=os.path.join(CAPTURAS, "cuentas-sin-sesion.png"))
        entrar(b)
        b.locator("#ejercicio-1 .estado:has-text('Ya lo resolviste')").wait_for(timeout=10_000)
        print("otro navegador:", b.inner_text("#ejercicio-1 .estado"))
        b.click("[data-salir]")
        b.locator("[data-sin-sesion]:not([hidden])").wait_for(timeout=10_000)
        if b.evaluate("fetch('/api/yo').then(r => r.status)") != 401:
            fallas.append("salir no cerró la sesión")
        if errores:
            fallas.append(f"errores de página: {errores}")
        nav.close()
    print("\n" + ("Todo bien." if not fallas else "FALLAS:\n- " + "\n- ".join(fallas)))
    sys.exit(1 if fallas else 0)


if __name__ == "__main__":
    main()
