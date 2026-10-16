/* ficha.js — el panel inferior: la ficha completa del evento.
 *
 * Va abajo y comprime el gráfico (no es un modal ni el panel lateral) porque
 * las cifras están enlazadas: si tocar un número lleva a ese año en el gráfico,
 * el gráfico tiene que seguir visible.
 *
 * El markdown del relato llega YA renderizado a HTML saneado desde el servidor
 * (cueva/datos/historia.py): el frontend no interpreta texto libre.
 */

import { cambiar, estado, eventoPorId } from './estado.js';
import { encuadrar, irAlAnio } from './grafico.js';

const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => (
  { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
));

let panel = null;

function etiquetaCategoria(cat) {
  return estado.datos?.vocabulario?.categorias?.[cat]?.etiqueta || cat;
}

function encabezado(e, ficha) {
  const fechas = e.hasta && e.hasta !== e.desde ? `${e.desde} → ${e.hasta}` : e.desde;
  const precision = e.precision === 'anio' ? ' (sólo se conoce el año)' : e.precision === 'mes' ? ' (precisión: mes)' : '';
  const estadoEditorial = ficha && ficha.verificado
    ? `<span class="chip ok"><span class="dot"></span>verificada ${esc(ficha.revisado)}</span>`
    : '<span class="chip warn"><span class="dot"></span>sin verificar</span>';
  return `
    <div class="ficha-hd">
      <div style="flex:1; min-width:240px">
        <h2 class="tt">${esc(e.titulo)}</h2>
        <div class="meta">${esc(fechas)}${precision} · ${esc(etiquetaCategoria(e.categoria))} · ${esc(e.nivel)}${
  e.gobierno ? ` · gob. ${esc(e.gobierno.nombre || e.gobierno)}` : ''}</div>
      </div>
      ${estadoEditorial}
      ${ficha ? `<span class="chip neutral">${ficha.cifras.length} cifras</span>` : ''}
      <button class="btn sm" id="ficha-link" title="Copiar el enlace permanente de esta ficha">Copiar enlace</button>
      <button class="btn sm" id="ficha-x">Cerrar ✕</button>
    </div>`;
}

function bloqueCifras(ficha) {
  if (!ficha.cifras.length) return '';
  const cards = ficha.cifras.map((c) => {
    const link = c.serie
      ? (c.serie_disponible
        ? '<span class="link">ver en el gráfico ↗</span>'
        : `<span class="link off" title="La serie '${esc(c.serie)}' todavía no existe (fase T3)">serie pendiente</span>`)
      : '<span class="link off">sin serie</span>';
    return `<button class="cifra-card" data-anio="${esc(c.anio)}" data-v="${esc(c.v)}">
        <span class="v">${esc(c.v)}</span>
        <span class="e">${esc(c.et)}<span class="fu">${esc(c.fuente)}</span></span>
        ${link}
      </button>`;
  }).join('');
  return `<h4>Cifras clave</h4>${cards}`;
}

function bloqueFuentes(ficha, e) {
  let out = '';
  if (e.fuente) {
    out += `<h4>Fuente primaria del evento</h4><ul class="fuentes-prim"><li><span class="tp">norma</span><span>${esc(e.fuente)}</span></li></ul>`;
  }
  if (ficha?.fuentes_primarias?.length) {
    const items = ficha.fuentes_primarias.map((f) => `<li><span class="tp">${esc(f.tipo || 'doc')}</span><span>${esc(f.ref)}${
      f.url ? ` — <a href="${esc(f.url)}" target="_blank" rel="noopener">texto original ↗</a>` : ''}</span></li>`).join('');
    out += `<h4>Fuentes primarias</h4><ul class="fuentes-prim">${items}</ul>`;
  }
  return out;
}

function bloqueBibliografia(lista) {
  if (!lista?.length) return '';
  const items = lista.map((b) => `<li>${esc(b.texto)}${
    b.verificable ? '' : ' <span class="marca">— cita no verificable</span>'}</li>`).join('');
  return `<h4>Bibliografía</h4><ul class="biblio">${items}</ul>`;
}

function bloqueMedios(ficha) {
  if (!ficha.medios?.length) {
    return `<div class="foto"><div class="ph"><svg width="32" height="32" viewBox="0 0 24 24" fill="none" style="color:var(--ink-faint)"><rect x="2.5" y="4.5" width="19" height="15" rx="2" stroke="currentColor" stroke-width="1.4"/><circle cx="8.5" cy="10" r="1.8" stroke="currentColor" stroke-width="1.4"/><path d="M3 17l5.5-5 4 3.5 3.5-2.5 5 4.5" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/></svg></div>
      <div class="cap">Sin imagen todavía.<div class="cred">Sin crédito, licencia y origen declarados no se usa: un marco vacío antes que un problema legal.</div></div></div>`;
  }
  return ficha.medios.map((m) => `<div class="foto">
      <img src="/historia-medios/${esc(String(m.archivo).replace(/^medios\//, ''))}" alt="${esc(m.epigrafe || '')}" loading="lazy">
      <div class="cap">${esc(m.epigrafe || '')}<div class="cred">${esc(m.credito)} · ${esc(m.licencia)}</div></div>
    </div>`).join('');
}

