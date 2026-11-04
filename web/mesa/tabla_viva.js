/* tabla_viva.js — Tablas y matrices de resultados que se pueden explorar y SELECCIONAR.
 *
 * Un solo componente para cualquier resultado tabular de la plataforma: la tabla de
 * coeficientes de una regresión, el ranking de un torneo, el universo de modelos (miles de
 * filas), una matriz de correlación o de Granger. Lo usan la pantalla Métodos
 * (web/mesa/metodos.js) y el mockup de la Mesa de investigación (el armador lo inyecta).
 *
 * Qué permite:
 *   · filtrar por columna  (escribí  <0.05   >0   =ARDL   !=VAR   o un texto)
 *   · agrupar por una columna y resumir otra  (n, media, mediana, mín, máx, suma, % < α, % > 0)
 *     — el resumen es otra tabla viva, que también se selecciona
 *   · seleccionar COLUMNAS (clic en el encabezado; hasta 2), FILAS (clic en la fila,
 *     shift = rango) o ambas: la intersección es la selección
 *   · ver la selección como histograma, barras, líneas o dispersión (2 columnas)
 *   · guardarla: como serie temporal (si la tabla tiene fechas) o como vector de resultados
 *
 * Uso:  montarTabla(contenedor, { nombre, columnas, filas, descripcion }, {
 *          origen: 'texto de procedencia',
 *          alGuardarSerie: async ({ nombre, fechas, valores, procedencia }) => '…mensaje',
 *          alGuardarVector: async ({ nombre, etiquetas, valores, procedencia }) => '…mensaje' })
 *
 * Todo texto se escapa. No depende de nada más que de los tokens de color del tema.
 */

const escT = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const numT = (v) => {
  if (v == null || v === '' || typeof v !== 'number' || !isFinite(v)) return v == null ? '—' : escT(v);
  const a = Math.abs(v);
  if (a !== 0 && (a < 1e-3 || a >= 1e7)) return v.toExponential(2).replace('.', ',');
  if (v === 0) return '0';
  return v.toLocaleString('es-AR', { maximumFractionDigits: a >= 100 ? 1 : a >= 1 ? 3 : 4 });
};
const esFecha = (v) => typeof v === 'string' && /^\d{4}-\d{2}(-\d{2})?/.test(v);
const POR_PAGINA = 100;
const AGG = {
  n: (v) => v.length,
  media: (v) => (v.length ? v.reduce((s, x) => s + x, 0) / v.length : null),
  mediana: (v) => { if (!v.length) return null; const o = v.slice().sort((a, b) => a - b); const m = o.length >> 1; return o.length % 2 ? o[m] : (o[m - 1] + o[m]) / 2; },
  'mín': (v) => (v.length ? Math.min(...v) : null),
  'máx': (v) => (v.length ? Math.max(...v) : null),
  suma: (v) => v.reduce((s, x) => s + x, 0),
  '% < α': (v, a) => (v.length ? (100 * v.filter((x) => x < a).length) / v.length : null),
  '% > 0': (v) => (v.length ? (100 * v.filter((x) => x > 0).length) / v.length : null),
};

function pasaFiltro(v, f) {
  if (!f) return true;
  const m = f.match(/^\s*(<=|>=|!=|<|>|=)\s*(.+?)\s*$/);
  if (m) {
    const [, op, raw] = m;
    const x = parseFloat(raw.replace(',', '.'));
    const num = typeof v === 'number' && !Number.isNaN(x) && /^[-+]?[\d.,e]+$/i.test(raw);
    const a = num ? v : String(v ?? '').toLowerCase(), b = num ? x : raw.toLowerCase();
    return { '<': a < b, '>': a > b, '<=': a <= b, '>=': a >= b, '=': a == b, '!=': a != b }[op]; // eslint-disable-line eqeqeq
  }
  return String(Array.isArray(v) ? v.join(', ') : v ?? '').toLowerCase().includes(f.toLowerCase());
}

