/* app.js — arranque de la Línea de Tiempo.
 *
 * Pide GET /api/v1/historia una vez, arma los rails y conecta el motor gráfico
 * con la ficha. Todo lo que se muestra sale de los datos: los conteos de cada
 * capa se CALCULAN, no se escriben a mano (si un día se escriben, mienten).
 */

import * as ficha from './ficha.js';
import { dibujar, encuadrar, montar as montarGrafico } from './grafico.js';
import {
  cambiar, escuchar, estado, eventoPorId, eventosDelRail, fijarRango,
} from './estado.js';

const $ = (sel) => document.querySelector(sel);
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => (
  { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
));

/* ─────────────────────────────────────────── rail izquierdo: capas */

function pintarCapas() {
  const d = estado.datos;
  const cats = d.vocabulario.categorias || {};

  $('#capas-inst').innerHTML = [
    ['pres', 'Presidencias', d.presidencias.length, '--s4'],
    ['ministros', 'Ministros de Economía', d.ministros.length, '--s5'],
    ['autoridades', 'Autoridad monetaria', d.autoridades.length, '--s1'],
  ].map(([k, nombre, n, color]) => `
    <label class="layer" style="color:var(${color}); ${n ? '' : 'opacity:.45'}">
      <input type="checkbox" data-capa="${k}" ${estado.capas[k] && n ? 'checked' : ''} ${n ? '' : 'disabled'}>
      <span class="name">${esc(nombre)}</span>
      <span class="meta">${n || 'falta'}</span>
    </label>`).join('');

  $('#capas-evt').innerHTML = Object.entries(cats).map(([id, v]) => {
    const n = d.eventos.filter((e) => e.categoria === id).length;
    return `<label class="layer" style="color:var(${v.color}); ${n ? '' : 'opacity:.45'}">
      <input type="checkbox" data-cat="${id}" ${estado.categorias.has(id) && n ? 'checked' : ''} ${n ? '' : 'disabled'}>
      <span class="swatch" style="background:var(${v.color})"></span>
      <span class="name">${esc(v.etiqueta)}</span>
      <span class="meta">${n}</span>
    </label>`;
  }).join('');

  $('#capas-nivel').innerHTML = [
    ['regimen', 'Regímenes', 'banda de fondo'],
    ['episodio', 'Episodios', 'barra con duración'],
    ['hito', 'Hitos', 'un punto en el tiempo'],
  ].map(([k, nombre, ayuda]) => {
    const n = d.eventos.filter((e) => e.nivel === k).length;
    return `<label class="layer" style="color:var(--accent)" title="${esc(ayuda)}">
      <input type="checkbox" data-nivel="${k}" ${estado.niveles.has(k) ? 'checked' : ''}>
      <span class="name">${esc(nombre)}</span>
      <span class="meta">${n}</span>
    </label>`;
  }).join('');

  // El catálogo cerrado de troncales (§2): se muestra lo que va a haber, apagado y dicho.
  const troncales = [
    ['pbipc', 'PBI per cápita', '1880'], ['inflacion', 'Inflación anual', '1900'],
    ['tcr', 'Tipo de cambio real', '1913'], ['deuda', 'Deuda pública / PBI', '1880'],
    ['resultado_primario', 'Resultado primario / PBI', '1900'], ['apertura', 'Apertura comercial', '1880'],
    ['toi', 'Términos de intercambio', '1880'], ['salario_real', 'Salario real', '1880'],
    ['desempleo', 'Desempleo', '1974'], ['poblacion', 'Población', '1880'],
  ];
  const hay = new Set((d.series || []).map((s) => s.id));
  $('#capas-series').innerHTML = troncales.map(([id, nombre, desde]) => `
    <label class="layer" style="opacity:${hay.has(id) ? 1 : 0.42}" title="${hay.has(id) ? '' : 'Todavía no construida (fase T3)'}">
      <input type="checkbox" data-serie="${id}" ${hay.has(id) ? '' : 'disabled'}>
      <span class="swatch" style="background:var(--ink-faint)"></span>
      <span class="name">${esc(nombre)}</span>
      <span class="meta">${hay.has(id) ? desde : '—'}</span>
    </label>`).join('');
  $('#cnt-series').textContent = `${hay.size}/4`;
  $('#cnt-eventos').textContent = d.estado.eventos;

  $('#nota-cobertura').innerHTML = `<b>Cobertura real:</b> hay <span class="num">${d.estado.eventos}</span> eventos entre
    <span class="num">1880</span> y <span class="num">${d.rango.eventos_hasta}</span>, y
    <span class="num">${d.estado.eventos_con_ficha}</span> tienen ficha completa. De 1936 en adelante todavía no se cargó nada,
    y ninguna de las 10 series troncales existe.`;
  $('#nota-alcance').innerHTML = `<b>Todo esto está sin verificar.</b> Las
    <span class="num">${d.estado.eventos}</span> filas y las <span class="num">${d.estado.presidencias}</span> presidencias
    nacen <code>verificado=no</code>: el sello lo pone una persona contra la fuente, nunca un script.`;

  $('#capas-inst').addEventListener('change', (ev) => {
    const k = ev.target.dataset.capa;
    if (k) cambiar({ capas: { ...estado.capas, [k]: ev.target.checked } });
  });
  $('#capas-evt').addEventListener('change', (ev) => {
    const c = ev.target.dataset.cat;
    if (!c) return;
    const s = new Set(estado.categorias);
    if (ev.target.checked) s.add(c); else s.delete(c);
    cambiar({ categorias: s });
  });
  $('#capas-nivel').addEventListener('change', (ev) => {
    const n = ev.target.dataset.nivel;
    if (!n) return;
    const s = new Set(estado.niveles);
    if (ev.target.checked) s.add(n); else s.delete(n);
    cambiar({ niveles: s });
  });
  $('#auto-zoom').addEventListener('change', (ev) => cambiar({ autoZoom: ev.target.checked }));
}

