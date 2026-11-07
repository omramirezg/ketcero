"""Servidor de prueba para sitio/: imita lo que hace Cloudflare.

- Aplica las reglas de sitio/_headers (encabezados de caché y de seguridad, incluida la CSP).
- Sirve las direcciones sin «.html» (/ia/cnn/Animacion_A4_la_CNN_completa → .html) y las carpetas con index.html.
- Usa sitio/404.html cuando una página no existe.

Uso:  python herramientas/servidor_local.py [puerto] [carpeta]
      carpeta: por omisión la salida de Astro (apps/web/dist); usa «sitio» para la del generador anterior.
"""
import fnmatch, http.server, os, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAIZ = os.path.join(REPO, sys.argv[2] if len(sys.argv) > 2 else os.path.join("apps", "web", "dist"))


def leer_reglas():
    reglas, actual = [], None
    ruta = os.path.join(RAIZ, "_headers")
    if not os.path.exists(ruta):
        return reglas
    for linea in open(ruta, encoding="utf-8"):
        if not linea.strip() or linea.lstrip().startswith("#"):
            continue
        if not linea[0].isspace():
            actual = (linea.strip(), [])
            reglas.append(actual)
        elif actual and ":" in linea:
            nombre, valor = linea.strip().split(":", 1)
            actual[1].append((nombre.strip(), valor.strip()))
    return reglas


class Manejador(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=RAIZ, **k)

    def translate_path(self, path):
        ruta = super().translate_path(path)
        if not os.path.exists(ruta) and os.path.exists(ruta + ".html"):
            return ruta + ".html"
        return ruta

    def send_error(self, code, message=None, explain=None):
        if code == 404 and os.path.exists(os.path.join(RAIZ, "404.html")):
            cuerpo = open(os.path.join(RAIZ, "404.html"), "rb").read()
            self.send_response(404)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(cuerpo)))
            self.end_headers()
            self.wfile.write(cuerpo)
            return
        super().send_error(code, message, explain)

    def end_headers(self):
        camino = self.path.split("?")[0]
        for patron, encabezados in leer_reglas():
            if fnmatch.fnmatch(camino, patron.replace("*", "*")):
                for nombre, valor in encabezados:
                    self.send_header(nombre, valor)
        super().end_headers()

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    puerto = int(sys.argv[1]) if len(sys.argv) > 1 else 8870
    print(f"Sirviendo {RAIZ} en http://localhost:{puerto}/")
    http.server.ThreadingHTTPServer(("127.0.0.1", puerto), Manejador).serve_forever()
