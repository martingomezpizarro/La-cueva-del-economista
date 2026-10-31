/* explorar.js — Explorar de la Mesa de Trabajo, con datos reales.
 *
 * Portado de docs/mockup/mesa-de-trabajo.html (§2 de docs/MODULO_MESA_DE_TRABAJO.md):
 * sidebar de «series del trabajo» con su receta (log, Δ), barra común (vista, frecuencia,
 * variación, rango), gráfico SVG con franja de gobiernos, pestañas (distribución, cuadro,
 * correlación, spread), ficha de procedencia y catálogo por familia.
 *
 * De dónde salen los datos (nada inventado):
 *   GET /api/v1/series?limite=0          catálogo resuelto (lo que hay en data/series)
 *   GET /api/v1/series/familias          conectadas / total por familia
 *   GET /api/v1/series/{id}/datos        ficha + valores (lo diario ya viene mensual)
 *   GET /api/v1/historia                 presidencias para la franja de gobiernos
 *
 * Qué NO hace: no corre econometría (eso es del servidor) ni guarda el proyecto. Avisa a la
 * página con window.CuevaMesa.seriesCambiaron(ids, dep) y la página persiste; la página le
 * fija las series con window.CuevaExplorar.fijarSeries(ids, dep).
 */

const COLORES = ['--s1', '--s2', '--s3', '--s4', '--s5'];
const PY = { M: 12, Q: 4, A: 1 };
const NOM_F = { M: 'mensual', Q: 'trimestral', A: 'anual' };
const TXT_AGG = { ult: 'fin de período', comp: 'compuesta', prom: 'promedio' };
const CLAVE_UI = 'cueva_explorar';

const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const css = (n) => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const fmt = (v, d) => {
  if (v == null || !isFinite(v)) return '—';
  const a = Math.abs(v);
  if (d == null) d = a >= 1000 ? 0 : a >= 100 ? 1 : 2;
  if (a >= 1e9) return (v / 1e9).toLocaleString('es-AR', { maximumFractionDigits: 1 }) + ' mil M';
  return v.toLocaleString('es-AR', { minimumFractionDigits: d, maximumFractionDigits: d });
};
const esTasa = (u) => /%|tna|^pb$|p\.p\./i.test(u || '');

/* ---------- estado ---------- */
const st = {
  trabajo: [],            // [{id, vis, log, dif, rol:'dep'|'expl'}]
  activa: null,
  vista: 'paneles', freq: 'M', vari: 'nivel', desde: null, hasta: null, rapido: 'todo',
  tab: 'dist', fam: null, q: '',
};
const DATOS = {};         // id → {estado:'cargando'|'ok'|'error', meta, pts:[{y,m,v}], nf}
let CATALOGO = [];        // listado de /api/v1/series
let FAMILIAS = [];
let PRES = [];
let R = null;             // raíz del módulo
const $ = (s) => R.querySelector(s);

function leerUI() {
  try { return JSON.parse(sessionStorage.getItem(CLAVE_UI) || 'null') || {}; } catch { return {}; }
}
function guardarUI() {
  const previas = leerUI().recetas || {};
  const recetas = { ...previas };
  st.trabajo.forEach((t) => { recetas[t.id] = { vis: t.vis, log: t.log, dif: t.dif }; });
  const { vista, freq, vari, desde, hasta, rapido, tab } = st;
  try { sessionStorage.setItem(CLAVE_UI, JSON.stringify({ recetas, vista, freq, vari, desde, hasta, rapido, tab })); } catch { /* modo privado */ }
}

/* ---------- datos ---------- */
async function json(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(url + ' → ' + r.status);
  return r.json();
}
async function cargarSerie(id) {
  if (DATOS[id] && DATOS[id].estado !== 'error') return;
  DATOS[id] = { estado: 'cargando' };
  try {
    const d = await json('/api/v1/series/' + encodeURIComponent(id) + '/datos');
    const pts = d.fechas.map((f, i) => { const [y, m] = f.split('-').map(Number); return { y, m, v: d.valores[i] }; });
    const { fechas, valores, ...meta } = d;   // eslint-disable-line no-unused-vars
    DATOS[id] = { estado: 'ok', meta, pts, nf: d.frecuencia_entrega in PY ? d.frecuencia_entrega : 'M' };
  } catch (e) {
    DATOS[id] = { estado: 'error', error: String(e) };
  }
  if (st.desde == null || st.rapido === 'todo') ajustarRangoTodo();
  todo();
}
function nombre(id) {
  const d = DATOS[id];
  return d?.meta?.nombre || CATALOGO.find((s) => s.id === id)?.nombre || id;
}
function unidadBase(id) { return DATOS[id]?.meta?.unidad || CATALOGO.find((s) => s.id === id)?.unidad || ''; }
const listas = () => st.trabajo.filter((t) => DATOS[t.id]?.estado === 'ok');

function anios() {
  const ys = listas().flatMap((t) => { const p = DATOS[t.id].pts; return p.length ? [p[0].y, p[p.length - 1].y] : []; });
  return ys.length ? [Math.min(...ys), Math.max(...ys)] : [1940, new Date().getFullYear()];
}
function ajustarRangoTodo() { const [a, b] = anios(); st.desde = a; st.hasta = b; }

