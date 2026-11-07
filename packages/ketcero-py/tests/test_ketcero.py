"""Pruebas del paquete `ketcero` (solo biblioteca estándar: python -m unittest discover packages/ketcero-py/tests).

Usan la carpeta apps/web/public del repositorio como si fuera el sitio (--sitio <carpeta>), así no hace falta red.
"""
import contextlib, io, json, os, shutil, subprocess, sys, tempfile, unittest

AQUI = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "packages", "ketcero-py", "src"))

from ketcero import arnes, cli, ejercicios  # noqa: E402
from ketcero.escena import Escena, validar  # noqa: E402

SITIO = os.path.join(REPO, "apps", "web", "public")
LECCION = "la-derivada-que-usa-una-red"


def correr(*args):
    salida, errores = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(salida), contextlib.redirect_stderr(errores):
        codigo = cli.main(["--sitio", SITIO, *args])
    return codigo, salida.getvalue() + errores.getvalue()


class Cli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.carpeta = os.path.join(self.tmp, LECCION)
        self.fuente = {e["id"]: e for e in ejercicios.de_leccion(os.path.join(REPO, "contenido", "practica", LECCION))}

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_listar(self):
        codigo, texto = correr("listar")
        self.assertEqual(codigo, 0)
        self.assertIn(LECCION, texto)
        self.assertIn("01-derivada-numerica", texto)
        self.assertIn("(borrador)", texto)

    def test_descargar_escribe_un_py_por_ejercicio_sin_la_solucion(self):
        codigo, _ = correr("descargar", LECCION, "-c", self.carpeta)
        self.assertEqual(codigo, 0)
        for id_, e in self.fuente.items():
            texto = io.open(os.path.join(self.carpeta, id_ + ".py"), encoding="utf-8").read()
            self.assertTrue(texto.startswith(f"# ketcero: {LECCION}/{id_}\n"))
            self.assertIn(e["inicial"], texto)
            self.assertNotIn(e["solucion"].strip(), texto)
            self.assertTrue(os.path.exists(os.path.join(self.carpeta, ".ketcero", id_ + ".json")))

    def test_descargar_no_pisa_tu_trabajo(self):
        correr("descargar", LECCION, "-c", self.carpeta)
        ruta = os.path.join(self.carpeta, "01-derivada-numerica.py")
        io.open(ruta, "a", encoding="utf-8").write("# mi trabajo\n")
        correr("descargar", LECCION, "-c", self.carpeta)
        self.assertIn("# mi trabajo", io.open(ruta, encoding="utf-8").read())

    def test_comprobar_el_inicial_falla_y_la_solucion_pasa(self):
        correr("descargar", LECCION, "-c", self.carpeta)
        for id_, e in self.fuente.items():
            ruta = os.path.join(self.carpeta, id_ + ".py")
            codigo, texto = correr("comprobar", ruta)
            self.assertEqual(codigo, 1, id_)
            self.assertIn("No pasa", texto)
            cabeza = io.open(ruta, encoding="utf-8").read().split("\n")[0]
            io.open(ruta, "w", encoding="utf-8").write(cabeza + "\n" + e["solucion"])
            codigo, texto = correr("comprobar", ruta)
            self.assertEqual(codigo, 0, texto)
            self.assertIn("Pasa", texto)

    def test_comprobar_cada_error_tipico_falla(self):
        correr("descargar", LECCION, "-c", self.carpeta)
        for id_, e in self.fuente.items():
            ruta = os.path.join(self.carpeta, id_ + ".py")
            for nombre, cod in e["errores"].items():
                io.open(ruta, "w", encoding="utf-8").write(f"# ketcero: {LECCION}/{id_}\n" + cod)
                self.assertEqual(correr("comprobar", ruta)[0], 1, nombre)

    def test_comprobar_en_json_para_editores(self):
        correr("descargar", LECCION, "-c", self.carpeta)
        salida = io.StringIO()
        with contextlib.redirect_stdout(salida):
            cli.main(["--sitio", SITIO, "comprobar", "--json", os.path.join(self.carpeta, "01-derivada-numerica.py")])
        texto = salida.getvalue()
        informe = json.loads(texto)  # la salida entera es JSON
        self.assertEqual(informe[0]["id"], "01-derivada-numerica")
        self.assertEqual({"nombre", "ok", "mensaje", "esperado", "obtenido"}, set(informe[0]["resultados"][0]))

    def test_comprobar_sin_cabecera_explica_que_falta(self):
        ruta = os.path.join(self.tmp, "suelto.py")
        io.open(ruta, "w", encoding="utf-8").write("x = 1\n")
        with self.assertRaises(SystemExit) as e:
            correr("comprobar", ruta)
        self.assertIn("# ketcero:", str(e.exception))

    def test_leccion_que_no_existe(self):
        self.assertEqual(correr("descargar", "no-existe", "-c", self.carpeta)[0], 2)


