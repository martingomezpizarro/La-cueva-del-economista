/* tema.js — el tema es del usuario, no de la pantalla.
 *
 * Lo comparten los dos módulos (Línea de Tiempo y Mesa de Trabajo) y se guarda,
 * así no hay que volver a elegirlo al cambiar de pestaña. Si nunca eligió, manda
 * el sistema operativo (tokens.css ya resuelve `prefers-color-scheme`).
 *
 * Se carga SIN defer y antes del contenido, para que no haya un parpadeo claro
 * al abrir una pantalla que el usuario dejó en oscuro.
 */
(function () {
  const CLAVE = 'cueva_tema';          // 'claro' | 'oscuro' | ausente = el del sistema
  const raiz = document.documentElement;

  function leer() {
    try { return localStorage.getItem(CLAVE); } catch { return null; }
  }
  function guardar(valor) {
    try { valor ? localStorage.setItem(CLAVE, valor) : localStorage.removeItem(CLAVE); } catch { /* modo privado */ }
  }
  function aplicar(valor) {
    if (valor === 'oscuro') raiz.setAttribute('data-theme', 'dark');
    else if (valor === 'claro') raiz.setAttribute('data-theme', 'light');
    else raiz.removeAttribute('data-theme');
  }
  function esOscuro() {
    const t = raiz.getAttribute('data-theme');
    if (t) return t === 'dark';
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  }
  function alternar() {
    const valor = esOscuro() ? 'claro' : 'oscuro';
    guardar(valor);
    aplicar(valor);
    document.dispatchEvent(new CustomEvent('cueva:tema', { detail: { oscuro: valor === 'oscuro' } }));
    return valor;
  }

  aplicar(leer());   // antes de pintar nada
  window.CuevaTema = { alternar, esOscuro, aplicar, leer };
})();
