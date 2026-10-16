/* grafico.js — el motor SVG de la línea de tiempo.
 *
 * Portado y ordenado desde docs/mockup/cueva-mockup.html (el mockup es la
 * especificación viva; el documento manda sobre el mockup). SVG propio y no
 * Plotly porque lo que hay que dibujar —bandas de gobierno, regímenes que se
 * superponen en carriles, jerarquía de eventos y zoom semántico— es justo lo
 * que en una librería de gráficos se vuelve incómodo.
 *
 * Mientras no haya series troncales (fase T3), el espacio del gráfico NO se
 * rellena con nada inventado: se declara vacío y la altura se le devuelve a los
 * carriles de eventos, que es lo que hoy sí tiene datos con fuente.
 */

import {
  LIMITE, cambiar, estado, eventoPorId, eventosVisibles, fijarRango, nivelesVisibles,
} from './estado.js';

const W = 1000;
const PAD = { l: 58, r: 18 };
const NS = 'http://www.w3.org/2000/svg';

let H = 480;
let geo = { carriles: [], regimenes: [], pres: null, series: null, mini: null, base: 0 };
let arrastre = null;
let refs = {};

/* ───────────────────────────────────────────────── utilidades */

function el(tag, attrs = {}) {
  const n = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v);
  return n;
}
function texto(t, attrs = {}) {
  const n = el('text', attrs);
  n.textContent = t;
  return n;
}
function cssv(nombre) {
  return getComputedStyle(document.documentElement).getPropertyValue(nombre).trim();
}
function colorCategoria(cat) {
  const v = estado.datos?.vocabulario?.categorias?.[cat];
  return cssv(v?.color || '--ink-dim');
}
function etiquetaCategoria(cat) {
  return estado.datos?.vocabulario?.categorias?.[cat]?.etiqueta || cat;
}
/* Nombres cortos para el margen izquierdo: 54 px no dan para «Monetarios y cambiarios». */
const ABREV_CAT = {
  monetario: 'MONETARIOS', fiscal: 'FISCALES', externo: 'S. EXTERNO', crisis: 'CRISIS',
  politico: 'POLÍTICOS', social: 'SOCIALES', internacional: 'INTERNAC.',
};
const ABREV_SUB = {
  regimen_cambiario: 'CONVERTIB.', creacion_institucion: 'INSTITUC.', control_cambios: 'CONTROL $',
  cambio_moneda: 'MONEDA', plan_estabilizacion: 'PLANES', norma: 'NORMAS', otro: 'OTROS',
};
/** Recorta un título al ancho real disponible; si no entra nada legible, devuelve ''. */
function recortar(txt, ancho, px = 5.2) {
  const n = Math.floor((ancho - 10) / px);
  if (n < 5) return '';
  return txt.length <= n ? txt : `${txt.slice(0, n - 1)}…`;
}
/** Etiqueta con fondo: los carriles se cruzan y sin halo dos títulos se vuelven ilegibles. */
function etiquetaConFondo(grupo, txt, { x: ex, y: ey, ancla = 'start', color, negrita = false }) {
  const w = txt.length * 5.3 + 6;
  grupo.appendChild(el('rect', {
    x: ancla === 'end' ? ex - w + 3 : ex - 3, y: ey - 9, width: w, height: 12, rx: 2,
    fill: cssv('--surface'), 'fill-opacity': 0.82,
  }));
  grupo.appendChild(texto(txt, {
    x: ex, y: ey, fill: color, 'font-size': 10, 'font-weight': negrita ? 600 : 400,
    'text-anchor': ancla, class: 'lab',
  }));
}

function colorGobierno(tipo) {
  if (tipo === 'de_facto' || tipo === 'junta_militar') return cssv('--facto');
  if (tipo === 'provisional' || tipo === 'interino') return cssv('--warn');
  return cssv('--const');
}
const anioDe = (iso) => Number(String(iso).slice(0, 4));
/** Fecha ISO → año fraccionario, para que un hito de diciembre no caiga en enero. */
function anioFrac(iso) {
  if (!iso) return null;
  const [a, m = '1', d = '1'] = String(iso).split('-');
  return Number(a) + ((Number(m) - 1) + (Number(d) - 1) / 30.4) / 12;
}