/* ---------- motor de la receta ---------- */
function clave(y, m, f) {
  if (f === 'M') return { f: `${y}-${String(m).padStart(2, '0')}`, t: y + (m - 1) / 12 };
  if (f === 'Q') { const q = Math.floor((m - 1) / 3) + 1; return { f: `${y}-T${q}`, t: y + (q - 1) / 4 }; }
  return { f: String(y), t: y };
}
function agregar(d, objetivo) {
  const efectiva = PY[objetivo] > PY[d.nf] ? d.nf : objetivo;   // no se inventan datos más finos
  if (efectiva === d.nf) return { efectiva, pts: d.pts.map((p) => ({ ...clave(p.y, p.m, efectiva), v: p.v })) };
  const g = new Map();
  for (const p of d.pts) {
    const k = clave(p.y, p.m, efectiva);
    if (!g.has(k.f)) g.set(k.f, { ...k, vs: [] });
    g.get(k.f).vs.push(p.v);
  }
  const necesita = PY[d.nf] / PY[efectiva];
  const agg = d.meta.agregacion;
  const pts = [];
  for (const o of g.values()) {
    if (o.vs.length < necesita) continue;        // período incompleto: afuera
    let v;
    if (agg === 'ult') v = o.vs[o.vs.length - 1];
    else if (agg === 'comp') v = (o.vs.reduce((a, x) => a * (1 + x / 100), 1) - 1) * 100;
    else v = o.vs.reduce((a, x) => a + x, 0) / o.vs.length;
    pts.push({ t: o.t, f: o.f, v });
  }
  return { efectiva, pts };
}
function procesar(tr) {
  const d = DATOS[tr.id];
  const { efectiva, pts: p0 } = agregar(d, st.freq);
  let pts = p0;
  const pasos = [];
  const bajada = ['diaria', 'semanal'].includes(d.meta.frecuencia_nativa) || efectiva !== d.nf;
  pasos.push({ t: NOM_F[efectiva] + (bajada ? ' · ' + TXT_AGG[d.meta.agregacion] : '') + (efectiva !== st.freq ? ' (nativa)' : ''), on: false });
  let unidad = d.meta.unidad;
  if (st.vari === 'ia') {
    const lag = PY[efectiva];
    const tasa = esTasa(unidad);
    pts = pts.map((p, i) => (i < lag ? null : { ...p, v: tasa ? p.v - pts[i - lag].v : (pts[i - lag].v > 0 ? (p.v / pts[i - lag].v - 1) * 100 : NaN) }))
      .filter((p) => p && isFinite(p.v));
    pasos.push({ t: tasa ? 'dif. i.a. (pp)' : 'var. % i.a.', on: true });
    unidad = tasa ? 'pp' : '% i.a.';
  }
  const logBloq = pts.some((p) => p.v <= 0);
  if (tr.log && !logBloq) { pts = pts.map((p) => ({ ...p, v: Math.log(p.v) })); pasos.push({ t: 'log', on: true }); unidad = 'log(' + unidad + ')'; }
  if (tr.dif) { pts = pts.slice(1).map((p, i) => ({ ...p, v: p.v - pts[i].v })); pasos.push({ t: 'Δ', on: true }); unidad = 'Δ ' + unidad; }
  return { pts, pasos, unidad, logBloq, efectiva };
}
const enRango = (pts) => pts.filter((p) => p.t >= st.desde && p.t < st.hasta + 1);
const colorDe = (id) => { const i = st.trabajo.findIndex((t) => t.id === id); return 'var(' + COLORES[(i < 0 ? 0 : i) % 5] + ')'; };

/* ---------- estadísticos ---------- */
function stats(vs) {
  const n = vs.length; if (!n) return null;
  const m = vs.reduce((a, x) => a + x, 0) / n;
  const sd = Math.sqrt(vs.reduce((a, x) => a + (x - m) ** 2, 0) / Math.max(1, n - 1));
  const s = [...vs].sort((a, b) => a - b);
  const q = (p) => { const i = (n - 1) * p, lo = Math.floor(i), hi = Math.ceil(i); return s[lo] + (s[hi] - s[lo]) * (i - lo); };
  const sk = sd ? vs.reduce((a, x) => a + ((x - m) / sd) ** 3, 0) / n : 0;
  const ku = sd ? vs.reduce((a, x) => a + ((x - m) / sd) ** 4, 0) / n - 3 : 0;
  return { n, m, sd, min: s[0], max: s[n - 1], ult: vs[n - 1], p25: q(0.25), med: q(0.5), p75: q(0.75), sk, ku };
}
function pearson(a, b) {
  const n = a.length; if (n < 3) return NaN;
  const ma = a.reduce((x, y) => x + y, 0) / n, mb = b.reduce((x, y) => x + y, 0) / n;
  let sab = 0, saa = 0, sbb = 0;
  for (let i = 0; i < n; i++) { sab += (a[i] - ma) * (b[i] - mb); saa += (a[i] - ma) ** 2; sbb += (b[i] - mb) ** 2; }
  return sab / Math.sqrt(saa * sbb);
}
function alinear(series) {
  const maps = series.map((s) => new Map(s.pts.map((p) => [p.f, p.v])));
  const fs = (series[0]?.pts || []).map((p) => p.f).filter((f) => maps.every((m) => m.has(f)));
  return { fs, cols: maps.map((m) => fs.map((f) => m.get(f))) };
}
function ticks(lo, hi, n) {
  const span = hi - lo || 1; const step0 = span / n; const mag = 10 ** Math.floor(Math.log10(step0));
  const step = [1, 2, 2.5, 5, 10].map((k) => k * mag).find((k) => k >= step0);
  const out = []; for (let v = Math.ceil(lo / step) * step; v <= hi + 1e-9; v += step) out.push(+v.toFixed(10));
  return out;
}
function añoFrac(f) { const [y, m, d] = f.split('-').map(Number); return y + ((m || 1) - 1) / 12 + ((d || 1) - 1) / 365; }
function apellido(n) { const s = n.split(' '); return s.length > 2 && /^(de|del)$/i.test(s[s.length - 2]) ? s.slice(-2).join(' ') : s[s.length - 1]; }

