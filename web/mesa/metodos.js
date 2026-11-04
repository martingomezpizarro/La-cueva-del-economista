/* metodos.js — Pantalla «Métodos» de la Mesa: el catálogo completo de análisis.
 *
 * Todo lo que se ve sale de la DECLARACIÓN de cada método (cueva/metodos): la pantalla no
 * conoce ningún método en particular. Sumar un método en Python lo hace aparecer acá, con
 * su formulario y su resultado, sin tocar este archivo.
 *
 * Datos:
 *   GET  /api/v1/metodos            familias + declaración de cada método
 *   GET  /api/v1/series?limite=0    catálogo de series (para elegir insumos)
 *   POST /api/v1/herramienta        corre {nombre, args, proyecto_id?} → resultado con bloques
 *   POST /api/v1/mis-series         sube un CSV propio
 *   POST /api/v1/mis-series/derivada guarda una salida como serie (encadenar métodos)
 *
 * Bloques que sabe dibujar (contrato de cueva/metodos/contrato.py): metricas, tabla, lineas,
 * bandas, barras, mapa_calor, dispersion, texto, veredicto. Todo texto del servidor se escapa.
 */

const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const css = (n) => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const COL = ['--s1', '--s2', '--s3', '--s4', '--s5'];
const color = (i) => `var(${COL[i % COL.length]})`;
const CLAVE = 'cueva_metodos';
const NIVEL = { basico: 'básico', intermedio: 'intermedio', avanzado: 'avanzado' };
const COSTO = { instantaneo: '⚡ instantáneo', segundos: '⏱ segundos', minutos: '⏳ minutos' };

function num(v, d) {
  if (v == null || v === '') return '—';
  if (typeof v !== 'number') return esc(v);
  if (!isFinite(v)) return '—';
  const a = Math.abs(v);
  if (a !== 0 && (a < 1e-3 || a >= 1e7)) return v.toExponential(2).replace('.', ',');
  if (d == null) d = a >= 1000 ? 0 : a >= 100 ? 1 : a >= 1 ? 3 : 4;
  return v.toLocaleString('es-AR', { minimumFractionDigits: 0, maximumFractionDigits: d });
}

/* ───────────────────────── estado ───────────────────────── */
const st = { clases: [], familias: [], metodos: [], eje: 'clase', fam: null, q: '', sel: null, resultados: [], series: [], corriendo: false };
let R = null;
const $ = (s) => R.querySelector(s);

function guardar() {
  try {
    // los conjuntos grandes (un universo de modelos) no entran en sessionStorage: se guardan recortados
    const livianos = st.resultados.slice(0, 12).map((r) => ({ ...r, conjuntos: (r.conjuntos || []).map((c) => ({ ...c, filas: c.filas.slice(0, 200) })) }));
    sessionStorage.setItem(CLAVE, JSON.stringify({ eje: st.eje, fam: st.fam, sel: st.sel, resultados: livianos }));
  } catch { /* cuota o modo privado: los resultados viven en memoria */ }
}
function leer() {
  try { return JSON.parse(sessionStorage.getItem(CLAVE) || 'null') || {}; } catch { return {}; }
}

/* ───────────────────────── montaje ───────────────────────── */
export async function montar(raiz) {
  R = raiz;
  R.classList.add('mt');
  R.innerHTML = `
    <aside class="mt-cat">
      <div class="mt-buscar"><input id="mt-q" type="search" placeholder="Buscar: garch, cluster, kalshi, quiebre…" aria-label="Buscar método"></div>
      <div class="mt-fams" id="mt-fams"></div>
      <div class="mt-lista" id="mt-lista"></div>
      <div class="mt-mis">
        <label class="btn sm" title="CSV con una columna de fechas y una o más columnas numéricas (precios, tasas…)">⬆ Subir mis series (CSV)<input type="file" id="mt-csv" accept=".csv" hidden></label>
        <div class="mt-mis-estado" id="mt-mis-estado"></div>
      </div>
    </aside>
    <section class="mt-main">
      <div class="mt-ficha" id="mt-ficha"></div>
      <div class="mt-res" id="mt-res"></div>
    </section>
    <datalist id="mt-series-dl"></datalist>`;
  const prev = leer();
  st.eje = prev.eje || 'clase';
  st.fam = prev.fam || null;
  st.resultados = prev.resultados || [];
  try {
    const [cat, ser] = await Promise.all([
      fetch('/api/v1/metodos').then((r) => r.json()),
      fetch('/api/v1/series?limite=0').then((r) => r.json()).catch(() => []),
    ]);
    st.familias = cat.familias || [];
    st.clases = cat.clases || [];
    // Las operaciones de recetas (transformar, combinar, descomponer) entran al MISMO listado
    // que los métodos: mismo formulario, y su resultado se guarda como serie CON su receta.
    const ops = (cat.operaciones || []).map(comoMetodo);
    st.metodos = [...ops, ...(cat.metodos || [])];
    if (ops.length) st.familias = [{ id: 'recetas', nombre: 'Recetas (series derivadas)', icono: '🧪', n: ops.length }, ...st.familias];
    st.series = Array.isArray(ser) ? ser : ser.series || [];
  } catch (e) {
    $('#mt-ficha').innerHTML = `<div class="note warn">No pude cargar el catálogo de métodos: ${esc(e.message)}. Esta pantalla necesita el servidor de Python.</div>`;
    return;
  }
  st.sel = prev.sel && st.metodos.some((m) => m.id === prev.sel) ? prev.sel : null;
  llenarDatalist();
  $('#mt-q').addEventListener('input', (e) => { st.q = e.target.value.trim().toLowerCase(); pintarLista(); });
  $('#mt-csv').addEventListener('change', subirCSV);
  pintarFamilias();
  pintarLista();
  pintarFicha();
  pintarResultados();
}

function llenarDatalist() {
  $('#mt-series-dl').innerHTML = st.series
    .map((s) => `<option value="${esc(s.id)}">${esc(s.nombre || s.id)}${s.origen === 'Mis series' ? ' · mis series' : ''}</option>`)
    .join('');
}