const x = (anio) => {
  const [a, z] = estado.rango;
  return PAD.l + ((anio - a) / (z - a)) * (W - PAD.l - PAD.r);
};
const xMini = (anio) => PAD.l + ((anio - LIMITE[0]) / (LIMITE[1] - LIMITE[0])) * (W - PAD.l - PAD.r);
const anioEn = (sx) => {
  const [a, z] = estado.rango;
  return a + ((sx - PAD.l) / (W - PAD.l - PAD.r)) * (z - a);
};

function svgX(ev) {
  const r = refs.svg.getBoundingClientRect();
  return ((ev.clientX - r.left) / r.width) * W;
}
function svgY(ev) {
  const r = refs.svg.getBoundingClientRect();
  return ((ev.clientY - r.top) / r.height) * H;
}

/* ───────────────────────────────────────────────── geometría */

function calcularGeometria() {
  const compacto = !!estado.ficha;
  const vis = eventosVisibles();
  let y = 12;

  const pres = { y, h: compacto ? 20 : 26 };
  y += pres.h + 10;

  // Los regímenes se superponen y está bien: describen dimensiones distintas del régimen
  // monetario (convertibilidad · organización de la emisión · control de cambios). Se separan
  // en carriles, nunca se apilan. Primero por subtipo y, si dentro de un subtipo dos se pisan
  // igual —pasa: «Bancos Nacionales Garantidos» corre por dentro de la inconvertibilidad—,
  // se abre otro carril. Empaquetado de intervalos, no una fila por etiqueta.
  const hReg = compacto ? 12 : 15;
  const regimenes = [];
  const porSubtipo = new Map();
  for (const e of vis.filter((v) => v.nivel === 'regimen')) {
    const k = e.subtipo || 'otro';
    if (!porSubtipo.has(k)) porSubtipo.set(k, []);
    porSubtipo.get(k).push(e);
  }
  for (const [subtipo, lista] of porSubtipo) {
    lista.sort((p1, p2) => anioFrac(p1.desde) - anioFrac(p2.desde));
    const filas = [];
    for (const e of lista) {
      const ini = anioFrac(e.desde);
      const fin = e.hasta ? anioFrac(e.hasta) : LIMITE[1];
      const libre = filas.find((f) => f.fin <= ini + 0.02);
      if (libre) { libre.fin = fin; libre.eventos.push(e); } else { filas.push({ fin, eventos: [e] }); }
    }
    filas.forEach((f, i) => regimenes.push({ subtipo, primera: i === 0, eventos: f.eventos }));
  }
  regimenes.forEach((carril, i) => { carril.y = y + i * (hReg + 3); carril.h = hReg; });
  if (regimenes.length) y += regimenes.length * (hReg + 3) + 8;

  // Un carril por capa de eventos con datos en la ventana.
  const cats = (estado.datos?.vocabulario?.categorias
    ? Object.keys(estado.datos.vocabulario.categorias)
    : []).filter((c) => estado.categorias.has(c) && vis.some((e) => e.categoria === c && e.nivel !== 'regimen'));
  const hCar = compacto ? 34 : 46;
  const carriles = cats.map((c, i) => ({ categoria: c, y: y + i * hCar, h: hCar }));
  y += cats.length * hCar;

  const base = y;               // línea del eje de años
  y += 22;

  const series = { y, h: compacto ? 30 : 52 };
  y += series.h + 14;

  const mini = { y, h: compacto ? 22 : 30 };
  H = mini.y + mini.h + 20;

  geo = { pres, regimenes, carriles, series, mini, base, compacto };
}

/* ───────────────────────────────────────────────── capas del dibujo */

