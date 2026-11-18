/* barra.js — la barra común de La Cueva del Economista.
 *
 * Un solo lugar define las pestañas de la plataforma:
 *   Inicio · Línea de tiempo ↗ (abre en otra pestaña del navegador) · Mesa de trabajo · Terminal
 *
 * Dos modos:
 *  - En las pantallas de La Cueva (portada, Mesa, Línea de tiempo) completa el
 *    `<nav class="modswitch" data-barra>` de la topbar que ya tiene cada página.
 *  - En la Terminal (React, se carga con data-modulo="terminal") no hay topbar de La Cueva:
 *    agrega una barra propia arriba de todo y avisa su alto con --alto-cueva, que la
 *    Terminal descuenta de sus paneles de altura completa.
 *
 * En el sitio publicado (window.CUEVA_ESTATICO) la Terminal no existe: la pestaña queda
 * visible pero apagada, con el aviso de que solo funciona en la versión local.
 */
(function () {
  const ICONOS = {
    inicio:
      '<svg width="15" height="15" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M2 7.2 8 2.5l6 4.7V14H2z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/><path d="M6.4 14V9.8h3.2V14" stroke="currentColor" stroke-width="1.5"/></svg>',
    tiempo:
      '<svg width="15" height="15" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M1.5 13h13M3 13V9.5M6.2 13V6M9.4 13V3.5M12.6 13V7.8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>',
    mesa:
      '<svg width="15" height="15" viewBox="0 0 16 16" fill="none" aria-hidden="true"><rect x="1.6" y="2.4" width="12.8" height="11.2" rx="1.8" stroke="currentColor" stroke-width="1.5"/><path d="M1.6 6.2h12.8M6.4 6.2v7.4" stroke="currentColor" stroke-width="1.5"/></svg>',
    terminal:
      '<svg width="15" height="15" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M1.5 12.5 5.5 8l3 2.6 6-7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M11 3.6h3.5v3.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  };

  const PESTANAS = [
    { id: 'inicio', texto: 'Inicio', href: '/' },
    { id: 'tiempo', texto: 'Línea de tiempo', href: '/tiempo', aparte: true },
    { id: 'mesa', texto: 'Mesa de trabajo', href: '/mesa' },
    { id: 'terminal', texto: 'Terminal', href: '/terminal/' },
  ];

  const estatico = !!window.CUEVA_ESTATICO;
  if (estatico) {
    // En el sitio publicado no hay portada: la Mesa vive en «/».
    PESTANAS.splice(0, 1);
    PESTANAS.find((p) => p.id === 'mesa').href = '/';
  }
  const script = document.currentScript || document.querySelector('script[src$="/web/estilo/barra.js"]');
  const modulo = script && script.dataset.modulo;

  function actual() {
    if (modulo) return modulo;
    const p = location.pathname;
    if (p.startsWith('/terminal')) return 'terminal';
    if (p.startsWith('/tiempo')) return 'tiempo';
    if (p.startsWith('/mesa') || p.startsWith('/explorador') || estatico) return 'mesa';
    return 'inicio';
  }

  function enlaces() {
    const aqui = actual();
    return PESTANAS.map((p) => {
      const apagada = estatico && p.id === 'terminal';
      const attrs = [
        `href="${apagada ? '#' : p.href}"`,
        `data-pestana="${p.id}"`,
        p.id === aqui ? 'aria-current="true"' : '',
        p.aparte && p.id !== aqui ? 'target="_blank" rel="noopener" title="Se abre en otra pestaña del navegador"' : '',
        apagada ? 'aria-disabled="true" title="La Terminal solo funciona en la versión local de La Cueva del Economista"' : '',
      ].join(' ');
      const flecha = p.aparte && p.id !== aqui ? ' <span class="barra-aparte" aria-hidden="true">↗</span>' : '';
      return `<a ${attrs}>${ICONOS[p.id]}${p.texto}${flecha}</a>`;
    }).join('');
  }

  function enPaginaDeLaCueva() {
    const nav = document.querySelector('nav.modswitch[data-barra]');
    if (!nav) return false;
    nav.innerHTML = enlaces();
    nav.setAttribute('aria-label', 'Pestañas de La Cueva del Economista');
    nav.querySelectorAll('a[aria-disabled="true"]').forEach((a) => a.addEventListener('click', (e) => e.preventDefault()));
    return true;
  }

  // Barra propia para la Terminal (que no carga tokens.css): mismos colores que la Terminal.
  const ALTO = 44;
  const CSS = `
  .cueva-barra{position:sticky;top:0;z-index:60;height:${ALTO}px;display:flex;align-items:center;gap:16px;
    padding:0 14px;background:#0d131b;border-bottom:1px solid #223041;color:#d8e0ea;
    font:14px "Inter","Segoe UI",system-ui,sans-serif}
  .cueva-barra .cb-marca{display:flex;align-items:center;gap:8px;color:#d8e0ea;text-decoration:none;font-weight:700;white-space:nowrap}
  .cueva-barra .cb-marca em{font-style:normal;color:#f5a524}
  .cueva-barra nav{display:flex;gap:2px;padding:3px;background:#0b0f14;border:1px solid #223041;border-radius:8px}
  .cueva-barra nav a{display:inline-flex;align-items:center;gap:6px;padding:4px 10px;border-radius:6px;color:#8b97a6;
    text-decoration:none;font-size:13px;white-space:nowrap}
  .cueva-barra nav a:hover{color:#d8e0ea;text-decoration:none}
  .cueva-barra nav a[aria-current="true"]{background:#16202c;color:#d8e0ea;box-shadow:inset 0 -2px 0 #f5a524}
  .cueva-barra .barra-aparte{font-size:11px;opacity:.7}`;

  function enTerminal() {
    const estilo = document.createElement('style');
    estilo.textContent = CSS;
    document.head.appendChild(estilo);
    const barra = document.createElement('header');
    barra.className = 'cueva-barra';
    barra.innerHTML =
      '<a class="cb-marca" href="/" title="Inicio de La Cueva del Economista">' +
      '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M3 21V13.5C3 7.7 7 3.5 12 3.5S21 7.7 21 13.5V21" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" opacity=".38"/><path d="M4.5 21l3.2-5.1 3 3.4 3.4-7.3 2.6 4.6 2.8-3.2" stroke="#f5a524" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" fill="none"/></svg>' +
      'La Cueva del <em>Economista</em></a>' +
      `<nav aria-label="Pestañas de La Cueva del Economista">${enlaces()}</nav>`;
    document.body.prepend(barra);
    document.documentElement.style.setProperty('--alto-cueva', `${ALTO}px`);
  }

  function iniciar() {
    if (modulo === 'terminal') enTerminal();
    else enPaginaDeLaCueva();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', iniciar);
  else iniciar();

  window.CuevaBarra = { PESTANAS, actual };
})();
