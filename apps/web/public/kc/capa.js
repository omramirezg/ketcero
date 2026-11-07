var KC_LECCIONES = {"la-cnn-completa": {"titulo": "La CNN completa, por dentro", "numero": "2.1", "pagina": "/cursos/deep-learning/la-cnn-completa/", "animacion": "/ia/cnn/Animacion_A4_la_CNN_completa", "anterior": null, "siguiente": {"titulo": "Mini-YOLO por dentro: dígitos en la calle", "pagina": "/cursos/deep-learning/mini-yolo-digitos-en-la-calle/"}}, "mini-yolo-digitos-en-la-calle": {"titulo": "Mini-YOLO por dentro: dígitos en la calle", "numero": "3.1", "pagina": "/cursos/deep-learning/mini-yolo-digitos-en-la-calle/", "animacion": "/ia/deteccion/Animacion_B1_Mini_YOLO_por_dentro", "anterior": {"titulo": "La CNN completa, por dentro", "pagina": "/cursos/deep-learning/la-cnn-completa/"}, "siguiente": {"titulo": "Tipos de segmentación: semántica, de instancias y panóptica", "pagina": "/cursos/deep-learning/tipos-de-segmentacion/"}}, "tipos-de-segmentacion": {"titulo": "Tipos de segmentación: semántica, de instancias y panóptica", "numero": "4.1", "pagina": "/cursos/deep-learning/tipos-de-segmentacion/", "animacion": "/ia/segmentacion/Animacion_U0_tipos_de_segmentacion", "anterior": {"titulo": "Mini-YOLO por dentro: dígitos en la calle", "pagina": "/cursos/deep-learning/mini-yolo-digitos-en-la-calle/"}, "siguiente": {"titulo": "U-Net por dentro: edificios en fotos satelitales", "pagina": "/cursos/deep-learning/unet-edificios-en-fotos-satelitales/"}}, "unet-edificios-en-fotos-satelitales": {"titulo": "U-Net por dentro: edificios en fotos satelitales", "numero": "4.2", "pagina": "/cursos/deep-learning/unet-edificios-en-fotos-satelitales/", "animacion": "/ia/segmentacion/Animacion_U1_UNet_por_dentro", "anterior": {"titulo": "Tipos de segmentación: semántica, de instancias y panóptica", "pagina": "/cursos/deep-learning/tipos-de-segmentacion/"}, "siguiente": null}};
var KC_ANALITICA = "";
// Ket Cero · capa del sitio sobre las animaciones del curso. Corre al final de la página, cuando el motor ya montó.
// Arriba de este archivo, construir.py escribe KC_LECCIONES (título, página, anterior y siguiente de cada lección) y KC_ANALITICA.
(function () {
  var r = document.documentElement, slug = r.getAttribute("data-kc-leccion"), lec = (window.KC_LECCIONES || {})[slug] || {};
  function guardar(clave, valor) { try { localStorage.setItem(clave, valor); } catch (e) {} }
  function leer(clave) { try { return localStorage.getItem(clave); } catch (e) { return null; } }
  function esc(t) { return String(t).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }

  // ---- cabecera del sitio ----
  var logo = '<svg width="34" height="24" viewBox="0 0 44 30" aria-hidden="true"><line x1="5" y1="3" x2="5" y2="27" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>' +
    '<ellipse class="kc-cero" cx="19" cy="15" rx="6" ry="11" fill="none" stroke-width="3"/>' +
    '<polyline points="31,3 39,15 31,27" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  // un solo grupo de navegación: ‹ Lección 4.2 › (las flechas van a la anterior y la siguiente; el número, a la página de la lección)
  function flecha(v, texto, cual) {
    return v ? '<a class="kc-flecha" href="' + v.pagina + '" title="Lección ' + cual + ': ' + esc(v.titulo) + '" aria-label="Lección ' + cual + ': ' + esc(v.titulo) + '">' + texto + '</a>'
             : '<span class="kc-flecha kc-sin" aria-hidden="true">' + texto + '</span>';
  }
  var grupo = '<span class="kc-grupo">' + flecha(lec.anterior, "‹", "anterior") +
    '<a class="kc-numero" href="' + (lec.pagina || "/cursos/") + '" title="Volver a la página de la lección: ' + esc(lec.titulo || "") + '">Lección ' + esc(lec.numero || "") + '</a>' +
    flecha(lec.siguiente, "›", "siguiente") + '</span>';
  document.body.insertAdjacentHTML("afterbegin",
    '<header id="kc-cab"><a class="kc-marca" href="/" aria-label="Ket Cero, inicio">' + logo + 'Ket Cero<small>Machine learning desde cero</small></a>' +
    '<nav aria-label="Lección"><span class="kc-aviso" title="Esta animación todavía está en revisión y puede tener errores">Versión preliminar: puede tener errores</span>' +
    grupo +
    '<button id="kc-ayuda-boton" type="button" aria-expanded="false" aria-controls="kc-ayuda" aria-label="Atajos de teclado y del mouse">?</button>' +
    '<button id="kc-tema" type="button" role="switch" aria-checked="true">Modo oscuro<span class="kc-pista"><span class="kc-perilla"></span></span></button></nav></header>' +
    '<div id="kc-ayuda" class="kc-caja" role="dialog" aria-label="Atajos" hidden><h2>Atajos</h2><dl>' +
    '<dt>→  Espacio</dt><dd>Paso siguiente</dd><dt>←</dt><dd>Paso anterior</dd><dt>Inicio  Fin</dt><dd>Primer y último paso</dd>' +
    '<dt>K</dt><dd>Pausar o seguir la animación del paso</dd><dt>P</dt><dd>Reproducir los pasos solos</dd>' +
    '<dt>Ctrl + rueda</dt><dd>Acercar el dibujo (o los botones + y −)</dd><dt>Arrastrar</dt><dd>Moverse por el dibujo acercado</dd>' +
    '<dt>Ampliar  Esc</dt><dd>Solo el dibujo en pantalla completa, y salir</dd></dl></div>');

  var bTema = document.getElementById("kc-tema");
  function ponerTema() { bTema.setAttribute("aria-checked", r.classList.contains("kc-oscuro") ? "true" : "false"); }
  bTema.addEventListener("click", function () {
    r.classList.toggle("kc-oscuro");
    guardar("tema", r.classList.contains("kc-oscuro") ? "oscuro" : "claro");
    ponerTema();
  });
  ponerTema();

  var bAyuda = document.getElementById("kc-ayuda-boton"), ayuda = document.getElementById("kc-ayuda");
  function ponerAyuda(si) { ayuda.hidden = !si; bAyuda.setAttribute("aria-expanded", si ? "true" : "false"); }
  bAyuda.addEventListener("click", function (e) { e.stopPropagation(); ponerAyuda(ayuda.hidden); });
  document.addEventListener("click", function (e) { if (!ayuda.hidden && !ayuda.contains(e.target)) ponerAyuda(false); });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && !ayuda.hidden) ponerAyuda(false);
    if (e.key === "?" && !e.ctrlKey && !e.metaKey) ponerAyuda(ayuda.hidden);
  });

  // ---- lección vista y «seguir donde quedaste» ----
  if (slug) {
    var vistas = [];
    try { vistas = JSON.parse(leer("kc-vistas") || "[]"); } catch (e) {}
    if (vistas.indexOf(slug) < 0) { vistas.push(slug); guardar("kc-vistas", JSON.stringify(vistas)); }
    var guardado = leer("kc-paso-" + slug), pasoValido = /^#[a-z_0-9]+\/\d+$/;
    if (guardado && pasoValido.test(guardado) && (location.hash === "" || location.hash === "#inicio")) {
      var p = guardado.slice(1).split("/");
      document.body.insertAdjacentHTML("beforeend", '<div id="kc-seguir" class="kc-caja" role="status"><span>Quedaste en ' + esc(p[0]) + ', paso ' + esc(p[1]) + '</span>' +
        '<button type="button" data-s="si">Seguir ahí</button><button type="button" data-s="no" aria-label="Cerrar">×</button></div>');
      var cajaSeguir = document.getElementById("kc-seguir");
      cajaSeguir.addEventListener("click", function (e) {
        var b = e.target.closest("button"); if (!b) return;
        if (b.getAttribute("data-s") === "si") location.hash = guardado;
        cajaSeguir.remove();
      });
      setTimeout(function () { if (document.getElementById("kc-seguir") && location.hash !== "#inicio" && location.hash !== "") cajaSeguir.remove(); }, 400);
    }
    var ultimo = location.hash;
    setInterval(function () {
      if (location.hash === ultimo) return;
      ultimo = location.hash;
      if (pasoValido.test(ultimo)) {
        guardar("kc-paso-" + slug, ultimo);
        var s = document.getElementById("kc-seguir"); if (s) s.remove();
      }
    }, 400);
  }

  // ---- celular: la animación tiene mucho detalle ----
  if (innerWidth < 900 && leer("kc-movil-ok") !== "1") {
    document.body.insertAdjacentHTML("beforeend", '<div id="kc-movil" class="kc-caja" role="dialog" aria-label="Aviso"><div>' +
      '<p>Esta animación se ve mejor en un computador</p><small>Tiene mucho detalle: matrices, números y varias capas a la vez.</small>' +
      '<button type="button">Seguir de todas formas</button><a href="' + (lec.pagina || "/") + '">Volver a la lección</a></div></div>');
    document.querySelector("#kc-movil button").addEventListener("click", function () { guardar("kc-movil-ok", "1"); document.getElementById("kc-movil").remove(); });
  }

  // ---- analítica (Cloudflare Web Analytics, sin cookies) ----
  if (window.KC_ANALITICA) {
    var a = document.createElement("script");
    a.defer = true; a.src = "https://static.cloudflareinsights.com/beacon.min.js";
    a.setAttribute("data-cf-beacon", JSON.stringify({ token: window.KC_ANALITICA }));
    document.head.appendChild(a);
  }

  // ---- el motor ya montó: se quita «Cargando la animación…» ----
  var carga = document.getElementById("kc-carga");
  if (carga) requestAnimationFrame(function () { requestAnimationFrame(function () { carga.style.opacity = "0"; setTimeout(function () { carga.remove(); }, 260); }); });
  addEventListener("pageshow", function () { var c = document.getElementById("kc-carga"); if (c) c.remove(); });
})();

