/* estatico.js — la plataforma publicada como sitio estático (GitHub Pages).
 *
 * Lo inyecta `scripts/construir_sitio.py` en el <head> de cada página del sitio, ANTES
 * de cualquier otro script. Nunca se carga cuando corre el servidor de verdad.
 *
 * Qué hace: intercepta `fetch` y traduce las rutas de lectura de la API a los JSON
 * congelados que generó el build. Así las pantallas no saben que no hay servidor.
 * Qué NO hace: ejecutar nada. Lo que en el servidor corre Python (Estudio, Kalman,
 * análisis básico, proyectos, agentes) falla con un mensaje claro, no con un 404 mudo.
 */
(function () {
  window.CUEVA_ESTATICO = true;

  const MENSAJE = 'Esta función necesita el servidor de La Cueva: la versión publicada '
    + 'es de solo lectura (explorar series y la Línea de Tiempo).';

  // GET de la API → archivo congelado por el build
  const LECTURAS = [
    [/^\/api\/v1\/historia\/?$/, '/api/v1/historia.json'],
    [/^\/api\/v1\/historia\/eventos\/([a-z0-9-]+)\/?$/, '/api/v1/historia/eventos/$1.json'],
    [/^\/api\/v1\/explorador\/datos\/?$/, '/api/v1/explorador/datos.json'],
  ];

  const original = window.fetch.bind(window);

  window.fetch = function (entrada, opciones) {
    const texto = typeof entrada === 'string' ? entrada : (entrada && entrada.url) || String(entrada);
    const url = new URL(texto, location.href);
    if (url.origin !== location.origin || !url.pathname.startsWith('/api/')) {
      return original(entrada, opciones);
    }
    const metodo = ((opciones && opciones.method) || (entrada && entrada.method) || 'GET').toUpperCase();
    if (metodo === 'GET') {
      for (const [patron, destino] of LECTURAS) {
        if (patron.test(url.pathname)) return original(url.pathname.replace(patron, destino));
      }
    }
    return Promise.reject(new Error(MENSAJE));
  };
})();
