// «El cero que aprende»: el filtro principal de conv1 recorre un 0 real de MNIST y llena su mapa 24 × 24.
// Uso: <div id="cero"></div> + cero_datos.js + cero.js  →  montarCero(document.getElementById("cero"), window.DATOS_CERO)
(function () {
  const NS = "http://www.w3.org/2000/svg";
  const CORAL = [216, 90, 48], TEAL = [29, 158, 117];

  function el(padre, tag, attrs, texto) {
    const e = document.createElementNS(NS, tag);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    if (texto != null) e.textContent = texto;
    padre.appendChild(e);
    return e;
  }
  // coma decimal y signo menos tipográfico
  const num = (v, d = 3) => (v < 0 ? "−" : "") + Math.abs(v).toFixed(d).replace(".", ",");

  function montarCero(caja, D) {
    const f = D.filtro_principal, K = D.filtros[f], b = D.sesgos[f], X = D.entrada, MAPA = D.mapas[f];
    const topePos = Math.max(...MAPA.flat().filter(v => v > 0), 1e-6);
    const topeNeg = Math.max(...MAPA.flat().filter(v => v < 0).map(v => -v), 1e-6);
    const colorSigno = (v, tPos, tNeg) => {
      if (v === 0) return "transparent";
      const [r, g, bb] = v > 0 ? CORAL : TEAL;
      const a = Math.pow(Math.min(1, Math.abs(v) / (v > 0 ? tPos : tNeg)), 0.9);
      return `rgba(${r},${g},${bb},${a.toFixed(3)})`;
    };
    const quieto = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let svg, celdasMapa, ventana, marca, linea1, linea2, mini, salida, ancho = 0;
    let k = 0, fase = "recorre", espera = 0, reloj = null, visible = true;

    function dibujar() {
      ancho = caja.clientWidth;
      // ancha: entrada | filtro | mapa; media: entrada | mapa (sin el filtro); angosta: entrada y mapa apilados
      const modo = ancho >= 860 ? "ancha" : ancho >= 500 ? "media" : "angosta", angosta = modo === "angosta";
      caja.innerHTML = "";
      // geometría: en pantalla ancha, entrada | filtro | mapa en una fila; en angosta, entrada y mapa apilados
      const c = modo === "ancha" ? 12 : modo === "media" ? 10 : Math.max(5, Math.floor((ancho - 16) / 52)), cf = modo === "ancha" ? 36 : 0;
      const xE = 0, yE = 22, anchoE = 28 * c;
      const xF = modo === "ancha" ? anchoE + 36 : 0, yF = 22;
      const xM = modo === "ancha" ? xF + 5 * cf + 36 : anchoE + (angosta ? 16 : 32), yM = yE + 2 * c;  // el mapa (24) centrado frente a la entrada (28)
      const anchoTotal = xM + 24 * c;
      const yTexto = yE + anchoE + 30;
      const yMini = yTexto + 34, lado = modo === "ancha" ? 72 : modo === "media" ? 58 : 44, sep = angosta ? 8 : 14;
      const alto = yMini + lado + 30;
      svg = el(caja, "svg", { viewBox: `0 0 ${Math.max(anchoTotal, 6 * lado + 5 * sep)} ${alto}`, width: "100%", role: "img",
        "aria-label": `Un filtro de la primera capa recorre un cero escrito a mano y llena su mapa; la red responde 0 con probabilidad ${num(D.probabilidades[0], 4)}` });
      svg.style.display = "block";
      svg.style.font = '13px "IBM Plex Mono", monospace';
      const rot = (x, y, t) => el(svg, "text", { x, y, fill: "var(--gris)", "font-size": 12 }, t);

      rot(xE, yE - 8, "un 0 escrito a mano");
      for (let i = 0; i < 28; i++) for (let j = 0; j < 28; j++) {
        el(svg, "rect", { x: xE + j * c, y: yE + i * c, width: c - 1, height: c - 1, fill: "var(--linea)", "fill-opacity": 0.35 });
        if (X[i][j] > 0) el(svg, "rect", { x: xE + j * c, y: yE + i * c, width: c - 1, height: c - 1, fill: "var(--tinta)", "fill-opacity": (X[i][j] * 0.9).toFixed(3) });
      }
      ventana = el(svg, "rect", { width: 5 * c - 1, height: 5 * c - 1, fill: "none", stroke: "var(--tinta)", "stroke-width": 1.6, opacity: 0 });

      if (modo === "ancha") {
        rot(xF, yF - 8, "un filtro de la red");
        const tK = Math.max(...K.flat().map(Math.abs));
        for (let i = 0; i < 5; i++) for (let j = 0; j < 5; j++) {
          el(svg, "rect", { x: xF + j * cf, y: yF + i * cf, width: cf - 1, height: cf - 1, fill: colorSigno(K[i][j], tK, tK), stroke: "var(--linea)", "stroke-width": 0.6 });
          el(svg, "text", { x: xF + j * cf + cf / 2 - 0.5, y: yF + i * cf + cf / 2 + 3.5, "text-anchor": "middle", "font-size": 9.5, fill: "var(--tinta)" }, num(K[i][j], 2));
        }
        el(svg, "text", { x: xF, y: yF + 5 * cf + 18, "font-size": 12, fill: "var(--gris)" }, `sesgo b = ${num(b)}`);
      }

      rot(xM, yE - 8, "lo que ve el filtro");
      celdasMapa = [];
      for (let i = 0; i < 24; i++) for (let j = 0; j < 24; j++)
        celdasMapa.push(el(svg, "rect", { x: xM + j * c, y: yM + i * c, width: c - 1, height: c - 1, fill: "transparent", stroke: "var(--linea)", "stroke-width": 0.5 }));
      marca = el(svg, "rect", { width: c - 1, height: c - 1, fill: "none", stroke: "var(--tinta)", "stroke-width": 1.4, opacity: 0 });
      dibujar.c = c; dibujar.xE = xE; dibujar.yE = yE; dibujar.xM = xM; dibujar.yM = yM;

      linea1 = el(svg, "text", { x: 0, y: yTexto, "font-size": angosta ? 12 : 14, fill: "var(--tinta)" }, "");
      linea2 = el(svg, "text", { x: 0, y: yTexto + 20, "font-size": 12, fill: "var(--gris)" }, "");

      // los 6 mapas pequeños y la salida, ocultos hasta su fase
      mini = el(svg, "g", { opacity: 0 });
      const cm = lado / 24;
      for (let m = 0; m < 6; m++) {
        const tp = Math.max(...D.mapas[m].flat().filter(v => v > 0), 1e-6), tn = Math.max(...D.mapas[m].flat().filter(v => v < 0).map(v => -v), 1e-6);
        const gx = m * (lado + sep);
        for (let i = 0; i < 24; i++) for (let j = 0; j < 24; j++) {
          const v = D.mapas[m][i][j];
          if (v !== 0) el(mini, "rect", { x: gx + j * cm, y: yMini + i * cm, width: cm + 0.05, height: cm + 0.05, fill: colorSigno(v, tp, tn) });
        }
        el(mini, "rect", { x: gx - 0.5, y: yMini - 0.5, width: lado + 1, height: lado + 1, fill: "none", stroke: m === f ? "var(--tinta)" : "var(--linea)", "stroke-width": m === f ? 1.4 : 0.8 });
        el(mini, "text", { x: gx, y: yMini + lado + 16, "font-size": 11, fill: "var(--gris)" }, angosta ? `f${m + 1}` : `filtro ${m + 1}`);
      }
      salida = el(svg, "text", { x: 0, y: yTexto, "font-size": angosta ? 13 : 15, fill: "var(--tinta)", opacity: 0 }, "");
      pintarHasta(fase === "recorre" ? k : 576);
      if (fase !== "recorre") mostrarFinal(fase);
    }

    function z(i, j) {
      let s = b;
      for (let a = 0; a < 5; a++) for (let c = 0; c < 5; c++) s += X[i + a][j + c] * K[a][c];
      return s;
    }

    function pintarHasta(n) {
      for (let q = 0; q < 576; q++) celdasMapa[q].setAttribute("fill", q < n ? colorSigno(MAPA[Math.floor(q / 24)][q % 24], topePos, topeNeg) : "transparent");
    }

    function ponerVentana(i, j) {
      const c = dibujar.c;
      ventana.setAttribute("x", dibujar.xE + j * c); ventana.setAttribute("y", dibujar.yE + i * c);
      marca.setAttribute("x", dibujar.xM + j * c); marca.setAttribute("y", dibujar.yM + i * c);
      ventana.setAttribute("opacity", 1); marca.setAttribute("opacity", 1);
    }

    function mostrarFinal(cual) {
      ventana.setAttribute("opacity", 0); marca.setAttribute("opacity", 0);
      mini.setAttribute("opacity", 1);
      if (cual === "mapas") {
        salida.setAttribute("opacity", 0);
        linea1.textContent = ancho < 860 ? "6 filtros, 6 mapas del mismo 0" : "los 6 filtros de conv1 dan 6 mapas: cada uno ve un borde distinto del 0";
        linea2.textContent = "coral: positivo · teal: negativo";
      } else {
        linea1.textContent = ""; linea2.textContent = "";
        salida.setAttribute("opacity", 1);
        salida.textContent = `salida de la red:  0 → ${num(D.probabilidades[0], 4)}`;
      }
    }

    function paso() {
      if (!visible) return;
      if (fase === "recorre") {
        const i = Math.floor(k / 24), j = k % 24;
        ponerVentana(i, j);
        celdasMapa[k].setAttribute("fill", colorSigno(MAPA[i][j], topePos, topeNeg));
        if (ancho < 600) {
          linea1.textContent = `casilla (${i + 1}, ${j + 1}) = ${num(z(i, j))}`;
          linea2.textContent = "suma de 25 productos x·w + b";
        } else {
          linea1.textContent = `casilla (${i + 1}, ${j + 1}): suma de 25 productos + b = ${num(z(i, j))}`;
          linea2.textContent = "z = Σ x·w + b   ·   coral: positivo · teal: negativo";
        }
        k++;
        if (k === 576) { fase = "mapas"; espera = 0; mostrarFinal("mapas"); }
        return programar(i === 0 ? 120 : i === 1 ? 45 : 14);
      }
      espera++;
      if (fase === "mapas" && espera > 0) { fase = "salida"; espera = 0; mostrarFinal("salida"); return programar(3500); }
      if (fase === "salida") { reiniciar(); return programar(600); }
      return programar(2800);
    }

    function reiniciar() {
      k = 0; fase = "recorre"; espera = 0;
      mini.setAttribute("opacity", 0); salida.setAttribute("opacity", 0);
      pintarHasta(0);
    }

    function programar(ms) { clearTimeout(reloj); reloj = setTimeout(paso, fase === "mapas" && ms < 2800 ? 2800 : ms); }

    dibujar();
    if (quieto) { k = 576; fase = "salida"; pintarHasta(576); mostrarFinal("salida"); return; }
    new IntersectionObserver(entradas => {
      visible = entradas[0].isIntersecting;
      if (visible) programar(200); else clearTimeout(reloj);
    }, { threshold: 0.15 }).observe(caja);
    new ResizeObserver(() => { if (Math.abs(caja.clientWidth - ancho) > 4) dibujar(); }).observe(caja);
  }

  window.montarCero = montarCero;
})();
