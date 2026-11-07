"""Arma escenas animadas de Ket Cero (formato «ketcero-escena», versión 1) desde Python.

La escena es solo datos: objetos (matrices, marcos, textos, fórmulas, flechas) y pasos que les cambian campos.
El sitio la dibuja con packages/motor/src/escena.ts. Especificación completa: packages/motor/ESCENA.md

    from ketcero.escena import Escena
    e = Escena("Una convolución", ancho=1600, alto=900, credito="Animación hecha por …")
    x = e.matriz("x", 40, 80, imagen, celda=20, etiqueta="x · 28 × 28")
    e.paso("La imagen", "Cada casilla es un píxel entre 0 y 1.", e.mostrar("x"))
    e.guardar("escena.json")

Las fórmulas se escriben en LaTeX y se compilan aquí (latex + dvisvgm) a trazos SVG que toman el color del texto.
"""
import hashlib, io, json, os, re, shutil, subprocess, tempfile

FORMATO, VERSION = "ketcero-escena", 1
TIPOS = {"matriz", "marco", "texto", "formula", "flecha"}


class Escena:
    def __init__(self, titulo, ancho=1600, alto=900, credito=None):
        self.datos = {"formato": FORMATO, "version": VERSION, "titulo": titulo,
                      "lienzo": {"ancho": ancho, "alto": alto}, "objetos": [], "pasos": []}
        if credito:
            self.datos["credito"] = credito
        self._ids = set()

    # -------- objetos (todos empiezan ocultos salvo que se diga lo contrario)
    def _nuevo(self, o, visible):
        if o["id"] in self._ids:
            raise ValueError(f"id repetido: {o['id']}")
        self._ids.add(o["id"])
        o["visible"] = visible
        self.datos["objetos"].append(o)
        return o["id"]

    def matriz(self, id, x, y, valores, celda=28, decimales=2, numeros=True, etiqueta=None, visible=False):
        valores = [[None if v is None else round(float(v), 6) for v in fila] for fila in valores]
        o = {"id": id, "tipo": "matriz", "x": x, "y": y, "valores": valores, "celda": celda, "decimales": decimales, "numeros": numeros}
        if etiqueta:
            o["etiqueta"] = etiqueta
        return self._nuevo(o, visible)

    def marco(self, id, sobre, fila, col, filas, cols, visible=False):
        return self._nuevo({"id": id, "tipo": "marco", "sobre": sobre, "fila": fila, "col": col, "filas": filas, "cols": cols}, visible)

    def texto(self, id, x, y, texto, tam=18, peso=400, ancla="start", tono="tinta", mono=False, visible=False):
        return self._nuevo({"id": id, "tipo": "texto", "x": x, "y": y, "texto": texto, "tam": tam, "peso": peso,
                            "ancla": ancla, "tono": tono, "mono": mono}, visible)

    def formula(self, id, x, y, tex, tam=22, visible=False):
        return self._nuevo({"id": id, "tipo": "formula", "x": x, "y": y, "tex": tex, "svg": compilar(tex, tam)}, visible)

    def flecha(self, id, de, a, visible=False):
        return self._nuevo({"id": id, "tipo": "flecha", "de": list(de), "a": list(a)}, visible)

    # -------- cambios
    @staticmethod
    def mostrar(*ids):
        return [{"id": i, "visible": True} for i in ids]

    @staticmethod
    def ocultar(*ids):
        return [{"id": i, "visible": False} for i in ids]

    @staticmethod
    def cambiar(id, **campos):
        return {"id": id, **campos}

    def nueva_formula(self, id, tex, tam=22, **campos):
        """Cambio que reemplaza el contenido de una fórmula ya declarada."""
        return {"id": id, "tex": tex, "svg": compilar(tex, tam), **campos}

    @staticmethod
    def celdas(id, lista):
        """lista de (fila, col, valor)."""
        return {"id": id, "celdas": [[int(f), int(c), None if v is None else round(float(v), 6)] for f, c, v in lista]}

    def paso(self, titulo, texto="", *grupos):
        cambios = []
        for g in grupos:
            cambios += g if isinstance(g, list) else [g]
        self.datos["pasos"].append({"titulo": titulo, "texto": texto, "cambios": cambios})

    # -------- salida
    def validar(self):
        return validar(self.datos)

    def guardar(self, ruta):
        problemas = self.validar()
        if problemas:
            raise ValueError("Escena inválida:\n- " + "\n- ".join(problemas))
        os.makedirs(os.path.dirname(os.path.abspath(ruta)), exist_ok=True)
        with io.open(ruta, "w", encoding="utf-8", newline="\n") as f:
            json.dump(self.datos, f, ensure_ascii=False, separators=(",", ":"))
        return ruta