/* ---------- gráfico ---------- */
let ultimo = null;
function dibujar() {
  const wrap = $('#ex-g-wrap'); const g = $('#ex-g');
  const W = Math.max(320, wrap.clientWidth - 12);
  const vis = listas().filter((t) => t.vis).map((t) => ({ tr: t, ...procesar(t) }));
  vis.forEach((s) => { s.vis = enRango(s.pts); });
  const aviso = [];
  let series = vis;
  if (st.vista === 'b100') {
    series = vis.filter((s) => { const ok = s.vis.length && s.vis.every((p) => p.v > 0); if (!ok) aviso.push(nombre(s.tr.id) + ' tiene valores ≤ 0 y no admite base 100: queda afuera.'); return ok; });
    series = series.map((s) => { const b = s.vis[0].v; return { ...s, vis: s.vis.map((p) => ({ ...p, v: (p.v / b) * 100 })), unidad: 'base 100 = ' + s.vis[0].f }; });
  }
  if (st.vista === 'z') series = series.map((s) => { const z = stats(s.vis.map((p) => p.v)); return { ...s, vis: s.vis.map((p) => ({ ...p, v: z && z.sd ? (p.v - z.m) / z.sd : 0 })), unidad: 'desvíos' }; });
  vis.forEach((s) => {
    if (s.tr.log && s.logBloq) aviso.push('Log no aplica a ' + nombre(s.tr.id) + ' (tiene valores ≤ 0).');
    if (s.efectiva !== st.freq) aviso.push(nombre(s.tr.id) + ' es ' + NOM_F[s.efectiva] + ': se muestra en su frecuencia nativa, no se inventan datos más finos.');
  });
  $('#ex-g-aviso').hidden = !aviso.length; $('#ex-g-aviso').textContent = aviso.join(' ');
  $('#ex-g-titulo').textContent = { paneles: 'Un panel por serie', b100: 'Base 100', z: 'Estandarizadas' }[st.vista];
  $('#ex-g-freq').textContent = NOM_F[st.freq];
  $('#ex-g-rango').textContent = st.desde != null ? st.desde + ' → ' + st.hasta : '';

  if (!vis.length) {
    g.setAttribute('viewBox', `0 0 ${W} 180`);
    const msg = st.trabajo.length ? (st.trabajo.some((t) => DATOS[t.id]?.estado === 'cargando') ? 'Cargando series…' : 'No hay series visibles con datos.') : 'Agregá series del catálogo para empezar.';
    g.innerHTML = `<text x="${W / 2}" y="90" text-anchor="middle" font-size="13" fill="${css('--ink-dim')}">${msg}</text>`;
    ultimo = null; return;
  }
  const L = 58, Rm = 14, x0 = st.desde, x1 = st.hasta + 1; const X = (t) => L + ((t - x0) / (x1 - x0)) * (W - L - Rm);
  const paneles = st.vista === 'paneles' ? series.map((s) => [s]) : [series];
  const PH = st.vista === 'paneles' ? Math.max(110, Math.min(170, 420 / Math.max(1, paneles.length))) : 300;
  const HD = st.vista === 'paneles' ? 22 : 6; const gob = 26; let y = 0; let svg = '';
  const ink = css('--ink-dim'), line = css('--line-soft'), faint = css('--ink-faint');
  for (const grupo of paneles) {
    const todos = grupo.flatMap((s) => s.vis.map((p) => p.v)); const top = y + HD, h = PH;
    if (st.vista === 'paneles' && grupo[0]) {
      const s = grupo[0]; const z = stats(s.vis.map((p) => p.v));
      svg += `<text x="${L}" y="${y + 14}" font-size="11.5" font-weight="600" style="fill:${colorDe(s.tr.id)}">${esc(nombre(s.tr.id))}</text>`;
      svg += `<text x="${W - Rm}" y="${y + 14}" text-anchor="end" font-size="10.5" font-family="var(--mono)" fill="${ink}">${esc(s.unidad)} · últ. ${z ? fmt(z.ult) : '—'}</text>`;
    }
    if (!todos.length) { svg += `<text x="${W / 2}" y="${top + h / 2}" text-anchor="middle" font-size="12" fill="${ink}">Sin datos en este rango</text>`; y = top + h + 10; continue; }
    let lo = Math.min(...todos), hi = Math.max(...todos); if (lo === hi) { lo -= 1; hi += 1; }
    const pad = (hi - lo) * 0.06; lo -= pad; hi += pad;
    const Y = (v) => top + h - ((v - lo) / (hi - lo)) * h;
    for (const tv of ticks(lo, hi, st.vista === 'paneles' ? 3 : 5)) {
      if (tv < lo || tv > hi) continue;
      svg += `<line x1="${L}" x2="${W - Rm}" y1="${Y(tv)}" y2="${Y(tv)}" stroke="${line}" stroke-width="1"/>`;
      svg += `<text x="${L - 6}" y="${Y(tv) + 3.5}" text-anchor="end" font-size="10" font-family="var(--mono)" fill="${faint}">${fmt(tv, Math.abs(hi - lo) < 10 ? 1 : 0)}</text>`;
    }
    if (lo < 0 && hi > 0) svg += `<line x1="${L}" x2="${W - Rm}" y1="${Y(0)}" y2="${Y(0)}" stroke="${ink}" stroke-width="1" stroke-dasharray="3 3" opacity=".6"/>`;
    for (const s of grupo) {
      if (!s.vis.length) continue;
      const d = s.vis.map((p, i) => (i ? 'L' : 'M') + X(p.t).toFixed(1) + ' ' + Y(p.v).toFixed(1)).join('');
      const c = colorDe(s.tr.id);
      if (st.vista === 'paneles') svg += `<path d="${d}L${X(s.vis[s.vis.length - 1].t).toFixed(1)} ${top + h}L${X(s.vis[0].t).toFixed(1)} ${top + h}Z" style="fill:${c}" opacity=".08"/>`;
      svg += `<path d="${d}" fill="none" style="stroke:${c}" stroke-width="${s.tr.id === st.activa ? 2 : 1.5}" stroke-linejoin="round"/>`;
      const u = s.vis[s.vis.length - 1]; svg += `<circle cx="${X(u.t)}" cy="${Y(u.v)}" r="3" style="fill:${c}"/>`;
    }
    y = top + h + 12;
  }
  const gy = y + 2;
  for (const p of PRES) {
    const a = añoFrac(p.desde), b = p.hasta ? añoFrac(p.hasta) : x1; if (b < x0 || a > x1) continue;
    const xa = X(Math.max(a, x0)), xb = X(Math.min(b, x1)); const df = p.tipo !== 'constitucional';
    svg += `<rect x="${xa}" y="${gy}" width="${Math.max(0, xb - xa - 1)}" height="${gob - 8}" rx="2" fill="${df ? css('--facto') : css('--const')}" opacity="${df ? 0.32 : 0.2}"/>`;
    if (xb - xa > 58) svg += `<text x="${xa + 4}" y="${gy + 12}" font-size="9.5" fill="${css('--ink-2')}">${esc(apellido(p.nombre))}</text>`;
  }
  const ay = gy + gob;
  for (const tv of ticks(x0, x1, W < 560 ? 4 : 8)) {
    if (tv < x0 || tv > x1) continue;
    svg += `<text x="${X(tv)}" y="${ay + 8}" text-anchor="middle" font-size="10" font-family="var(--mono)" fill="${faint}">${tv}</text>`;
    svg += `<line x1="${X(tv)}" x2="${X(tv)}" y1="0" y2="${gy - 4}" stroke="${line}" stroke-width="1" opacity=".5"/>`;
  }
  svg += `<line class="ex-cruz" x1="0" x2="0" y1="0" y2="${gy + gob - 8}" stroke="${css('--ink-2')}" stroke-width="1" opacity="0"/>`;
  const H = ay + 14; g.setAttribute('viewBox', `0 0 ${W} ${H}`); g.innerHTML = svg;
  ultimo = { series, L, Rm, W, x0, x1 };
}
function mover(e) {
  if (!ultimo) return;
  const r = $('#ex-g').getBoundingClientRect(); const sc = ultimo.W / r.width;
  const px = (e.clientX - r.left) * sc; if (px < ultimo.L || px > ultimo.W - ultimo.Rm) { ocultarTip(); return; }
  const t = ultimo.x0 + ((px - ultimo.L) / (ultimo.W - ultimo.L - ultimo.Rm)) * (ultimo.x1 - ultimo.x0);
  let filas = '', fecha = '';
  for (const s of ultimo.series) {
    if (!s.vis.length) continue; let best = s.vis[0];
    for (const p of s.vis) if (Math.abs(p.t - t) < Math.abs(best.t - t)) best = p;
    if (Math.abs(best.t - t) > 1.1) continue; fecha = fecha || best.f;
    filas += `<div class="t-r"><i style="background:${colorDe(s.tr.id)}"></i>${fmt(best.v)} <span style="color:var(--ink-dim)">${esc(s.unidad)}</span></div>`;
  }
  const pres = PRES.find((p) => añoFrac(p.desde) <= t && (!p.hasta || añoFrac(p.hasta) > t));
  const tip = $('#ex-tip');
  tip.innerHTML = `<div class="t-f">${fecha || Math.floor(t)}</div>${filas}${pres ? `<div class="t-g">${esc(pres.nombre)}${pres.tipo !== 'constitucional' ? ' · de facto' : ''}</div>` : ''}`;
  const c = R.querySelector('.ex-cruz'); if (c) { c.setAttribute('x1', px); c.setAttribute('x2', px); c.setAttribute('opacity', 0.35); }
  const wr = $('#ex-g-wrap').getBoundingClientRect(); let lx = e.clientX - wr.left + 14; if (lx + 190 > wr.width) lx = e.clientX - wr.left - 200;
  tip.style.left = lx + 'px'; tip.style.top = Math.max(4, e.clientY - wr.top - 30) + 'px'; tip.style.opacity = 1;
}
function ocultarTip() { $('#ex-tip').style.opacity = 0; const c = R.querySelector('.ex-cruz'); if (c) c.setAttribute('opacity', 0); }

