/* pie.js — pie de página institucional de La Cueva del Economista.
 *
 * Un solo componente para todas las pantallas. Cada página pone un contenedor
 *   <footer data-cueva-pie="barra"></footer>      (pantallas de trabajo a 100vh)
 *   <footer data-cueva-pie="completo"></footer>   (páginas de lectura: términos, inicio)
 *   <div    data-cueva-pie="flotante"></div>      (pantallas legadas sin lugar para una barra)
 * y carga, en este orden: /web/estilo/sitio.js → /web/estilo/pie.js (+ pie.css).
 *
 * Los datos (autor, mail, links de colaboración, fecha) salen de window.CUEVA_SITIO
 * (web/estilo/sitio.js). Este archivo NO tiene datos propios.
 *
 * Además, en cualquier página, rellena los elementos con data-sitio="clave"
 * (lo usa web/terminos.html para no repetir el mail ni la fecha).
 *
 * Todo lo que viene de la configuración se escapa antes de ir al DOM.
 */
(function () {
  const S = window.CUEVA_SITIO || {};
  const FALTA = '[COMPLETAR]';
  const RUTA_TERMINOS = '/terminos';

  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const ext = (href, texto, cls = '') =>
    `<a href="${esc(href)}" target="_blank" rel="noopener noreferrer"${cls ? ` class="${cls}"` : ''}>${texto}</a>`;
  const falta = (que) => `<span class="pie-falta" title="Dato pendiente en web/estilo/sitio.js">${FALTA}${que ? ' ' + esc(que) : ''}</span>`;

  const anio = new Date().getFullYear();
  const anios = S.anioInicio && S.anioInicio < anio ? `${S.anioInicio}–${anio}` : String(S.anioInicio || anio);

  function fechaLarga(iso) {
    if (!iso) return FALTA;
    const d = new Date(iso + 'T12:00:00');
    if (isNaN(d)) return esc(iso);
    return d.toLocaleDateString('es-AR', { day: 'numeric', month: 'long', year: 'numeric' });
  }

  function textoLicencia() {
    return S.licencia
      ? `© ${anios} ${esc(S.autor)}. ${esc(S.licencia)}.`
      : `© ${anios} ${esc(S.autor)}. Todos los derechos reservados.`;
  }

  // Valores que la página de términos pide por data-sitio="…"
  const VALORES = {
    proyecto: () => esc(S.proyecto),
    autor: () => esc(S.autor),
    email: () => S.email ? `<a href="mailto:${esc(S.email)}">${esc(S.email)}</a>` : falta('mail'),
    sitio: () => S.sitioPersonal ? ext(S.sitioPersonal, esc(S.sitioPersonal.replace(/^https?:\/\//, ''))) : falta('sitio'),
    actualizado: () => fechaLarga(S.actualizado),
    jurisdiccion: () => esc(S.jurisdiccion || 'República Argentina'),
    licencia: () => textoLicencia(),
    fuentes: () => (S.fuentesPrincipales || []).map(esc).join(', '),
  };

  // ── bloques reutilizables ────────────────────────────────────────────
  function autoria() {
    const mail = S.email ? `<a href="mailto:${esc(S.email)}">${esc(S.email)}</a>` : falta('mail');
    const sitio = S.sitioPersonal
      ? ext(S.sitioPersonal, esc(S.sitioPersonal.replace(/^https?:\/\//, '')))
      : falta('sitio');
    return { mail, sitio, nombre: esc(S.autor || FALTA) };
  }

  function bloqueColaborar() {
    const c = S.colaborar || {};
    const cafecito = c.cafecito
      ? ext(c.cafecito, '<span aria-hidden="true">☕</span> Invitame un cafecito', 'pie-boton pie-boton-primario')
      : `<span class="pie-boton pie-boton-primario is-falta" title="Falta el link en web/estilo/sitio.js">☕ Cafecito ${FALTA}</span>`;

    let alt = '';
    const a = c.alternativa;
    if (a) {
      const etiqueta = esc(a.etiqueta || 'Otra opción');
      if (!a.valor) {
        alt = `<div class="pie-alt"><span class="pie-alt-lbl">${etiqueta}</span> ${falta()}</div>`;
      } else if (a.tipo === 'link') {
        alt = ext(a.valor, etiqueta, 'pie-boton');
      } else {
        alt = `<div class="pie-alt"><span class="pie-alt-lbl">${etiqueta}</span>
          <code class="pie-alias">${esc(a.valor)}</code>
          <button type="button" class="pie-copiar" data-copiar="${esc(a.valor)}">Copiar</button></div>`;
      }
    }
    return `
      <p class="pie-texto">Este proyecto es gratuito e independiente. Si te resulta útil, podés colaborar voluntariamente para sostenerlo.</p>
      <div class="pie-acciones">${cafecito}${alt}</div>
      <p class="pie-aclaracion">Las colaboraciones son voluntarias, no constituyen contraprestación por ningún servicio ni otorgan derechos sobre el contenido.</p>`;
  }

  const DESCARGO_CORTO =
    'Contenido informativo y educativo, ofrecido «tal cual». No es asesoramiento financiero ni una publicación oficial de los organismos citados.';

  // ── variante «barra»: una línea, para pantallas de trabajo a pantalla completa ──
  function renderBarra(el) {
    const a = autoria();
    el.classList.add('pie', 'pie-barra');
    el.setAttribute('role', 'contentinfo');
    el.innerHTML = `
      <span class="pie-item pie-autor">Desarrollado por <b>${a.nombre}</b></span>
      <span class="pie-item pie-oculta-movil">${a.mail}</span>
      <span class="pie-item pie-oculta-movil">${a.sitio}</span>
      <span class="pie-item pie-descargo" title="${esc(DESCARGO_CORTO)}">Informativo · no es asesoramiento financiero · datos: ${esc((S.fuentesPrincipales || []).slice(0, 3).join(', '))} y otros</span>
      <span class="pie-sep"></span>
      <button type="button" class="pie-item pie-link" data-pie-colaborar aria-expanded="false">☕ Colaborar</button>
      <a class="pie-item pie-link" href="${RUTA_TERMINOS}" target="_blank" rel="noopener noreferrer">Términos y condiciones</a>
      <span class="pie-item pie-meta pie-oculta-movil" title="${esc(textoLicencia().replace(/<[^>]+>/g, ''))}">© ${anios}</span>`;
  }

  // ── variante «completo»: para páginas de lectura ─────────────────────
  function renderCompleto(el) {
    const a = autoria();
    el.classList.add('pie', 'pie-completo');
    el.setAttribute('role', 'contentinfo');
    el.innerHTML = `
      <div class="pie-grilla">
        <section class="pie-col">
          <h2 class="pie-h">Autoría</h2>
          <p class="pie-texto">Desarrollado por <b>${a.nombre}</b></p>
          <p class="pie-texto">Contacto: ${a.mail}</p>
          <p class="pie-texto">Sitio personal: ${a.sitio}</p>
        </section>
        <section class="pie-col">
          <h2 class="pie-h">Colaborar</h2>
          ${bloqueColaborar()}
        </section>
        <section class="pie-col">
          <h2 class="pie-h">Aviso</h2>
          <p class="pie-texto">${esc(DESCARGO_CORTO)} Los resultados de las herramientas y de los asistentes de IA son estimaciones y pueden contener errores.</p>
          <p class="pie-texto"><a href="${RUTA_TERMINOS}">Términos y condiciones de uso y privacidad</a></p>
        </section>
      </div>
      <div class="pie-legal">
        <span>${textoLicencia()} Los datos de terceros conservan sus licencias.</span>
        <span>Última actualización: ${fechaLarga(S.actualizado)} · Jurisdicción: ${esc(S.jurisdiccion || 'República Argentina')}</span>
      </div>`;
  }

  // ── variante «flotante»: un botón chico en una esquina ────────────────
  function renderFlotante(el) {
    el.classList.add('pie', 'pie-flotante');
    el.setAttribute('role', 'contentinfo');
    el.innerHTML = `
      <button type="button" class="pie-flotante-btn" data-pie-colaborar aria-expanded="false"
        title="Autoría, colaboración y términos" aria-label="Autoría, colaboración y términos">i</button>`;
  }

  // ── panel de colaboración (lo abren «barra» y «flotante») ─────────────
  let panel = null;
  let disparador = null;

  function crearPanel() {
    const a = autoria();
    panel = document.createElement('div');
    panel.className = 'pie-panel';
    panel.setAttribute('role', 'dialog');
    panel.setAttribute('aria-label', 'Colaborar y datos del proyecto');
    panel.hidden = true;
    panel.innerHTML = `
      <div class="pie-panel-hd">
        <b>${esc(S.proyecto || 'La Cueva del Economista')}</b>
        <button type="button" class="pie-cerrar" aria-label="Cerrar">✕</button>
      </div>
      ${bloqueColaborar()}
      <div class="pie-panel-pie">
        <div>Desarrollado por <b>${a.nombre}</b> · ${a.mail} · ${a.sitio}</div>
        <div>${esc(DESCARGO_CORTO)}</div>
        <div><a href="${RUTA_TERMINOS}" target="_blank" rel="noopener noreferrer">Términos y condiciones</a> · ${textoLicencia()} · Actualizado: ${fechaLarga(S.actualizado)}</div>
      </div>`;
    document.body.appendChild(panel);
    panel.querySelector('.pie-cerrar').addEventListener('click', cerrarPanel);
  }

  function abrirPanel(btn) {
    if (!panel) crearPanel();
    disparador = btn;
    panel.hidden = false;
    panel.classList.toggle('pie-panel-izq', btn.closest('.pie-flotante') !== null);
    btn.setAttribute('aria-expanded', 'true');
    panel.querySelector('.pie-cerrar').focus();
  }
  function cerrarPanel() {
    if (!panel || panel.hidden) return;
    panel.hidden = true;
    if (disparador) { disparador.setAttribute('aria-expanded', 'false'); disparador.focus(); }
  }

  document.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-pie-colaborar]');
    if (btn) { e.stopPropagation(); (panel && !panel.hidden) ? cerrarPanel() : abrirPanel(btn); return; }
    const copiar = e.target.closest('[data-copiar]');
    if (copiar) {
      const v = copiar.getAttribute('data-copiar');
      (navigator.clipboard ? navigator.clipboard.writeText(v) : Promise.reject())
        .then(() => { copiar.textContent = 'Copiado'; setTimeout(() => { copiar.textContent = 'Copiar'; }, 1600); })
        .catch(() => { copiar.textContent = v; });
      return;
    }
    if (panel && !panel.hidden && !panel.contains(e.target)) cerrarPanel();
  });
  // En captura: así el Escape cierra el panel antes que los atajos de la pantalla.
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && panel && !panel.hidden) { e.stopPropagation(); cerrarPanel(); }
  }, true);

  // ── arranque ─────────────────────────────────────────────────────────
  function montar() {
    document.querySelectorAll('[data-cueva-pie]').forEach((el) => {
      const v = el.getAttribute('data-cueva-pie');
      if (v === 'completo') renderCompleto(el);
      else if (v === 'flotante') renderFlotante(el);
      else renderBarra(el);
    });
    document.querySelectorAll('[data-sitio]').forEach((el) => {
      const f = VALORES[el.getAttribute('data-sitio')];
      if (f) el.innerHTML = f();
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', montar);
  else montar();
})();