def validar(e):
    """Las mismas reglas que validarEscena() del runtime de TypeScript."""
    p = []
    if e.get("formato") != FORMATO:
        p.append(f"formato debe ser «{FORMATO}»")
    if e.get("version") != VERSION:
        p.append(f"versión {e.get('version')} no soportada")
    l = e.get("lienzo") or {}
    if not (l.get("ancho", 0) > 0 and l.get("alto", 0) > 0):
        p.append("lienzo.ancho y lienzo.alto deben ser positivos")
    ids = set()
    for o in e.get("objetos", []):
        if o.get("id") in ids:
            p.append(f"id repetido: {o.get('id')}")
        ids.add(o.get("id"))
        if o.get("tipo") not in TIPOS:
            p.append(f"{o.get('id')}: tipo desconocido «{o.get('tipo')}»")
        if o.get("tipo") == "matriz" and len({len(f) for f in o["valores"]}) != 1:
            p.append(f"{o['id']}: valores debe ser una matriz rectangular")
    for o in e.get("objetos", []):
        if o.get("tipo") == "marco" and o.get("sobre") not in ids:
            p.append(f"{o['id']}: la matriz «{o.get('sobre')}» no existe")
    if not e.get("pasos"):
        p.append("la escena necesita al menos un paso")
    for i, paso in enumerate(e.get("pasos", [])):
        if not paso.get("titulo"):
            p.append(f"paso {i + 1}: falta el título")
        for c in paso.get("cambios", []):
            if c.get("id") not in ids:
                p.append(f"paso {i + 1}: cambia «{c.get('id')}», que no existe")
    return p


# ------------------------------------------------------------------ LaTeX → trazos SVG

DOC = r"""\documentclass[border=0pt]{standalone}
\usepackage[T1]{fontenc}\usepackage{lmodern,amsmath,amssymb,xcolor}
\DeclareUnicodeCharacter{2212}{\ensuremath{-}}\DeclareUnicodeCharacter{00B7}{\ensuremath{\cdot}}
\DeclareUnicodeCharacter{2026}{\ensuremath{\dots}}\DeclareUnicodeCharacter{2248}{\ensuremath{\approx}}
\newsavebox\formula
\begin{document}
\savebox\formula{\color[HTML]{010203}$\displaystyle %s$}%%
\typeout{MEDIDAS:\the\wd\formula:\the\ht\formula:\the\dp\formula}%%
\usebox\formula
\end{document}
"""
CACHE = os.environ.get("KETCERO_TEX_CACHE", os.path.join(os.path.expanduser("~"), ".cache", "ketcero-tex"))


def compilar(tex, tam=22):
    """Compila una fórmula a {vb, cuerpo, ancho, alto, base}: trazos sin fuentes, color = currentColor."""
    if re.search(r"[\t\f\b\a\v\r\n]", tex):
        raise ValueError(f"fórmula con un carácter de control (¿faltó la r de r\"…\"?): {tex!r}")
    clave = hashlib.sha1(tex.encode("utf-8")).hexdigest()[:16]
    os.makedirs(CACHE, exist_ok=True)
    ruta = os.path.join(CACHE, clave + ".json")
    if os.path.exists(ruta):
        with io.open(ruta, encoding="utf-8") as f:
            d = json.load(f)
    else:
        if not (shutil.which("latex") and shutil.which("dvisvgm")):
            raise RuntimeError("Para las fórmulas hace falta LaTeX (latex y dvisvgm en el PATH).")
        with tempfile.TemporaryDirectory() as tmp:
            with io.open(os.path.join(tmp, "f.tex"), "w", encoding="utf-8") as f:
                f.write(DOC % tex)
            r = subprocess.run(["latex", "-interaction=nonstopmode", "-halt-on-error", "f.tex"], cwd=tmp,
                               capture_output=True, text=True, encoding="utf-8", errors="replace")
            m = re.search(r"MEDIDAS:([\d.]+)pt:([\d.]+)pt:([\d.]+)pt", r.stdout)
            if r.returncode or not m:
                raise RuntimeError(f"LaTeX no compiló: {tex}\n" + r.stdout[-1200:])
            subprocess.run(["dvisvgm", "--no-fonts", "--bbox=papersize", "-o", "f.svg", "f.dvi"], cwd=tmp, capture_output=True)
            with io.open(os.path.join(tmp, "f.svg"), encoding="utf-8") as f:
                svg = f.read()
        vb = re.search(r"viewBox=['\"]([^'\"]+)['\"]", svg).group(1)
        cuerpo = svg[svg.index(">", svg.index("<svg")) + 1:svg.rindex("</svg>")]
        cuerpo = re.sub(r"<!--.*?-->", "", cuerpo, flags=re.S)
        cuerpo = re.sub(r"id='([^']+)'", lambda q: f"id='k{clave}{q.group(1)}'", cuerpo)
        cuerpo = re.sub(r"xlink:href='#([^']+)'", lambda q: f"href='#k{clave}{q.group(1)}'", cuerpo)
        cuerpo = re.sub(r"#010203", "currentColor", cuerpo, flags=re.I)
        ht = float(m.group(2))
        d = {"vb": vb, "cuerpo": cuerpo.strip(), "ht": ht}
        with io.open(ruta, "w", encoding="utf-8") as f:
            json.dump(d, f)
    k = tam / 10 * 1.06  # pt de LaTeX → unidades del lienzo (la letra a 10 pt queda pareja con un texto del mismo tamaño)
    _, _, vw, vh = (float(v) for v in d["vb"].split())
    return {"vb": d["vb"], "cuerpo": d["cuerpo"], "ancho": round(vw * k, 1), "alto": round(vh * k, 1),
            "base": round(d["ht"] * 72 / 72.27 * k, 1)}