/* ─────────────────────────────────────────── rail derecho: eventos */

function pintarDetalle() {
  const e = eventoPorId(estado.seleccion);
  const caja = $('#evt-detalle');
  if (!e) {
    caja.innerHTML = '<div class="vacio">Ningún evento seleccionado. Tocá un pin, una barra o un nombre de la lista.</div>';
    return;
  }
  const cat = estado.datos.vocabulario.categorias[e.categoria] || {};
  const fechas = e.hasta && e.hasta !== e.desde ? `${e.desde} → ${e.hasta}` : e.desde;
  caja.innerHTML = `<div class="evt-card">
      <div class="evt-date">${esc(fechas)}${e.precision === 'anio' ? ' · sólo año' : ''}</div>
      <div class="evt-title">${esc(e.titulo)}</div>
      <div class="evt-desc">${esc(e.resumen)}</div>
      <dl class="kv">
        <dt>Capa</dt><dd style="color:var(${cat.color || '--ink-dim'})">${esc(cat.etiqueta || e.categoria)}</dd>
        <dt>Tipo</dt><dd>${esc(e.subtipo || '—')} · ${esc(e.nivel)}</dd>
        <dt>Gobierno</dt><dd>${esc(e.gobierno || '—')}</dd>
        ${e.fuente ? `<dt>Fuente</dt><dd>${esc(e.fuente)}</dd>` : ''}
        ${e.refs.length ? `<dt>Refs</dt><dd class="num" style="font-size:11px">${esc(e.refs.join(' · '))}</dd>` : ''}
        <dt>Estado</dt><dd>${e.verificado ? 'verificado' : 'sin verificar'}</dd>
      </dl>
      ${e.nota ? `<div class="evt-desc" style="margin-top:10px; font-size:11.5px; color:var(--ink-dim)"><b>Nota:</b> ${esc(e.nota)}</div>` : ''}
      <div style="display:flex; gap:7px; margin-top:12px">
        <button class="btn sm ${e.ficha ? 'primary' : ''}" id="ver-ficha">${e.ficha ? 'Ver ficha' : 'Ver detalle'}</button>
        <button class="btn sm" id="encuadrar">Encuadrar</button>
      </div>
    </div>`;
  $('#ver-ficha').addEventListener('click', () => ficha.abrir(e.id));
  $('#encuadrar').addEventListener('click', () => encuadrar(e, 10));
}