/* ---------- panel izquierdo ---------- */
function pintarLista() {
  $('#ex-n-series').textContent = st.trabajo.length;
  if (!st.trabajo.length) {
    $('#ex-lista').innerHTML = '<p class="vacio-ex">Todavía no hay series en el trabajo. Agregalas desde el catálogo: solo aparecen las que ya están en <span class="num">data/series</span>.</p>';
    return;
  }
  $('#ex-lista').innerHTML = st.trabajo.map((t) => {
    const d = DATOS[t.id];
    const top = `<div class="s-top">
        <button class="s-dot" data-acc="vis" title="${t.vis ? 'Ocultar' : 'Mostrar'} en el gráfico" aria-label="${t.vis ? 'Ocultar' : 'Mostrar'} ${esc(nombre(t.id))}"></button>
        <div style="flex:1;min-width:0"><div class="s-nom">${esc(nombre(t.id))}</div><div class="s-meta">${esc(t.id)} · ${esc(unidadBase(t.id))}</div></div>
        <button class="rol ${t.rol}" data-acc="rol" title="Rol en el estudio: dependiente o explicativa">${t.rol === 'dep' ? 'dep' : 'expl'}</button>
        <button class="quitar" data-acc="quitar" aria-label="Quitar ${esc(nombre(t.id))}" title="Quitar del trabajo">×</button></div>`;
    const base = `class="serie" data-id="${esc(t.id)}" data-activa="${t.id === st.activa}" data-vis="${t.vis}" style="--c:${colorDe(t.id)}" tabindex="0"`;
    if (!d || d.estado === 'cargando') return `<div ${base}>${top}<div class="cargando">cargando…</div></div>`;
    if (d.estado === 'error') return `<div ${base}>${top}<div class="error-s">No se pudo cargar. <button class="btn sm" data-acc="reintentar">Reintentar</button></div></div>`;
    const p = procesar(t);
    return `<div ${base}>
      ${top}
      <div class="receta" aria-label="Receta">${p.pasos.map((x) => `<span class="paso ${x.on ? 'on' : ''}">${esc(x.t)}</span>`).join('<span class="flecha">→</span>')}</div>
      <div class="s-ctl"><span class="lbl" style="font-size:9.5px;margin-right:2px">Transformar</span>
        <button class="tg" data-acc="log" aria-pressed="${t.log}" ${p.logBloq ? 'disabled title="Tiene valores ≤ 0"' : ''}>log</button>
        <button class="tg" data-acc="dif" aria-pressed="${t.dif}">Δ dif.</button></div>
    </div>`;
  }).join('');
}
function clicLista(e) {
  const card = e.target.closest('.serie'); if (!card) return;
  const t = st.trabajo.find((x) => x.id === card.dataset.id); if (!t) return;
  const acc = e.target.closest('[data-acc]')?.dataset.acc;
  let avisar = false;
  if (acc === 'vis') t.vis = !t.vis;
  else if (acc === 'rol') { const era = t.rol; st.trabajo.forEach((x) => { x.rol = 'expl'; }); t.rol = era === 'dep' ? 'expl' : 'dep'; avisar = true; }
  else if (acc === 'log') t.log = !t.log;
  else if (acc === 'dif') t.dif = !t.dif;
  else if (acc === 'reintentar') { delete DATOS[t.id]; cargarSerie(t.id); }
  else if (acc === 'quitar') { st.trabajo = st.trabajo.filter((x) => x !== t); avisar = true; }
  else st.activa = t.id;
  if (avisar) avisarPagina();
  todo();
}