/* ───────────────────────── catálogo ───────────────────────── */
function comoMetodo(o) {
  const clase = st.clases.find((c) => c.id === o.clase) || { nombre: o.clase, flujo: '' };
  const params = [{ nombre: 'a', tipo: 'serie', etiqueta: o.aridad === 2 ? 'Serie A' : 'Serie', requerido: true }];
  if (o.aridad === 2) params.push({ nombre: 'b', tipo: 'serie', etiqueta: 'Serie B', requerido: true });
  Object.entries(o.params || {}).forEach(([k, v]) => params.push(v.tipo === 'opcion'
    ? { nombre: k, tipo: 'opcion', etiqueta: k, defecto: v.defecto, opciones: v.min }
    : { nombre: k, tipo: v.tipo, etiqueta: k, defecto: v.defecto === '' ? null : v.defecto, minimo: v.min, maximo: v.max }));
  params.push({ nombre: 'freq', tipo: 'opcion', etiqueta: 'Frecuencia', defecto: 'mensual', opciones: ['mensual', 'trimestral', 'anual'] });
  return {
    id: 'op_' + o.id, _op: o.id, _aridad: o.aridad, nombre: o.nombre, clase: o.clase, clase_nombre: clase.nombre,
    familia: 'recetas', familia_nombre: 'Recetas', pregunta: o.ayuda || `${clase.nombre}: ${clase.flujo}. Crea una serie derivada.`,
    cuando: 'El resultado es una serie con su receta: se puede guardar en Mis series y usar como insumo de cualquier método, y se recalcula si cambian los datos.',
    supuestos: [], trampas: [], referencias: [], etiquetas: [o.id, 'receta', 'serie derivada'], nivel: 'basico', costo: 'instantaneo', disponible: true, falta: [], params,
  };
}

// Dos ejes sobre el mismo catálogo: el VERBO (qué le hace a lo que hay en la mesa) y el TEMA
function pintarFamilias() {
  const total = st.metodos.length;
  const grupos = st.eje === 'clase'
    ? st.clases.map((c) => ({ id: c.id, nombre: c.nombre, ayuda: c.flujo, n: st.metodos.filter((m) => m.clase === c.id).length }))
    : st.familias.map((f) => ({ id: f.id, nombre: `${f.icono} ${f.nombre}`, ayuda: '', n: f.n }));
  $('#mt-fams').innerHTML =
    `<div class="seg mt-eje" role="group" aria-label="Ordenar por"><button type="button" data-eje="clase" aria-pressed="${st.eje === 'clase'}">Por verbo</button><button type="button" data-eje="familia" aria-pressed="${st.eje === 'familia'}">Por tema</button></div>` +
    `<button class="mt-fam ${st.fam ? '' : 'on'}" data-f="">Todos <span>${total}</span></button>` +
    grupos.filter((g) => g.n).map((g) =>
      `<button class="mt-fam ${st.fam === g.id ? 'on' : ''}" data-f="${esc(g.id)}" title="${esc(g.ayuda)}">${esc(g.nombre)} <span>${g.n}</span></button>`).join('');
  R.querySelectorAll('.mt-fam').forEach((b) => b.addEventListener('click', () => {
    st.fam = b.dataset.f || null; guardar(); pintarFamilias(); pintarLista();
  }));
  R.querySelectorAll('.mt-eje button').forEach((b) => b.addEventListener('click', () => {
    st.eje = b.dataset.eje; st.fam = null; guardar(); pintarFamilias(); pintarLista();
  }));
}

function coincide(m, q) {
  if (!q) return true;
  const txt = [m.id, m.nombre, m.pregunta, m.cuando, ...(m.etiquetas || []), m.familia_nombre, m.clase_nombre].join(' ').toLowerCase();
  return q.split(/\s+/).every((p) => txt.includes(p));
}

function pintarLista() {
  const lista = st.metodos.filter((m) => (!st.fam || m[st.eje] === st.fam) && coincide(m, st.q));
  $('#mt-lista').innerHTML = lista.length ? lista.map((m) => `
    <button class="mt-item ${st.sel === m.id ? 'on' : ''} ${m.disponible ? '' : 'nodisp'}" data-id="${esc(m.id)}">
      <b>${esc(m.nombre)}</b>
      <small>${esc(m.pregunta)}</small>
      <span class="mt-tags"><i class="n-${esc(m.nivel)}">${NIVEL[m.nivel] || ''}</i>${m.disponible ? '' : '<i class="falta">falta instalar</i>'}</span>
    </button>`).join('') : '<p class="mt-vacio">Nada coincide con la búsqueda.</p>';
  R.querySelectorAll('.mt-item').forEach((b) => b.addEventListener('click', () => {
    st.sel = b.dataset.id; guardar(); pintarLista(); pintarFicha();
    $('#mt-ficha').scrollIntoView({ block: 'start', behavior: 'smooth' });
  }));
}

/* ───────────────────────── ficha + formulario ───────────────────────── */
function contexto() {
  const est = window.CuevaMesa?.estado?.() || { series: [], dep: null };
  return { series: est.series || [], dep: est.dep || (est.series || [])[0] || null };
}

function valorInicial(p, ctx, usados) {
  if (p.tipo === 'serie') {
    if (!p.requerido && p.defecto == null) return '';
    const cand = [ctx.dep, ...ctx.series].filter((x) => x && !usados.has(x));
    const v = cand[0] || '';
    if (v) usados.add(v);
    return v;
  }
  if (p.tipo === 'series') {
    const resto = ctx.series.filter((x) => !usados.has(x));
    return resto.slice(0, p.max_items || 8);
  }
  return p.defecto;
}

