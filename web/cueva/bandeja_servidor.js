/* bandeja_servidor.js — la bandeja de la Mesa, compartida con el resto de La Cueva.
 *
 * La bandeja de la Mesa vivía solo en el navegador (st.bandeja + localStorage). Este
 * script la sincroniza con la bandeja del servidor (/api/v1/bandeja), que es la misma que
 * ve la Terminal: lo que se manda desde la ficha de un activo aparece acá, y lo que se
 * agrega o se quita en la Mesa se refleja allá.
 *
 * Correspondencia de ítems:
 *   Mesa {tipo:"cat", id}            ⇄  servidor {tipo:"serie", ref:id}            (sin datos)
 *   Mesa {tipo:"serie", k, x, y, …}  ⇄  servidor {tipo:"serie", ref:k, datos:{x,y,…}}
 *
 * Las series de la Terminal que todavía no están en el catálogo cargado se traen a pedido
 * (CuevaTerminalAPedido.asegurar). En el sitio publicado no hay servidor: no hace nada.
 */
(function () {
  if (window.CUEVA_ESTATICO) return;
  const API = "/api/v1/bandeja";
  const CLAVE = "cueva_bandeja_sinc_v1"; // k de la Mesa → id del servidor ya sincronizados
  let sinc = new Map();
  try { sinc = new Map(Object.entries(JSON.parse(localStorage.getItem(CLAVE) || "{}"))); } catch (_) { /* vacío */ }
  const recordar = () => { try { localStorage.setItem(CLAVE, JSON.stringify(Object.fromEntries(sinc))); } catch (_) { /* sin almacenamiento */ } };

  const claveDe = (sv) => (sv.datos && sv.datos.y ? sv.ref : "cat:" + sv.ref);
  let listo = false, ocupado = false;

  function aServidor(it) {
    if (it.tipo === "cat") return { tipo: "serie", ref: it.id, etiqueta: it.nombre, procedencia: { origen: "mesa" } };
    const n = it.x ? it.x.length : 0, d = n > 4000 ? n - 4000 : 0;
    return {
      tipo: "serie", ref: it.k.slice(0, 200), etiqueta: (it.nombre || it.alias || "serie").slice(0, 200),
      receta: it.receta ? { texto: String(it.receta).slice(0, 2000) } : null,
      procedencia: { origen: "mesa" },
      datos: { x: (it.x || []).slice(d), y: (it.y || []).slice(d), unidad: it.unidad || "", alias: it.alias || null },
    };
  }

  async function deMesaItem(sv) {
    if (sv.datos && sv.datos.y) {
      return { k: sv.ref, tipo: "serie", nombre: sv.etiqueta || sv.ref, alias: sv.datos.alias || null, receta: sv.receta?.texto || "desde la bandeja", x: sv.datos.x, y: sv.datos.y, unidad: sv.datos.unidad || "" };
    }
    if (!CATS[sv.ref] && window.CuevaTerminalAPedido) {
      try { await window.CuevaTerminalAPedido.asegurar(sv.ref); } catch (e) { console.warn("bandeja:", e.message); return null; }
    }
    return CATS[sv.ref] ? itemDeCat(sv.ref) : null;
  }

  // Lo que cambió en la Mesa sube al servidor.
  async function empujar() {
    if (ocupado) return;
    ocupado = true;
    try {
      const enMesa = new Set(st.bandeja.map((b) => b.k));
      for (const [k, id] of [...sinc]) {
        if (enMesa.has(k)) continue;
        sinc.delete(k);
        if (id && id !== "…") await fetch(`${API}/${id}`, { method: "DELETE" }).catch(() => {});
      }
      for (const it of st.bandeja) {
        if (sinc.has(it.k)) continue;
        sinc.set(it.k, "…");
        try {
          const r = await fetch(API, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(aServidor(it)) });
          if (!r.ok) throw new Error(r.status);
          sinc.set(it.k, (await r.json()).id);
        } catch (_) { sinc.delete(it.k); }
      }
      recordar();
    } finally { ocupado = false; }
  }

  // Lo que llegó al servidor (desde la Terminal u otra pestaña) baja a la Mesa.
  async function traer() {
    if (ocupado) return;
    let items;
    try { const r = await fetch(API); if (!r.ok) return; items = (await r.json()).items || []; } catch (_) { return; }
    ocupado = true;
    let cambio = false;
    try {
      const vivos = new Set(items.map((i) => i.id));
      // quitados en otro lado: salen también de la Mesa
      for (const [k, id] of [...sinc]) {
        if (id === "…" || vivos.has(id)) continue;
        sinc.delete(k);
        const i = st.bandeja.findIndex((b) => b.k === k);
        if (i >= 0) { st.bandeja.splice(i, 1); cambio = true; }
      }
      const conocidos = new Set(sinc.values());
      const nuevos = [];
      for (const sv of items) {
        if (sv.tipo !== "serie" || conocidos.has(sv.id)) continue;
        const k = claveDe(sv);
        if (sinc.has(k)) { // duplicado en el servidor: se queda con el primero
          continue;
        }
        sinc.set(k, sv.id);
        if (st.bandeja.some((b) => b.k === k)) continue;
        const it = await deMesaItem(sv);
        if (it) { st.bandeja.push(it); nuevos.push(it); cambio = true; }
      }
      recordar();
      if (cambio) {
        ORIG_render(); guardar();
        if (nuevos.length && listo) {
          toast(nuevos.length === 1 ? `Llegó «${nuevos[0].nombre.slice(0, 50)}» a la bandeja.` : `Llegaron ${nuevos.length} series a la bandeja.`);
          const b = document.getElementById("bandeja");
          if (b) { b.classList.remove("pulso"); void b.offsetWidth; b.classList.add("pulso"); }
        }
      }
    } finally { ocupado = false; }
  }

  const ORIG_render = renderBandeja;
  // eslint-disable-next-line no-global-assign
  renderBandeja = function () { ORIG_render(); if (listo) empujar(); };

  (async function iniciar() {
    // primera vez: lo que ya tenía la Mesa sube; después, el servidor manda
    await traer();
    listo = true;
    await empujar();
    setInterval(() => { if (document.visibilityState === "visible") traer(); }, 4000);
    window.addEventListener("focus", traer);
  })();

  window.CuevaBandeja = { traer, empujar };
})();
