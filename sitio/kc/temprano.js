// Ket Cero · lo primero que corre en una animación, antes de pintar: el alto de la cabecera, el tema y «Cargando la animación…».
// En modo oscuro la página entera se invierte (ver capa.css), por eso aquí los colores son los del modo claro.
var KC_ALTO = 65;
(function () {
  var r = document.documentElement, oscuro = true;
  try { oscuro = localStorage.getItem("tema") !== "claro"; } catch (e) {}
  if (oscuro) r.classList.add("kc-oscuro");
  var c = document.createElement("div");
  c.id = "kc-carga";
  c.setAttribute("role", "status");
  c.style.cssText = "position:fixed;inset:0;z-index:2147483000;display:flex;align-items:center;justify-content:center;" +
    "background:#FFFFFF;color:#161616;font:15px/1.6 'IBM Plex Sans',system-ui,sans-serif;text-align:center;transition:opacity .25s";
  c.innerHTML = '<div><svg width="68" height="48" viewBox="0 0 44 30" aria-hidden="true"><line x1="5" y1="3" x2="5" y2="27" stroke="#161616" stroke-width="2.6" stroke-linecap="round"/>' +
    '<ellipse cx="19" cy="15" rx="6" ry="11" fill="none" stroke="' + (oscuro ? "#FF8255" : "#C8502A") + '" stroke-width="2.6"/>' +
    '<polyline points="31,3 39,15 31,27" fill="none" stroke="#161616" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg>' +
    '<p style="margin:18px 0 4px;font-weight:500">Cargando la animación…</p>' +
    '<small style="color:#616161;font-size:13px">Trae los datos reales de cada paso: la primera vez tarda unos segundos.</small></div>';
  r.appendChild(c);
})();