function campo(p, v) {
  const id = `mt-p-${p.nombre}`;
  const ayuda = p.ayuda ? `<small>${esc(p.ayuda)}</small>` : '';
  const req = p.requerido ? ' <em>*</em>' : '';
  let ctl = '';
  if (p.tipo === 'serie') {
    ctl = `<input id="${id}" list="mt-series-dl" value="${esc(v || '')}" placeholder="id de la serie" autocomplete="off">`;
  } else if (p.tipo === 'series') {
    const chips = (v || []).map((s) => `<span class="mt-chip" data-v="${esc(s)}">${esc(s)}<button type="button" aria-label="quitar">×</button></span>`).join('');
    ctl = `<div class="mt-multi" id="${id}" data-tipo="series">${chips}<input list="mt-series-dl" placeholder="＋ agregar serie" autocomplete="off"></div>`;
  } else if (p.tipo === 'opcion') {
    ctl = `<select id="${id}">${(p.opciones || []).map((o) => `<option ${o === v ? 'selected' : ''}>${esc(o)}</option>`).join('')}</select>`;
  } else if (p.tipo === 'opciones') {
    const sel = new Set(v || []);
    ctl = `<div class="mt-checks" id="${id}" data-tipo="opciones">${(p.opciones || []).map((o) => `<label><input type="checkbox" value="${esc(o)}" ${sel.has(o) ? 'checked' : ''}> ${esc(o)}</label>`).join('')}</div>`;
  } else if (p.tipo === 'bool') {
    ctl = `<label class="mt-bool"><input type="checkbox" id="${id}" ${v ? 'checked' : ''}> sí</label>`;
  } else if (p.tipo === 'entero' || p.tipo === 'real') {
    const paso = p.tipo === 'entero' ? 1 : 'any';
    ctl = `<input id="${id}" type="number" step="${paso}" ${p.minimo != null ? `min="${p.minimo}"` : ''} ${p.maximo != null ? `max="${p.maximo}"` : ''} value="${v ?? ''}">`;
  } else {
    ctl = `<input id="${id}" value="${esc(v ?? '')}" placeholder="${p.tipo === 'fecha' ? 'AAAA-MM' : ''}">`;
  }
  return `<div class="mt-campo ${p.tipo === 'series' || p.tipo === 'opciones' ? 'ancho' : ''}"><label for="${id}">${esc(p.etiqueta)}${req}</label>${ctl}${ayuda}</div>`;
}

function pintarFicha() {
  const m = st.metodos.find((x) => x.id === st.sel);
  if (!m) {
    const n = st.metodos.length;
    $('#mt-ficha').innerHTML = `
      <div class="mt-intro">
        <h2>Métodos</h2>
        <p>${n} métodos en ${st.familias.filter((f) => f.n).length} familias: pruebas, filtros, modelos univariados y multivariados, cointegración, regímenes, Kalman, inferencia causal, aprendizaje automático, redes neuronales, finanzas cuantitativas y el torneo que los pone a competir.</p>
        <p>Elegí uno a la izquierda. Los insumos se completan con las series que elegiste en <b>Explorar</b>; cualquier salida (un ciclo, un factor, una probabilidad) se puede guardar como serie y usar en otro método.</p>
        <p class="mt-regla">Regla de la casa: todo pronóstico se evalúa fuera de muestra contra un benchmark ingenuo, y todo método declara sus supuestos y sus trampas.</p>
      </div>`;
    return;
  }
  const ctx = contexto();
  const usados = new Set();
  const campos = m.params.map((p) => campo(p, valorInicial(p, ctx, usados))).join('');
  const lista = (t, xs) => xs && xs.length ? `<div class="mt-bloque-ficha"><h4>${t}</h4><ul>${xs.map((x) => `<li>${esc(x)}</li>`).join('')}</ul></div>` : '';
  $('#mt-ficha').innerHTML = `
    <header class="mt-cab">
      <div>
        <span class="mt-fam-nom">${esc(m.familia_nombre)}</span>
        <h2>${esc(m.nombre)}</h2>
        <p class="mt-preg">${esc(m.pregunta)}</p>
      </div>
      <div class="mt-meta"><span class="chip neutral">${NIVEL[m.nivel] || ''}</span><span class="chip neutral">${COSTO[m.costo] || ''}</span></div>
    </header>
    ${m.cuando ? `<p class="mt-cuando"><b>Cuándo:</b> ${esc(m.cuando)}</p>` : ''}
    <details class="mt-det"><summary>Supuestos, trampas y referencias</summary>
      <div class="mt-det-grid">${lista('Supuestos', m.supuestos)}${lista('Trampas típicas', m.trampas)}${lista('Referencias', m.referencias)}</div>
    </details>
    ${m.disponible ? '' : `<div class="note warn">Este método necesita paquetes que no están instalados en el servidor: ${esc(m.falta.join(', '))}.</div>`}
    <form class="mt-form" id="mt-form">${campos}
      <div class="mt-acc"><button class="btn primary" id="mt-run" type="submit" ${m.disponible ? '' : 'disabled'}>▶ Correr</button><span id="mt-estado" class="mt-estado"></span></div>
    </form>`;
  R.querySelectorAll('.mt-multi').forEach(prepararMulti);
  $('#mt-form').addEventListener('submit', (e) => { e.preventDefault(); correr(m); });
}

function prepararMulti(box) {
  const inp = box.querySelector('input');
  const agregar = () => {
    const v = inp.value.trim();
    if (!v) return;
    if (![...box.querySelectorAll('.mt-chip')].some((c) => c.dataset.v === v)) {
      const span = document.createElement('span');
      span.className = 'mt-chip'; span.dataset.v = v;
      span.innerHTML = `${esc(v)}<button type="button" aria-label="quitar">×</button>`;
      box.insertBefore(span, inp);
    }
    inp.value = '';
  };
  inp.addEventListener('change', agregar);
  inp.addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); agregar(); } });
  box.addEventListener('click', (e) => { if (e.target.tagName === 'BUTTON') e.target.parentElement.remove(); });
}

function leerArgs(m) {
  const args = {};
  for (const p of m.params) {
    const el = $(`#mt-p-${p.nombre}`);
    if (!el) continue;
    let v;
    if (p.tipo === 'series') v = [...el.querySelectorAll('.mt-chip')].map((c) => c.dataset.v);
    else if (p.tipo === 'opciones') v = [...el.querySelectorAll('input:checked')].map((c) => c.value);
    else if (p.tipo === 'bool') v = el.checked;
    else if (p.tipo === 'entero') v = el.value === '' ? null : parseInt(el.value, 10);
    else if (p.tipo === 'real') v = el.value === '' ? null : parseFloat(el.value);
    else v = el.value.trim();
    if (v === '' || v == null || (Array.isArray(v) && !v.length)) continue;
    args[p.nombre] = v;
  }
  return args;
}