function dibujarRejilla(g) {
  const [a, z] = estado.rango;
  const span = z - a;
  const paso = span > 110 ? 20 : span > 55 ? 10 : span > 22 ? 5 : span > 9 ? 2 : 1;
  const faint = cssv('--ink-faint');
  const soft = cssv('--line-soft');
  for (let anio = Math.ceil(a / paso) * paso; anio <= z; anio += paso) {
    g.appendChild(el('line', {
      x1: x(anio), x2: x(anio), y1: geo.pres.y, y2: geo.base, stroke: soft, 'stroke-width': 1,
    }));
    g.appendChild(texto(anio, {
      x: x(anio), y: geo.base + 15, 'text-anchor': 'middle', fill: faint,
      'font-size': 10.5, 'font-family': 'var(--mono)',
    }));
  }
  g.appendChild(el('line', {
    x1: PAD.l, x2: W - PAD.r, y1: geo.base, y2: geo.base, stroke: cssv('--line'), 'stroke-width': 1,
  }));
}

function dibujarPresidencias(g) {
  const { y, h } = geo.pres;
  g.appendChild(texto('GOB.', { x: 4, y: y + h / 2 + 3, fill: cssv('--ink-faint'), 'font-size': 9 }));
  if (!estado.capas.pres || !estado.datos) return;
  const [a, z] = estado.rango;
  const ink = cssv('--ink');
  for (const p of estado.datos.presidencias) {
    const y0 = anioFrac(p.desde);
    const y1 = p.hasta ? anioFrac(p.hasta) : LIMITE[1];
    if (y1 < a || y0 > z) continue;
    const x0 = x(Math.max(y0, a));
    const x1 = x(Math.min(y1, z));
    const w = Math.max(1, x1 - x0);
    const col = colorGobierno(p.tipo);
    const grupo = el('g', { class: 'pres-block', 'data-pres': p.orden });
    grupo.appendChild(el('rect', {
      x: x0, y, width: w, height: h, rx: 2, fill: col,
      'fill-opacity': p.tipo === 'constitucional' ? 0.17 : 0.3,
      stroke: col, 'stroke-opacity': 0.5, 'stroke-width': 1,
    }));
    if (w > 46) {
      const apellido = p.nombre.split(' ').slice(-1)[0];
      grupo.appendChild(texto(w > 130 ? p.nombre : apellido, {
        x: x0 + 5, y: y + h / 2 + 3.5, fill: ink, 'font-size': 10.5,
      }));
    }
    g.appendChild(grupo);
  }
}

function dibujarRegimenes(g) {
  const [a, z] = estado.rango;
  for (const carril of geo.regimenes) {
    if (carril.primera) {
      g.appendChild(texto(ABREV_SUB[carril.subtipo] || carril.subtipo.slice(0, 10).toUpperCase(), {
        x: 4, y: carril.y + carril.h - 3.5, fill: cssv('--ink-faint'), 'font-size': 8,
      }));
    }
    for (const e of carril.eventos) {
      const y0 = anioFrac(e.desde);
      const y1 = e.hasta ? anioFrac(e.hasta) : LIMITE[1];
      const x0 = x(Math.max(y0, a));
      const x1 = x(Math.min(y1, z));
      const w = Math.max(2, x1 - x0);
      const col = colorCategoria(e.categoria);
      const sel = e.id === estado.seleccion;
      const grupo = el('g', { class: 'reg-band', 'data-evt-id': e.id, tabindex: '0', role: 'button' });
      grupo.appendChild(el('rect', {
        x: x0, y: carril.y, width: w, height: carril.h, rx: 2, fill: col,
        'fill-opacity': sel ? 0.36 : 0.18, stroke: col, 'stroke-opacity': sel ? 0.95 : 0.45,
        'stroke-width': sel ? 1.6 : 1,
      }));
      const rotulo = recortar(e.titulo, w, 4.9);
      if (rotulo) {
        grupo.appendChild(texto(rotulo, {
          x: x0 + 5, y: carril.y + carril.h - 4, fill: cssv('--ink-2'), 'font-size': 9.5,
          'font-weight': sel ? 600 : 400, class: 'lab',
        }));
      }
      g.appendChild(grupo);
    }
  }
}