function pintarLista() {
  const lista = eventosDelRail();
  $('#evt-cnt').textContent = lista.length;
  const caja = $('#evt-lista');
  if (!lista.length) {
    caja.innerHTML = '<div class="vacio">Ningún evento con esas capas o esa búsqueda.</div>';
    return;
  }
  caja.innerHTML = lista.map((e) => {
    const cat = estado.datos.vocabulario.categorias[e.categoria] || {};
    return `<div class="evtlist-item" data-id="${esc(e.id)}" role="option" aria-selected="${e.id === estado.seleccion}">
      <span class="sw" style="background:var(${cat.color || '--ink-dim'})"></span>
      <span class="y">${e.anio}</span>
      <span class="t">${esc(e.titulo)}</span>
      ${e.ficha ? '<span class="fi" title="tiene ficha completa">◆</span>' : ''}
    </div>`;
  }).join('');
  caja.querySelectorAll('.evtlist-item').forEach((item) => {
    item.addEventListener('click', () => {
      const e = eventoPorId(item.dataset.id);
      cambiar({ seleccion: item.dataset.id });
      if (estado.ficha) ficha.abrir(item.dataset.id);
      else if (e && (e.anio < estado.rango[0] || e.anio > estado.rango[1])) encuadrar(e, 12);
    });
    item.addEventListener('dblclick', () => ficha.abrir(item.dataset.id));
  });
}

/* ─────────────────────────────────────────── arranque */

function pintarEncabezado() {
  const d = estado.datos;
  const porNivel = d.estado.eventos_por_nivel;
  $('#tl-sub').innerHTML = `<span class="num">1880</span>–<span class="num">${d.rango.eventos_hasta}</span> cargado ·
    <span class="num">${d.estado.eventos}</span> eventos (${porNivel.hito || 0} hitos · ${porNivel.episodio || 0} episodios ·
    ${porNivel.regimen || 0} regímenes) · <span class="num">${d.estado.presidencias}</span> presidencias ·
    <span class="num">${d.estado.eventos_con_ficha}</span> fichas · series troncales: pendientes`;
  $('#chip-eventos').textContent = `${d.estado.eventos} eventos · ${d.estado.referencias} obras`;
  $('#chip-verif').textContent = `${d.estado.eventos_verificados}/${d.estado.eventos} verificados`;
}

function conectarControles() {
  document.querySelectorAll('#rangos button').forEach((b) => b.addEventListener('click', () => {
    const [a, z] = b.dataset.rango.split(',').map(Number);
    fijarRango(a, z);
  }));
  $('#zoom-reset').addEventListener('click', () => fijarRango(1880, estado.datos.rango.eventos_hasta));
  $('#evt-buscar').addEventListener('input', (ev) => cambiar({ busqueda: ev.target.value }));
  // el tema lo maneja /web/estilo/tema.js: es del usuario y lo comparten los dos
  // módulos. Hay que redibujar porque el SVG lee los colores del CSS al pintarse.
  $('#tema').addEventListener('click', () => { window.CuevaTema.alternar(); dibujar(); });
  window.addEventListener('resize', () => dibujar());
}

/** Abrir el index.html con doble clic no funciona: hay que servirlo. Que lo diga la pantalla. */
function avisar(titulo, cuerpo) {
  $('#tl-sub').textContent = titulo;
  $('#tl-canvas').innerHTML = `<div class="note" style="max-width:62ch; margin:30px auto">
      <span>⚠</span><div>${cuerpo}</div></div>`;
}

async function arrancar() {
  let r;
  try {
    r = await fetch('/api/v1/historia');
  } catch (err) {
    avisar('no hay servidor respondiendo', `No pude pedir <code>/api/v1/historia</code> (${esc(err.message)}).
      ¿Está levantada la app? <code>scripts\\levantar_cueva.bat</code>`);
    return;
  }
  if (!r.ok) {
    avisar(`/api/v1/historia respondió ${r.status}`, `El servidor está, pero la ruta falló con
      <code>${r.status}</code>. Mirá la consola del servidor.`);
    return;
  }
  const datos = await r.json();
  estado.datos = datos;
  estado.categorias = new Set(Object.keys(datos.vocabulario.categorias || {}));
  estado.rango = [1880, datos.rango.eventos_hasta];

  montarGrafico({
    svg: $('#tlsvg'),
    tip: $('#tl-tip'),
    canvas: $('#tl-canvas'),
    zoomLbl: $('#zoom-lbl'),
    onSeleccion: (id) => {
      cambiar({ seleccion: id });
      if (estado.ficha) ficha.abrir(id);
    },
    onFicha: (id) => ficha.abrir(id),
  });
  ficha.montar($('#ficha'));

  pintarEncabezado();
  pintarCapas();
  conectarControles();

  escuchar(() => { dibujar(); pintarDetalle(); pintarLista(); });
  dibujar();
  pintarDetalle();
  pintarLista();

  // permalink: /tiempo/<id> abre con la ficha puesta
  const id = decodeURIComponent(location.pathname.replace(/^\/tiempo\/?/, ''));
  if (id) ficha.abrir(id);
}

arrancar();