async function correrReceta(m, args) {
  const p = {};
  m.params.forEach((q) => { if (!['a', 'b', 'freq'].includes(q.nombre) && args[q.nombre] != null) p[q.nombre] = args[q.nombre]; });
  const receta = { op: m._op, de: m._aridad === 2 ? [args.a, args.b] : [args.a] };
  if (Object.keys(p).length) receta.p = p;
  const t0 = performance.now();
  const r = await fetch('/api/v1/recetas/evaluar', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ receta, freq: args.freq || 'mensual' }) });
  const d = await r.json();
  if (!r.ok) return { ok: false, metodo: 'receta', args, resumen: d.error?.mensaje || 'No se pudo evaluar la receta.' };
  return {
    ok: true, metodo: 'receta', args, nombre: m.nombre,
    resumen: `${d.texto} · ${d.valores.length} obs. · depende de ${d.hojas.join(', ')} · huella ${d.huella}`,
    bloques: [{ tipo: 'lineas', titulo: d.texto, x: d.fechas, series: { [d.texto]: d.valores }, estilos: {}, marcas: [], y2: [] }],
    series_salida: [{ nombre: d.texto, descripcion: `Receta ${d.texto}`, fechas: d.fechas, valores: d.valores, receta }],
    meta: { segundos: (performance.now() - t0) / 1000 },
  };
}