function dibujarCarriles(g) {
  const [a, z] = estado.rango;
  const { etiquetas } = nivelesVisibles();
  const vis = eventosVisibles().filter((e) => e.nivel !== 'regimen');
  const faint = cssv('--ink-faint');
  const surf = cssv('--surface');

  for (const carril of geo.carriles) {
    const col = colorCategoria(carril.categoria);
    const yb = carril.y + (geo.compacto ? 15 : 22);
    g.appendChild(el('rect', {
      x: PAD.l, y: carril.y + 1, width: W - PAD.l - PAD.r, height: carril.h - 3,
      fill: cssv('--surface-2'), 'fill-opacity': 0.45, rx: 3,
    }));
    g.appendChild(el('line', {
      x1: PAD.l, x2: W - PAD.r, y1: yb, y2: yb, stroke: col, 'stroke-opacity': 0.22, 'stroke-width': 1,
    }));
    g.appendChild(texto(ABREV_CAT[carril.categoria] || carril.categoria.toUpperCase().slice(0, 10), {
      x: 4, y: yb + 3, fill: col, 'font-size': 8.5, 'letter-spacing': '.04em',
    }));

    // el seleccionado se coloca PRIMERO para que reserve su lugar y no lo pise otro rótulo
    const propios = vis.filter((e) => e.categoria === carril.categoria)
      .sort((p, q) => (q.id === estado.seleccion) - (p.id === estado.seleccion)
        || anioFrac(p.desde) - anioFrac(q.desde));
    // Con la ficha abierta el carril no da para dos filas de rótulos: se usa una sola.
    const filas = geo.compacto ? [yb - 10] : [yb - 11, yb + 17];
    const ocupado = filas.map(() => -1e9);   // borde derecho del último rótulo, por fila

    for (const e of propios) {
      const sel = e.id === estado.seleccion;
      const grupo = el('g', {
        class: e.nivel === 'episodio' ? 'evt-barra' : 'evt-pin',
        'data-evt-id': e.id, tabindex: '0', role: 'button',
      });
      // clamp al área de dibujo: un episodio que entra por la izquierda no puede
      // pisar el rótulo del carril, que vive en el margen
      const x0 = Math.max(PAD.l, x(anioFrac(e.desde)));

      if (e.nivel === 'episodio') {
        const x1 = Math.min(W - PAD.r, x(anioFrac(e.hasta || e.desde) + 0.4));
        const w = Math.max(3, x1 - x0);
        grupo.appendChild(el('rect', {
          x: x0, y: yb - 6, width: w, height: 12, rx: 3, fill: col,
          'fill-opacity': sel ? 0.5 : 0.28, stroke: col, 'stroke-width': sel ? 1.8 : 1,
          'stroke-opacity': sel ? 1 : 0.6,
        }));
      } else {
        grupo.appendChild(el('circle', {
          class: 'pin-head', cx: x0, cy: yb, r: sel ? 5 : 3.4,
          fill: e.ficha ? col : surf, stroke: col, 'stroke-width': sel ? 2.4 : 1.6,
        }));
      }
      if (sel) {
        grupo.appendChild(el('line', {
          x1: x0, x2: x0, y1: geo.pres.y + geo.pres.h, y2: geo.base,
          stroke: col, 'stroke-width': 1.2, 'stroke-opacity': 0.4, 'stroke-dasharray': '3 3',
        }));
      }

      // etiqueta: dos filas alternadas y sin pisarse; el que no entra queda como pin
      if (etiquetas || sel) {
        const ancho = e.titulo.length * 5.3 + 16;
        const flip = x0 + ancho > W - PAD.r;
        const izq = flip ? x0 - ancho : x0;
        const fila = ocupado.findIndex((borde) => borde <= izq);
        if (fila >= 0) {
          etiquetaConFondo(grupo, e.titulo, {
            x: x0 + (flip ? -7 : 7), y: filas[fila],
            ancla: flip ? 'end' : 'start', color: sel ? cssv('--ink') : cssv('--ink-2'), negrita: sel,
          });
          ocupado[fila] = izq + ancho + 4;
        }
      }
      g.appendChild(grupo);
    }
  }

  if (!geo.carriles.length) {
    g.appendChild(texto('Ninguna capa de eventos encendida en esta ventana', {
      x: (PAD.l + W - PAD.r) / 2, y: geo.base - 20, 'text-anchor': 'middle', fill: faint, 'font-size': 11,
    }));
  }
}