/* ---------- pestañas inferiores ---------- */
function pintarTab() {
  const vis = listas().filter((t) => t.vis).map((t) => ({ tr: t, ...procesar(t) })); vis.forEach((s) => { s.vis = enRango(s.pts); });
  const bd = $('#ex-tab-bd');
  if (!vis.length) { bd.innerHTML = '<p class="explica" style="margin:0">Sin series visibles.</p>'; return; }
  if (st.tab === 'dist') {
    const t = listas().find((x) => x.id === st.activa) || vis[0].tr;
    const p = procesar(t); const vs = enRango(p.pts).map((x) => x.v); const z = stats(vs);
    if (!z) { bd.innerHTML = '<p class="explica">Sin datos en el rango.</p>'; return; }
    const nb = 24, lo = z.min, hi = z.max, w = (hi - lo) / nb || 1; const cnt = Array(nb).fill(0);
    vs.forEach((v) => { cnt[Math.min(nb - 1, Math.floor((v - lo) / w))]++; });
    const mx = Math.max(...cnt); const HW = 520, HH = 120; const bw = (HW - 40) / nb;
    let h = cnt.map((c, i) => `<rect x="${30 + i * bw}" y="${HH - 18 - (c / mx) * (HH - 28)}" width="${bw - 1.5}" height="${(c / mx) * (HH - 28)}" rx="1.5" style="fill:${colorDe(t.id)}" opacity=".75"/>`).join('');
    const xm = 30 + ((z.m - lo) / (hi - lo || 1)) * (HW - 40);
    h += `<line x1="${xm}" x2="${xm}" y1="6" y2="${HH - 18}" stroke="${css('--accent')}" stroke-dasharray="3 3"/><text x="${xm + 4}" y="14" font-size="10" fill="${css('--accent')}">media</text>`;
    h += `<text x="30" y="${HH - 4}" font-size="10" font-family="var(--mono)" fill="${css('--ink-faint')}">${fmt(lo)}</text><text x="${HW - 10}" y="${HH - 4}" text-anchor="end" font-size="10" font-family="var(--mono)" fill="${css('--ink-faint')}">${fmt(hi)}</text>`;
    bd.innerHTML = `<div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;flex-wrap:wrap"><b style="font-size:13px">${esc(nombre(t.id))}</b><span class="chip neutral">${esc(p.unidad)}</span><span class="chip neutral">sobre el rango visible</span></div>
      <div class="stats">${[['Último', z.ult], ['Media', z.m], ['Desvío', z.sd], ['Mín', z.min], ['p25', z.p25], ['Mediana', z.med], ['p75', z.p75], ['Máx', z.max], ['Asimetría', z.sk], ['Curtosis exc.', z.ku], ['Obs.', z.n]].map(([k, v]) => `<div><span class="lbl" style="font-size:9.5px">${k}</span><b>${k === 'Obs.' ? v : fmt(v)}</b></div>`).join('')}</div>
      <svg viewBox="0 0 ${HW} ${HH}" style="width:100%;max-width:560px;margin-top:12px" role="img" aria-label="Histograma">${h}</svg>
      ${z.ku > 3 ? '<p class="explica">Curtosis alta: colas pesadas. En series argentinas suele ser un régimen (hiperinflación, salida de la convertibilidad) más que ruido; antes de modelar, mirar quiebres.</p>' : ''}`;
    return;
  }
  if (st.tab === 'cmp') {
    bd.innerHTML = `<div class="tablewrap"><table><thead><tr><th>Serie</th><th>Unidad</th><th>Desde</th><th>Último</th><th>Media</th><th>Desvío</th><th>Mín</th><th>Máx</th><th>Obs.</th></tr></thead><tbody>${vis.map((s) => { const z = stats(s.vis.map((p) => p.v)); return `<tr><td><span style="display:inline-block;width:8px;height:8px;border-radius:2px;background:${colorDe(s.tr.id)};margin-right:6px"></span>${esc(nombre(s.tr.id))}</td><td>${esc(s.unidad)}</td><td class="c">${s.vis[0]?.f || '—'}</td>${z ? [z.ult, z.m, z.sd, z.min, z.max].map((v) => `<td class="c">${fmt(v)}</td>`).join('') + `<td class="c">${z.n}</td>` : '<td colspan="6">—</td>'}</tr>`; }).join('')}</tbody></table></div>`;
    return;
  }
  if (st.tab === 'corr') {
    if (vis.length < 2) { bd.innerHTML = '<p class="explica">Hacen falta al menos dos series visibles.</p>'; return; }
    const al = alinear(vis.map((s) => ({ pts: s.vis }))); const n = vis.length;
    let t = `<div class="tablewrap"><table style="width:auto"><thead><tr><th></th>${vis.map((s) => `<th>${esc(s.tr.id)}</th>`).join('')}</tr></thead><tbody>`;
    for (let i = 0; i < n; i++) {
      t += `<tr><td class="c">${esc(vis[i].tr.id)}</td>`;
      for (let j = 0; j < n; j++) {
        const r = i === j ? 1 : pearson(al.cols[i], al.cols[j]); const c = r >= 0 ? '--info' : '--crit';
        t += `<td class="c" style="background:color-mix(in srgb,var(${c}) ${Math.round(Math.abs(isFinite(r) ? r : 0) * 55)}%,transparent)">${isFinite(r) ? r.toFixed(2) : '—'}</td>`;
      }
      t += '</tr>';
    }
    const niveles = st.vari === 'nivel' && vis.some((s) => !s.tr.dif);
    bd.innerHTML = t + `</tbody></table></div><p class="explica">${al.fs.length} fechas en común. Pearson sobre las series <b>tal como las transformaste</b>, alineadas por fecha.${niveles ? ' <span style="color:var(--warn)">Hay series en nivel: con tendencia, una correlación alta puede ser espuria (Granger-Newbold). Probá Interanual o Δ.</span>' : ''}</p>`;
    return;
  }
  if (st.tab === 'spread') {
    if (vis.length !== 2) { bd.innerHTML = `<p class="explica">El spread necesita exactamente <b>dos</b> series visibles; hay ${vis.length}. Apagá ${vis.length > 2 ? 'las que sobren' : 'o prendé una'} con el cuadrado de color del panel izquierdo.</p>`; return; }
    const [a, b] = vis; const mismo = a.unidad === b.unidad; const al = alinear([{ pts: a.vis }, { pts: b.vis }]);
    if (al.fs.length < 2) { bd.innerHTML = '<p class="explica">Las dos series no tienen fechas en común en este rango y frecuencia.</p>'; return; }
    const d = al.cols[0].map((v, i) => v - al.cols[1][i]);
    const W = 900, H = 150, lo = Math.min(0, ...d), hi = Math.max(0, ...d);
    const X = (i) => 40 + (i / (d.length - 1 || 1)) * (W - 50), Y = (v) => 8 + ((hi - v) / (hi - lo || 1)) * (H - 26);
    const path = d.map((v, i) => (i ? 'L' : 'M') + X(i).toFixed(1) + ' ' + Y(v).toFixed(1)).join('');
    bd.innerHTML = `<div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:8px"><b style="font-size:13px">${esc(nombre(a.tr.id))} − ${esc(nombre(b.tr.id))}</b><span class="chip ${d[d.length - 1] >= 0 ? 'ok' : 'crit'} num">último ${fmt(d[d.length - 1])}</span>${mismo ? '' : '<span class="chip warn">unidades distintas: indicativo</span>'}</div>
      <svg viewBox="0 0 ${W} ${H}" style="width:100%" role="img" aria-label="Spread"><path d="${path}L${X(d.length - 1)} ${Y(0)}L${X(0)} ${Y(0)}Z" fill="${css('--info')}" opacity=".18"/><path d="${path}" fill="none" stroke="${css('--info')}" stroke-width="1.4"/><line x1="40" x2="${W - 10}" y1="${Y(0)}" y2="${Y(0)}" stroke="${css('--ink-dim')}" stroke-dasharray="3 3"/>
      <text x="${W - 10}" y="${H - 2}" text-anchor="end" font-size="10" font-family="var(--mono)" fill="${css('--ink-faint')}">${al.fs[al.fs.length - 1]}</text><text x="40" y="${H - 2}" font-size="10" font-family="var(--mono)" fill="${css('--ink-faint')}">${al.fs[0]}</text></svg>
      <p class="explica">Con tasas en la misma unidad (por ejemplo plazo fijo − inflación anualizada) el spread es la tasa real ex post.</p>`;
  }
}