export function montarTabla(cont, conjunto, opciones = {}) {
  if (!document.getElementById('tv-css')) {
    const st = document.createElement('style'); st.id = 'tv-css'; st.textContent = CSS_TABLA_VIVA; document.head.appendChild(st);
  }
  const pila = [conjunto]; // tablas derivadas por «agrupar»: se puede volver
  let t, filtros, colsSel, filasSel, ultimaFila, pagina, vista, mensaje;
  function reiniciar(tabla) {
    t = tabla; filtros = {}; colsSel = []; filasSel = new Set(); ultimaFila = null; pagina = 0; vista = null; mensaje = '';
  }
  reiniciar(conjunto);

  const numericas = () => t.columnas.map((_, j) => t.filas.some((f) => typeof f[j] === 'number'));
  const colFecha = () => t.columnas.findIndex((_, j) => t.filas.length && t.filas.slice(0, 20).every((f) => esFecha(f[j])));
  const colEtiqueta = () => {
    const nums = numericas();
    const j = t.columnas.findIndex((_, k) => !nums[k] && k !== colFecha());
    return j;
  };
  function visibles() {
    const idx = [];
    t.filas.forEach((f, i) => { if (t.columnas.every((_, j) => pasaFiltro(f[j], filtros[j]))) idx.push(i); });
    return idx;
  }
  function filtroTexto() {
    const p = Object.entries(filtros).filter(([, v]) => v).map(([j, v]) => `${t.columnas[j]} ${/^[<>=!]/.test(v) ? v : '∋ ' + v}`);
    return p.length ? ` (filtro: ${p.join(', ')})` : '';
  }
  /** La selección actual como datos. */
  function seleccion() {
    const vis = visibles();
    const filas = filasSel.size ? vis.filter((i) => filasSel.has(i)) : vis;
    const nums = numericas();
    const jEt = colEtiqueta(), jF = colFecha();
    const etiq = (i) => (jEt >= 0 ? String(t.filas[i][jEt]) : jF >= 0 ? t.filas[i][jF] : `fila ${i + 1}`);
    if (colsSel.length) {
      const cols = colsSel.filter((j) => nums[j]);
      return {
        modo: 'columnas', cols, filas,
        etiquetas: filas.map(etiq),
        fechas: jF >= 0 ? filas.map((i) => t.filas[i][jF]) : null,
        valores: cols.map((j) => filas.map((i) => (typeof t.filas[i][j] === 'number' ? t.filas[i][j] : null))),
        nombre: cols.map((j) => t.columnas[j]).join(' vs '),
      };
    }
    if (filasSel.size) {
      // filas sin columna: cada fila es un vector a lo ancho (una fila de una matriz)
      const cols = t.columnas.map((_, j) => j).filter((j) => nums[j]);
      return {
        modo: 'filas', cols, filas,
        etiquetas: cols.map((j) => t.columnas[j]),
        fechas: null,
        valores: filas.map((i) => cols.map((j) => (typeof t.filas[i][j] === 'number' ? t.filas[i][j] : null))),
        nombre: filas.map(etiq).join(' · '),
        nombresFilas: filas.map(etiq),
      };
    }
    return null;
  }

  function render() {
    const vis = visibles();
    const nums = numericas();
    const paginas = Math.max(1, Math.ceil(vis.length / POR_PAGINA));
    pagina = Math.min(pagina, paginas - 1);
    const muestra = vis.slice(pagina * POR_PAGINA, (pagina + 1) * POR_PAGINA);
    const sel = seleccion();
    const nsel = sel ? (sel.modo === 'columnas' ? sel.filas.length : sel.filas.length) : 0;
    const colsOpc = t.columnas.map((c, j) => `<option value="${j}">${escT(c)}</option>`).join('');
    const numOpc = t.columnas.map((c, j) => (nums[j] ? `<option value="${j}">${escT(c)}</option>` : '')).join('');
    cont.innerHTML = `
      <div class="tv-barra">
        ${pila.length > 1 ? '<button type="button" class="tv-b" data-tv="volver">← volver</button>' : ''}
        <span class="tv-n">${vis.length.toLocaleString('es-AR')} de ${t.filas.length.toLocaleString('es-AR')} filas</span>
        <span class="tv-sep"></span>
        <label>Agrupar por <select data-tv="gcol"><option value="">—</option>${colsOpc}</select></label>
        <label>resumir <select data-tv="gval">${numOpc}</select></label>
        <label>con <select data-tv="gagg">${Object.keys(AGG).map((k) => `<option>${escT(k)}</option>`).join('')}</select></label>
        <label>α <input data-tv="alfa" value="0.05" size="4"></label>
        <button type="button" class="tv-b" data-tv="agrupar">Agrupar</button>
      </div>
      <div class="tv-scroll"><table class="tv-t">
        <thead><tr><th class="tv-i">#</th>${t.columnas.map((c, j) => `<th data-col="${j}" class="${colsSel.includes(j) ? 'sel' : ''} ${nums[j] ? 'num' : ''}" title="Clic: seleccionar la columna${nums[j] ? '' : ' (no numérica)'}">${escT(c)}${colsSel.includes(j) ? ` <b>${colsSel.indexOf(j) === 0 ? 'x' : 'y'}</b>` : ''}</th>`).join('')}</tr>
        <tr class="tv-f"><th></th>${t.columnas.map((c, j) => `<th><input data-filtro="${j}" value="${escT(filtros[j] || '')}" placeholder="${nums[j] ? 'ej. <0.05' : 'ej. =ARDL'}" aria-label="Filtrar ${escT(c)}"></th>`).join('')}</tr></thead>
        <tbody>${muestra.map((i) => `<tr data-fila="${i}" class="${filasSel.has(i) ? 'sel' : ''}"><td class="tv-i">${i + 1}</td>${t.filas[i].map((v, j) => `<td class="${typeof v === 'number' ? 'n' : ''} ${colsSel.includes(j) ? 'csel' : ''}">${typeof v === 'number' ? numT(v) : escT(Array.isArray(v) ? v.join(', ') : v)}</td>`).join('')}</tr>`).join('')}</tbody>
      </table></div>
      ${paginas > 1 ? `<div class="tv-pag"><button type="button" class="tv-b" data-tv="ant" ${pagina ? '' : 'disabled'}>‹</button><span>página ${pagina + 1} de ${paginas}</span><button type="button" class="tv-b" data-tv="sig" ${pagina < paginas - 1 ? '' : 'disabled'}>›</button></div>` : ''}
      <div class="tv-sel ${sel ? 'on' : ''}">
        ${sel ? `<span><b>Selección:</b> ${sel.modo === 'columnas' ? `columna${sel.cols.length > 1 ? 's' : ''} «${escT(sel.nombre)}»` : `${sel.filas.length} fila${sel.filas.length > 1 ? 's' : ''} (a lo ancho)`} · ${nsel.toLocaleString('es-AR')} ${sel.modo === 'columnas' ? 'valores' : 'vectores'}${escT(filtroTexto())}</span>
        <span class="tv-acc">
          <button type="button" class="tv-b" data-ver="hist">Histograma</button>
          <button type="button" class="tv-b" data-ver="barras">Barras</button>
          ${sel.fechas || sel.modo === 'columnas' ? '<button type="button" class="tv-b" data-ver="lineas">Líneas</button>' : ''}
          ${sel.modo === 'columnas' && sel.cols.length === 2 ? '<button type="button" class="tv-b" data-ver="disp">Dispersión</button>' : ''}
          ${sel.fechas && opciones.alGuardarSerie ? '<button type="button" class="tv-b pri" data-tv="serie">Guardar como serie</button>' : ''}
          ${opciones.alGuardarVector ? '<button type="button" class="tv-b pri" data-tv="vector">Guardar como vector</button>' : ''}
          <button type="button" class="tv-b" data-tv="copiar">Copiar</button>
          <button type="button" class="tv-b" data-tv="limpiar">Limpiar</button>
        </span>` : '<span class="tv-ayuda">Clic en un encabezado = columna (hasta 2) · clic en una fila = fila (shift = rango) · filtrá con <code>&lt;0.05</code>, <code>=ARDL</code>, <code>&gt;0</code> o texto.</span>'}
      </div>
      ${mensaje ? `<div class="tv-msg">${escT(mensaje)}</div>` : ''}
      ${vista && sel ? `<div class="tv-graf">${graficar(vista, sel)}</div>` : ''}`;
  }

  /* ── mini gráficos de la selección (SVG propio sobre los tokens del tema) ── */
  function graficar(tipo, sel) {
    const nCats = tipo === 'barras' || tipo === 'lineas' ? (sel.fechas || sel.etiquetas).length : 0;
    const rotar = nCats > 8 && !sel.fechas;
    const W = 640, H = rotar ? 270 : 220, L = rotar ? 84 : 52, Rr = 14, T = 10, B = rotar ? 76 : 26;
    const series = sel.modo === 'columnas' ? sel.valores : sel.valores;
    const nombres = sel.modo === 'columnas' ? sel.cols.map((j) => t.columnas[j]) : sel.nombresFilas;
    const col = (k) => `var(--s${(k % 5) + 1})`;
    const ext = (arrs) => { const v = arrs.flat().filter((x) => x != null && isFinite(x)); if (!v.length) return [0, 1]; let lo = Math.min(...v), hi = Math.max(...v); if (lo === hi) { lo -= 1; hi += 1; } const p = (hi - lo) * 0.06; return [lo - p, hi + p]; };
    const eje = (sy, y0, y1) => [y0, (y0 + y1) / 2, y1].map((v) => `<line x1="${L}" x2="${W - Rr}" y1="${sy(v)}" y2="${sy(v)}" class="tv-grid"/><text x="${L - 5}" y="${sy(v) + 3}" text-anchor="end">${numT(v)}</text>`).join('') + (y0 < 0 && y1 > 0 ? `<line x1="${L}" x2="${W - Rr}" y1="${sy(0)}" y2="${sy(0)}" class="tv-cero"/>` : '');
    let g = '';
    if (tipo === 'disp') {
      const [xs, ys] = sel.valores;
      const [x0, x1] = ext([xs]), [y0, y1] = ext([ys]);
      const sx = (v) => L + ((v - x0) / (x1 - x0)) * (W - L - Rr), sy = (v) => H - B - ((v - y0) / (y1 - y0)) * (H - T - B);
      g = eje(sy, y0, y1) + [x0, (x0 + x1) / 2, x1].map((v) => `<text x="${sx(v)}" y="${H - 8}" text-anchor="middle">${numT(v)}</text>`).join('');
      xs.forEach((x, i) => { if (x != null && ys[i] != null) g += `<circle cx="${sx(x).toFixed(1)}" cy="${sy(ys[i]).toFixed(1)}" r="2.6" fill="${col(0)}" opacity=".6"><title>${escT(sel.etiquetas[i])}: (${numT(x)}, ${numT(ys[i])})</title></circle>`; });
      return `<svg viewBox="0 0 ${W} ${H}" class="tv-svg">${g}</svg><div class="tv-ley">x: ${escT(nombres[0])} · y: ${escT(nombres[1])} · n=${xs.length}</div>`;
    }
    if (tipo === 'hist') {
      const todos = series.flat().filter((x) => x != null && isFinite(x));
      if (!todos.length) return '<p class="tv-ayuda">Sin valores numéricos.</p>';
      const o = todos.slice().sort((a, b) => a - b); const lo = o[Math.floor(o.length * 0.01)], hi = o[Math.ceil(o.length * 0.99) - 1] ?? o[o.length - 1];
      const nb = 24, w = (hi - lo) / nb || 1;
      const cnt = series.map((s) => { const c = new Array(nb).fill(0); s.forEach((v) => { if (v == null || !isFinite(v)) return; c[Math.min(nb - 1, Math.max(0, Math.floor((v - lo) / w)))]++; }); return c; });
      const [, y1] = ext(cnt); const sx = (v) => L + ((v - lo) / (hi - lo || 1)) * (W - L - Rr), sy = (v) => H - B - (v / y1) * (H - T - B);
      g = eje(sy, 0, y1) + [lo, (lo + hi) / 2, hi].map((v) => `<text x="${sx(v)}" y="${H - 8}" text-anchor="middle">${numT(v)}</text>`).join('');
      const bw = (W - L - Rr) / nb / cnt.length;
      cnt.forEach((c, k) => c.forEach((v, i) => { g += `<rect x="${sx(lo + i * w) + k * bw}" y="${sy(v)}" width="${Math.max(1, bw - 1)}" height="${H - B - sy(v)}" fill="${col(k)}" opacity=".85"><title>${numT(lo + i * w)} a ${numT(lo + (i + 1) * w)}: ${v}</title></rect>`; }));
      return `<svg viewBox="0 0 ${W} ${H}" class="tv-svg">${g}</svg><div class="tv-ley">${nombres.map((n, k) => `<i style="background:${col(k)}"></i>${escT(n)}`).join(' ')} · ${todos.length.toLocaleString('es-AR')} valores (1 % de colas fuera)</div>`;
    }
    // barras y líneas: categorías = etiquetas (columnas) o filas
    const cats = sel.fechas || sel.etiquetas;
    const n = cats.length;
    const [y0, y1] = ext(series.map((s) => s.concat([0])));
    const sy = (v) => H - B - ((v - y0) / (y1 - y0)) * (H - T - B);
    g = eje(sy, y0, y1);
    const paso = rotar ? 1 : Math.ceil(n / 10);
    if (tipo === 'lineas') {
      const sx = (i) => L + (n > 1 ? (i / (n - 1)) * (W - L - Rr) : 0);
      series.forEach((s, k) => { let d = '', pl = false; s.forEach((v, i) => { if (v == null || !isFinite(v)) { pl = false; return; } d += `${pl ? 'L' : 'M'}${sx(i).toFixed(1)},${sy(v).toFixed(1)}`; pl = true; }); g += `<path d="${d}" fill="none" stroke="${col(k)}" stroke-width="1.6"/>`; });
      cats.forEach((c, i) => { if (i % paso === 0) g += `<text x="${sx(i)}" y="${H - 8}" text-anchor="middle">${escT(String(c).slice(0, 10))}</text>`; });
    } else {
      const ancho = (W - L - Rr) / Math.max(1, n), bw = Math.max(1, (ancho - 2) / series.length);
      series.forEach((s, k) => s.forEach((v, i) => { if (v == null || !isFinite(v)) return; g += `<rect x="${L + i * ancho + 1 + k * bw}" y="${sy(Math.max(0, v))}" width="${bw - 0.5}" height="${Math.max(0.5, Math.abs(sy(v) - sy(0)))}" fill="${col(k)}"><title>${escT(cats[i])}: ${numT(v)}</title></rect>`; }));
      cats.forEach((c, i) => {
        if (rotar) { g += `<text transform="translate(${L + i * ancho + ancho / 2},${H - B + 10}) rotate(-40)" text-anchor="end">${escT(String(c).slice(0, 16))}</text>`; return; }
        if (i % paso === 0) g += `<text x="${L + i * ancho + ancho / 2}" y="${H - 8}" text-anchor="middle">${escT(String(c).slice(0, 12))}</text>`;
      });
    }
    return `<svg viewBox="0 0 ${W} ${H}" class="tv-svg">${g}</svg><div class="tv-ley">${nombres.map((nn, k) => `<i style="background:${col(k)}"></i>${escT(nn)}`).join(' ')}</div>`;
  }

  /* ── eventos ── */
  cont.addEventListener('click', async (e) => {
    const th = e.target.closest('th[data-col]');
    if (th) { const j = +th.dataset.col; colsSel = colsSel.includes(j) ? colsSel.filter((x) => x !== j) : [...colsSel, j].slice(-2); mensaje = ''; render(); return; }
    const tr = e.target.closest('tr[data-fila]');
    if (tr) {
      const i = +tr.dataset.fila;
      if (e.shiftKey && ultimaFila != null) { const vis = visibles(); const a = vis.indexOf(ultimaFila), b = vis.indexOf(i); vis.slice(Math.min(a, b), Math.max(a, b) + 1).forEach((k) => filasSel.add(k)); }
      else { filasSel.has(i) ? filasSel.delete(i) : filasSel.add(i); }
      ultimaFila = i; mensaje = ''; render(); return;
    }
    const b = e.target.closest('[data-tv],[data-ver]');
    if (!b) return;
    if (b.dataset.ver) { vista = b.dataset.ver; render(); return; }
    const a = b.dataset.tv;
    if (a === 'ant') { pagina--; render(); }
    else if (a === 'sig') { pagina++; render(); }
    else if (a === 'limpiar') { colsSel = []; filasSel.clear(); vista = null; render(); }
    else if (a === 'volver') { pila.pop(); reiniciar(pila[pila.length - 1]); render(); }
    else if (a === 'agrupar') agrupar();
    else if (a === 'copiar') copiar();
    else if (a === 'serie' || a === 'vector') guardar(a);
  });
  cont.addEventListener('change', (e) => {
    const f = e.target.dataset.filtro;
    if (f != null) { filtros[f] = e.target.value.trim(); pagina = 0; render(); }
  });
  cont.addEventListener('keydown', (e) => { if (e.key === 'Enter' && e.target.dataset.filtro != null) e.target.blur(); });

  function agrupar() {
    const gc = cont.querySelector('[data-tv="gcol"]').value, gv = cont.querySelector('[data-tv="gval"]').value;
    const ag = cont.querySelector('[data-tv="gagg"]').value, alfa = parseFloat(cont.querySelector('[data-tv="alfa"]').value.replace(',', '.')) || 0.05;
    if (gc === '' || gv === '') { mensaje = 'Elegí por qué columna agrupar y qué columna numérica resumir.'; render(); return; }
    const grupos = new Map();
    visibles().forEach((i) => { const k = String(t.filas[i][gc]); const v = t.filas[i][gv]; if (!grupos.has(k)) grupos.set(k, []); if (typeof v === 'number' && isFinite(v)) grupos.get(k).push(v); });
    const filas = [...grupos.entries()].map(([k, v]) => [k, v.length, AGG[ag](v, alfa)]).sort((a, b) => (b[2] ?? -Infinity) - (a[2] ?? -Infinity));
    const nueva = { nombre: `${t.nombre} · ${ag} de ${t.columnas[gv]} por ${t.columnas[gc]}`, columnas: [t.columnas[gc], 'n', `${ag} ${t.columnas[gv]}`], filas };
    pila.push(nueva); reiniciar(nueva); colsSel = [2]; vista = 'barras'; render();
  }
  function texto() {
    const sel = seleccion(); if (!sel) return '';
    if (sel.modo === 'columnas') return ['etiqueta', ...sel.cols.map((j) => t.columnas[j])].join('\t') + '\n' + sel.filas.map((_, r) => [sel.etiquetas[r], ...sel.valores.map((v) => v[r])].join('\t')).join('\n');
    return ['fila', ...sel.etiquetas].join('\t') + '\n' + sel.valores.map((v, r) => [sel.nombresFilas[r], ...v].join('\t')).join('\n');
  }
  async function copiar() {
    try { await navigator.clipboard.writeText(texto()); mensaje = 'Copiado (separado por tabulaciones: se pega en una planilla).'; }
    catch { mensaje = 'El navegador no dejó copiar.'; }
    render();
  }
  async function guardar(tipo) {
    const sel = seleccion(); if (!sel) return;
    const procedencia = `${opciones.origen || ''} · ${t.nombre} · ${sel.nombre}${filtroTexto()}`.slice(0, 480);
    try {
      if (tipo === 'serie') {
        const j = 0;
        mensaje = await opciones.alGuardarSerie({ nombre: `${sel.nombre} · ${t.nombre}${filtroTexto()}`.slice(0, 80), fechas: sel.fechas, valores: sel.valores[j], procedencia });
      } else {
        const valores = sel.modo === 'columnas' ? sel.valores[0] : sel.valores[0];
        const etiquetas = sel.modo === 'columnas' ? sel.etiquetas : sel.etiquetas;
        mensaje = await opciones.alGuardarVector({ nombre: `${sel.nombre} · ${t.nombre}${filtroTexto()}`.slice(0, 80), etiquetas, valores, procedencia });
      }
    } catch (err) { mensaje = `No se pudo guardar: ${err.message}`; }
    render();
  }
  render();
  return { seleccion };
}