function dibujarSeries(g) {
  const { y, h } = geo.series;
  const faint = cssv('--ink-faint');
  const hay = (estado.datos?.series || []).length;
  g.appendChild(el('rect', {
    class: 'gapband', x: PAD.l, y, width: W - PAD.l - PAD.r, height: h, rx: 4,
  }));
  g.appendChild(texto('SERIES TRONCALES', {
    x: PAD.l + 8, y: y + 13, fill: faint, 'font-size': 8.5, 'letter-spacing': '.07em',
  }));
  if (hay) return;
  const cx = (PAD.l + W - PAD.r) / 2;
  g.appendChild(texto('Sin cobertura: el catálogo cerrado de series anuales todavía no existe (fase T3).', {
    x: cx, y: y + h / 2 + 2, 'text-anchor': 'middle', fill: cssv('--ink-dim'), 'font-size': 11,
  }));
  if (!geo.compacto) {
    g.appendChild(texto('Ninguna curva se dibuja hasta que cada serie declare sus tramos y su empalme.', {
      x: cx, y: y + h / 2 + 17, 'text-anchor': 'middle', fill: faint, 'font-size': 10,
    }));
  }
}

function dibujarMini(g) {
  const { y, h } = geo.mini;
  const soft = cssv('--line-soft');
  const faint = cssv('--ink-faint');
  const mg = el('g', { id: 'mini' });
  mg.appendChild(el('rect', {
    x: PAD.l, y, width: W - PAD.l - PAD.r, height: h, fill: cssv('--sunken'),
    stroke: soft, 'stroke-width': 1, rx: 4,
  }));

  // silueta: gobiernos de facto + regímenes, para ubicarse sin series
  for (const p of estado.datos?.presidencias || []) {
    if (p.tipo === 'constitucional') continue;
    const x0 = xMini(anioDe(p.desde));
    const x1 = xMini(p.hasta ? anioDe(p.hasta) : LIMITE[1]);
    mg.appendChild(el('rect', {
      x: x0, y: y + 1, width: Math.max(1, x1 - x0), height: h - 2,
      fill: cssv('--facto'), 'fill-opacity': 0.14,
    }));
  }
  for (const e of estado.datos?.eventos || []) {
    if (e.categoria !== 'crisis') continue;
    mg.appendChild(el('line', {
      x1: xMini(e.anio), x2: xMini(e.anio), y1: y + 2, y2: y + h - 2,
      stroke: cssv('--crit'), 'stroke-width': 1, 'stroke-opacity': 0.45,
    }));
  }
  // hasta dónde llegan los datos cargados
  const hasta = estado.datos?.rango?.eventos_hasta || LIMITE[0];
  const xh = xMini(hasta);
  mg.appendChild(el('rect', {
    x: xh, y, width: Math.max(0, W - PAD.r - xh), height: h,
    fill: cssv('--ground'), 'fill-opacity': 0.55,
  }));
  if (W - PAD.r - xh > 150) {
    mg.appendChild(texto('sin cargar todavía', {
      x: (xh + W - PAD.r) / 2, y: y + h / 2 + 3, 'text-anchor': 'middle', fill: faint, 'font-size': 9,
    }));
  }

  const [a, z] = estado.rango;
  const bx0 = xMini(a);
  const bx1 = xMini(z);
  mg.appendChild(el('rect', {
    x: PAD.l, y, width: Math.max(0, bx0 - PAD.l), height: h, fill: cssv('--ground'), 'fill-opacity': 0.5,
  }));
  mg.appendChild(el('rect', {
    x: bx1, y, width: Math.max(0, W - PAD.r - bx1), height: h, fill: cssv('--ground'), 'fill-opacity': 0.5,
  }));
  mg.appendChild(el('rect', {
    id: 'brush', x: bx0, y, width: Math.max(3, bx1 - bx0), height: h, fill: cssv('--accent'),
    'fill-opacity': 0.1, stroke: cssv('--accent'), 'stroke-width': 1.2, rx: 3, style: 'cursor:grab',
  }));
  for (const [id, px] of [['bh-i', bx0], ['bh-f', bx1]]) {
    mg.appendChild(el('rect', {
      id, x: px - 3, y, width: 6, height: h, fill: cssv('--accent'), 'fill-opacity': 0.55,
      rx: 2, style: 'cursor:ew-resize',
    }));
  }
  for (const [i, anio] of [LIMITE[0], LIMITE[1]].entries()) {
    mg.appendChild(texto(anio, {
      x: i ? W - PAD.r : PAD.l, y: y + h + 12, 'text-anchor': i ? 'end' : 'start',
      fill: faint, 'font-size': 9, 'font-family': 'var(--mono)',
    }));
  }
  g.appendChild(mg);
}

