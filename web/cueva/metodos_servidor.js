/* metodos_servidor.js — los 102 métodos del servidor en la caja de herramientas de la Mesa.
 *
 * La Mesa (web/cueva/index.html) trae herramientas que corren en el navegador. Este módulo
 * suma las del catálogo del servidor (GET /api/v1/metodos), cada una bajo su VERBO, y
 * reemplaza las que el mockup mostraba punteadas («En la plataforma: …»).
 *
 * Al usar una: formulario con sus parámetros (las fichas seleccionadas van a los parámetros
 * de serie, en el orden de selección), se manda a POST /api/v1/mesa/metodo con los DATOS de
 * cada ficha (así sirven igual las del catálogo, las de la Terminal y las transformadas) y el
 * resultado queda en el registro: resumen, métricas, gráficos, tablas, advertencias y series
 * de salida (que se vuelven fichas con «→ ficha»).
 *
 * Usa las funciones globales de la página: HERR, CLASES, renderHerr, aplicar, abrirPop,
 * cerrarPop, objetivoDe, registrar, render, cambio, toast, esc, num, kitLineas, cajaG, RUNVIS.
 */
(function () {
  "use strict";
  const MET = new Map(); // id → declaración del servidor
  const ROTULO = { serie: "serie", series: "series" };

  async function cargar() {
    let cat;
    try {
      const r = await fetch("/api/v1/metodos");
      if (!r.ok) throw new Error(r.status);
      cat = await r.json();
    } catch (e) {
      console.warn("Mesa: no se pudo leer el catálogo de métodos del servidor", e);
      return;
    }
    const clases = new Set(CLASES.map((c) => c.id));
    cat.metodos.forEach((m) => {
      MET.set(m.id, m);
      const herramienta = {
        clase: clases.has(m.clase) ? m.clase : "modelar",
        id: "srv_" + m.id,
        nombre: m.nombre,
        aridad: "metodo",
        srv: m.id,
        desc: [m.pregunta, m.cuando].filter(Boolean).join(" — "),
      };
      const i = HERR.findIndex((t) => t.plat === m.id);
      if (i >= 0) HERR[i] = herramienta; // la punteada del mockup ahora corre de verdad
      else HERR.push(herramienta);
    });
    renderHerr();
    const n = cat.metodos.length;
    const p = document.querySelector("aside.herr .hd p");
    if (p) p.innerHTML = `Arrastrá una herramienta a una ficha o al gráfico, o tocala para aplicarla a las fichas seleccionadas. Las que tienen parámetros abren un formulario. Incluye los <b>${n} métodos del servidor</b> (econometría, ML, regímenes, finanzas); las punteadas todavía no existen.`;
  }

  /* ── formulario ── */
  function valorDefecto(p) {
    if (p.defecto === null || p.defecto === undefined) return "";
    return Array.isArray(p.defecto) ? p.defecto.join(", ") : p.defecto;
  }
  function campo(p, fichas, usadas) {
    const et = esc(p.etiqueta) + (p.requerido ? " *" : "");
    const ayuda = p.ayuda ? ` title="${esc(p.ayuda)}"` : "";
    if (p.tipo === "serie") {
      const elegida = fichas.find((f) => !usadas.has(f.id)) || fichas[0];
      if (elegida) usadas.add(elegida.id);
      return `<label${ayuda}>${et} <select data-sp="${p.nombre}">${p.requerido ? "" : '<option value="">—</option>'}${fichas.map((f) => `<option value="${f.id}" ${f === elegida ? "selected" : ""}>${esc(f.alias)}</option>`).join("")}</select></label>`;
    }
    if (p.tipo === "series") {
      const resto = fichas.filter((f) => !usadas.has(f.id));
      const marcar = new Set((resto.length >= (p.min_items || 1) ? resto : fichas).map((f) => f.id));
      return `<fieldset class="sp-series" data-sps="${p.nombre}"${ayuda}><legend>${et}</legend>${fichas.map((f) => `<label><input type="checkbox" value="${f.id}" ${marcar.has(f.id) ? "checked" : ""}> ${esc(f.alias)}</label>`).join(" ")}</fieldset>`;
    }
    if (p.tipo === "opcion") return `<label${ayuda}>${et} <select data-sp="${p.nombre}">${(p.opciones || []).map((o) => `<option ${o === p.defecto ? "selected" : ""}>${esc(o)}</option>`).join("")}</select></label>`;
    if (p.tipo === "opciones") return `<label${ayuda}>${et} <input type="text" data-sp="${p.nombre}" value="${esc(valorDefecto(p))}" placeholder="${esc((p.opciones || []).join(", "))}"></label>`;
    if (p.tipo === "bool") return `<label${ayuda}><input type="checkbox" data-sp="${p.nombre}" ${p.defecto ? "checked" : ""}> ${et}</label>`;
    if (p.tipo === "entero" || p.tipo === "real") return `<label${ayuda}>${et} <input type="number" data-sp="${p.nombre}" value="${esc(valorDefecto(p))}" ${p.minimo != null ? `min="${p.minimo}"` : ""} ${p.maximo != null ? `max="${p.maximo}"` : ""} step="${p.tipo === "entero" ? 1 : "any"}"></label>`;
    return `<label${ayuda}>${et} <input type="text" data-sp="${p.nombre}" value="${esc(valorDefecto(p))}" ${p.tipo === "fecha" ? 'placeholder="AAAA-MM" size="8"' : ""}></label>`;
  }
  function leer(el, m) {
    const args = {}, usadas = new Set();
    m.params.forEach((p) => {
      if (p.tipo === "series") {
        const ids = [...el.querySelectorAll(`[data-sps="${p.nombre}"] input:checked`)].map((i) => i.value);
        ids.forEach((i) => usadas.add(i));
        if (ids.length) args[p.nombre] = ids.map((i) => "@" + i);
        return;
      }
      const c = el.querySelector(`[data-sp="${p.nombre}"]`);
      if (!c) return;
      if (p.tipo === "bool") { args[p.nombre] = c.checked; return; }
      const v = String(c.value).trim();
      if (v === "") return;
      if (p.tipo === "serie") { usadas.add(v); args[p.nombre] = "@" + v; return; }
      if (p.tipo === "entero" || p.tipo === "real") { const x = parseFloat(v.replace(",", ".")); if (isFinite(x)) args[p.nombre] = p.tipo === "entero" ? Math.round(x) : x; return; }
      args[p.nombre] = v;
    });
    return { args, usadas };
  }

  function popServidor(t, ancla, destino, panel) {
    const m = MET.get(t.srv);
    const fichas = objetivoDe(destino, panel).filter((s) => s && s.x && s.x.length);
    const pideSeries = m.params.some((p) => p.tipo === "serie" || p.tipo === "series");
    if (pideSeries && !fichas.length) { toast(`${m.nombre}: seleccioná una o más fichas (el orden de selección cuenta) o soltá la herramienta sobre un gráfico.`); return; }
    const usadas = new Set();
    const cuerpo = m.params.map((p) => campo(p, fichas, usadas)).join("");
    abrirPop(ancla, `<b>${esc(m.nombre)}</b>
      <div class="lbl" style="margin:2px 0 4px">${esc(m.familia_nombre || "")} · servidor</div>
      ${m.pregunta ? `<div style="font-size:12px;margin-bottom:6px">${esc(m.pregunta)}</div>` : ""}
      <div class="pop-f">${cuerpo || '<span class="lbl">sin parámetros</span>'}</div>
      ${m.supuestos?.length ? `<details style="font-size:11.5px;margin:6px 0"><summary>Supuestos y trampas</summary><ul style="margin:4px 0 0 16px;padding:0">${[...m.supuestos, ...(m.trampas || [])].map((x) => `<li>${esc(x)}</li>`).join("")}</ul></details>` : ""}
      <div class="pop-acc"><button class="btn sm primary" type="button" data-srv-ok>▶ Correr en el servidor</button></div>`, (el) => el.addEventListener("click", (e) => {
      if (!e.target.closest("[data-srv-ok]")) return;
      const { args, usadas } = leer(el, m);
      cerrarPop();
      correr(m, args, fichas.filter((f) => usadas.has(f.id)));
    }));
  }

  async function correr(m, args, fichas) {
    const series = {};
    fichas.forEach((f) => {
      const x = [], y = [];
      f.x.forEach((d, i) => { const v = f.y[i]; if (v != null && isFinite(v)) { x.push(String(d).slice(0, 10)); y.push(v); } });
      series[f.id] = { nombre: f.alias, fechas: x, valores: y };
    });
    toast(`${m.nombre}: corriendo en el servidor…`);
    let res;
    try {
      const r = await fetch("/api/v1/mesa/metodo", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ metodo: m.id, args, series }) });
      res = await r.json();
      if (!r.ok) throw new Error(res?.error?.mensaje || res?.detail || r.status);
    } catch (e) { toast("✕ " + m.nombre + ": " + e.message); return; }
    if (res.ok === false) { toast("✕ " + (res.error || res.resumen || "el método no pudo correr")); return; }
    cambio();
    registrar(aCorrida(m, args, fichas, res));
    render();
    document.getElementById("res-card")?.scrollIntoView({ behavior: "smooth", block: "start" });
    toast(`${m.nombre}: listo, quedó en el registro de resultados.`);
  }

  /* ── resultado del servidor → corrida del registro ── */
  function fmt(v, formato) {
    if (v == null) return "—";
    if (typeof v !== "number") return String(v);
    if (formato === "pct") return num(v * 100, 1) + " %";
    if (formato === "p") return v < 0.0001 ? "< 0,0001" : num(v, 4);
    return Math.abs(v) >= 1000 ? num(v, 0) : num(v, Math.abs(v) < 1 ? 3 : 2);
  }
  function aCorrida(m, args, fichas, res) {
    const bl = res.bloques || [];
    const metricas = [];
    bl.filter((b) => b.tipo === "metricas").forEach((b) => b.items.forEach((it) => metricas.push([it.nombre, fmt(it.valor, it.formato), it.ayuda || ""])));
    const tablas = [];
    bl.forEach((b) => {
      if (b.tipo === "tabla") tablas.push({ nombre: b.titulo || "Tabla", columnas: b.columnas, filas: b.filas, fechasCols: b.fechas_columnas || null });
      if (b.tipo === "mapa_calor") tablas.push({ nombre: b.titulo || "Matriz", columnas: ["", ...b.columnas], filas: b.filas.map((f, i) => [f, ...b.valores[i]]) });
      if (b.tipo === "barras") { const ks = Object.keys(b.series); tablas.push({ nombre: b.titulo || "Barras", columnas: ["", ...ks], filas: b.categorias.map((c, i) => [c, ...ks.map((k) => b.series[k][i])]) }); }
    });
    (res.conjuntos || []).forEach((c) => tablas.push({ nombre: c.nombre, columnas: c.columnas, filas: c.filas }));
    const textos = bl.filter((b) => b.tipo === "veredicto" || b.tipo === "texto").map((b) => esc(b.texto || `${b.titulo ? b.titulo + ": " : ""}${b.cuerpo}`));
    const nota = [...textos, ...(res.advertencias || []).map((a) => "⚠ " + esc(a))].join("<br>");
    const graficos = bl.filter((b) => b.tipo === "lineas" || b.tipo === "bandas" || b.tipo === "dispersion");
    const aliases = fichas.map((f) => f.alias).join(", ");
    const alias = Object.fromEntries(fichas.map((f) => ["@" + f.id, f.alias]));
    const txt = (v) => (typeof v === "string" && alias[v]) || v;
    const argsTxt = Object.entries(args).map(([k, v]) => `${k}=${Array.isArray(v) ? v.map(txt).join("+") : txt(v)}`).join(" · ");
    return {
      tipo: m.clase_nombre || "Método", metodo: m.id,
      titulo: `${m.nombre}${aliases ? " · " + aliases : ""}`,
      insumos: fichas.map((f) => f.id), params: args,
      spec: `${m.id}(${argsTxt}) · servidor`,
      resumen: res.resumen || "",
      metricas, nota, tablas,
      salidas: (res.series_salida || []).map((s) => ({ nombre: s.nombre, x: s.fechas, y: s.valores, unidad: "" })),
      vista: graficos.length ? "srv" : undefined,
      datos: { graficos },
      codigo: res.codigo || "",
    };
  }

  /* ── dibujo de los gráficos del servidor en el registro ── */
  const COLS = ["--s1", "--s2", "--s3", "--s4", "--s5", "--s6", "--ink-dim"];
  RUNVIS.srv = (r, H) => {
    const gs = r.datos.graficos.slice(0, 4), alto1 = gs.length > 1 ? 230 : Math.max(H, 280);
    let svg = "", ley = [];
    gs.forEach((b, i) => {
      const caja = cajaG(0, i * (alto1 + 8), W, alto1);
      if (b.tipo === "lineas") {
        const der = new Set(b.y2 || []);
        const ls = Object.entries(b.series).map(([k, y], j) => ({ nombre: k, x: b.x, y, color: COLS[j % COLS.length], ancho: b.estilos?.[k]?.ancho || 1.6, guion: b.estilos?.[k]?.guion === "dash" ? "6 4" : b.estilos?.[k]?.guion === "dot" ? "2 3" : undefined, eje: der.has(k) ? "der" : undefined }));
        svg += kitLineas(caja, ls, { titulo: b.titulo });
        if (i === 0) ley = ls.map((l) => [l.color, l.nombre]);
      } else if (b.tipo === "bandas") {
        const ls = [{ nombre: "historia", x: b.x_hist, y: b.historia, color: "--ink", ancho: 1.6 },
          { nombre: b.nombre_banda || "pronóstico", x: b.x_pron, y: b.media, color: "--s3", ancho: 2, banda: b.inferior && b.superior ? { lo: b.inferior, hi: b.superior } : undefined }];
        Object.entries(b.extra || {}).forEach(([k, v], j) => ls.push({ nombre: k, x: v.x, y: v.y, color: COLS[(j + 1) % COLS.length], ancho: 1.2, guion: "4 3" }));
        svg += kitLineas(caja, ls, { titulo: b.titulo });
        if (i === 0) ley = ls.map((l) => [l.color, l.nombre]);
      } else if (b.tipo === "dispersion") {
        const xs = b.x, ys = b.y, n = Math.min(xs.length, ys.length);
        const ok = [...Array(n).keys()].filter((k) => isFinite(xs[k]) && isFinite(ys[k]));
        if (!ok.length) return;
        const x0 = Math.min(...ok.map((k) => xs[k])), x1 = Math.max(...ok.map((k) => xs[k])), y0 = Math.min(...ok.map((k) => ys[k])), y1 = Math.max(...ok.map((k) => ys[k]));
        const sx = (v) => caja.x + 54 + ((v - x0) / ((x1 - x0) || 1)) * (caja.w - 70), sy = (v) => caja.y + caja.h - 24 - ((v - y0) / ((y1 - y0) || 1)) * (caja.h - 46);
        svg += `<text x="${caja.x + 54}" y="${caja.y + 12}">${esc(b.titulo || "")}</text>`;
        ok.forEach((k) => { svg += `<circle cx="${sx(xs[k]).toFixed(1)}" cy="${sy(ys[k]).toFixed(1)}" r="2.3" fill="var(--s1)" opacity=".65"/>`; });
        if (b.recta) svg += `<line x1="${sx(x0)}" y1="${sy(b.recta[0] + b.recta[1] * x0)}" x2="${sx(x1)}" y2="${sy(b.recta[0] + b.recta[1] * x1)}" stroke="var(--s3)" stroke-width="1.6"/>`;
        svg += `<text x="${caja.x + caja.w - 8}" y="${caja.y + caja.h - 6}" text-anchor="end">${esc(b.etiqueta_x || "")}</text><text x="${caja.x + 4}" y="${caja.y + 26}">${esc(b.etiqueta_y || "")}</text>`;
      }
    });
    return { svg, alto: gs.length * (alto1 + 8), ley: ley.map(([c, n]) => `<span><i style="background:var(${c})"></i>${esc(n)}</span>`).join("") };
  };

  /* ── aplicar: las del servidor abren su formulario; el resto sigue igual ── */
  const aplicarOriginal = aplicar;
  aplicar = function (t, destino, ancla, panelDestino) {
    if (t && t.srv) {
      ancla = ancla || document.querySelector(`.tool[data-tool="${t.id}"]`) || document.body;
      popServidor(t, ancla, destino, panelDestino);
      return;
    }
    return aplicarOriginal(t, destino, ancla, panelDestino);
  };

  cargar();
  // Abre el formulario de un método por su id (lo usa la tarjeta de valuación), con valores sugeridos.
  function abrir(id, ancla, valores) {
    const t = HERR.find((x) => x.srv === id), m = MET.get(id);
    if (!t || !m) { toast("Ese método todavía no está cargado: reiniciá La Cueva."); return; }
    if (valores) MET.set(id, { ...m, params: m.params.map((p) => (p.nombre in valores ? { ...p, defecto: valores[p.nombre] } : p)) });
    try { aplicar(t, null, ancla); } finally { MET.set(id, m); }
  }

  window.CuevaMetodos = { MET, abrir, correr: (id, args, fichas) => correr(MET.get(id), args, fichas) };
})();