function bloqueRelacionados(ficha) {
  const rel = (ficha.relacionados || []).filter((r) => r.existe);
  if (!rel.length) return '';
  const tags = rel.map((r) => `<button class="ev-tag" data-goto="${esc(r.id)}">${esc(r.titulo)} · ${esc(r.anio)}</button>`).join(' ');
  return `<h4>Eventos relacionados</h4><div style="display:flex;flex-wrap:wrap;gap:6px">${tags}</div>`;
}

function pintar(datos) {
  const e = datos.evento;
  const ficha = datos.ficha;

  if (!ficha) {
    panel.innerHTML = `${encabezado(e, null)}
      <div class="ficha-bd" style="grid-template-columns:1fr">
        <div class="ficha-col">
          <div class="note"><span>⚠</span><div><b>Ficha pendiente de redacción.</b>
            Este evento tiene fecha, resumen y fuente, pero todavía no cronología, cifras enlazadas ni bibliografía comentada.</div></div>
          <p style="margin-top:14px">${esc(e.resumen)}</p>
          ${e.nota ? `<h4>Nota de trabajo</h4><p>${esc(e.nota)}</p>` : ''}
          ${bloqueFuentes(null, e)}
          ${bloqueBibliografia(datos.bibliografia_evento)}
        </div>
      </div>`;
  } else {
    const citas = ficha.secciones.filter((s) => /cita/i.test(s.titulo));
    const relato = ficha.secciones.filter((s) => !/cita/i.test(s.titulo));
    panel.innerHTML = `${encabezado(e, ficha)}
      <div class="ficha-bd">
        <div class="ficha-col">
          <p style="font-size:14px; color:var(--ink)">${esc(e.resumen)}</p>
          ${relato.map((s) => `<h4>${esc(s.titulo)}</h4>${s.html}`).join('')}
        </div>
        <div class="ficha-col">
          ${bloqueMedios(ficha)}
          ${bloqueCifras(ficha)}
          ${citas.map((s) => `<h4>${esc(s.titulo)}</h4>${s.html}`).join('')}
          ${bloqueFuentes(ficha, e)}
          ${bloqueBibliografia(ficha.bibliografia)}
          ${bloqueRelacionados(ficha)}
          <div style="margin-top:14px; font-size:10.5px; color:var(--ink-faint); line-height:1.5">
            ${esc(ficha.redactor || 'sin redactor declarado')}${ficha.revisado ? ` · revisado ${esc(ficha.revisado)}` : ''}
          </div>
        </div>
      </div>`;
  }

  panel.classList.add('on');

  panel.querySelector('#ficha-x')?.addEventListener('click', cerrar);
  panel.querySelector('#ficha-link')?.addEventListener('click', async (ev) => {
    try {
      await navigator.clipboard.writeText(`${location.origin}/tiempo/${e.id}`);
      ev.target.textContent = 'Enlace copiado';
      setTimeout(() => { ev.target.textContent = 'Copiar enlace'; }, 1800);
    } catch { ev.target.textContent = `${location.origin}/tiempo/${e.id}`; }
  });
  panel.querySelectorAll('.cifra').forEach((b) => b.addEventListener('click', () => {
    const anio = Number(b.dataset.anio);
    if (anio) irAlAnio(anio, b.textContent.trim());
  }));
  panel.querySelectorAll('.cifra-card').forEach((b) => b.addEventListener('click', () => {
    const anio = Number(b.dataset.anio);
    if (anio) irAlAnio(anio, b.dataset.v);
  }));
  panel.querySelectorAll('[data-goto]').forEach((b) => b.addEventListener('click', () => abrir(b.dataset.goto)));
}

export async function abrir(id) {
  const e = eventoPorId(id);
  if (!e) return;
  cambiar({ seleccion: id, ficha: id });
  history.replaceState(null, '', `/tiempo/${id}`);
  panel.classList.add('on');
  panel.innerHTML = '<div class="ficha-col" style="padding:22px">Cargando la ficha…</div>';
  encuadrar(e, e.nivel === 'hito' ? 9 : 6);
  try {
    const r = await fetch(`/api/v1/historia/eventos/${encodeURIComponent(id)}`);
    if (!r.ok) throw new Error(`${r.status}`);
    const datos = await r.json();
    cambiar({ fichaDatos: datos });
    pintar(datos);
  } catch (err) {
    panel.innerHTML = `<div class="ficha-col" style="padding:22px"><div class="note"><span>⚠</span><div>No se pudo cargar la ficha (${esc(err.message)}).</div></div></div>`;
  }
}

export function cerrar() {
  panel.classList.remove('on');
  history.replaceState(null, '', '/tiempo');
  cambiar({ ficha: null, fichaDatos: null });
}

export function montar(elemento) {
  panel = elemento;
  document.addEventListener('keydown', (ev) => {
    if (ev.key === 'Escape' && estado.ficha) cerrar();
  });
}
