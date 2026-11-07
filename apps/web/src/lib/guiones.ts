// Scripts pequeños que van dentro de cada página (sin empaquetar), los mismos del sitio que arma construir.py.

// Aplica el tema guardado antes de pintar (sin parpadeo).
export const TEMA_JS = 'try{var t=localStorage.getItem("tema");if(t)document.documentElement.dataset.tema=t}catch(e){}';

export const CLIP_JS = `
(function () {
  var quieto = matchMedia("(prefers-reduced-motion: reduce)").matches;
  document.querySelectorAll("video.clip").forEach(function (v) {
    if (quieto) { v.removeAttribute("autoplay"); v.pause(); return; }
    // más rápido que el clip grabado: cada paso dura ~1,3 s en vez de 2,6 s
    v.defaultPlaybackRate = 2; v.playbackRate = 2;
    v.addEventListener("play", function () { v.playbackRate = 2; });
    if (!v.hasAttribute("data-al-pasar")) return;
    var fila = v.closest("a") || v;
    fila.addEventListener("mouseenter", function () { v.play().catch(function () {}); });
    fila.addEventListener("mouseleave", function () { v.pause(); });
  });
})();
`;

export const BOTON_JS = `
(function () {
  var b = document.getElementById("tema"), r = document.documentElement;
  function oscuro() { return r.dataset.tema !== "claro"; }  // oscuro por defecto
  function rotulo() { b.setAttribute("aria-checked", oscuro() ? "true" : "false"); }
  b.addEventListener("click", function () {
    r.dataset.tema = oscuro() ? "claro" : "oscuro";
    try { localStorage.setItem("tema", r.dataset.tema); } catch (e) {}
    rotulo();
  });
  rotulo();
})();
(function () {
  var m = document.getElementById("menu"), c = document.getElementById("cajon"), v = document.getElementById("velo");
  function medir() {
    var raya = document.querySelector(".marca small");
    var x = raya && raya.offsetParent ? raya.getBoundingClientRect().left : 0;
    document.documentElement.style.setProperty("--ancho-cajon", x > 200 ? x + "px" : "86vw");
  }
  medir();
  addEventListener("resize", medir);
  function poner(abierto) {
    m.setAttribute("aria-expanded", abierto ? "true" : "false");
    c.classList.toggle("abierto", abierto);
    v.hidden = !abierto;
    if (abierto) c.querySelector("a").focus();
  }
  m.addEventListener("click", function () { poner(m.getAttribute("aria-expanded") !== "true"); });
  v.addEventListener("click", function () { poner(false); });
  c.addEventListener("click", function (e) { if (e.target.closest("a")) poner(false); });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape" && !v.hidden) { poner(false); m.focus(); } });
})();
(function () {
  var b = document.getElementById("cursos"), l = document.getElementById("lista-cursos");
  function poner(abierto) { b.setAttribute("aria-expanded", abierto ? "true" : "false"); l.hidden = !abierto; }
  b.addEventListener("click", function (e) { e.stopPropagation(); poner(l.hidden); });
  document.addEventListener("click", function (e) { if (!l.hidden && !l.contains(e.target)) poner(false); });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape" && !l.hidden) { poner(false); b.focus(); } });
})();
(function () {
  // lecciones ya abiertas (las marca la capa de las animaciones) y «seguir donde quedaste»
  var vistas = [];
  try { vistas = JSON.parse(localStorage.getItem("kc-vistas") || "[]"); } catch (e) {}
  [].forEach.call(document.querySelectorAll("[data-leccion]"), function (el) {
    if (vistas.indexOf(el.getAttribute("data-leccion")) < 0 || el.id === "seguir") return;
    var s = document.createElement("span"); s.className = "vista"; s.textContent = "vista";
    (el.querySelector(".d") || el).appendChild(s);
  });
  var seguir = document.getElementById("seguir");
  if (seguir) try {
    var h = localStorage.getItem("kc-paso-" + seguir.getAttribute("data-leccion"));
    if (h && /^#[a-z_0-9]+\\/\\d+$/.test(h)) {
      var p = h.slice(1).split("/");
      seguir.href = seguir.getAttribute("data-animacion") + h;
      seguir.textContent = "Seguir donde quedaste: " + p[0] + ", paso " + p[1] + " →";
      seguir.hidden = false;
    }
  } catch (e) {}
})();
(function () {
  // «Cargando la animación…» mientras el navegador trae una animación pesada
  var c = document.getElementById("cargando");
  document.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest("a[data-abre-animacion]");
    if (a && c && e.button === 0 && !e.ctrlKey && !e.metaKey && !e.shiftKey) c.hidden = false;
  });
  addEventListener("pageshow", function () { if (c) c.hidden = true; });
})();
`;