/* ---------- columna derecha ---------- */
function pintarDer() {
  const d = DATOS[st.activa];
  if (!d || d.estado !== 'ok') {
    $('#ex-ficha').innerHTML = '<span class="lbl">Ficha de la serie</span><p class="def">Elegí una serie del trabajo para ver de dónde sale.</p>';
  } else {
    const m = d.meta; const p = m.proc || {};
    const verif = String(p.verificado || '').startsWith('20');
    const fuente = [p.fuente ? String(p.fuente).toUpperCase() : null, p.id_externo ? 'id ' + p.id_externo : null].filter(Boolean).join(' · ') || '—';
    $('#ex-ficha').innerHTML = `<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap"><span class="lbl" style="flex:1">Ficha de la serie</span>
        ${m.origen !== 'data/series' ? '<span class="chip warn" title="El archivo no está en data/series: se leyó de la carpeta del Trabajo Final">del Trabajo Final</span>' : ''}
        <span class="chip ${verif ? 'ok' : 'warn'}"><span class="dot"></span>${verif ? 'verificada' : 'sin verificar'}</span></div>
      <h3 class="ficha-tit">${esc(m.nombre)}</h3>
      ${p.definicion ? `<p class="def">${esc(p.definicion)}</p>` : '<p class="def" style="color:var(--ink-dim)">El catálogo no trae definición para esta serie.</p>'}
      <dl class="kv"><dt>Fuente</dt><dd>${esc(fuente)}</dd><dt>Cobertura</dt><dd>${esc(m.desde)} → ${esc(m.hasta)}</dd>
        <dt>Frec. nativa</dt><dd>${esc(m.frecuencia_nativa)}</dd><dt>Unidad</dt><dd>${esc(m.unidad)}</dd>
        <dt>Al agregar</dt><dd>${TXT_AGG[m.agregacion]}${m.agregacion_supuesta ? ' <span title="El catálogo no lo declara: sale de una regla sobre nombre y unidad" style="color:var(--ink-faint)">(supuesto)</span>' : ''}</dd>
        <dt>Confianza</dt><dd>${esc(p.confianza || '—')}</dd><dt>Archivo</dt><dd>${m.origen === 'data/series' ? 'data/series/' : ''}${esc(m.archivo)}</dd>
        ${p.script ? `<dt>Se repone con</dt><dd>${esc(p.script)}</dd>` : ''}</dl>
      ${p.notas ? `<p class="def" style="font-size:12px;color:var(--warn)">${esc(p.notas)}</p>` : ''}`;
  }
  const tr = listas().filter((t) => t.vis); const niveles = tr.filter((t) => !t.dif && st.vari === 'nivel').length;
  const msj = !tr.length ? 'Cuando sumes series, acá aparece qué mirar antes de modelarlas.'
    : st.vista === 'paneles' && niveles > 1 ? `Estás mirando ${niveles} series en nivel. Para comparar comovimientos pasá a <b>Interanual</b> o diferenciá: en nivel, dos tendencias se parecen aunque no tengan nada que ver.`
      : st.vista === 'b100' ? 'Base 100 deja afuera las series que pasan por cero o negativo (como la inflación mensual). Para esas, Estandarizado.'
        : 'Con las series ya transformadas, el paso siguiente es correr raíz unitaria antes de llevarlas al Estudio.';
  $('#ex-copiloto').innerHTML = `<div class="quien" title="Reglas fijas sobre lo que estás mirando; no consulta a la IA">Metodólogo · lectura rápida</div>${msj}`;
  $('#ex-familias').innerHTML = FAMILIAS.length
    ? FAMILIAS.map((f) => `<div class="fam"><div class="fam-r"><span>${esc(f.familia)}</span><span class="num" style="color:var(--ink-dim)">${f.conectadas}/${f.total}</span></div><div class="barrita"><i style="width:${f.total ? (f.conectadas / f.total) * 100 : 0}%"></i></div></div>`).join('')
    : '<span class="cargando">cargando…</span>';
}

/* ---------- catálogo ---------- */
function pintarCat() {
  if (!st.fam && FAMILIAS.length) st.fam = FAMILIAS[0].familia;
  $('#ex-dlg-fams').innerHTML = FAMILIAS.map((f) => `<button data-f="${esc(f.familia)}" aria-pressed="${f.familia === st.fam}"><span style="display:flex;justify-content:space-between;gap:8px;font-size:12.5px;font-weight:600"><span>${esc(f.familia)}</span><span class="num" style="font-weight:400;color:var(--ink-dim)">${f.conectadas}/${f.total}</span></span><span class="barrita"><i style="width:${f.total ? (f.conectadas / f.total) * 100 : 0}%"></i></span></button>`).join('');
  const q = st.q.trim().toLowerCase();
  const filas = q ? CATALOGO.filter((s) => (s.nombre + ' ' + s.id + ' ' + s.subgrupo).toLowerCase().includes(q)).slice(0, 200) : CATALOGO.filter((s) => s.grupo === st.fam);
  const fam = FAMILIAS.find((f) => f.familia === st.fam);
  let html = '';
  if (!q && fam) {
    const faltan = fam.total - fam.conectadas;
    html += `<div class="bloque" style="padding:12px 14px"><span class="lbl">Esta familia</span><p class="def" style="margin:0">${fam.conectadas} de ${fam.total} entradas del catálogo tienen su archivo en <span class="num">data/series</span>.${faltan ? ` Las ${faltan} que faltan no se listan: hay que bajarlas o migrarlas primero.` : ''}</p></div>`;
  }
  let sub = null;
  for (const s of filas) {
    if (!q && s.subgrupo !== sub) { sub = s.subgrupo; html += `<div class="sub-hd">${esc(sub || 'Sin subgrupo')}</div>`; }
    const ya = st.trabajo.some((t) => t.id === s.id);
    html += `<div class="fila"><div class="f-n">${esc(s.nombre)}</div><div style="display:flex;gap:6px;align-items:center;grid-row:span 2">
      ${ya ? '<span class="chip neutral">en el trabajo</span>' : `<button class="btn sm primary" data-add="${esc(s.id)}">Agregar</button>`}</div>
      <div class="f-m">${esc(s.id)} · ${esc(s.unidad || '—')} · desde ${esc(s.desde || '—')}</div>${q ? `<div class="f-c">${esc(s.grupo)} › ${esc(s.subgrupo)}</div>` : ''}</div>`;
  }
  $('#ex-dlg-lista').innerHTML = html + (filas.length ? '' : `<p class="explica" style="padding:14px">${CATALOGO.length ? 'Nada coincide.' : 'Cargando el catálogo…'}</p>`);
}
function abrirCat() { $('#ex-velo').hidden = false; pintarCat(); $('#ex-buscar').focus(); }
function cerrarCat() { $('#ex-velo').hidden = true; }