/* ───────────────────────────────────────────────── dibujo completo */

export function dibujar() {
  if (!estado.datos) return;
  calcularGeometria();
  const svg = refs.svg;
  svg.innerHTML = '';
  svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
  const g = el('g');
  svg.appendChild(g);

  dibujarRejilla(g);
  dibujarPresidencias(g);
  dibujarRegimenes(g);
  dibujarCarriles(g);
  dibujarSeries(g);
  dibujarMini(g);

  // resaltado temporal de una cifra de la ficha (§5.3)
  if (estado.marca) {
    const mx = x(estado.marca.anio);
    if (mx >= PAD.l && mx <= W - PAD.r) {
      g.appendChild(el('line', {
        x1: mx, x2: mx, y1: geo.pres.y, y2: geo.base, stroke: cssv('--accent'), 'stroke-width': 2,
        'stroke-opacity': 0.85,
      }));
      g.appendChild(texto(`${estado.marca.anio} · ${estado.marca.v || ''}`, {
        x: mx + 6, y: geo.pres.y - 1, fill: cssv('--accent'), 'font-size': 11, 'font-weight': 600,
        'font-family': 'var(--mono)',
      }));
    }
  }

  g.appendChild(el('g', { id: 'hover' }));
  refs.zoomLbl.textContent = `${Math.round(estado.rango[0])}–${Math.round(estado.rango[1])}`;
  for (const b of refs.rangos) {
    const [a, z] = b.dataset.rango.split(',').map(Number);
    b.setAttribute('aria-pressed', String(Math.round(estado.rango[0]) === a && Math.round(estado.rango[1]) === z));
  }
}

/* ───────────────────────────────────────────────── interacción */

