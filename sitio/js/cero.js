// «El cero que aprende»: el filtro principal de conv1 recorre un 0 real de MNIST y llena su mapa 24 × 24.
// Uso: <div id="cero"></div> + cero_datos.js + cero.js  →  montarCero(document.getElementById("cero"), window.DATOS_CERO, { codigo: panel })
// Fases de cada vuelta: arranque (líneas 1 a 4, una por una) → recorre (doble for, con una casilla en cámara lenta)
// → mapas (los 6 filtros) → salida (tabla de probabilidades) → vuelve a empezar.
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
  const num = (v, d = 3) => { const t = Math.abs(v).toFixed(d); return (v < 0 && +t !== 0 ? "−" : "") + t.replace(".", ","); };

  // Colores de sintaxis al estilo de VS Code: palabras clave, funciones, módulos, variables y números.
  const PALABRAS = /^(for|in|import|from|def|return|if|else)$/, MODULOS = /^(torch|F|nn)$/;
  function colorear(codigo) {
    const fuera = t => t.replace(/&/g, "&amp;").replace(/</g, "&lt;");
    return codigo.replace(/([A-Za-z_]\w*)(\s*\()?|(\d+)|([^A-Za-z_\d]+)/g, (m, nombre, parentesis, numero, resto) => {
      if (numero) return '<span class="t-num">' + numero + "</span>";
      if (resto) return fuera(resto);
      const clase = PALABRAS.test(nombre) ? "t-clave" : MODULOS.test(nombre) ? "t-modulo" : parentesis ? "t-funcion" : "t-var";
      return '<span class="' + clase + '">' + nombre + "</span>" + (parentesis || "");
    });
  }

  // Panel de código que acompaña la animación: la línea que se ejecuta lleva la flecha ▶, las del bucle se resaltan
  // y los comentarios muestran los valores reales. Debajo del panel queda un bloque (cámara lenta y tabla final).
  function montarCodigo(caja, D) {
    const f = D.filtro_principal, n = D.indice_prueba;
    const lineas = [
      ["x = X_test[" + n + ", 0]", "el 0 escrito a mano, 28 × 28"],
      ["w = cnn[0].weight[" + f + ", 0]", "filtro " + (f + 1) + " de la primera capa, 5 × 5"],
      ["b = cnn[0].bias[" + f + "]", ""],
      ["mapa = torch.zeros(24, 24)", ""],
      ["for i in range(24):", ""],
      ["    for j in range(24):", ""],
      ["        ventana = x[i:i+5, j:j+5]", ""],
      ["        mapa[i, j] = (ventana * w).sum() + b", ""],
      ["mapas = cnn[0](X_test[" + n + ":" + (n + 1) + "])", "los 6 filtros a la vez"],
      ["prob = F.softmax(cnn(X_test[" + n + ":" + (n + 1) + "]), 1)", ""],
    ];
    caja.innerHTML = "";
    const pre = document.createElement("pre");
    pre.className = "codigo-cero";
    const filas = lineas.map(([codigo, nota], k) => {
      const fila = document.createElement("div");
      fila.className = "linea";
      fila.innerHTML = '<span class="flecha">▶</span><span class="num">' + (k + 1) + '</span><span class="cod"></span><span class="nota"></span>';
      fila.children[2].innerHTML = colorear(codigo);
      fila.children[3].textContent = nota ? "# " + nota : "";
      pre.appendChild(fila);
      return fila;
    });
    caja.appendChild(pre);
    const bloque = document.createElement("div");
    bloque.className = "bloque-codigo";
    caja.parentNode.insertBefore(bloque, caja.nextSibling);
    const notas = lineas.map(l => l[1]);
    function marcar(activas, valores, actual) {
      filas.forEach((fila, k) => {
        fila.classList.toggle("activa", activas.indexOf(k) >= 0);
        fila.classList.toggle("actual", k === actual);
        const v = valores && valores[k];
        fila.children[3].textContent = v ? "# " + v : notas[k] ? "# " + notas[k] : "";
      });
    }
    return { marcar, bloque };
  }

  function montarCero(caja, D, opciones) {
    const panel = opciones && opciones.codigo ? montarCodigo(opciones.codigo, D) : null;
    const marcar = panel ? panel.marcar : () => {};
    const bloque = panel ? panel.bloque : null;
    const f = D.filtro_principal, K = D.filtros[f], b = D.sesgos[f], X = D.entrada, MAPA = D.mapas[f];
    const topePos = Math.max(...MAPA.flat().filter(v => v > 0), 1e-6);
    const topeNeg = Math.max(...MAPA.flat().filter(v => v < 0).map(v => -v), 1e-6);
    const tK = Math.max(...K.flat().map(Math.abs));
    const colorSigno = (v, tPos, tNeg, escala = 1) => {
      if (v === 0) return "transparent";
      const [r, g, bb] = v > 0 ? CORAL : TEAL;
      const a = Math.pow(Math.min(1, Math.abs(v) / (v > 0 ? tPos : tNeg)), 0.9) * escala;
      return `rgba(${r},${g},${bb},${a.toFixed(3)})`;
    };
    const z = (i, j) => {
      let s = b;
      for (let a = 0; a < 5; a++) for (let c = 0; c < 5; c++) s += X[i + a][j + c] * K[a][c];
      return s;
    };
    // la casilla en cámara lenta: la primera cuya ventana pisa bien el trazo del 0
    let kLenta = -1;
    for (let q = 0; q < 576 && kLenta < 0; q++) {
      const i = Math.floor(q / 24), j = q % 24;
      let n = 0;
      for (let a = 0; a < 5; a++) for (let c = 0; c < 5; c++) if (X[i + a][j + c] > 0.3) n++;
      if (n >= 8) kLenta = q;
    }

    const quieto = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let svg, celdasMapa, ventana, marca, punto, linea1, linea2, mini, salida, gEntrada, gMapa, gFiltro, rotMapa, ancho = 0;
    let k = 0, fase = "arranque", a = 0, t = 0, suma = 0, lentaHecha = false, espera = 0, reloj = null, visible = true;
    const ver = { entrada: false, filtro: false, mapa: false };
    let celdasLenta = [];

    function mostrar(g, si, animar) {
      if (!g) return;
      g.style.transition = animar ? "opacity .7s ease" : "none";
      g.style.opacity = si ? 1 : 0;
    }

    function dibujar() {
      ancho = caja.clientWidth;
      // ancha: entrada | filtro | mapa; media: entrada | mapa (sin el filtro); angosta: casillas más pequeñas
      const modo = ancho >= 860 ? "ancha" : ancho >= 500 ? "media" : "angosta", angosta = modo === "angosta";
      caja.innerHTML = "";
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
      const rot = (x, y, txt) => el(svg, "text", { x, y, fill: "var(--gris)", "font-size": 12 }, txt);

      rot(xE, yE - 8, "un 0 escrito a mano");
      for (let i = 0; i < 28; i++) for (let j = 0; j < 28; j++)
        el(svg, "rect", { x: xE + j * c, y: yE + i * c, width: c - 1, height: c - 1, fill: "var(--linea)", "fill-opacity": 0.35 });
      gEntrada = el(svg, "g", {});
      for (let i = 0; i < 28; i++) for (let j = 0; j < 28; j++)
        if (X[i][j] > 0) el(gEntrada, "rect", { x: xE + j * c, y: yE + i * c, width: c - 1, height: c - 1, fill: "var(--tinta)", "fill-opacity": (X[i][j] * 0.9).toFixed(3) });
      ventana = el(svg, "rect", { width: 5 * c - 1, height: 5 * c - 1, fill: "none", stroke: "var(--tinta)", "stroke-width": 1.6, opacity: 0 });
      punto = el(svg, "rect", { width: c - 1, height: c - 1, fill: "none", stroke: "rgb(216,90,48)", "stroke-width": 1.6, opacity: 0 });

      gFiltro = null;
      if (modo === "ancha") {
        rot(xF, yF - 8, "un filtro de la red");
        for (let i = 0; i < 5; i++) for (let j = 0; j < 5; j++) {
          el(svg, "rect", { x: xF + j * cf, y: yF + i * cf, width: cf - 1, height: cf - 1, fill: colorSigno(K[i][j], tK, tK), stroke: "var(--linea)", "stroke-width": 0.6 });
          el(svg, "text", { x: xF + j * cf + cf / 2 - 0.5, y: yF + i * cf + cf / 2 + 3.5, "text-anchor": "middle", "font-size": 9.5, fill: "var(--tinta)" }, num(K[i][j], 2));
        }
        el(svg, "text", { x: xF, y: yF + 5 * cf + 18, "font-size": 12, fill: "var(--gris)" }, `sesgo b = ${num(b)}`);
      } else {
        // sin columna para el filtro: en el arranque (línea 2) sus 25 pesos se muestran donde luego estará el mapa
        gFiltro = el(svg, "g", {});
        const cg = 24 * c / 5;
        for (let i = 0; i < 5; i++) for (let j = 0; j < 5; j++) {
          el(gFiltro, "rect", { x: xM + j * cg, y: yM + i * cg, width: cg - 2, height: cg - 2, fill: colorSigno(K[i][j], tK, tK), stroke: "var(--linea)", "stroke-width": 0.6 });
          el(gFiltro, "text", { x: xM + j * cg + cg / 2 - 1, y: yM + i * cg + cg / 2 + 4, "text-anchor": "middle", "font-size": cg >= 40 ? 12 : 9, fill: "var(--tinta)" }, num(K[i][j], 2));
        }
      }

      rotMapa = rot(xM, yE - 8, "lo que ve el filtro");
      gMapa = el(svg, "g", {});
      celdasMapa = [];
      for (let i = 0; i < 24; i++) for (let j = 0; j < 24; j++)
        celdasMapa.push(el(gMapa, "rect", { x: xM + j * c, y: yM + i * c, width: c - 1, height: c - 1, fill: "transparent", stroke: "var(--linea)", "stroke-width": 0.5 }));
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

      // al redibujar (cambio de tamaño) se repone el estado de la fase actual, sin animar
      mostrar(gEntrada, ver.entrada, false); mostrar(gFiltro, ver.filtro, false); mostrar(gMapa, ver.mapa, false);
      if (ver.filtro && gFiltro) rotMapa.textContent = "el filtro: 25 pesos";
      pintarHasta(fase === "recorre" || fase === "lenta" ? k : fase === "arranque" ? 0 : 576);
      if (fase === "mapas" || fase === "salida") mostrarFinal(fase);
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

    // ---- bloque bajo el código: cámara lenta de una casilla y tabla final de probabilidades ----
    function tabla(M, clase, celda) {
      return '<table class="m5 ' + clase + '">' + M.map((fila, i) => "<tr>" + fila.map((v, j) => celda(v, i, j)).join("") + "</tr>").join("") + "</table>";
    }
    function abrirLenta(i, j) {
      if (!bloque) return;
      const V = [0, 1, 2, 3, 4].map(a => [0, 1, 2, 3, 4].map(c => X[i + a][j + c]));
      const vacia = [0, 1, 2, 3, 4].map(() => [0, 0, 0, 0, 0]);
      bloque.innerHTML =
        `<div class="b-tit">mapa[${i}, ${j}] en cámara lenta: ventana · w, los 25 productos uno por uno</div>` +
        '<div class="b-mats">' +
        tabla(V, "px", v => `<td style="background:rgba(128,128,128,${(v * 0.45).toFixed(3)})">${num(v, 2)}</td>`) +
        '<span class="op">·</span>' +
        tabla(K, "w", v => `<td style="background:${colorSigno(v, tK, tK, 0.55)}">${num(v, 2)}</td>`) +
        '<span class="op">=</span>' +
        tabla(vacia, "p", () => "<td></td>") +
        '</div><div class="b-suma"></div>';
      celdasLenta = [...bloque.querySelectorAll("table.p td")];
      bloque.classList.add("visible");
    }
    function pasoLenta(i, j) {
      const a = Math.floor(t / 5), c = t % 5, p = X[i + a][j + c] * K[a][c];
      suma += p;
      const tP = Math.max(tK, 1e-6);
      if (bloque) {
        const td = celdasLenta[t];
        td.textContent = num(p, 2);
        td.style.background = colorSigno(p, tP, tP, 0.55);
        bloque.querySelector(".b-suma").innerHTML = `suma de ${t + 1} de 25 productos = ${num(suma)}`;
      }
      const cc = dibujar.c;
      punto.setAttribute("x", dibujar.xE + (j + c) * cc); punto.setAttribute("y", dibujar.yE + (i + a) * cc); punto.setAttribute("opacity", 1);
      marcar([4, 5, 6, 7], { 4: "i = " + i, 5: "j = " + j, 6: "fila " + (i + a) + ", columna " + (j + c), 7: "producto " + (t + 1) + " de 25" }, 7);
      linea1.textContent = `mapa[${i}, ${j}]: producto ${t + 1} de 25 = ${num(p)}`;
      linea2.textContent = `suma hasta aquí = ${num(suma)}`;
    }
    function cerrarBloque() { if (bloque) { bloque.classList.remove("visible"); } }
    function tablaProb() {
      if (!bloque) return;
      const P = D.probabilidades;
      bloque.innerHTML =
        '<div class="b-tit">prob: lo que responde la red completa para este 0, clase por clase</div>' +
        '<table class="prob"><tr><th>clase</th>' + P.map((_, c) => `<td class="${c === 0 ? "top" : ""}">${c}</td>`).join("") + "</tr>" +
        "<tr><th>prob</th>" + P.map((v, c) => `<td class="${c === 0 ? "top" : ""}">${num(v, 4)}</td>`).join("") + "</tr></table>";
      bloque.classList.add("visible");
    }

    function mostrarFinal(cual) {
      ventana.setAttribute("opacity", 0); marca.setAttribute("opacity", 0); punto.setAttribute("opacity", 0);
      mini.setAttribute("opacity", 1);
      if (cual === "mapas") {
        marcar([], { 8: "6 mapas de 24 × 24, uno por filtro" }, 8);
        salida.setAttribute("opacity", 0);
        linea1.textContent = ancho < 860 ? "6 filtros, 6 mapas del mismo 0" : "los 6 filtros de conv1 dan 6 mapas: cada uno ve un borde distinto del 0";
        linea2.textContent = "coral: positivo · teal: negativo";
      } else {
        marcar([], { 9: "0 → " + num(D.probabilidades[0], 4) }, 9);
        linea1.textContent = ""; linea2.textContent = "";
        salida.setAttribute("opacity", 1);
        salida.textContent = `salida de la red:  0 → ${num(D.probabilidades[0], 4)}`;
        tablaProb();
      }
    }

    function paso() {
      if (!visible) return;
      if (fase === "arranque") {
        // las líneas 1 a 4 se ejecutan una por una y cada una se ve en las cuadrículas
        if (a === 0) {
          ver.entrada = true; mostrar(gEntrada, true, true);
          marcar([], {}, 0);
          linea1.textContent = "x: el 0, 28 × 28 píxeles entre 0 y 1"; linea2.textContent = "";
        } else if (a === 1) {
          ver.filtro = true; mostrar(gFiltro, true, true);
          if (gFiltro) rotMapa.textContent = "el filtro: 25 pesos";
          marcar([], {}, 1);
          linea1.textContent = `w: los 25 pesos del filtro ${f + 1}`; linea2.textContent = "coral: positivo · teal: negativo";
        } else if (a === 2) {
          marcar([], { 2: "b = " + num(b) }, 2);
          linea1.textContent = `b = ${num(b)}: el sesgo, se suma al final`; linea2.textContent = "";
        } else {
          ver.filtro = false; mostrar(gFiltro, false, true);
          ver.mapa = true; mostrar(gMapa, true, true);
          rotMapa.textContent = "lo que ve el filtro";
          marcar([], { 3: "24 × 24 casillas, todas en 0" }, 3);
          linea1.textContent = "mapa: 24 × 24 casillas por llenar"; linea2.textContent = "";
        }
        a++;
        if (a === 4) { fase = "recorre"; k = 0; }
        return programar(a === 4 ? 1400 : 1200);
      }
      if (fase === "lenta") {
        const i = Math.floor(k / 24), j = k % 24;
        if (t < 25) { pasoLenta(i, j); t++; return programar(t === 25 ? 700 : 230); }
        if (t === 25) {
          const zz = suma + b;
          if (bloque) bloque.querySelector(".b-suma").innerHTML = `suma de los 25 productos ${num(suma)} + b ${num(b)} = <b>${num(zz)}</b>`;
          marcar([4, 5, 6, 7], { 4: "i = " + i, 5: "j = " + j, 6: "filas " + i + "–" + (i + 4) + ", columnas " + j + "–" + (j + 4), 7: "= " + num(zz) }, 7);
          linea1.textContent = `mapa[${i}, ${j}] = ${num(suma)} + ${num(b)} = ${num(zz)}`; linea2.textContent = "z = Σ x·w + b";
          punto.setAttribute("opacity", 0);
          t++; return programar(1900);
        }
        cerrarBloque(); lentaHecha = true; fase = "recorre";
        return programar(400);
      }
      if (fase === "recorre") {
        const i = Math.floor(k / 24), j = k % 24;
        ponerVentana(i, j);
        if (k === kLenta && !lentaHecha && bloque) {
          // esta casilla se calcula producto por producto antes de seguir
          fase = "lenta"; t = 0; suma = 0;
          abrirLenta(i, j);
          marcar([4, 5, 6, 7], { 4: "i = " + i, 5: "j = " + j, 6: "filas " + i + "–" + (i + 4) + ", columnas " + j + "–" + (j + 4) }, 7);
          linea1.textContent = `mapa[${i}, ${j}]: ahora, despacio`; linea2.textContent = "";
          return programar(900);
        }
        celdasMapa[k].setAttribute("fill", colorSigno(MAPA[i][j], topePos, topeNeg));
        marcar([4, 5, 6, 7], { 4: "i = " + i, 5: "j = " + j, 6: "filas " + i + "–" + (i + 4) + ", columnas " + j + "–" + (j + 4), 7: "= " + num(z(i, j)) }, 7);
        if (ancho < 600) {
          linea1.textContent = `mapa[${i}, ${j}] = ${num(z(i, j))}`;
          linea2.textContent = "suma de 25 productos x·w + b";
        } else {
          linea1.textContent = `mapa[${i}, ${j}] = suma de 25 productos + b = ${num(z(i, j))}`;
          linea2.textContent = "z = Σ x·w + b   ·   coral: positivo · teal: negativo";
        }
        k++;
        if (k === 576) { fase = "mapas"; espera = 0; mostrarFinal("mapas"); }
        return programar(i === 0 ? 120 : i === 1 ? 45 : 14);
      }
      espera++;
      if (fase === "mapas" && espera > 0) { fase = "salida"; espera = 0; mostrarFinal("salida"); return programar(5000); }
      if (fase === "salida") { reiniciar(); return programar(700); }
      return programar(2800);
    }

    function reiniciar() {
      k = 0; a = 0; t = 0; suma = 0; lentaHecha = false; fase = "arranque"; espera = 0;
      mini.setAttribute("opacity", 0); salida.setAttribute("opacity", 0);
      ventana.setAttribute("opacity", 0); marca.setAttribute("opacity", 0); punto.setAttribute("opacity", 0);
      cerrarBloque();
      ver.entrada = false; ver.filtro = false; ver.mapa = false;
      mostrar(gEntrada, false, false); mostrar(gFiltro, false, false); mostrar(gMapa, false, false);
      rotMapa.textContent = "lo que ve el filtro";
      linea1.textContent = ""; linea2.textContent = "";
      marcar([], {}, -1);
      pintarHasta(0);
    }

    function programar(ms) { clearTimeout(reloj); reloj = setTimeout(paso, fase === "mapas" && ms < 2800 ? 2800 : ms); }

    dibujar();
    if (quieto) {
      // sin movimiento: el estado final, quieto
      ver.entrada = true; ver.mapa = true;
      mostrar(gEntrada, true, false); mostrar(gMapa, true, false);
      k = 576; fase = "salida"; pintarHasta(576); mostrarFinal("salida"); return;
    }
    reiniciar();
    new IntersectionObserver(entradas => {
      visible = entradas[0].isIntersecting;
      if (visible) programar(200); else clearTimeout(reloj);
    }, { threshold: 0.15 }).observe(caja);
    new ResizeObserver(() => { if (Math.abs(caja.clientWidth - ancho) > 4) dibujar(); }).observe(caja);
  }

  window.montarCero = montarCero;
})();