/** Una matriz (mapa de calor) como tabla viva: primera columna = filas, resto = columnas. */
export function matrizComoConjunto(b) {
  return { nombre: b.titulo, columnas: ['', ...b.columnas], filas: b.filas.map((f, i) => [f, ...b.valores[i]]) };
}

/** Un bloque `tabla` del contrato como conjunto. */
export function tablaComoConjunto(b) {
  return { nombre: b.titulo, columnas: b.columnas, filas: b.filas, descripcion: b.nota || '' };
}

export const CSS_TABLA_VIVA = `
.tv-barra{display:flex;flex-wrap:wrap;gap:6px 10px;align-items:center;font-size:11.5px;color:var(--ink-2);margin-bottom:6px}
.tv-barra label{display:flex;gap:4px;align-items:center}
.tv-barra select,.tv-barra input{font:inherit;font-size:11.5px;padding:2px 5px;border:1px solid var(--line);border-radius:4px;background:var(--surface-2);color:var(--ink);min-width:0}
.tv-n{font-family:var(--mono);color:var(--ink-dim)}
.tv-sep{flex:1}
.tv-b{font:inherit;font-size:11.5px;padding:3px 8px;border:1px solid var(--line);border-radius:5px;background:var(--surface);color:var(--ink-2);cursor:pointer}
.tv-b:hover{border-color:var(--ink-faint);color:var(--ink)}
.tv-b.pri{background:var(--accent);border-color:var(--accent);color:var(--accent-ink);font-weight:600}
.tv-b[disabled]{opacity:.4;cursor:default}
.tv-scroll{overflow:auto;max-height:380px;border:1px solid var(--line-soft);border-radius:6px}
.tv-t{border-collapse:collapse;width:100%;font-size:11.5px}
.tv-t th{position:sticky;top:0;background:var(--surface-2);text-align:left;color:var(--ink-dim);padding:5px 7px;border-bottom:1px solid var(--line);font-weight:600;cursor:pointer;white-space:nowrap;z-index:1}
.tv-t th.num::after{content:" #";color:var(--ink-faint);font-weight:400}
.tv-t th.sel{background:var(--accent-soft);color:var(--ink)}
.tv-t th b{font-family:var(--mono);color:var(--accent)}
.tv-t tr.tv-f th{top:27px;padding:3px 5px;cursor:default;background:var(--surface)}
.tv-t tr.tv-f input{width:100%;min-width:56px;font:inherit;font-size:11px;padding:2px 5px;border:1px solid var(--line-soft);border-radius:4px;background:var(--surface-2);color:var(--ink)}
.tv-t td{padding:3px 7px;border-bottom:1px solid var(--line-soft);white-space:nowrap}
.tv-t td.n{font-family:var(--mono);text-align:right;font-variant-numeric:tabular-nums}
.tv-t td.csel{background:color-mix(in srgb,var(--accent) 9%,transparent)}
.tv-t tbody tr{cursor:pointer}
.tv-t tbody tr:hover td{background:var(--surface-2)}
.tv-t tbody tr.sel td{background:var(--accent-soft)}
.tv-i{color:var(--ink-faint);font-family:var(--mono);width:1%}
.tv-pag{display:flex;gap:8px;align-items:center;justify-content:flex-end;font-size:11.5px;color:var(--ink-dim);margin-top:5px}
.tv-sel{display:flex;flex-wrap:wrap;gap:6px 12px;align-items:center;margin-top:7px;padding:7px 9px;border-radius:6px;background:var(--surface-2);border:1px dashed var(--line);font-size:12px;color:var(--ink-2)}
.tv-sel.on{border-style:solid;border-color:var(--accent-line);background:var(--accent-soft)}
.tv-acc{display:flex;flex-wrap:wrap;gap:5px}
.tv-ayuda{color:var(--ink-dim);font-size:11.5px}
.tv-ayuda code{font-family:var(--mono);font-size:10.5px}
.tv-msg{margin-top:6px;font-size:11.5px;color:var(--ok)}
.tv-graf{margin-top:8px}
.tv-svg{width:100%;max-width:760px;height:auto;display:block}
.tv-svg text{fill:var(--ink-dim);font-family:var(--mono);font-size:10px}
.tv-svg .tv-grid{stroke:var(--line-soft)}
.tv-svg .tv-cero{stroke:var(--ink-faint)}
.tv-ley{font-size:11px;color:var(--ink-2);margin-top:3px;display:flex;gap:4px 10px;flex-wrap:wrap;align-items:center}
.tv-ley i{display:inline-block;width:10px;height:3px;border-radius:2px;margin-right:3px}
`;
