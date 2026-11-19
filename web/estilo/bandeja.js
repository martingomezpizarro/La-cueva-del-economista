/* bandeja.js — la bandeja de series de La Cueva, vista desde la Terminal.
 *
 * La bandeja es UNA sola (en el servidor: /api/v1/bandeja) y la comparten la Terminal y la
 * Mesa. Este script lo carga barra.js cuando está en la Terminal y agrega:
 *   - en la barra de arriba, el botón «Bandeja · n» que abre el panel;
 *   - en la ficha de un activo (/terminal/activo/<ticker>) o de una serie macro
 *     (/terminal/macro/<id>), el botón «⇩ <ticker> a la bandeja» y, en el panel, el menú de
 *     sus series (precio diario y cada variable de los balances) para mandar una por una;
 *   - el acceso directo «Abrir en la Mesa →», donde las series llegan solas.
 * La Mesa (web/cueva/bandeja_servidor.js) mira la misma bandeja y trae los datos a pedido.
 */
(function () {
  if (window.CUEVA_ESTATICO || window.__cuevaBandeja) return;
  window.__cuevaBandeja = true;
  const API = '/api/v1/bandeja';
  let items = [];
  let abierta = false;
  let activo = null; // {ticker, series:[…]} del activo a la vista
  let pedido = null;

  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
  const refs = () => new Set(items.filter((i) => i.tipo === 'serie' && !(i.datos && i.datos.y)).map((i) => i.ref));

  const CSS = `
  .cb-bj-btn{margin-left:auto;display:inline-flex;align-items:center;gap:7px;padding:5px 11px;border-radius:7px;
    border:1px solid #223041;background:#0b0f14;color:#d8e0ea;font:13px inherit;cursor:pointer;white-space:nowrap}
  .cb-bj-btn:hover{border-color:#f5a524}
  .cb-bj-btn b{min-width:18px;padding:0 5px;border-radius:9px;background:#f5a524;color:#0b0f14;font-size:11.5px;text-align:center}
  .cb-bj-btn.pulso{animation:cbpulso .9s}
  @keyframes cbpulso{0%{box-shadow:0 0 0 0 rgba(245,165,36,.7)}100%{box-shadow:0 0 0 12px rgba(245,165,36,0)}}
  .cb-bj-mandar{display:inline-flex;align-items:center;gap:6px;padding:5px 11px;border-radius:7px;border:1px solid #f5a524;
    background:rgba(245,165,36,.12);color:#f5a524;font:600 13px inherit;cursor:pointer;white-space:nowrap}
  .cb-bj-mandar:hover{background:rgba(245,165,36,.22)}
  .cb-bj-mandar[disabled]{opacity:.6;cursor:default;border-color:#2ecc8a;color:#2ecc8a;background:rgba(46,204,138,.1)}
  .cb-bj-panel{position:fixed;top:50px;right:12px;z-index:70;width:360px;max-height:calc(100vh - 66px);display:flex;flex-direction:column;
    background:#111821;border:1px solid #223041;border-radius:10px;box-shadow:0 14px 40px rgba(0,0,0,.5);color:#d8e0ea;
    font:13px "Inter","Segoe UI",system-ui,sans-serif;overflow:hidden}
  .cb-bj-panel[hidden]{display:none}
  .cb-bj-panel h4{margin:0;padding:10px 12px 6px;font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:#8b97a6;font-weight:600;display:flex;justify-content:space-between;align-items:center}
  .cb-bj-panel h4 button{font:11px inherit;text-transform:none;letter-spacing:0}
  .cb-bj-sec{overflow:auto;padding:0 6px 6px}
  .cb-bj-fila{display:flex;align-items:center;gap:8px;padding:5px 6px;border-radius:6px}
  .cb-bj-fila:hover{background:#16202c}
  .cb-bj-fila .t{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .cb-bj-fila .m{color:#8b97a6;font-size:11.5px;white-space:nowrap}
  .cb-bj-panel button.mini{border:1px solid #223041;background:#0b0f14;color:#d8e0ea;border-radius:6px;padding:2px 8px;cursor:pointer;font:12px inherit}
  .cb-bj-panel button.mini:hover{border-color:#f5a524;color:#f5a524}
  .cb-bj-panel button.mini.ok{border-color:#2ecc8a;color:#2ecc8a;cursor:default}
  .cb-bj-grupo{padding:6px 6px 2px;color:#8b97a6;font-size:11px}
  .cb-bj-vacio{padding:8px 12px 12px;color:#8b97a6;line-height:1.45}
  .cb-bj-pie{display:flex;gap:8px;align-items:center;padding:9px 12px;border-top:1px solid #223041;background:#0d131b}
  .cb-bj-pie a{margin-left:auto;color:#0b0f14;background:#f5a524;border-radius:7px;padding:6px 12px;text-decoration:none;font-weight:600}
  .cb-bj-sep{height:1px;background:#223041;margin:4px 0}`;

  function tickerDeRuta() {
    const m = location.pathname.match(/\/terminal\/(activo|macro)\/([^/?#]+)/);
    if (!m) return null;
    const id = decodeURIComponent(m[2]).split(':').pop();
    return /^[A-Za-z0-9.\-^=]{1,30}$/.test(id) ? id : null;
  }

  async function cargar() {
    try {
      const r = await fetch(API);
      if (!r.ok) return;
      items = (await r.json()).items || [];
      pintar();
    } catch (_) { /* sin servidor: la bandeja queda como estaba */ }
  }

  async function mirarActivo() {
    const t = tickerDeRuta();
    if (!t) { activo = null; pintar(); return; }
    if (activo && activo.ticker === t) return;
    activo = { ticker: t, series: null };
    pintar();
    const yo = (pedido = t);
    try {
      const r = await fetch('/api/v1/mesa/activo/' + encodeURIComponent(t));
      const j = r.ok ? await r.json() : { series: [] };
      if (pedido === yo) { activo = { ticker: t, series: j.series || [] }; pintar(); }
    } catch (_) {
      if (pedido === yo) { activo = { ticker: t, series: [] }; pintar(); }
    }
  }

  async function mandar(series) {
    const ya = refs();
    for (const s of series) {
      if (ya.has(s.id)) continue;
      try {
        await fetch(API, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ tipo: 'serie', ref: s.id, etiqueta: s.nombre, procedencia: { origen: 'terminal', ruta: location.pathname } }),
        });
      } catch (_) { /* se reintenta a mano */ }
    }
    await cargar();
    const b = document.querySelector('.cb-bj-btn');
    if (b) { b.classList.remove('pulso'); void b.offsetWidth; b.classList.add('pulso'); }
  }

  async function quitar(id) {
    await fetch(`${API}/${id}`, { method: 'DELETE' }).catch(() => {});
    await cargar();
  }

  async function vaciar() {
    await fetch(API, { method: 'DELETE' }).catch(() => {});
    await cargar();
  }

  function pintar() {
    const n = items.length;
    const btn = document.querySelector('.cb-bj-btn');
    if (btn) btn.innerHTML = `<svg width="15" height="15" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M2 9.5h3.2l1 1.8h3.6l1-1.8H14V13a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1z" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/><path d="M8 2v6M5.6 5.8 8 8.2l2.4-2.4" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>Bandeja <b>${n}</b>`;

    // botón rápido en la ficha de un activo
    const rapido = document.querySelector('.cb-bj-mandar');
    const principal = activo && activo.series && activo.series[0];
    if (rapido) {
      rapido.hidden = !activo;
      if (activo) {
        const esta = principal && refs().has(principal.id);
        rapido.disabled = !principal || esta;
        rapido.textContent = !activo.series ? `${activo.ticker}…` : !principal ? `${activo.ticker}: sin series` : esta ? `✓ ${activo.ticker} en la bandeja` : `⇩ ${activo.ticker} a la bandeja`;
        rapido.title = principal ? `Manda «${principal.nombre}» a la bandeja; en el panel elegís también las variables de sus balances` : '';
      }
    }

    const panel = document.querySelector('.cb-bj-panel');
    if (!panel) return;
    panel.hidden = !abierta;
    if (!abierta) return;
    const ya = refs();
    let html = '';
    if (activo) {
      html += `<h4><span>Mandar de ${esc(activo.ticker)}</span>${activo.series && activo.series.length > 1 ? '<button class="mini" data-bj="todo">Todo</button>' : ''}</h4><div class="cb-bj-sec">`;
      if (!activo.series) html += '<div class="cb-bj-vacio">Buscando sus series…</div>';
      else if (!activo.series.length) html += '<div class="cb-bj-vacio">Este activo todavía no tiene series en la base de la Terminal (falta actualizar precios o balances).</div>';
      else {
        let grupo = null;
        activo.series.forEach((s, i) => {
          if (s.grupo !== grupo) { grupo = s.grupo; html += `<div class="cb-bj-grupo">${esc(grupo)}</div>`; }
          const esta = ya.has(s.id);
          html += `<div class="cb-bj-fila"><span class="t" title="${esc(s.nombre)}">${esc(s.etiqueta)}</span><span class="m">${esc(s.freq)}</span>` +
            `<button class="mini${esta ? ' ok' : ''}" data-bj="uno" data-i="${i}" ${esta ? 'disabled' : ''}>${esta ? '✓' : '+'}</button></div>`;
        });
      }
      html += '</div><div class="cb-bj-sep"></div>';
    }
    html += `<h4><span>En la bandeja (${n})</span>${n ? '<button class="mini" data-bj="vaciar">Vaciar</button>' : ''}</h4><div class="cb-bj-sec">`;
    if (!n) html += '<div class="cb-bj-vacio">Vacía. Abrí un activo y mandá su precio o sus balances: después los llevás a la Mesa de investigación.</div>';
    else html += items.slice().reverse().map((it) => {
      const origen = it.procedencia && it.procedencia.origen ? it.procedencia.origen : it.autor;
      return `<div class="cb-bj-fila"><span class="t" title="${esc(it.ref)}">${esc(it.etiqueta || it.ref)}</span><span class="m">${esc(origen)}</span><button class="mini" data-bj="x" data-id="${esc(it.id)}" title="Quitar de la bandeja">✕</button></div>`;
    }).join('');
    html += '</div><div class="cb-bj-pie"><span class="m" style="color:#8b97a6;font-size:11.5px">Se comparte con la Mesa</span><a href="/mesa#mesa">Abrir en la Mesa →</a></div>';
    panel.innerHTML = html;
  }

  function iniciar() {
    const barra = document.querySelector('.cueva-barra');
    if (!barra) return;
    const estilo = document.createElement('style');
    estilo.textContent = CSS;
    document.head.appendChild(estilo);

    const rapido = document.createElement('button');
    rapido.className = 'cb-bj-mandar';
    rapido.hidden = true;
    rapido.addEventListener('click', () => { if (activo && activo.series && activo.series[0]) mandar([activo.series[0]]); });
    const btn = document.createElement('button');
    btn.className = 'cb-bj-btn';
    btn.title = 'La bandeja de series: lo que mandes acá aparece en la Mesa de investigación';
    btn.addEventListener('click', () => { abierta = !abierta; pintar(); if (abierta) cargar(); });
    barra.append(btn, rapido);
    // el botón rápido va antes de «Bandeja»
    barra.insertBefore(rapido, btn);
    rapido.style.marginLeft = 'auto';
    btn.style.marginLeft = '0';

    const panel = document.createElement('div');
    panel.className = 'cb-bj-panel';
    panel.hidden = true;
    panel.addEventListener('click', (e) => {
      const b = e.target.closest('[data-bj]');
      if (!b || b.disabled) return;
      if (b.dataset.bj === 'uno') mandar([activo.series[+b.dataset.i]]);
      else if (b.dataset.bj === 'todo') mandar(activo.series);
      else if (b.dataset.bj === 'x') quitar(b.dataset.id);
      else if (b.dataset.bj === 'vaciar') vaciar();
    });
    document.body.appendChild(panel);
    document.addEventListener('click', (e) => {
      if (abierta && !e.target.closest('.cb-bj-panel,.cb-bj-btn,.cb-bj-mandar')) { abierta = false; pintar(); }
    });
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && abierta) { abierta = false; pintar(); } });

    // la Terminal es una SPA: se mira cada cambio de ruta
    for (const m of ['pushState', 'replaceState']) {
      const orig = history[m];
      history[m] = function () { const r = orig.apply(this, arguments); setTimeout(mirarActivo, 0); return r; };
    }
    window.addEventListener('popstate', mirarActivo);
    setInterval(() => { if (document.visibilityState === 'visible') cargar(); }, 5000);
    window.addEventListener('focus', cargar);
    pintar();
    cargar();
    mirarActivo();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', iniciar);
  else iniciar();
  window.CuevaBandejaTerminal = { cargar, mandar };
})();