function moverTip(ev) {
  const tip = refs.tip;
  const hov = refs.svg.querySelector('#hover');
  if (arrastre) { tip.classList.remove('on'); return; }
  const sx = svgX(ev);
  const sy = svgY(ev);
  if (hov) hov.innerHTML = '';

  const destino = ev.target.closest('[data-evt-id]');
  const pres = ev.target.closest('[data-pres]');
  let html = '';

  if (destino) {
    const e = eventoPorId(destino.dataset.evtId);
    if (e) {
      const fechas = e.hasta && e.hasta !== e.desde ? `${e.desde} → ${e.hasta}` : e.desde;
      html = `<span class="yr">${fechas}</span><div class="tt">${escapar(e.titulo)}</div>`
        + `<div class="sb">${escapar(etiquetaCategoria(e.categoria))} · ${escapar(e.nivel)}`
        + `${e.gobierno ? ` · ${escapar(e.gobierno)}` : ''}</div>`
        + (e.resumen ? `<div class="sb">${escapar(e.resumen.slice(0, 160))}${e.resumen.length > 160 ? '…' : ''}</div>` : '')
        + (e.ficha ? '<div class="ev">● ficha completa — doble clic para abrirla</div>' : '');
    }
  } else if (pres) {
    const p = estado.datos.presidencias.find((q) => String(q.orden) === pres.dataset.pres);
    if (p) {
      html = `<span class="yr">${p.desde} → ${p.hasta || 'hoy'}</span><div class="tt">${escapar(p.nombre)}</div>`
        + `<div class="sb">${escapar(p.tipo.replace('_', ' '))}`
        + `${p.fuerza_politica ? ` · ${escapar(p.fuerza_politica)}` : ''}</div>`
        + `<div class="sb">acceso: ${escapar(p.acceso || '—')} · salida: ${escapar(p.salida || '—')}</div>`;
    }
  } else if (sy >= geo.pres.y && sy <= geo.base && sx >= PAD.l && sx <= W - PAD.r) {
    const anio = Math.round(anioEn(sx));
    const g = estado.datos.presidencias.find(
      (p) => anioDe(p.desde) <= anio && (!p.hasta || anio < anioDe(p.hasta)),
    );
    if (hov) {
      hov.appendChild(el('line', {
        x1: x(anio), x2: x(anio), y1: geo.pres.y, y2: geo.base, stroke: cssv('--ink-dim'),
        'stroke-width': 1, 'stroke-dasharray': '3 3', 'stroke-opacity': 0.55,
      }));
    }
    const delAnio = (estado.datos.eventos || []).filter((e) => e.anio === anio);
    html = `<span class="yr">${anio}</span>`
      + (g ? `<div class="sb">${escapar(g.nombre)}</div>` : '')
      + (delAnio.length ? `<div class="ev">● ${delAnio.slice(0, 3).map((e) => escapar(e.titulo)).join(' · ')}</div>` : '');
  }

  if (!html) { tip.classList.remove('on'); return; }
  tip.innerHTML = html;
  tip.classList.add('on');

  const r = refs.svg.getBoundingClientRect();
  const c = refs.canvas.getBoundingClientRect();
  const px = (r.left - c.left) + (sx / W) * r.width;
  const py = ev.clientY - c.top;
  const flip = px > c.width - 200;
  tip.style.left = `${px + (flip ? -14 - tip.offsetWidth : 16)}px`;
  tip.style.top = `${Math.max(4, Math.min(py - 18, c.height - tip.offsetHeight - 8))}px`;
}

function escapar(s) {
  return String(s ?? '').replace(/[&<>"']/g, (c) => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
  ));
}