/* ---------- comunicación con la página ---------- */
function avisarPagina() {
  guardarUI();
  const ids = st.trabajo.map((t) => t.id); const dep = st.trabajo.find((t) => t.rol === 'dep')?.id || null;
  window.CuevaMesa?.seriesCambiaron?.(ids, dep);
}
function agregarSerie(id) {
  if (st.trabajo.some((t) => t.id === id)) return;
  const rec = leerUI().recetas?.[id] || {};
  st.trabajo.push({ id, vis: rec.vis ?? true, log: !!rec.log, dif: !!rec.dif, rol: 'expl' });
  cargarSerie(id);
  avisarPagina();
}

/* ---------- barra superior ---------- */
function marcarSeg(sel, valor, attr = 'v') { [...$(sel).children].forEach((x) => x.setAttribute('aria-pressed', x.dataset[attr] === valor)); }
function marcarBarra() {
  marcarSeg('#ex-c-vista', st.vista); marcarSeg('#ex-c-freq', st.freq); marcarSeg('#ex-c-var', st.vari); marcarSeg('#ex-c-rapido', st.rapido, 'a');
  const [a, b] = anios(); ['#ex-desde', '#ex-hasta'].forEach((id) => { $(id).min = a; $(id).max = b; });
  if (st.desde != null) { $('#ex-desde').value = st.desde; $('#ex-hasta').value = st.hasta; }
  const proy = window.CuevaMesa?.modo?.() === 'proyecto';
  $('#ex-llevar').textContent = proy ? 'Abrir el Estudio (explorador clásico) ↗' : 'Crear proyecto con estas series →';
  $('#ex-llevar').title = proy ? 'Tests, Transformaciones y Modelado todavía no tienen pantalla propia: el Estudio sigue en el explorador clásico.' : 'Se lleva las series y la dependiente a un proyecto con nombre.';
}

function todo() {
  if (!R) return;
  if (!st.activa || !st.trabajo.some((t) => t.id === st.activa)) st.activa = st.trabajo[0]?.id || null;
  pintarLista(); marcarBarra(); dibujar(); pintarTab(); pintarDer(); guardarUI();
}

const PLANTILLA = `
<main class="mesa">
  <aside class="col col-izq" aria-label="Series del trabajo">
    <div class="panel-hd"><span class="lbl">Series del trabajo</span><span class="chip neutral num" id="ex-n-series"></span>
      <button class="iconbtn" id="ex-ocultar" title="Ocultar panel" aria-label="Ocultar panel de series"><svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M9.5 3.5L5 8l4.5 4.5" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg></button></div>
    <div id="ex-lista"></div>
    <button class="btn agregar" id="ex-abrir-cat">＋ Agregar serie del catálogo</button>
    <p class="nota-izq">Cada serie guarda su <b>receta</b>: lo que le hiciste, en el orden en que se aplica. Lo de arriba del gráfico vale para todas.</p>
  </aside>
  <section class="centro" aria-label="Gráfico">
    <div class="barra" role="toolbar" aria-label="Controles del gráfico">
      <button class="iconbtn" id="ex-mostrar" title="Mostrar panel de series" aria-label="Mostrar panel de series" hidden><svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M6.5 3.5L11 8l-4.5 4.5" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg></button>
      <div class="grupo"><span class="lbl">Vista</span><div class="seg" id="ex-c-vista">
        <button data-v="paneles" title="Un panel por serie, cada una con su escala real">Paneles</button>
        <button data-v="b100" title="Todas en base 100 en la primera fecha visible">Base 100</button>
        <button data-v="z" title="Estandarizadas: (x − media) / desvío del rango visible">Estandarizado</button></div></div>
      <div class="grupo"><span class="lbl">Frecuencia común</span><div class="seg" id="ex-c-freq">
        <button data-v="M">Mensual</button><button data-v="Q">Trim.</button><button data-v="A">Anual</button></div></div>
      <div class="grupo"><span class="lbl">Variación</span><div class="seg" id="ex-c-var">
        <button data-v="nivel">Nivel</button><button data-v="ia" title="Var. % interanual; en tasas, diferencia en puntos">Interanual</button></div></div>
      <div class="grupo"><span class="lbl">Rango</span><div class="rango">
        <input id="ex-desde" type="number" aria-label="Año desde"><span class="num" style="color:var(--ink-faint)">→</span><input id="ex-hasta" type="number" aria-label="Año hasta">
        <div class="seg" id="ex-c-rapido"><button data-a="5">5A</button><button data-a="20">20A</button><button data-a="todo">Todo</button></div></div></div>
      <div class="spacer"></div>
      <div class="grupo"><span class="lbl">Siguiente</span><button class="btn primary sm" id="ex-llevar"></button></div>
    </div>
    <article class="card">
      <div class="card-hd"><h2 id="ex-g-titulo">Paneles</h2><span class="chip neutral" id="ex-g-freq"></span><div class="spacer"></div><span class="lbl num" id="ex-g-rango"></span></div>
      <div class="aviso" id="ex-g-aviso" hidden></div>
      <div class="grafico" id="ex-g-wrap"><svg id="ex-g" role="img" aria-label="Gráfico de las series del trabajo"></svg><div class="tip" id="ex-tip"></div></div>
      <div class="pie"><span class="lbl" style="font-size:9.5px">Franja de gobiernos</span>
        <span class="ley"><i style="background:color-mix(in srgb,var(--const) 30%,transparent)"></i>constitucional</span>
        <span class="ley"><i style="background:color-mix(in srgb,var(--facto) 35%,transparent)"></i>de facto</span>
        <span>· sale de la Línea de Tiempo (data/historia/presidencias.csv)</span></div>
    </article>
    <article class="card">
      <div class="tabs" id="ex-tabs"><button data-t="dist">Distribución</button><button data-t="cmp">Cuadro comparativo</button><button data-t="corr">Correlación</button><button data-t="spread">Spread A − B</button></div>
      <div class="tab-bd" id="ex-tab-bd"></div>
    </article>
  </section>
  <aside class="col col-der" aria-label="Ficha y estado de los datos">
    <div class="bloque" id="ex-ficha"></div>
    <div class="bloque"><div class="copiloto" id="ex-copiloto"></div></div>
    <div class="bloque">
      <div style="display:flex;align-items:center;gap:8px"><span class="lbl" style="flex:1">Datos conectados por familia</span><button class="btn sm ghost" id="ex-abrir-cat2">Catálogo →</button></div>
      <div id="ex-familias" style="display:flex;flex-direction:column;gap:10px"></div>
      <p class="explica" style="margin:0">Conectada = el archivo está en <span class="num">data/series/</span>. Lo que falta sigue en el Trabajo Final o no se bajó.</p>
      <p class="clasico">¿Buscás el explorador anterior (Kalman, Estudio)? <a href="/explorador" target="_blank" rel="noopener">Explorador clásico ↗</a></p>
    </div>
  </aside>
</main>
<div class="velo" id="ex-velo" hidden>
  <div class="dialogo" role="dialog" aria-modal="true" aria-labelledby="ex-dlg-t">
    <div class="panel-hd" style="gap:10px;flex-wrap:wrap"><span class="lbl" id="ex-dlg-t" style="flex:0 0 auto">Catálogo de series</span>
      <input class="buscar" id="ex-buscar" type="search" placeholder="Buscar por nombre o id…" aria-label="Buscar serie">
      <button class="iconbtn" id="ex-cerrar" aria-label="Cerrar catálogo">✕</button></div>
    <div class="dlg-cuerpo"><div class="dlg-fams" id="ex-dlg-fams"></div><div class="dlg-lista" id="ex-dlg-lista"></div></div>
  </div>
</div>`;

