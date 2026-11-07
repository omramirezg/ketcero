"""La línea de comandos `ketcero`.

  ketcero listar                       lecciones de práctica y sus ejercicios
  ketcero descargar <lección> [-c dir] un .py por ejercicio (enunciado + código inicial) y sus pruebas en .ketcero/
  ketcero comprobar <archivo.py> …     corre las pruebas del ejercicio con tu código

--sitio cambia de dónde se leen los ejercicios: una URL (por omisión https://ketcero.com) o una carpeta local
con la misma forma (por ejemplo apps/web/public de este repositorio).
"""
import argparse, io, json, os, re, sys, urllib.request

from . import __version__, arnes

SITIO = os.environ.get("KETCERO_SITIO", "https://ketcero.com")
CABECERA = re.compile(r"^# ketcero: (?P<leccion>[\w-]+)/(?P<id>[\w-]+)\s*$", re.M)


def leer(sitio, ruta):
    """Lee /practica/… del sitio (URL) o de una carpeta local con la misma forma."""
    if re.match(r"^https?://", sitio):
        pedido = urllib.request.Request(sitio.rstrip("/") + ruta, headers={"User-Agent": f"ketcero/{__version__}"})
        with urllib.request.urlopen(pedido, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))
    with io.open(os.path.join(sitio, *ruta.strip("/").split("/")), encoding="utf-8") as f:
        return json.load(f)


def listar(args):
    indice = leer(args.sitio, "/practica/indice.json")
    for l in indice["lecciones"]:
        marca = "" if l.get("estado") == "publicada" else "  (borrador)"
        print(f"{l['slug']}{marca}\n  {l['titulo']}")
        for e in l["ejercicios"]:
            print(f"    {e['id']:28s} {e['titulo']}")
    return 0


def archivo_de_ejercicio(e):
    lineas = [f"# ketcero: {e['leccion']}/{e['id']}", f"# {e['titulo']}", "#"]
    for parrafo in e["enunciado"]:
        lineas += ["# " + l for l in envolver(parrafo.replace("`", ""), 100)] + ["#"]
    lineas += ["# Cuando termines:  ketcero comprobar " + e["id"] + ".py", ""]
    return "\n".join(lineas) + "\n" + e["inicial"]


def envolver(texto, ancho):
    out, linea = [], ""
    for palabra in texto.split():
        if linea and len(linea) + 1 + len(palabra) > ancho:
            out.append(linea)
            linea = palabra
        else:
            linea = (linea + " " + palabra).strip()
    return out + ([linea] if linea else [])


def descargar(args):
    indice = leer(args.sitio, "/practica/indice.json")
    leccion = next((l for l in indice["lecciones"] if l["slug"] == args.leccion), None)
    if not leccion:
        print(f"No existe la lección «{args.leccion}». Mira las que hay con: ketcero listar", file=sys.stderr)
        return 2
    carpeta = args.carpeta or args.leccion
    os.makedirs(os.path.join(carpeta, ".ketcero"), exist_ok=True)
    for item in leccion["ejercicios"]:
        e = leer(args.sitio, f"/practica/{args.leccion}/{item['id']}.json")
        destino = os.path.join(carpeta, e["id"] + ".py")
        if os.path.exists(destino) and not args.reemplazar:
            print(f"  ya existe {destino} (no lo toco; usa --reemplazar para empezar de cero)")
        else:
            with io.open(destino, "w", encoding="utf-8", newline="\n") as f:
                f.write(archivo_de_ejercicio(e))
            print(f"  {destino}")
        with io.open(os.path.join(carpeta, ".ketcero", e["id"] + ".json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(e, f, ensure_ascii=False, indent=1)
    print(f"\nListo. Abre la carpeta «{carpeta}», resuelve cada archivo y compruébalo con: ketcero comprobar <archivo>.py")
    return 0


def pruebas_de(ruta, sitio):
    """Encuentra las pruebas: primero en .ketcero/ junto al archivo; si no están, las baja del sitio."""
    with io.open(ruta, encoding="utf-8") as f:
        codigo = f.read()
    m = CABECERA.search(codigo)
    if not m:
        raise SystemExit(f"{ruta}: no tiene la línea «# ketcero: <lección>/<ejercicio>» que pone «ketcero descargar».")
    guardado = os.path.join(os.path.dirname(os.path.abspath(ruta)), ".ketcero", m["id"] + ".json")
    if os.path.exists(guardado):
        with io.open(guardado, encoding="utf-8") as f:
            e = json.load(f)
    else:
        e = leer(sitio, f"/practica/{m['leccion']}/{m['id']}.json")
    return codigo, e


def comprobar(args):
    todo_bien, informe = True, []
    for ruta in args.archivos:
        codigo, e = pruebas_de(ruta, args.sitio)
        res = arnes.corregir(codigo, e["pruebas"])
        todo_bien &= all(r["ok"] for r in res)
        if args.json:  # solo JSON en la salida: lo lee una extensión del editor
            informe.append({"archivo": ruta, "leccion": e["leccion"], "id": e["id"], "titulo": e["titulo"], "resultados": res})
        else:
            print(f"{e['titulo']}  ({os.path.basename(ruta)})")
            arnes.imprimir(res)
            print()
    if args.json:
        print(json.dumps(informe, ensure_ascii=False))
    return 0 if todo_bien else 1


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # tildes y ∂ en la terminal de Windows
    p = argparse.ArgumentParser(prog="ketcero", description="Ket Cero desde la terminal.")
    p.add_argument("--version", action="version", version=f"ketcero {__version__}")
    p.add_argument("--sitio", default=SITIO, help="URL del sitio o carpeta local (por omisión https://ketcero.com)")
    sub = p.add_subparsers(dest="orden", required=True)
    sub.add_parser("listar", help="lecciones de práctica y sus ejercicios").set_defaults(f=listar)
    d = sub.add_parser("descargar", help="baja los ejercicios de una lección como archivos .py")
    d.add_argument("leccion")
    d.add_argument("-c", "--carpeta", help="dónde guardarlos (por omisión, una carpeta con el nombre de la lección)")
    d.add_argument("--reemplazar", action="store_true", help="sobrescribe los .py que ya existan")
    d.set_defaults(f=descargar)
    c = sub.add_parser("comprobar", help="corre las pruebas del sitio con tu código")
    c.add_argument("archivos", nargs="+")
    c.add_argument("--json", action="store_true", help="resultado en JSON (para editores y extensiones)")
    c.set_defaults(f=comprobar)
    args = p.parse_args(argv)
    try:
        return args.f(args)
    except OSError as e:
        print(f"No pude leer {args.sitio}: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
