/* recorrido.js — recorrido guiado por cada pantalla de La Cueva del Economista.
 *
 * Uso: <script src="/web/estilo/recorrido.js" data-modulo="mesa"></script>
 *   · Se abre solo la PRIMERA vez que alguien entra a esa pantalla (queda marcado en
 *     localStorage, clave `cueva_recorrido_<modulo>`).
 *   · Se repite con cualquier botón que tenga el atributo data-recorrido-abrir (el «?»
 *     de la barra superior) o entrando con ?recorrido=1 (los enlaces de la portada).
 *
 * Los pasos de cada módulo están acá abajo, en PASOS. Cada paso apunta a un selector
 * de la pantalla REAL; si ese elemento no está a la vista (todavía no cargó, está
 * oculto, el usuario lo cerró), el paso se saltea en vez de señalar a la nada.
 * Un paso sin selector se muestra centrado.
 *
 * No toca el estado de la pantalla: sólo dibuja encima (velo + foco + tarjeta).
 */
(function () {
  const PASOS = {
    mesa: [
      { titulo: 'Bienvenido a la Mesa de Trabajo',
        texto: 'Acá elegís series económicas, las transformás y las comparás; cuando algo vale la pena, lo convertís en un proyecto con agentes que te acompañan. Son unos pocos pasos.' },
      { sel: '#ex-abrir-cat', titulo: 'Sumá series del catálogo',
        texto: 'El catálogo está ordenado por familia (actividad, precios, monetario y cambiario, y más) y se puede buscar por nombre o por id. Lo que agregás aparece en «Series del trabajo».' },
      { sel: ['#ex-lista .serie', '.mesa .col-izq'], titulo: 'Cada serie tiene su receta',
        texto: '«log» y «Δ dif.» transforman sólo esa serie, en el orden en que se aplican. «dep / expl» marca cuál es la variable a explicar. El punto de color la muestra u oculta.' },
      { sel: '.mesa .barra', titulo: 'Controles comunes',
        texto: 'Vista (paneles, base 100 o estandarizado), frecuencia común, nivel o variación interanual y rango de años. Valen para todas las series a la vez.' },
      { sel: '.mesa .centro .card', titulo: 'El gráfico, con la franja de gobiernos',
        texto: 'Debajo del gráfico se ve qué gobierno estaba en cada momento, constitucional o de facto; sale de la Línea de Tiempo. Más abajo hay distribución, cuadro comparativo, correlación y spread.' },
      { sel: ['#ex-ficha', '.mesa .col-der'], titulo: 'De dónde sale cada dato',
        texto: 'La ficha de la serie activa dice organismo, definición y transformaciones. Cuando algo es un supuesto (por ejemplo, cómo se pasó de diario a mensual), lo dice.' },
      { sel: '#vistas', titulo: 'Explorar y Métodos',
        texto: '«Métodos» abre el catálogo completo de análisis: pruebas, filtros, modelos, cointegración, regímenes, inferencia causal, aprendizaje automático, redes y finanzas. Usa las series que elegiste acá, y todo pronóstico se evalúa contra un benchmark ingenuo.' },
      { sel: '#modo-switch', titulo: 'Vista Rápida o Proyecto',
        texto: 'La Vista Rápida es un espacio para explorar: no se guarda nada. Cuando encontrás algo, «Promover a proyecto» se lleva las series y lo que hiciste a un proyecto con nombre.' },
      { sel: '#sidebar', titulo: 'El cuaderno del proyecto',
        texto: 'Dentro de un proyecto se habilitan la pregunta y los objetivos, la bibliografía, las notas, la pizarra donde debaten los agentes y el informe. El botón flotante consulta a un agente puntual.' },
      { sel: '#ayuda', titulo: 'Cuando quieras, de nuevo',
        texto: 'Este botón repite el recorrido. Recordá que lo que dicen los agentes puede tener errores: verificalo siempre.' },
    ],
    tiempo: [
      { titulo: 'La Línea de Tiempo',
        texto: 'La historia económica argentina desde 1880: gobiernos, regímenes, episodios e hitos, con fichas que citan su fuente. Te muestro cómo moverte.' },
      { sel: '#rangos', titulo: 'Elegí el período',
        texto: 'Atajos por etapa histórica. «Todo» abre de 1880 a hoy; el tramo cargado con más detalle, por ahora, es 1880–1935.' },
      { sel: '#tl-canvas', titulo: 'Navegá la línea',
        texto: 'La rueda acerca y aleja, arrastrar desplaza y el doble clic en el fondo reinicia. Un clic en un evento lo selecciona; doble clic abre su ficha.' },
      { sel: '.module > .rail:not(.rail-r)', titulo: 'Capas',
        texto: 'Prendé y apagá instituciones, tipos de evento y niveles de detalle. Con «Detalle por zoom», a mayor acercamiento aparecen episodios y después hitos.' },
      { sel: '.rail-r', titulo: 'Todos los eventos',
        texto: 'Buscá un evento por nombre y elegilo de la lista: su resumen aparece arriba y la línea se centra en él.' },
      { sel: '#ficha', titulo: 'Fichas con fuente',
        texto: 'Cada ficha tiene cifras enlazadas, citas a la bibliografía y un enlace permanente para compartir ese evento.' },
      { sel: '#chip-verif', titulo: 'Sin verificar, hasta que alguien lo controle',
        texto: 'Toda fila nace sin verificar y sólo pasa a verificada cuando una persona la contrasta con fuentes oficiales. Tomalo como material de estudio, no como dato oficial.' },
      { sel: '#ayuda', titulo: 'Cuando quieras, de nuevo',
        texto: 'Este botón repite el recorrido.' },
    ],
  };

  const script = document.currentScript;
  const MODULO = script && script.dataset.modulo;
  const CLAVE = 'cueva_recorrido_' + MODULO;
  if (!MODULO || !PASOS[MODULO]) return;
  const pasos = PASOS[MODULO];

  const leer = () => { try { return localStorage.getItem(CLAVE); } catch { return 'sin-storage'; } };
  const marcar = () => { try { localStorage.setItem(CLAVE, 'visto'); } catch { /* modo privado */ } };
  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  function objetivo(paso) {
    if (!paso.sel) return null;
    for (const s of [].concat(paso.sel)) {
      const el = document.querySelector(s);
      if (!el || el.hidden) continue;
      const r = el.getBoundingClientRect();
      if (r.width < 4 || r.height < 4) continue;
      const cs = getComputedStyle(el);
      if (cs.visibility === 'hidden' || cs.display === 'none') continue;
      return el;
    }
    return undefined;   // tenía selector y no está a la vista → se saltea
  }

  let velo, foco, tarjeta, i = 0, activo = false, anterior = null;

  function construir() {
    velo = document.createElement('div');
    velo.className = 'rc-velo';
    foco = document.createElement('div');
    foco.className = 'rc-foco';
    tarjeta = document.createElement('div');
    tarjeta.className = 'rc-tarjeta';
    tarjeta.setAttribute('role', 'dialog');
    tarjeta.setAttribute('aria-modal', 'true');
    tarjeta.setAttribute('aria-labelledby', 'rc-titulo');
    document.body.append(velo, foco, tarjeta);
    tarjeta.addEventListener('click', (e) => {
      const b = e.target.closest('[data-rc]'); if (!b) return;
      const a = b.dataset.rc;
      if (a === 'sig') ir(+1); else if (a === 'ant') ir(-1); else cerrar();
    });
  }

  function indicesVisibles() {
    return pasos.map((p, k) => (objetivo(p) === undefined ? -1 : k)).filter((k) => k >= 0);
  }

  function pintar() {
    const vis = indicesVisibles();
    if (!vis.includes(i)) { const sig = vis.find((k) => k > i); if (sig == null) return cerrar(); i = sig; }
    const paso = pasos[i];
    const el = objetivo(paso);
    const pos = vis.indexOf(i), total = vis.length;
    const ultimo = pos === total - 1;

    tarjeta.innerHTML = `
      <div class="rc-num">${pos + 1} de ${total}</div>
      <h2 class="rc-titulo" id="rc-titulo">${esc(paso.titulo)}</h2>
      <p class="rc-texto">${esc(paso.texto)}</p>
      <div class="rc-barra" aria-hidden="true">${vis.map((_, k) => `<i${k === pos ? ' class="on"' : ''}></i>`).join('')}</div>
      <div class="rc-acciones">
        <button type="button" class="rc-btn rc-saltar" data-rc="cerrar">${ultimo ? 'Cerrar' : 'Saltar recorrido'}</button>
        <span class="rc-esp"></span>
        ${pos > 0 ? '<button type="button" class="rc-btn" data-rc="ant">Anterior</button>' : ''}
        <button type="button" class="rc-btn rc-primario" data-rc="sig">${ultimo ? 'Listo' : (pos === 0 ? 'Empezar' : 'Siguiente')}</button>
      </div>`;

    if (el) {
      el.scrollIntoView({ block: 'nearest', inline: 'nearest' });
      const r = el.getBoundingClientRect(), m = 6;
      const x = Math.max(4, r.left - m), y = Math.max(4, r.top - m);
      const w = Math.min(innerWidth - 8, r.right + m) - x, h = Math.min(innerHeight - 8, r.bottom + m) - y;
      Object.assign(foco.style, { left: x + 'px', top: y + 'px', width: w + 'px', height: h + 'px' });
      foco.classList.remove('rc-sin');
      tarjeta.classList.remove('rc-centro');
      ubicar({ x, y, w, h });
    } else {
      foco.classList.add('rc-sin');
      tarjeta.classList.add('rc-centro');
      Object.assign(tarjeta.style, { left: '', top: '' });
    }
    tarjeta.querySelector('.rc-primario').focus({ preventScroll: true });
  }

  function ubicar(r) {
    if (innerWidth <= 640) { Object.assign(tarjeta.style, { left: '', top: '' }); tarjeta.classList.add('rc-hoja'); return; }
    tarjeta.classList.remove('rc-hoja');
    const tw = tarjeta.offsetWidth, th = tarjeta.offsetHeight, g = 14, M = 12;
    const lugares = [
      { x: r.x, y: r.y + r.h + g, ok: r.y + r.h + g + th < innerHeight - M },          // abajo
      { x: r.x, y: r.y - th - g, ok: r.y - th - g > M },                              // arriba
      { x: r.x + r.w + g, y: r.y, ok: r.x + r.w + g + tw < innerWidth - M },          // derecha
      { x: r.x - tw - g, y: r.y, ok: r.x - tw - g > M },                              // izquierda
    ];
    const l = lugares.find((p) => p.ok) || { x: (innerWidth - tw) / 2, y: innerHeight - th - M };
    const x = Math.min(Math.max(M, l.x), innerWidth - tw - M);
    const y = Math.min(Math.max(M, l.y), innerHeight - th - M);
    Object.assign(tarjeta.style, { left: x + 'px', top: y + 'px' });
  }

  function ir(d) {
    const vis = indicesVisibles();
    const pos = vis.indexOf(i);
    const nuevo = vis[pos + d];
    if (nuevo == null) { if (d > 0) cerrar(); return; }
    i = nuevo; pintar();
  }

  function abrir() {
    if (activo) return;
    if (!velo) construir();
    anterior = document.activeElement;
    activo = true; i = 0;
    document.documentElement.classList.add('rc-activo');
    velo.hidden = foco.hidden = tarjeta.hidden = false;
    pintar();
  }
  function cerrar() {
    if (!activo) return;
    activo = false; marcar();
    document.documentElement.classList.remove('rc-activo');
    velo.hidden = foco.hidden = tarjeta.hidden = true;
    if (anterior && anterior.focus) anterior.focus({ preventScroll: true });
  }

  document.addEventListener('keydown', (e) => {
    if (!activo) return;
    if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); cerrar(); }
    else if (e.key === 'ArrowRight') { e.preventDefault(); e.stopPropagation(); ir(+1); }
    else if (e.key === 'ArrowLeft') { e.preventDefault(); e.stopPropagation(); ir(-1); }
    else if (e.key === 'Tab') {   // el foco no se escapa de la tarjeta
      const bs = [...tarjeta.querySelectorAll('button')]; if (!bs.length) return;
      const k = bs.indexOf(document.activeElement);
      if (e.shiftKey && k <= 0) { e.preventDefault(); bs[bs.length - 1].focus(); }
      else if (!e.shiftKey && k === bs.length - 1) { e.preventDefault(); bs[0].focus(); }
    }
  }, true);
  let rz;
  addEventListener('resize', () => { if (!activo) return; clearTimeout(rz); rz = setTimeout(pintar, 80); });

  document.addEventListener('click', (e) => {
    if (e.target.closest('[data-recorrido-abrir]')) { e.preventDefault(); abrir(); }
  });

  // ── arranque: primera visita o ?recorrido=1 ───────────────────────────
  function pedidoPorUrl() {
    const u = new URL(location.href);
    if (u.searchParams.get('recorrido') !== '1') return false;
    u.searchParams.delete('recorrido');
    history.replaceState(history.state, '', u.pathname + u.search + u.hash);
    return true;
  }
  function cuandoEsteLista(fn) {
    // Las pantallas pintan su contenido después de cargar (módulos ES, fetch a la API):
    // se espera a que aparezca el segundo paso, con un tope para no colgarse.
    const sel = pasos.find((p) => p.sel)?.sel;
    const t0 = Date.now();
    (function mirar() {
      if (!sel || objetivo({ sel }) || Date.now() - t0 > 5000) return setTimeout(fn, 250);
      setTimeout(mirar, 150);
    })();
  }
  function iniciar() {
    const forzado = pedidoPorUrl();
    if (forzado || !leer()) cuandoEsteLista(abrir);
  }
  window.CuevaRecorrido = { abrir, cerrar };
  if (document.readyState === 'complete') iniciar();
  else addEventListener('load', iniciar);
})();