class Escenas(unittest.TestCase):
    def test_validar_atrapa_errores(self):
        e = Escena("x", 100, 100)
        e.matriz("m", 0, 0, [[1, 2]])
        e.paso("uno", "", e.mostrar("m"), {"id": "fantasma"})
        self.assertTrue(any("fantasma" in p for p in e.validar()))
        with self.assertRaises(ValueError):
            e.guardar(os.path.join(tempfile.gettempdir(), "no.json"))

    def test_id_repetido(self):
        e = Escena("x")
        e.texto("t", 0, 0, "hola")
        with self.assertRaises(ValueError):
            e.texto("t", 0, 0, "otra vez")

    def test_formato(self):
        e = Escena("x")
        e.matriz("m", 0, 0, [[1, None]])
        e.paso("uno", "", e.mostrar("m"), e.celdas("m", [(0, 1, 2.5)]))
        self.assertEqual(validar(e.datos), [])
        self.assertEqual(e.datos["objetos"][0]["valores"], [[1.0, None]])
        self.assertEqual(e.datos["pasos"][0]["cambios"][1], {"id": "m", "celdas": [[0, 1, 2.5]]})

    @unittest.skipUnless(shutil.which("latex") and shutil.which("dvisvgm"), "sin LaTeX")
    def test_formula_compilada(self):
        e = Escena("x")
        e.formula("f", 0, 0, r"\frac{\partial L}{\partial w}")
        svg = e.datos["objetos"][0]["svg"]
        self.assertIn("currentColor", svg["cuerpo"])
        self.assertGreater(svg["ancho"], 0)

    def test_exportador_del_cero_cuadra_con_el_entrenamiento(self):
        sys.path.insert(0, os.path.join(REPO, "herramientas"))
        import exportar_escena_cero as ex
        D = ex.leer_datos()
        f = D["filtro_principal"]
        for i, j in [(0, 0), (11, 20), (23, 23)]:
            self.assertAlmostEqual(ex.conv(D["entrada"], D["filtros"][f], D["sesgos"][f], i, j), D["mapas"][f][i][j], delta=0.01)


class Instalacion(unittest.TestCase):
    def test_arnes_es_el_mismo_que_corre_en_el_navegador(self):
        # el Worker de Pyodide importa este mismo archivo (packages/practica/src/trabajador.ts)
        trabajador = io.open(os.path.join(REPO, "packages", "practica", "src", "trabajador.ts"), encoding="utf-8").read()
        self.assertIn("ketcero-py/src/ketcero/arnes.py?raw", trabajador)

    @unittest.skipUnless(os.environ.get("KETCERO_PROBAR_PIP"), "pon KETCERO_PROBAR_PIP=1 para instalar en un venv")
    def test_pip_install_y_la_orden_ketcero(self):
        with tempfile.TemporaryDirectory() as d:
            subprocess.run([sys.executable, "-m", "venv", d], check=True)
            py = os.path.join(d, "Scripts" if os.name == "nt" else "bin", "python")
            subprocess.run([py, "-m", "pip", "install", "-q", os.path.join(REPO, "packages", "ketcero-py")], check=True)
            exe = os.path.join(d, "Scripts" if os.name == "nt" else "bin", "ketcero")
            r = subprocess.run([exe, "--sitio", SITIO, "listar"], capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn(LECCION, r.stdout)


if __name__ == "__main__":
    unittest.main()
