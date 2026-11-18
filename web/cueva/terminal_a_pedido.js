/* terminal_a_pedido.js — cualquier serie de la Terminal, traída a la Mesa cuando se la pide.
 *
 * El catálogo de la Mesa (CAT) trae precargadas unas 68 series de la Terminal; el resto del
 * universo (cada activo por ticker, la macro de FRED, los balances trimestrales) aparece con
 * estado «terminal». Este módulo las baja de GET /api/v1/mesa/serie/{id} en el momento en que
 * se tocan en el catálogo o se buscan con «Traer», y desde ahí son fichas como cualquier otra:
 * se grafican, se transforman y entran a los 102 métodos.
 *
 * Usa las globales de la página: CAT, CATS, datosCat, delCatalogo, mostrarFicha, cambio,
 * render, renderCatSide, toast, st, esc.
 */
(function () {
  "use strict";
  const enCurso = new Map();

  // las series traídas guardan x/y propios (no están alineadas al calendario de CAT)
  const datosCatOriginal = datosCat;
  datosCat = function (id) {
    const m = CATS[id];
    if (m && m.x) return { x: m.x.slice(), y: m.y.slice() };
    return datosCatOriginal(id);
  };

  function filaTerminal(id) {
    return CAT.arbol.find((a) => a[6] === id && a[7] === "terminal");
  }

  async function asegurar(id) {
    if (CATS[id]) return CATS[id];
    if (enCurso.has(id)) return enCurso.get(id);
    const p = (async () => {
      const r = await fetch("/api/v1/mesa/serie/" + encodeURIComponent(id));
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(j?.error?.mensaje || j?.detail || `no se pudo traer ${id}`);
      CATS[id] = { nombre: j.nombre, corto: j.corto, freq: j.freq, unidad: j.unidad, fuente: j.fuente, familia: j.familia, grupo: j.grupo, subgrupo: j.subgrupo, url: j.url || undefined, x: j.x, y: j.y };
      const fila = filaTerminal(id);
      if (fila) fila[7] = "datos";
      const dl = document.getElementById("dl-panel");
      if (dl) dl.insertAdjacentHTML("beforeend", `<option value="${esc(j.corto)}">${esc(j.nombre)}</option>`);
      try { renderCatSide(); } catch (_) { /* el catálogo puede no estar a la vista */ }
      return CATS[id];
    })();
    enCurso.set(id, p);
    try { return await p; } finally { enCurso.delete(id); }
  }

  async function traerAMesa(id) {
    toast(`Trayendo «${id}» de la Terminal…`);
    try { await asegurar(id); } catch (e) { toast("✕ " + e.message); return null; }
    cambio();
    const s = delCatalogo(id);
    mostrarFicha(s);
    st.sel.clear(); st.sel.add(s.id);
    render();
    toast(`«${s.alias}» en la Mesa y en el gráfico activo (de la Terminal).`);
    return s;
  }

  // catálogo lateral: tocar una fila «Terminal»
  document.addEventListener("click", (e) => {
    const it = e.target.closest("[data-cs-term]");
    if (!it) return;
    e.preventDefault(); e.stopPropagation();
    traerAMesa(it.dataset.csTerm);
  }, true);
  document.addEventListener("keydown", (e) => {
    const it = e.target.closest?.("[data-cs-term]");
    if (it && e.key === "Enter") { e.preventDefault(); traerAMesa(it.dataset.csTerm); }
  });

  // buscador «Traer»: si no está entre las cargadas pero sí en la Terminal, la trae
  function buscarEnTerminal(q) {
    q = q.trim().toLowerCase(); if (!q) return null;
    const filas = CAT.arbol.filter((a) => a[7] === "terminal");
    const txt = (a) => `${a[6]} ${a[3]} ${a[1]} ${a[2]}`.toLowerCase();
    const exacta = filas.find((a) => a[6].toLowerCase() === q || a[3].toLowerCase() === q);
    return (exacta || filas.find((a) => txt(a).includes(q)) || filas.find((a) => q.split(/\s+/).every((w) => txt(a).includes(w))))?.[6] || null;
  }
  function yaCargada(q) {
    q = q.trim().toLowerCase();
    return Object.keys(CATS).some((k) => k.toLowerCase() === q || (CATS[k].corto || "").toLowerCase() === q || (CATS[k].corto + " " + CATS[k].nombre + " " + k).toLowerCase().includes(q));
  }
  function interceptar(e) {
    const q = document.getElementById("buscar")?.value || "";
    if (!q.trim() || yaCargada(q)) return; // lo resuelve la Mesa como siempre
    const id = buscarEnTerminal(q);
    if (!id) return;
    e.preventDefault(); e.stopImmediatePropagation();
    document.getElementById("buscar").value = "";
    traerAMesa(id);
  }
  document.getElementById("traer")?.addEventListener("click", interceptar, true);
  document.getElementById("buscar")?.addEventListener("keydown", (e) => { if (e.key === "Enter") interceptar(e); }, true);

  // sugerencias del buscador: también las series de la Terminal
  const dl = document.getElementById("dl-panel");
  if (dl) dl.insertAdjacentHTML("beforeend", CAT.arbol.filter((a) => a[7] === "terminal").slice(0, 3000).map((a) => `<option value="${esc(a[6])}">${esc(a[3])} · Terminal</option>`).join(""));

  window.CuevaTerminalAPedido = { asegurar, traerAMesa };
})();
