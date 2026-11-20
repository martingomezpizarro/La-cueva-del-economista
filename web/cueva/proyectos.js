/* proyectos.js — selector de proyectos de la Mesa (La Cueva).
   «+ Nuevo proyecto», los proyectos guardados en el servidor y los predeterminados
   («Valuación de empresa»). Sin proyecto abierto la Mesa es la Vista rápida: lo de siempre,
   guardado sólo en este navegador. Con un proyecto abierto, el Documento, las figuras del
   Proyecto y las corridas que esas figuras usan se guardan en el servidor
   (GET|PUT /api/v1/proyectos/{id}/mesa).
   Depende de los globales de index.html: st, render, renderTablero, guardar, toast, esc. */
(function () {
  "use strict";
  const CLAVE = "cueva_proyecto_actual";
  const P = { actual: null, titulo: "", plantilla: null, lista: [], plantillas: [], vr: null, timer: null };
  const e$ = (s, r = document) => r.querySelector(s);
  const ec = (t) => String(t ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const api = async (url, op = {}) => {
    const r = await fetch(url, { headers: { "Content-Type": "application/json" }, ...op });
    if (!r.ok) throw new Error((await r.json().catch(() => ({})))?.detail || r.statusText);
    return r.json();
  };

  /* ── estilos (sólo tokens) ── */
  const css = document.createElement("style");
  css.textContent = `
  .pz{position:relative}
  .pz-btn{display:flex;align-items:center;gap:6px;max-width:260px}
  .pz-btn b{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-weight:600}
  .pz-btn .lbl{color:var(--ink-dim)}
  .pz-menu{position:absolute;right:0;top:calc(100% + 6px);z-index:60;width:330px;max-height:70vh;overflow:auto;background:var(--surface);border:1px solid var(--line);border-radius:var(--r-lg);box-shadow:var(--shadow);padding:6px}
  .pz-menu h4{margin:8px 8px 4px;font-size:10.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--ink-dim);font-weight:600}
  .pz-it{display:flex;gap:8px;align-items:flex-start;width:100%;text-align:left;background:none;border:0;border-radius:var(--r);padding:7px 8px;color:var(--ink);cursor:pointer;font:inherit}
  .pz-it:hover,.pz-it[aria-current="true"]{background:var(--sunken)}
  .pz-it small{display:block;color:var(--ink-dim);font-size:11px;margin-top:1px}
  .pz-it .ico{width:18px;flex:none;text-align:center;color:var(--accent)}
  .pz-nuevo{color:var(--accent);font-weight:600}
  .pz-sep{height:1px;background:var(--line-soft);margin:6px 4px}
  .pz-dlg{border:1px solid var(--line);border-radius:var(--r-lg);background:var(--surface);color:var(--ink);padding:18px 20px;width:min(520px,92vw);box-shadow:var(--shadow)}
  .pz-dlg::backdrop{background:rgba(0,0,0,.45)}
  .pz-dlg h3{margin:0 0 4px;font-size:17px}
  .pz-dlg label{display:block;font-size:12px;color:var(--ink-2);margin:12px 0 4px}
  .pz-dlg input[type=text]{width:100%;box-sizing:border-box;padding:7px 9px;border:1px solid var(--line);border-radius:var(--r);background:var(--surface-2);color:var(--ink);font:inherit}
  .pz-tipos{display:grid;gap:6px}
  .pz-tipo{display:flex;gap:8px;align-items:flex-start;border:1px solid var(--line);border-radius:var(--r);padding:8px 10px;cursor:pointer}
  .pz-tipo:has(input:checked){border-color:var(--accent);background:var(--accent-soft)}
  .pz-tipo small{display:block;color:var(--ink-dim);font-size:11.5px}
  .pz-met{display:grid;gap:4px;margin-top:4px}
  .pz-met label{display:flex;gap:8px;margin:0;font-size:12.5px;color:var(--ink)}
  .pz-met small{color:var(--ink-dim)}
  .pz-pie{display:flex;justify-content:flex-end;gap:8px;margin-top:16px}
  .val-card{margin:0 0 12px;border:1px solid var(--accent-line);background:var(--accent-soft);border-radius:var(--r-lg);padding:10px 14px}
  .val-card .hd{display:flex;gap:10px;align-items:baseline;flex-wrap:wrap}
  .val-card .hd b{font-size:14px}
  .val-card ol{margin:8px 0 2px;padding-left:20px;display:grid;gap:3px;font-size:12.5px}
  .val-card .est{font-size:10.5px;color:var(--warn);margin-left:6px}
  .val-card small{color:var(--ink-dim)}`;
  document.head.appendChild(css);

  /* ── selector en la barra ── */
  const caja = document.createElement("div");
  caja.className = "pz";
  caja.innerHTML = `<button class="btn sm pz-btn" type="button" id="pz-btn" aria-haspopup="true" aria-expanded="false" title="Elegir o crear un proyecto"><span class="lbl">Proyecto:</span><b id="pz-nom">Vista rápida</b><span aria-hidden="true">▾</span></button><div class="pz-menu" id="pz-menu" hidden></div>`;
  const der = e$("header.top .der");
  if (der) der.prepend(caja);

  const dlg = document.createElement("dialog");
  dlg.className = "pz-dlg";
  document.body.appendChild(dlg);

  function nombre() { e$("#pz-nom").textContent = P.actual ? P.titulo : "Vista rápida"; }

  async function cargarListas() {
    try { P.lista = await api("/api/v1/proyectos"); } catch (_) { P.lista = []; }
    try { P.plantillas = await api("/api/v1/plantillas"); } catch (_) { P.plantillas = []; }
  }

  function renderMenu() {
    const m = e$("#pz-menu");
    const icoPl = (id) => (id ? "◆" : "•");
    const guardados = P.lista.map((p) => `<button type="button" class="pz-it" data-abrir="${ec(p.id)}" aria-current="${p.id === P.actual}"><span class="ico">${icoPl(p.plantilla)}</span><span><b>${ec(p.titulo)}</b><small>${p.plantilla ? ec((P.plantillas.find((t) => t.id === p.plantilla) || {}).titulo || p.plantilla) + " · " : ""}${new Date(p.actualizado * 1000).toLocaleDateString("es-AR")}</small></span></button>`).join("") || `<div class="pz-it"><small>Todavía no hay proyectos guardados.</small></div>`;
    const pred = P.plantillas.map((t) => `<button type="button" class="pz-it" data-plantilla="${ec(t.id)}"><span class="ico">◆</span><span><b>${ec(t.titulo)}</b><small>${ec(t.descripcion)}</small></span></button>`).join("");
    m.innerHTML = `<button type="button" class="pz-it pz-nuevo" data-nuevo="1"><span class="ico">＋</span><span>Nuevo proyecto</span></button>
      <button type="button" class="pz-it" data-vr="1" aria-current="${!P.actual}"><span class="ico">⚡</span><span><b>Vista rápida</b><small>Sin guardar en el servidor; queda en este navegador</small></span></button>
      ${pred ? `<div class="pz-sep"></div><h4>Predeterminados</h4>${pred}` : ""}
      <div class="pz-sep"></div><h4>Mis proyectos</h4>${guardados}
      ${P.actual ? `<div class="pz-sep"></div><button type="button" class="pz-it" data-renombrar="1"><span class="ico">✎</span><span>Renombrar «${ec(P.titulo)}»</span></button>` : ""}`;
  }

  async function abrirMenu(abrir) {
    const m = e$("#pz-menu"), b = e$("#pz-btn");
    if (abrir === undefined) abrir = m.hidden;
    if (abrir) { await cargarListas(); renderMenu(); }
    m.hidden = !abrir; b.setAttribute("aria-expanded", String(abrir));
  }
  e$("#pz-btn").addEventListener("click", () => abrirMenu());
  document.addEventListener("click", (ev) => { if (!caja.contains(ev.target)) abrirMenu(false); });
  document.addEventListener("keydown", (ev) => { if (ev.key === "Escape") abrirMenu(false); });

  e$("#pz-menu").addEventListener("click", async (ev) => {
    const b = ev.target.closest("button"); if (!b) return;
    abrirMenu(false);
    if (b.dataset.nuevo) return dialogoNuevo(null);
    if (b.dataset.plantilla) return dialogoNuevo(b.dataset.plantilla);
    if (b.dataset.vr) return abrir(null);
    if (b.dataset.abrir) return abrir(b.dataset.abrir);
    if (b.dataset.renombrar) return renombrar();
  });

  /* ── diálogo «Nuevo proyecto» ── */
  function dialogoNuevo(plantillaId) {
    const val = P.plantillas.find((t) => t.id === "valuacion_empresa");
    const tipos = [{ id: "", titulo: "En blanco", descripcion: "Una investigación vacía: elegís vos las series y los métodos." }, ...P.plantillas];
    dlg.innerHTML = `<form method="dialog" id="pz-form">
      <h3>Nuevo proyecto</h3>
      <label>Tipo</label>
      <div class="pz-tipos">${tipos.map((t) => `<label class="pz-tipo"><input type="radio" name="tipo" value="${ec(t.id)}" ${(plantillaId || "") === t.id ? "checked" : ""}><span><b>${ec(t.titulo)}</b><small>${ec(t.descripcion)}</small></span></label>`).join("")}</div>
      <div id="pz-val" hidden>
        <label for="pz-activo">Empresa (id de la Terminal, ej. NVDA, RIO, MUX)</label>
        <input type="text" id="pz-activo" maxlength="40" placeholder="NVDA" autocomplete="off">
        <label>Métodos</label>
        <div class="pz-met">${(val?.metodos || []).map((m) => `<label><input type="checkbox" name="met" value="${ec(m.id)}" ${m.sector ? "" : "checked"}><span>${ec(m.nombre)} <small>— ${ec(m.pregunta)}</small></span></label>`).join("")}</div>
      </div>
      <label for="pz-tit">Nombre</label>
      <input type="text" id="pz-tit" maxlength="200" required placeholder="Ej.: Riesgo país y tasas">
      <div class="pz-pie"><button class="btn" value="cancelar" type="submit" formnovalidate>Cancelar</button><button class="btn primary" value="crear" type="submit">Crear</button></div>
    </form>`;
    const f = e$("#pz-form", dlg);
    const sincro = () => {
      const tipo = f.tipo.value;
      e$("#pz-val", dlg).hidden = tipo !== "valuacion_empresa";
      const act = e$("#pz-activo", dlg).value.trim().toUpperCase();
      const tit = e$("#pz-tit", dlg);
      if (tipo === "valuacion_empresa" && (!tit.value || tit.dataset.auto)) { tit.value = act ? `Valuación de ${act}` : ""; tit.dataset.auto = "1"; }
    };
    f.addEventListener("change", sincro);
    e$("#pz-activo", dlg).addEventListener("input", sincro);
    e$("#pz-tit", dlg).addEventListener("input", (ev) => { delete ev.target.dataset.auto; });
    dlg.onclose = async () => {
      if (dlg.returnValue !== "crear") return;
      const tipo = f.tipo.value || null;
      const cuerpo = { titulo: e$("#pz-tit", dlg).value.trim() || "Investigación sin título" };
      if (tipo) {
        cuerpo.plantilla = tipo;
        cuerpo.metodos = [...f.querySelectorAll('input[name="met"]:checked')].map((i) => i.value);
        cuerpo.activo = e$("#pz-activo", dlg).value.trim().toUpperCase() || null;
      }
      try {
        const d = await api("/api/v1/proyectos", { method: "POST", body: JSON.stringify(cuerpo) });
        await abrir(d.id, true);
        toast(`Proyecto «${d.proyecto.titulo}» creado.`);
      } catch (err) { toast(`No pude crear el proyecto: ${err.message}`); }
    };
    sincro();
    dlg.showModal();
    e$(plantillaId ? "#pz-activo" : "#pz-tit", dlg).focus();
  }

  async function renombrar() {
    const nuevo = prompt("Nuevo nombre del proyecto:", P.titulo);
    if (!nuevo || !nuevo.trim() || !P.actual) return;
    try { await api(`/api/v1/proyectos/${P.actual}`, { method: "PATCH", body: JSON.stringify({ titulo: nuevo.trim() }) }); P.titulo = nuevo.trim(); nombre(); toast("Proyecto renombrado."); }
    catch (err) { toast(`No pude renombrar: ${err.message}`); }
  }

  /* ── foto del estado que vive en el proyecto ── */
  function foto() {
    const usados = new Set();
    for (const p of st.pines) { if (p.spec?.rid) usados.add(p.spec.rid); (p.origen || []).forEach((o) => usados.add(o)); }
    let runs = [];
    try { runs = JSON.parse(JSON.stringify(st.runs.filter((r) => usados.has(r.id)))); } catch (_) { runs = []; }
    return { version: 1, doc: st.doc, docTit: st.docTit, pines: st.pines, runs, valuacion: st.valuacion || null };
  }

  function aplicar(mesa) {
    // las corridas guardadas reciben ids nuevos para no chocar con las de esta sesión
    const mapa = {};
    for (const r of mesa.runs || []) { const viejo = r.id; registrar(r); mapa[viejo] = r.id; }
    st.pines = (mesa.pines || []).map((p) => ({ ...p, origen: (p.origen || []).map((o) => mapa[o] || o), spec: p.spec?.rid ? { ...p.spec, rid: mapa[p.spec.rid] || p.spec.rid } : p.spec }));
    st.doc = (mesa.doc || []).slice();
    st.docTit = mesa.docTit || P.titulo;
    st.valuacion = mesa.valuacion || null;
  }

  async function guardarServidor() {
    if (!P.actual) return;
    try { await api(`/api/v1/proyectos/${P.actual}/mesa`, { method: "PUT", body: JSON.stringify(foto()) }); }
    catch (err) { toast(`No se guardó el proyecto: ${err.message}`); }
  }
  function programar() { if (!P.actual) return; clearTimeout(P.timer); P.timer = setTimeout(guardarServidor, 1200); }

  async function abrir(pid, recienCreado = false) {
    if (P.actual) { clearTimeout(P.timer); await guardarServidor(); }
    else if (pid) { P.vr = { doc: st.doc, docTit: st.docTit, pines: st.pines, valuacion: st.valuacion || null }; }
    if (!pid) {
      P.actual = null; P.titulo = ""; P.plantilla = null;
      try { localStorage.removeItem(CLAVE); } catch (_) {}
      if (P.vr) { st.doc = P.vr.doc; st.docTit = P.vr.docTit; st.pines = P.vr.pines; st.valuacion = P.vr.valuacion; }
      else { st.valuacion = null; }
      nombre(); refrescar(); return;
    }
    let d;
    try { d = await api(`/api/v1/proyectos/${pid}/mesa`); }
    catch (err) { toast(`No pude abrir el proyecto: ${err.message}`); try { localStorage.removeItem(CLAVE); } catch (_) {} return; }
    P.actual = d.id; P.titulo = d.titulo; P.plantilla = d.plantilla;
    try { localStorage.setItem(CLAVE, d.id); } catch (_) {}
    aplicar({ ...d.mesa, docTit: d.mesa.docTit || d.titulo });
    nombre(); refrescar();
    if (recienCreado) guardarServidor();
  }

  function refrescar() {
    try { render(); } catch (_) {}
    try { renderTablero(); } catch (_) {}
    try { renderDoc(); } catch (_) {}
    tarjetaValuacion();
  }

  /* ── tarjeta del proyecto «Valuación de empresa» (los bloques se construyen de a uno) ── */
  function tarjetaValuacion() {
    let c = e$("#val-card");
    const v = st.valuacion;
    if (!v) { c?.remove(); return; }
    const plant = P.plantillas.find((t) => t.id === "valuacion_empresa");
    const info = Object.fromEntries((plant?.metodos || []).map((m) => [m.id, m]));
    if (!c) { c = document.createElement("div"); c.id = "val-card"; c.className = "val-card"; e$("#v-mesa")?.prepend(c); }
    c.innerHTML = `<div class="hd"><b>Valuación${v.activo ? " de " + ec(v.activo) : ""}</b><small>Cada método trae su ficha para aprenderlo y un (i) por parámetro. Los datos los cargás vos desde la Ficha.</small></div>
      <ol>${(v.metodos || []).map((id) => `<li><b>${ec(info[id]?.nombre || id)}</b> — ${ec(info[id]?.pregunta || "")}<span class="est">${ec(info[id]?.estado || "")}</span></li>`).join("")}</ol>`;
  }

  /* ── enganches con la página ── */
  const guardarOriginal = window.guardar;
  if (typeof guardarOriginal === "function") {
    window.guardar = function () { if (!P.actual) return guardarOriginal.apply(this, arguments); programar(); };
  }
  // las figuras y el documento cambian por muchos caminos: se compara la foto cada 5 s
  let ultima = "";
  setInterval(() => {
    if (!P.actual) return;
    let f = ""; try { f = JSON.stringify(foto()); } catch (_) { return; }
    if (f !== ultima) { ultima = f; programar(); }
  }, 5000);
  window.addEventListener("beforeunload", () => {
    if (!P.actual) return;
    try { fetch(`/api/v1/proyectos/${P.actual}/mesa`, { method: "PUT", keepalive: true, headers: { "Content-Type": "application/json" }, body: JSON.stringify(foto()) }); } catch (_) {}
  });
  window.CuevaProyectos = { abrir, actual: () => P.actual, guardar: guardarServidor, programar };

  async function arrancar() {
    await cargarListas();
    let pid = null; try { pid = localStorage.getItem(CLAVE); } catch (_) {}
    if (pid) await abrir(pid); else nombre();
  }
  if (window.__cuevaLista) arrancar(); else document.addEventListener("cueva:lista", arrancar, { once: true });
})();
