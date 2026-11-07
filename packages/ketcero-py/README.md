# ketcero (paquete de Python)

Ket Cero desde la terminal: baja los ejercicios de práctica, resuélvelos en tu editor y compruébalos con las
mismas pruebas que corre el sitio en el navegador (es el mismo `arnes.py`).

```bash
pip install "ketcero @ git+https://github.com/omramirezg/ketcero.git#subdirectory=packages/ketcero-py"
ketcero listar
ketcero descargar la-derivada-que-usa-una-red
ketcero comprobar la-derivada-que-usa-una-red/01-derivada-numerica.py
```

- `ketcero comprobar --json …` imprime solo JSON (para extensiones de editor).
- `--sitio <url o carpeta>` lee los ejercicios de otro lado (por omisión https://ketcero.com); en este repositorio,
  `--sitio apps/web/public` funciona sin red.
- Sin dependencias: solo la biblioteca estándar. Los ejercicios que usan NumPy necesitan NumPy instalado.

Para quien hace material, `ketcero.escena` arma escenas animadas (formato `ketcero-escena`, ver
`packages/motor/ESCENA.md`) con matrices, marcos, textos, flechas y fórmulas en LaTeX.

Pruebas: `python -m unittest discover -s packages/ketcero-py/tests` (con `KETCERO_PROBAR_PIP=1` además instala
el paquete en un entorno virtual y corre la orden `ketcero`).