// Zoom del dibujo (svg#dibujo): se acerca cambiando su viewBox, así solo se mueve lo de adentro del cuadro
// (el SVG recorta lo que sale de su caja) y el texto vectorial queda nítido. «Ampliar» deja solo el dibujo en pantalla completa.
// Al cambiar de paso (cambia el #hash) o si el motor pone otro viewBox, vuelve a la vista completa.
(function () {
  var svg = document.getElementById("dibujo"), r = document.documentElement;
  if (!svg) return;
  document.body.insertAdjacentHTML("beforeend", '<div id="kc-zoom" role="toolbar" aria-label="Zoom del dibujo">' +
    '<button type="button" data-z="menos" aria-label="Alejar" title="Alejar">−</button><span class="kc-nivel" aria-live="polite">1×</span>' +
    '<button type="button" data-z="mas" aria-label="Acercar" title="Acercar (también Ctrl + rueda del mouse o pellizcar)">+</button>' +
    '<button type="button" data-z="cero" aria-label="Vista completa" title="Vista completa">⟲</button>' +
    '<button type="button" data-z="ampliar" title="Ver solo el dibujo en pantalla completa (Esc para salir)">Ampliar</button></div>');
  var caja = document.getElementById("kc-zoom");
  var nivel = caja.querySelector(".kc-nivel"), botonAmpliar = caja.querySelector('[data-z="ampliar"]');
  var z = 1, base = null, propio = null, hash = location.hash, MAX = 6;
  function leer() { var v = (svg.getAttribute("viewBox") || "").trim().split(/[\s,]+/).map(Number); return v.length === 4 && v.every(isFinite) ? v : null; }
  function texto(v) { return v.map(function (n) { return +n.toFixed(3); }).join(" "); }
  // pone el zoom nz manteniendo fijo el punto (px, py) del dibujo; sin punto, acerca hacia el centro de lo que se ve
  function poner(nz, px, py) {
    if (!base) { base = leer(); if (!base) return; }
    nz = Math.max(1, Math.min(MAX, nz));
    var c = leer() || base, w = base[2] / nz, h = base[3] / nz, x, y;
    if (px == null) { x = c[0] + c[2] / 2 - w / 2; y = c[1] + c[3] / 2 - h / 2; }
    else { x = px - (px - c[0]) * (w / c[2]); y = py - (py - c[1]) * (h / c[3]); }
    x = Math.max(base[0], Math.min(base[0] + base[2] - w, x));
    y = Math.max(base[1], Math.min(base[1] + base[3] - h, y));
    z = nz;
    if (z <= 1.001) { z = 1; propio = null; svg.setAttribute("viewBox", texto(base)); }
    else { propio = texto([x, y, w, h]); svg.setAttribute("viewBox", propio); }
    r.classList.toggle("kc-zoom-activo", z > 1);
    nivel.textContent = (Math.round(z * 10) / 10).toString().replace(".", ",") + "×";
  }
  function reiniciar() { if (z > 1 && base) poner(1); base = null; z = 1; propio = null; r.classList.remove("kc-zoom-activo"); nivel.textContent = "1×"; }
  // si el motor cambia el viewBox (un paso nuevo, un paso ancho), esa pasa a ser la vista completa
  new MutationObserver(function () {
    var v = svg.getAttribute("viewBox");
    if (v === propio || (z === 1 && base && v === texto(base))) return;
    base = null; z = 1; propio = null; r.classList.remove("kc-zoom-activo"); nivel.textContent = "1×";
  }).observe(svg, { attributes: true, attributeFilter: ["viewBox"] });
  setInterval(function () { if (location.hash !== hash) { hash = location.hash; reiniciar(); } ubicar(); }, 250);
  function punto(ev) { var p = svg.createSVGPoint(); p.x = ev.clientX; p.y = ev.clientY; return p.matrixTransform(svg.getScreenCTM().inverse()); }
  caja.addEventListener("click", function (ev) {
    var b = ev.target.closest("button"); if (!b) return;
    var q = b.getAttribute("data-z");
    if (q === "mas") poner(z * 1.5); else if (q === "menos") poner(z / 1.5); else if (q === "cero") poner(1); else if (q === "ampliar") ampliar(!r.classList.contains("kc-ampliado"));
  });
  // Ctrl + rueda: acerca alrededor del puntero (la rueda sola sigue siendo de la página)
  svg.addEventListener("wheel", function (ev) {
    if (!ev.ctrlKey) return;
    ev.preventDefault(); ev.stopPropagation();
    var p = punto(ev); poner(z * Math.exp(-Math.max(-120, Math.min(120, ev.deltaY)) * 0.0015), p.x, p.y);
  }, { passive: false, capture: true });
  // arrastrar para moverse (solo con zoom) y pellizcar con dos dedos
  var dedos = {}, arrastre = null, pellizco = null, movido = false;
  svg.addEventListener("pointerdown", function (ev) {
    dedos[ev.pointerId] = { x: ev.clientX, y: ev.clientY };
    var ids = Object.keys(dedos);
    if (ids.length === 2) {
      var a = dedos[ids[0]], b = dedos[ids[1]];
      pellizco = { d: Math.hypot(a.x - b.x, a.y - b.y), z: z }; arrastre = null; return;
    }
    if (z > 1 && ev.button === 0) { arrastre = { x: ev.clientX, y: ev.clientY, v: leer() }; movido = false; svg.setPointerCapture(ev.pointerId); }
  });
  svg.addEventListener("pointermove", function (ev) {
    if (!dedos[ev.pointerId]) return;
    dedos[ev.pointerId] = { x: ev.clientX, y: ev.clientY };
    var ids = Object.keys(dedos);
    if (pellizco && ids.length === 2) {
      var a = dedos[ids[0]], b = dedos[ids[1]], m = punto({ clientX: (a.x + b.x) / 2, clientY: (a.y + b.y) / 2 });
      poner(pellizco.z * Math.hypot(a.x - b.x, a.y - b.y) / pellizco.d, m.x, m.y); ev.preventDefault(); return;
    }
    if (!arrastre || !base) return;
    var dx = ev.clientX - arrastre.x, dy = ev.clientY - arrastre.y;
    if (Math.abs(dx) + Math.abs(dy) > 3) { movido = true; r.classList.add("kc-arrastrando"); }
    var k = svg.getScreenCTM().a, v = arrastre.v;
    var x = Math.max(base[0], Math.min(base[0] + base[2] - v[2], v[0] - dx / k));
    var y = Math.max(base[1], Math.min(base[1] + base[3] - v[3], v[1] - dy / k));
    propio = texto([x, y, v[2], v[3]]); svg.setAttribute("viewBox", propio);
  });
  function soltar(ev) {
    delete dedos[ev.pointerId];
    if (Object.keys(dedos).length < 2) pellizco = null;
    arrastre = null; r.classList.remove("kc-arrastrando");
  }
  svg.addEventListener("pointerup", soltar); svg.addEventListener("pointercancel", soltar);
  // un arrastre no cuenta como clic sobre el dibujo
  svg.addEventListener("click", function (ev) { if (movido) { ev.stopPropagation(); ev.preventDefault(); movido = false; } }, true);
  function ampliar(si) {
    r.classList.toggle("kc-ampliado", si);
    botonAmpliar.textContent = si ? "Cerrar" : "Ampliar";
    try {
      if (si && r.requestFullscreen && !document.fullscreenElement) r.requestFullscreen().catch(function () {});
      if (!si && document.fullscreenElement) document.exitFullscreen().catch(function () {});
    } catch (e) {}
    ubicar();
  }
  document.addEventListener("fullscreenchange", function () { if (!document.fullscreenElement && r.classList.contains("kc-ampliado")) ampliar(false); });
  document.addEventListener("keydown", function (ev) { if (ev.key === "Escape" && r.classList.contains("kc-ampliado")) ampliar(false); });
  // los controles van en la esquina inferior derecha del cuadro del dibujo, solo cuando hay dibujo a la vista
  function ubicar() {
    if (r.classList.contains("kc-ampliado")) {
      caja.style.display = "flex"; caja.style.left = "auto"; caja.style.top = "auto"; caja.style.right = "24px"; caja.style.bottom = "14px"; return;
    }
    var b = svg.getBoundingClientRect(), inicio = document.getElementById("inicio");
    var hay = b.width > 120 && b.height > 80 && getComputedStyle(svg).display !== "none" && getComputedStyle(svg).visibility !== "hidden"
      && svg.childElementCount > 1 && !(inicio && inicio.offsetParent !== null && getComputedStyle(inicio).display !== "none");
    caja.style.display = hay ? "flex" : "none";
    if (!hay) return;
    caja.style.right = "auto"; caja.style.bottom = "auto";
    caja.style.left = Math.max(8, b.right - caja.offsetWidth - 8) + "px";
    caja.style.top = Math.max(8, b.bottom - caja.offsetHeight - 8) + "px";
  }
  addEventListener("resize", ubicar);
  ubicar();
  // la barra solo aparece con el mouse sobre el dibujo (o sobre la barra), si hay zoom o si está ampliado
  var sobre = false, quitar = null;
  document.addEventListener("mousemove", function (ev) {
    var b = svg.getBoundingClientRect(), c = caja.getBoundingClientRect();
    var dentro = (ev.clientX >= b.left && ev.clientX <= b.right && ev.clientY >= b.top && ev.clientY <= b.bottom) ||
      (ev.clientX >= c.left && ev.clientX <= c.right && ev.clientY >= c.top && ev.clientY <= c.bottom);
    if (dentro) { clearTimeout(quitar); if (!sobre) { sobre = true; r.classList.add("kc-sobre-dibujo"); } }
    else if (sobre) { clearTimeout(quitar); quitar = setTimeout(function () { sobre = false; r.classList.remove("kc-sobre-dibujo"); }, 600); }
  });
})();