function cablear() {
  $('#ex-lista').addEventListener('click', clicLista);
  $('#ex-lista').addEventListener('keydown', (e) => { if (e.key === 'Enter' && e.target.classList.contains('serie')) { st.activa = e.target.dataset.id; todo(); } });
  $('#ex-g-wrap').addEventListener('mousemove', mover);
  $('#ex-g-wrap').addEventListener('mouseleave', ocultarTip);
  $('#ex-tabs').addEventListener('click', (e) => { const b = e.target.closest('button'); if (!b) return; st.tab = b.dataset.t; marcarSeg('#ex-tabs', st.tab, 't'); pintarTab(); guardarUI(); });
  for (const [sel, k] of [['#ex-c-vista', 'vista'], ['#ex-c-freq', 'freq'], ['#ex-c-var', 'vari']]) {
    $(sel).addEventListener('click', (e) => { const b = e.target.closest('button'); if (!b) return; st[k] = b.dataset.v; todo(); });
  }
  $('#ex-c-rapido').addEventListener('click', (e) => {
    const b = e.target.closest('button'); if (!b) return; const [a, z] = anios(); st.rapido = b.dataset.a;
    if (b.dataset.a === 'todo') { st.desde = a; st.hasta = z; } else { st.hasta = z; st.desde = Math.max(a, z - Number(b.dataset.a) + 1); }
    todo();
  });
  ['#ex-desde', '#ex-hasta'].forEach((id) => $(id).addEventListener('change', () => {
    let a = +$('#ex-desde').value, b = +$('#ex-hasta').value; if (a > b) [a, b] = [b, a];
    const [mn, mx] = anios(); st.desde = Math.max(mn, a); st.hasta = Math.min(mx, b); st.rapido = ''; todo();
  }));
  $('#ex-ocultar').onclick = () => { R.querySelector('.mesa').classList.add('sin-izq'); $('#ex-mostrar').hidden = false; requestAnimationFrame(dibujar); };
  $('#ex-mostrar').onclick = () => { R.querySelector('.mesa').classList.remove('sin-izq'); $('#ex-mostrar').hidden = true; requestAnimationFrame(dibujar); };
  $('#ex-abrir-cat').onclick = abrirCat; $('#ex-abrir-cat2').onclick = abrirCat; $('#ex-cerrar').onclick = cerrarCat;
  $('#ex-velo').addEventListener('click', (e) => { if (e.target.id === 'ex-velo') cerrarCat(); });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && !$('#ex-velo').hidden) cerrarCat(); });
  $('#ex-dlg-fams').addEventListener('click', (e) => { const b = e.target.closest('button'); if (!b) return; st.fam = b.dataset.f; st.q = ''; $('#ex-buscar').value = ''; pintarCat(); });
  $('#ex-buscar').addEventListener('input', (e) => { st.q = e.target.value; pintarCat(); });
  $('#ex-dlg-lista').addEventListener('click', (e) => { const b = e.target.closest('[data-add]'); if (!b) return; agregarSerie(b.dataset.add); st.activa = b.dataset.add; pintarCat(); todo(); });
  $('#ex-llevar').onclick = () => {
    if (window.CuevaMesa?.modo?.() === 'proyecto') window.open('/explorador', '_blank', 'noopener');
    else window.CuevaMesa?.pasarAProyecto?.();
  };
  let rz; addEventListener('resize', () => { clearTimeout(rz); rz = setTimeout(dibujar, 120); });
  document.addEventListener('cueva:tema', () => todo());
}

/* ---------- API pública ---------- */
export async function montar(raiz, { series = [], dep = null } = {}) {
  R = raiz; R.classList.add('ex'); R.innerHTML = PLANTILLA;
  const ui = leerUI();
  for (const k of ['vista', 'freq', 'vari', 'desde', 'hasta', 'rapido', 'tab']) if (ui[k] != null) st[k] = ui[k];
  marcarSeg('#ex-tabs', st.tab, 't');
  cablear();
  fijarSeries(series, dep);
  const [cat, fams, hist] = await Promise.allSettled([json('/api/v1/series?limite=0'), json('/api/v1/series/familias'), json('/api/v1/historia')]);
  if (cat.status === 'fulfilled') CATALOGO = cat.value.filter((s) => s.grupo);   // solo lo curado del catálogo
  if (fams.status === 'fulfilled') FAMILIAS = fams.value;
  if (hist.status === 'fulfilled') PRES = hist.value.presidencias || [];
  todo();
}

export function fijarSeries(ids, dep) {
  const ui = leerUI().recetas || {};
  const prev = new Map(st.trabajo.map((t) => [t.id, t]));
  st.trabajo = (ids || []).map((id) => {
    const p = prev.get(id); const r = ui[id] || {};
    return { id, vis: p?.vis ?? r.vis ?? true, log: p?.log ?? !!r.log, dif: p?.dif ?? !!r.dif, rol: id === dep ? 'dep' : 'expl' };
  });
  st.trabajo.forEach((t) => cargarSerie(t.id));
  todo();
}

window.CuevaExplorar = { montar, fijarSeries, redibujar: () => todo() };