function conectar() {
  const svg = refs.svg;

  svg.addEventListener('wheel', (ev) => {
    if (svgY(ev) > geo.mini.y - 10) return;
    ev.preventDefault();
    const foco = Math.min(LIMITE[1], Math.max(LIMITE[0], anioEn(svgX(ev))));
    const [a, z] = estado.rango;
    const f = ev.deltaY > 0 ? 1.18 : 1 / 1.18;
    fijarRango(foco - (foco - a) * f, foco + (z - foco) * f);
  }, { passive: false });

  svg.addEventListener('mousedown', (ev) => {
    const sx = svgX(ev);
    const sy = svgY(ev);
    if (sy >= geo.mini.y && sy <= geo.mini.y + geo.mini.h) {
      const id = ev.target.id;
      arrastre = (id === 'bh-i' || id === 'bh-f') ? { tipo: id } : { tipo: 'brush', x0: sx, r0: [...estado.rango] };
      if (arrastre.tipo === 'brush' && (sx < xMini(estado.rango[0]) || sx > xMini(estado.rango[1]))) {
        const anio = LIMITE[0] + ((sx - PAD.l) / (W - PAD.l - PAD.r)) * (LIMITE[1] - LIMITE[0]);
        const w = estado.rango[1] - estado.rango[0];
        fijarRango(anio - w / 2, anio + w / 2);
        arrastre.r0 = [...estado.rango];
      }
    } else if (sy <= geo.base && !ev.target.closest('[data-evt-id]')) {
      arrastre = { tipo: 'pan', x0: sx, r0: [...estado.rango] };
      svg.style.cursor = 'grabbing';
    }
  });

  window.addEventListener('mousemove', (ev) => {
    if (!arrastre) return;
    const sx = svgX(ev);
    const anioMini = LIMITE[0] + ((sx - PAD.l) / (W - PAD.l - PAD.r)) * (LIMITE[1] - LIMITE[0]);
    if (arrastre.tipo === 'pan' || arrastre.tipo === 'brush') {
      const [a, z] = arrastre.r0;
      const d = arrastre.tipo === 'pan'
        ? ((arrastre.x0 - sx) / (W - PAD.l - PAD.r)) * (z - a)
        : ((sx - arrastre.x0) / (W - PAD.l - PAD.r)) * (LIMITE[1] - LIMITE[0]);
      let A = a + d;
      let Z = z + d;
      if (A < LIMITE[0]) { Z += LIMITE[0] - A; A = LIMITE[0]; }
      if (Z > LIMITE[1]) { A -= Z - LIMITE[1]; Z = LIMITE[1]; }
      fijarRango(A, Z);
    } else if (arrastre.tipo === 'bh-i') {
      fijarRango(Math.min(anioMini, estado.rango[1] - 6), estado.rango[1]);
    } else {
      fijarRango(estado.rango[0], Math.max(anioMini, estado.rango[0] + 6));
    }
  });

  window.addEventListener('mouseup', () => { arrastre = null; svg.style.cursor = ''; });

  svg.addEventListener('click', (ev) => {
    const destino = ev.target.closest('[data-evt-id]');
    if (!destino) return;
    refs.onSeleccion(destino.dataset.evtId);
  });

  svg.addEventListener('dblclick', (ev) => {
    const destino = ev.target.closest('[data-evt-id]');
    if (destino) { refs.onFicha(destino.dataset.evtId); return; }
    fijarRango(1880, estado.datos?.rango?.eventos_hasta || 1935);
  });

  svg.addEventListener('keydown', (ev) => {
    const destino = ev.target.closest?.('[data-evt-id]');
    if (!destino || (ev.key !== 'Enter' && ev.key !== ' ')) return;
    ev.preventDefault();
    refs.onFicha(destino.dataset.evtId);
  });

  svg.addEventListener('mousemove', moverTip);
  svg.addEventListener('mouseleave', () => {
    refs.tip.classList.remove('on');
    const hov = svg.querySelector('#hover');
    if (hov) hov.innerHTML = '';
  });
}

/** Encuadra el gráfico en un evento, con aire a los costados. */
export function encuadrar(e, aire = 8) {
  const a = anioDe(e.desde);
  const z = e.hasta ? anioDe(e.hasta) : a;
  fijarRango(a - aire, z + aire);
}

/** Zoom a un año puntual y resaltado temporal (cifra enlazada). */
export function irAlAnio(anio, v) {
  const w = Math.max(14, estado.rango[1] - estado.rango[0]);
  cambiar({ marca: { anio, v } });
  fijarRango(anio - w / 2, anio + w / 2);
  setTimeout(() => cambiar({ marca: null }), 2600);
}

export function montar(opciones) {
  refs = { ...opciones, rangos: [...document.querySelectorAll('#rangos button')] };
  conectar();
  return { dibujar };
}