async function correr(m) {
  if (st.corriendo) return;
  const args = leerArgs(m);
  const body = { nombre: m.id, args };
  const pid = window.CuevaMesa?.proyectoId?.();
  if (pid) body.proyecto_id = pid;
  st.corriendo = true;
  $('#mt-run').disabled = true;
  $('#mt-estado').textContent = m.costo === 'minutos' ? '⏳ Corriendo (puede tardar un par de minutos)…' : '⏳ Corriendo en el servidor…';
  try {
    let res;
    if (m._op) {
      res = await correrReceta(m, args);
    } else {
      const r = await fetch('/api/v1/herramienta', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
      res = await r.json();
    }
    if (res.error) throw new Error(res.error.mensaje || 'error de la API');
    res._id = res.estudio_id || `r${Date.now().toString(36)}`;
    res._nombre = m.nombre;
    st.resultados.unshift(res);
    st.resultados = st.resultados.slice(0, 20);
    guardar();
    pintarResultados();
    $('#mt-estado').textContent = res.ok ? `✓ listo en ${num(res.meta?.segundos, 2)} s` : '⚠ el método devolvió un problema (mirá la tarjeta)';
    $('#mt-res').scrollIntoView({ block: 'start', behavior: 'smooth' });
    if (pid) window.CuevaMesa?.estudiosCambiaron?.();
  } catch (e) {
    $('#mt-estado').textContent = `✗ ${e.message}`;
  } finally {
    st.corriendo = false;
    const b = $('#mt-run'); if (b) b.disabled = false;
  }
}

/* ───────────────────────── resultados ───────────────────────── */
function argsTexto(a) {
  return Object.entries(a || {}).filter(([, v]) => v != null && v !== '' && v !== false)
    .map(([k, v]) => `${k}=${Array.isArray(v) ? v.join(',') : v}`).join(' · ');
}

function pintarResultados() {
  const cont = $('#mt-res');
  if (!st.resultados.length) { cont.innerHTML = ''; return; }
  cont.innerHTML = `<div class="mt-res-cab"><h3>Resultados</h3><button class="btn sm" id="mt-limpiar">Limpiar</button></div>` +
    st.resultados.map((res, i) => tarjeta(res, i)).join('');
  $('#mt-limpiar').addEventListener('click', () => { st.resultados = []; guardar(); pintarResultados(); });
  cont.querySelectorAll('[data-quitar]').forEach((b) => b.addEventListener('click', () => {
    st.resultados.splice(+b.dataset.quitar, 1); guardar(); pintarResultados();
  }));
  cont.querySelectorAll('[data-guardar]').forEach((b) => b.addEventListener('click', () => guardarSalida(b)));
  cont.querySelectorAll('svg.mt-g').forEach(activarTooltip);
}

function tarjeta(res, i) {
  const sem = res.semaforo ? `<span class="mt-sem ${esc(res.semaforo)}">${esc(res.semaforo)}</span>` : '';
  const cuerpo = res.ok === false
    ? `<div class="note warn">${esc(res.resumen)}</div>`
    : (res.bloques || []).map((b, j) => bloque(b, `${i}-${j}`)).join('');
  const adv = (res.advertencias || []).map((a) => `<div class="note warn">⚠ ${esc(a)}</div>`).join('');
  const salidas = (res.series_salida || []).length ? `<div class="mt-salidas"><h4>Series que produjo este paso</h4>${res.series_salida.map((s, k) => `
      <div class="mt-salida"><span><b>${esc(s.nombre)}</b> · ${s.valores.length} obs. <small>${esc(s.descripcion || '')}</small></span>
      <button class="btn sm" data-guardar="${i}:${k}" title="Queda en «Mis series» y se puede usar como insumo de cualquier método">Guardar como serie</button></div>`).join('')}</div>` : '';
  const conjuntos = (res.conjuntos || []).map((c) => `<details class="mt-cod"><summary>Datos · ${esc(c.nombre)} (${c.filas.length.toLocaleString('es-AR')} filas)${c.descripcion ? ' — ' + esc(c.descripcion) : ''}</summary>
      <div class="mt-tabla"><div class="mt-scroll"><table><thead><tr>${c.columnas.map((h) => `<th>${esc(h)}</th>`).join('')}</tr></thead><tbody>${c.filas.slice(0, 100).map((f) => `<tr>${f.map((v) => `<td class="${typeof v === 'number' ? 'n' : ''}">${typeof v === 'number' ? num(v) : esc(Array.isArray(v) ? v.join(', ') : v)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>${c.filas.length > 100 ? `<small>Se muestran 100 de ${c.filas.length.toLocaleString('es-AR')} filas: el conjunto completo viaja con el resultado y se puede volver a graficar.</small>` : ''}</div></details>`).join('');
  const codigo = res.codigo ? `<details class="mt-cod"><summary>Código equivalente</summary><pre>${esc(res.codigo)}</pre></details>` : '';
  return `<article class="mt-card ${res.ok === false ? 'err' : ''}">
    <header><b>${esc(res._nombre || res.nombre || res.metodo)}</b>${sem}<span class="mt-args">${esc(argsTexto(res.args))}</span>
      <span class="mt-t">${res.meta ? num(res.meta.segundos, 2) + ' s' : ''}</span><button class="mt-x" data-quitar="${i}" title="Quitar">×</button></header>
    <p class="mt-resumen">${esc(res.resumen)}</p>${adv}${cuerpo}${salidas}${conjuntos}${codigo}</article>`;
}

async function guardarSalida(btn) {
  const [i, k] = btn.dataset.guardar.split(':').map(Number);
  const res = st.resultados[i];
  const s = res.series_salida[k];
  // procedencia: de qué método y con qué argumentos salió (queda guardada al lado de los datos)
  const origen = `${res.metodo}(${argsTexto(res.args)})`;
  btn.disabled = true; btn.textContent = 'Guardando…';
  try {
    const r = await fetch('/api/v1/mis-series/derivada', { method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ nombre: s.nombre, fechas: s.fechas, valores: s.valores, descripcion: `${s.descripcion || s.nombre} · sale de ${origen}`.slice(0, 500), receta: s.receta || null }) });
    const d = await r.json();
    if (!r.ok) throw new Error(d.error?.mensaje || 'no se pudo guardar');
    btn.textContent = `✓ guardada como ${d.id}`;
    await refrescarSeries();
  } catch (e) { btn.textContent = `✗ ${e.message}`; btn.disabled = false; }
}

async function refrescarSeries() {
  try {
    const ser = await fetch('/api/v1/series?limite=0&refrescar=true').then((r) => r.json());
    st.series = Array.isArray(ser) ? ser : ser.series || [];
    llenarDatalist();
  } catch { /* sin red: queda el listado anterior */ }
}

async function subirCSV(e) {
  const f = e.target.files[0];
  if (!f) return;
  const est = $('#mt-mis-estado');
  est.textContent = 'Subiendo…';
  const fd = new FormData(); fd.append('archivo', f);
  try {
    const r = await fetch('/api/v1/mis-series', { method: 'POST', body: fd });
    const d = await r.json();
    if (!r.ok) throw new Error(d.error?.mensaje || 'no se pudo subir');
    est.innerHTML = `✓ ${d.series.length} serie(s): ${d.series.map((s) => `<code>${esc(s.id)}</code>`).join(' ')}`;
    await refrescarSeries();
  } catch (err) { est.textContent = `✗ ${err.message}`; }
  e.target.value = '';
}

/* ───────────────────────── bloques ───────────────────────── */
function bloque(b, key) {
  switch (b.tipo) {
    case 'metricas':
      return `<div class="mt-mets">${b.items.map((it) => `<div class="mt-met" title="${esc(it.ayuda || '')}"><span>${esc(it.nombre)}</span><b>${num(it.valor)}</b></div>`).join('')}</div>`;
    case 'tabla': return tabla(b);
    case 'veredicto': return `<div class="mt-ver ${esc(b.semaforo || '')}">${esc(b.texto)}</div>`;
    case 'texto': return `<div class="mt-txt"><h4>${esc(b.titulo)}</h4><p>${esc(b.cuerpo)}</p></div>`;
    case 'lineas': return figura(b, svgLineas(b, key));
    case 'bandas': return figura(b, svgBandas(b, key));
    case 'barras': return figura(b, svgBarras(b));
    case 'mapa_calor': return figura(b, svgCalor(b));
    case 'dispersion': return figura(b, svgDispersion(b));
    default: return '';
  }
}

function tabla(b) {
  const ip = b.resaltar_p ? b.columnas.indexOf(b.resaltar_p) : -1;
  const filas = b.filas.slice(0, 200).map((f) => `<tr>${f.map((c, j) => {
    const sig = j === ip && typeof c === 'number' && c < 0.05;
    return `<td class="${typeof c === 'number' ? 'n' : ''} ${sig ? 'sig' : ''}">${typeof c === 'number' ? num(c) : esc(c)}</td>`;
  }).join('')}</tr>`).join('');
  const mas = b.filas.length > 200 ? `<caption>Se muestran 200 de ${b.filas.length} filas.</caption>` : '';
  return `<div class="mt-tabla"><h4>${esc(b.titulo)}</h4><div class="mt-scroll"><table>${mas}<thead><tr>${b.columnas.map((c) => `<th>${esc(c)}</th>`).join('')}</tr></thead><tbody>${filas}</tbody></table></div>${b.nota ? `<small>${esc(b.nota)}</small>` : ''}</div>`;
}

function figura(b, svg) {
  return `<figure class="mt-fig"><figcaption>${esc(b.titulo)}</figcaption>${svg}</figure>`;
}

/* ── escalas ── */
const W = 680, H = 250, M = { l: 54, r: 18, t: 12, b: 30 };

function tipoX(xs) {
  if (xs.every((x) => typeof x === 'number')) return 'num';
  if (xs.every((x) => typeof x === 'string' && /^\d{4}-\d{2}-\d{2}/.test(x))) return 'fecha';
  return 'cat';
}
function aNum(xs, t) {
  if (t === 'num') return xs;
  if (t === 'fecha') return xs.map((x) => Date.parse(x.length > 10 ? x.replace(' ', 'T') : x));
  return xs.map((_, i) => i);
}
function extremos(arrs) {
  let lo = Infinity, hi = -Infinity;
  arrs.forEach((a) => (a || []).forEach((v) => { if (v != null && isFinite(v)) { if (v < lo) lo = v; if (v > hi) hi = v; } }));
  if (!isFinite(lo)) return [0, 1];
  if (lo === hi) { lo -= 1; hi += 1; }
  const pad = (hi - lo) * 0.06;
  return [lo - pad, hi + pad];
}
function ticks(lo, hi, n = 5) {
  const paso = Math.pow(10, Math.floor(Math.log10((hi - lo) / n)));
  const m = [1, 2, 2.5, 5, 10].find((k) => (hi - lo) / (k * paso) <= n) * paso;
  const out = [];
  for (let v = Math.ceil(lo / m) * m; v <= hi + 1e-12; v += m) out.push(+v.toFixed(10));
  return out;
}
function etiquetaX(v, t, cats) {
  if (t === 'fecha') { const d = new Date(v); return `${d.getUTCFullYear()}${d.getUTCMonth() ? '-' + String(d.getUTCMonth() + 1).padStart(2, '0') : ''}`; }
  if (t === 'cat') return cats[Math.round(v)] ?? '';
  return num(v);
}
function ejes(sx, sy, x0, x1, y0, y1, t, cats) {
  let g = '';
  ticks(y0, y1).forEach((v) => {
    g += `<line class="grid" x1="${M.l}" x2="${W - M.r}" y1="${sy(v)}" y2="${sy(v)}"/><text class="ty" x="${M.l - 6}" y="${sy(v) + 3}">${num(v)}</text>`;
  });
  const nx = t === 'cat' ? Math.min(cats.length, 10) : 6;
  for (let i = 0; i < nx; i++) {
    const v = x0 + (x1 - x0) * (nx === 1 ? 0 : i / (nx - 1));
    g += `<text class="tx" x="${sx(v)}" y="${H - 8}">${esc(etiquetaX(v, t, cats))}</text>`;
  }
  if (y0 < 0 && y1 > 0) g += `<line class="cero" x1="${M.l}" x2="${W - M.r}" y1="${sy(0)}" y2="${sy(0)}"/>`;
  return g;
}
function camino(xs, ys, sx, sy) {
  let d = '', pluma = false;
  for (let i = 0; i < xs.length; i++) {
    const v = ys[i];
    if (v == null || !isFinite(v) || xs[i] == null || !isFinite(xs[i])) { pluma = false; continue; }
    d += `${pluma ? 'L' : 'M'}${sx(xs[i]).toFixed(1)},${sy(v).toFixed(1)}`;
    pluma = true;
  }
  return d;
}
function estiloLinea(nombre, est, i) {
  const e = (est || {})[nombre] || {};
  const ic = /^IC |^banda|^\+tol|^−tol|^p5$|^p95$/.test(nombre);
  const dash = e.guion === 'dash' ? '6 4' : e.guion === 'dot' || ic ? '2 3' : '';
  const ancho = e.ancho || (ic ? 1 : 1.6);
  return `stroke="${color(i)}" stroke-width="${ancho}" ${dash ? `stroke-dasharray="${dash}"` : ''}`;
}
function leyenda(nombres) {
  return `<div class="mt-ley">${nombres.map((n, i) => `<span><i style="background:${color(i)}"></i>${esc(n)}</span>`).join('')}</div>`;
}

function svgLineas(b, key) {
  const t = tipoX(b.x);
  const xs = aNum(b.x, t);
  const nombres = Object.keys(b.series);
  const izq = nombres.filter((n) => !(b.y2 || []).includes(n));
  const der = nombres.filter((n) => (b.y2 || []).includes(n));
  const [x0, x1] = [Math.min(...xs.filter(isFinite)), Math.max(...xs.filter(isFinite))];
  const [y0, y1] = extremos(izq.map((n) => b.series[n]));
  const sx = (v) => M.l + ((v - x0) / (x1 - x0 || 1)) * (W - M.l - M.r);
  const sy = (v) => H - M.b - ((v - y0) / (y1 - y0)) * (H - M.t - M.b);
  let g = ejes(sx, sy, x0, x1, y0, y1, t, b.x);
  izq.forEach((n) => { g += `<path d="${camino(xs, b.series[n], sx, sy)}" fill="none" ${estiloLinea(n, b.estilos, nombres.indexOf(n))}/>`; });
  if (der.length) {
    const [z0, z1] = extremos(der.map((n) => b.series[n]));
    const sz = (v) => H - M.b - ((v - z0) / (z1 - z0)) * (H - M.t - M.b);
    der.forEach((n) => { g += `<path d="${camino(xs, b.series[n], sx, sz)}" fill="none" ${estiloLinea(n, b.estilos, nombres.indexOf(n))} opacity=".75"/>`; });
    g += `<text class="ty der" x="${W - 4}" y="${M.t + 8}">${num(z1)}</text><text class="ty der" x="${W - 4}" y="${H - M.b}">${num(z0)}</text>`;
  }
  (b.marcas || []).forEach((mk) => {
    const xv = t === 'fecha' ? Date.parse(mk.x) : t === 'num' ? +mk.x : b.x.indexOf(String(mk.x));
    if (!isFinite(xv)) return;
    g += `<line class="marca" x1="${sx(xv)}" x2="${sx(xv)}" y1="${M.t}" y2="${H - M.b}"/>${mk.texto ? `<text class="tm" x="${sx(xv) + 3}" y="${M.t + 9}">${esc(String(mk.texto).slice(0, 34))}</text>` : ''}`;
  });
  const datos = encodeURIComponent(JSON.stringify({ x: b.x, s: b.series, t }));
  return `<svg class="mt-g" viewBox="0 0 ${W} ${H}" data-k="${key}" data-d="${datos}" data-x0="${x0}" data-x1="${x1}">${g}<line class="cursor" y1="${M.t}" y2="${H - M.b}" x1="-10" x2="-10"/></svg>${leyenda(nombres)}`;
}

function svgBandas(b, key) {
  const t = 'fecha';
  const xh = aNum(b.x_hist, t), xp = aNum(b.x_pron, t);
  const extra = b.extra || {};
  const todosX = [...xh, ...xp, ...Object.values(extra).flatMap((e) => aNum(e.x, t))].filter(isFinite);
  const [x0, x1] = [Math.min(...todosX), Math.max(...todosX)];
  const [y0, y1] = extremos([b.historia, b.media, b.inferior, b.superior, ...Object.values(extra).map((e) => e.y)]);
  const sx = (v) => M.l + ((v - x0) / (x1 - x0 || 1)) * (W - M.l - M.r);
  const sy = (v) => H - M.b - ((v - y0) / (y1 - y0)) * (H - M.t - M.b);
  let g = ejes(sx, sy, x0, x1, y0, y1, t, []);
  if (b.inferior && b.superior) {
    const arriba = xp.map((x, i) => `${sx(x).toFixed(1)},${sy(b.superior[i]).toFixed(1)}`);
    const abajo = xp.map((x, i) => `${sx(x).toFixed(1)},${sy(b.inferior[i]).toFixed(1)}`).reverse();
    g += `<polygon class="banda" points="${[...arriba, ...abajo].join(' ')}"/>`;
  }
  g += `<path d="${camino(xh, b.historia, sx, sy)}" fill="none" stroke="${color(0)}" stroke-width="1.6"/>`;
  const xu = xh[xh.length - 1], yu = b.historia[b.historia.length - 1];
  g += `<path d="M${sx(xu)},${sy(yu)}${camino(xp, b.media, sx, sy).replace('M', 'L')}" fill="none" stroke="${color(1)}" stroke-width="2" stroke-dasharray="6 4"/>`;
  Object.entries(extra).forEach(([, e], i) => { g += `<path d="${camino(aNum(e.x, t), e.y, sx, sy)}" fill="none" stroke="${color(i + 2)}" stroke-width="1.3" stroke-dasharray="2 3"/>`; });
  const nombres = ['historia', 'pronóstico', ...Object.keys(extra)];
  return `<svg class="mt-g" viewBox="0 0 ${W} ${H}" data-k="${key}">${g}</svg>${leyenda(nombres)}${b.inferior ? `<div class="mt-ley"><span><i class="banda-i"></i>${esc(b.nombre_banda || 'IC')}</span></div>` : ''}`;
}

function svgBarras(b) {
  const nombres = Object.keys(b.series);
  const cats = b.categorias;
  const vals = nombres.map((n) => b.series[n]);
  let [y0, y1] = extremos([...vals, b.banda != null ? [b.banda, -b.banda] : []]);
  if (y0 > 0) y0 = 0;
  if (y1 < 0) y1 = 0;
  if (b.horizontal) {
    const alto = Math.max(140, cats.length * (14 * nombres.length + 6) + 30);
    const ml = Math.min(260, 12 + Math.max(...cats.map((c) => c.length)) * 6.2);
    const sx = (v) => ml + ((v - y0) / (y1 - y0)) * (W - ml - M.r);
    const bh = (alto - 30) / cats.length;
    let g = '';
    ticks(y0, y1).forEach((v) => { g += `<line class="grid" x1="${sx(v)}" x2="${sx(v)}" y1="4" y2="${alto - 22}"/><text class="tx" x="${sx(v)}" y="${alto - 8}">${num(v)}</text>`; });
    cats.forEach((c, i) => {
      g += `<text class="ty" x="${ml - 6}" y="${i * bh + bh / 2 + 7}">${esc(c.length > 40 ? c.slice(0, 39) + '…' : c)}</text>`;
      nombres.forEach((n, k) => {
        const v = b.series[n][i];
        if (v == null) return;
        const a = sx(Math.min(0, v)), w = Math.abs(sx(v) - sx(0));
        const hh = Math.max(3, (bh - 6) / nombres.length);
        g += `<rect x="${a}" y="${i * bh + 4 + k * hh}" width="${Math.max(1, w)}" height="${hh - 1}" fill="${color(k)}"><title>${esc(c)}: ${num(v)}</title></rect>`;
      });
    });
    g += `<line class="cero" x1="${sx(0)}" x2="${sx(0)}" y1="4" y2="${alto - 22}"/>`;
    return `<svg class="mt-g bar" viewBox="0 0 ${W} ${alto}">${g}</svg>${nombres.length > 1 ? leyenda(nombres) : ''}`;
  }
  const sy = (v) => H - M.b - ((v - y0) / (y1 - y0)) * (H - M.t - M.b);
  const ancho = (W - M.l - M.r) / cats.length;
  const sx = (i) => M.l + i * ancho;
  let g = '';
  ticks(y0, y1).forEach((v) => { g += `<line class="grid" x1="${M.l}" x2="${W - M.r}" y1="${sy(v)}" y2="${sy(v)}"/><text class="ty" x="${M.l - 6}" y="${sy(v) + 3}">${num(v)}</text>`; });
  const salto = Math.ceil(cats.length / 14);
  cats.forEach((c, i) => {
    nombres.forEach((n, k) => {
      const v = b.series[n][i];
      if (v == null) return;
      const bw = Math.max(1, (ancho - 2) / nombres.length);
      g += `<rect x="${sx(i) + 1 + k * bw}" y="${sy(Math.max(0, v))}" width="${bw - 0.5}" height="${Math.max(0.5, Math.abs(sy(v) - sy(0)))}" fill="${color(k)}"><title>${esc(c)}: ${num(v)}</title></rect>`;
    });
    if (i % salto === 0) g += `<text class="tx" x="${sx(i) + ancho / 2}" y="${H - 8}">${esc(c.length > 10 ? c.slice(0, 9) + '…' : c)}</text>`;
  });
  if (b.banda != null) g += `<line class="umbral" x1="${M.l}" x2="${W - M.r}" y1="${sy(b.banda)}" y2="${sy(b.banda)}"/><line class="umbral" x1="${M.l}" x2="${W - M.r}" y1="${sy(-b.banda)}" y2="${sy(-b.banda)}"/>`;
  g += `<line class="cero" x1="${M.l}" x2="${W - M.r}" y1="${sy(0)}" y2="${sy(0)}"/>`;
  return `<svg class="mt-g bar" viewBox="0 0 ${W} ${H}">${g}</svg>${nombres.length > 1 ? leyenda(nombres) : ''}`;
}

function svgCalor(b) {
  const nf = b.filas.length, nc = b.columnas.length;
  const ml = Math.min(220, 10 + Math.max(...b.filas.map((f) => f.length)) * 6.2);
  const mt = 70;
  const alto = Math.max(160, mt + nf * 22 + 10);
  const cw = (W - ml - 10) / nc, ch = (alto - mt - 10) / nf;
  const vals = b.valores.flat().filter((v) => v != null && isFinite(v));
  const [lo, hi] = b.rango || [Math.min(...vals), Math.max(...vals)];
  const div = b.rango ? lo < 0 && hi > 0 : Math.min(...vals) < 0 && Math.max(...vals) > 0;
  const pos = css('--s1') || '#26607F', neg = css('--s3') || '#A32F4C', base = css('--surface') || '#fff';
  const tinte = (v) => {
    if (v == null || !isFinite(v)) return 'transparent';
    let f, c;
    if (div) { const m = Math.max(Math.abs(lo), Math.abs(hi)) || 1; f = Math.min(1, Math.abs(v) / m); c = v >= 0 ? pos : neg; }
    else { f = (v - lo) / (hi - lo || 1); c = pos; }
    return `color-mix(in srgb, ${c} ${Math.round(f * 85)}%, ${base})`;
  };
  let g = '';
  b.columnas.forEach((c, j) => { g += `<text class="tc" transform="translate(${ml + j * cw + cw / 2},${mt - 6}) rotate(-40)">${esc(c.length > 16 ? c.slice(0, 15) + '…' : c)}</text>`; });
  b.filas.forEach((f, i) => {
    g += `<text class="ty" x="${ml - 6}" y="${mt + i * ch + ch / 2 + 4}">${esc(f.length > 30 ? f.slice(0, 29) + '…' : f)}</text>`;
    b.columnas.forEach((c, j) => {
      const v = b.valores[i][j];
      g += `<rect x="${ml + j * cw}" y="${mt + i * ch}" width="${cw - 1}" height="${ch - 1}" fill="${tinte(v)}"><title>${esc(f)} × ${esc(c)}: ${num(v)}</title></rect>`;
      if (nc <= 14 && nf <= 20 && v != null) g += `<text class="tv" x="${ml + j * cw + cw / 2}" y="${mt + i * ch + ch / 2 + 4}">${num(v, 2)}</text>`;
    });
  });
  return `<svg class="mt-g calor" viewBox="0 0 ${W} ${alto}">${g}</svg>`;
}

function svgDispersion(b) {
  const xs = b.x, ys = b.y;
  const [x0, x1] = extremos([xs]);
  const [y0, y1] = extremos([ys]);
  const sx = (v) => M.l + ((v - x0) / (x1 - x0)) * (W - M.l - M.r);
  const sy = (v) => H - M.b - ((v - y0) / (y1 - y0)) * (H - M.t - M.b);
  let g = ejes(sx, sy, x0, x1, y0, y1, 'num', []);
  xs.forEach((x, i) => {
    if (x == null || ys[i] == null) return;
    g += `<circle cx="${sx(x).toFixed(1)}" cy="${sy(ys[i]).toFixed(1)}" r="2.6" fill="${color(0)}" opacity=".65">${b.textos ? `<title>${esc(b.textos[i])}: (${num(x)}, ${num(ys[i])})</title>` : ''}</circle>`;
  });
  if (b.recta) {
    const [m, c] = b.recta;
    g += `<line x1="${sx(x0)}" y1="${sy(m * x0 + c)}" x2="${sx(x1)}" y2="${sy(m * x1 + c)}" stroke="${color(1)}" stroke-width="1.6" stroke-dasharray="6 4"/>`;
  }
  g += `<text class="tx" x="${(W + M.l) / 2}" y="${H}">${esc(b.etiqueta_x)}</text>`;
  return `<svg class="mt-g" viewBox="0 0 ${W} ${H + 6}">${g}<text class="ty" x="${M.l}" y="9" text-anchor="start">${esc(b.etiqueta_y)}</text></svg>`;
}

/* tarjetita del mouse para los gráficos de líneas */
function activarTooltip(svg) {
  if (!svg.dataset.d) return;
  const d = JSON.parse(decodeURIComponent(svg.dataset.d));
  const xs = aNum(d.x, d.t);
  const x0 = +svg.dataset.x0, x1 = +svg.dataset.x1;
  const tip = document.createElement('div');
  tip.className = 'mt-tip';
  svg.parentElement.style.position = 'relative';
  svg.parentElement.appendChild(tip);
  const cur = svg.querySelector('.cursor');
  svg.addEventListener('mousemove', (e) => {
    const r = svg.getBoundingClientRect();
    const px = ((e.clientX - r.left) / r.width) * W;
    const xv = x0 + ((px - M.l) / (W - M.l - M.r)) * (x1 - x0);
    let best = 0, dist = Infinity;
    xs.forEach((x, i) => { const dd = Math.abs(x - xv); if (dd < dist) { dist = dd; best = i; } });
    const sxp = M.l + ((xs[best] - x0) / (x1 - x0 || 1)) * (W - M.l - M.r);
    cur.setAttribute('x1', sxp); cur.setAttribute('x2', sxp);
    tip.innerHTML = `<b>${esc(d.x[best])}</b>` + Object.entries(d.s).map(([n, v], i) => `<div><i style="background:${color(i)}"></i>${esc(n)}: ${num(v[best])}</div>`).join('');
    tip.style.display = 'block';
    const izq = (e.clientX - r.left) > r.width * 0.6;
    tip.style.left = izq ? 'auto' : `${e.clientX - r.left + 14}px`;
    tip.style.right = izq ? `${r.right - e.clientX + 14}px` : 'auto';
    tip.style.top = `${e.clientY - r.top + 10}px`;
  });
  svg.addEventListener('mouseleave', () => { tip.style.display = 'none'; cur.setAttribute('x1', -10); cur.setAttribute('x2', -10); });
}

export function refrescar() { pintarFicha(); }
