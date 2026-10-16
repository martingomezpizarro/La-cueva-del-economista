/* estado.js — el estado único de la pantalla.
 *
 * Una sola fuente de verdad para rango, capas, selección y ficha; los módulos
 * (grafico, ficha, app) leen de acá y avisan con `cambiar()`. Nadie guarda una
 * copia: si dos módulos derivan el mismo dato de dos lugares, se desincronizan.
 */

export const LIMITE = [1880, 2026];
export const MIN_VENTANA = 6;      // años: menos que esto no se lee

const oyentes = [];

export const estado = {
  datos: null,                     // payload de GET /api/v1/historia
  rango: [1880, 1935],             // ventana visible [desde, hasta]
  capas: { pres: true, ministros: true, autoridades: true },
  categorias: new Set(),           // capas de eventos encendidas
  niveles: new Set(['regimen', 'episodio', 'hito']),
  autoZoom: true,                  // el detalle se filtra por zoom (§6.1)
  seleccion: null,                 // id del evento seleccionado
  ficha: null,                     // id del evento con ficha abierta
  fichaDatos: null,                // payload de la ficha abierta
  marca: null,                     // {anio, cifra} resaltado temporal de una cifra
  busqueda: '',
};

export function escuchar(fn) { oyentes.push(fn); }

export function cambiar(parcial = {}) {
  Object.assign(estado, parcial);
  oyentes.forEach((fn) => fn(estado));
}

/** Ventana con topes: nunca sale del dominio ni baja de MIN_VENTANA años. */
export function fijarRango(a, z) {
  let A = Math.max(LIMITE[0], a);
  let Z = Math.min(LIMITE[1], z);
  if (Z - A < MIN_VENTANA) {
    const c = (A + Z) / 2;
    A = Math.max(LIMITE[0], c - MIN_VENTANA / 2);
    Z = Math.min(LIMITE[1], A + MIN_VENTANA);
  }
  cambiar({ rango: [A, Z] });
}

/** Qué niveles se dibujan a esta escala. El detalle se filtra por zoom, como un mapa. */
export function nivelesVisibles() {
  const span = estado.rango[1] - estado.rango[0];
  const pedidos = estado.niveles;
  if (!estado.autoZoom) return { ver: new Set(pedidos), etiquetas: span <= 40 };
  const ver = new Set();
  if (pedidos.has('regimen')) ver.add('regimen');
  if (pedidos.has('episodio') && span <= 120) ver.add('episodio');
  if (pedidos.has('hito') && span <= 80) ver.add('hito');
  return { ver, etiquetas: span <= 32 };
}

/** Los eventos que pasan todos los filtros (capa, nivel, zoom) y tocan la ventana. */
export function eventosVisibles() {
  if (!estado.datos) return [];
  const [a, z] = estado.rango;
  const { ver } = nivelesVisibles();
  return estado.datos.eventos.filter(
    (e) => estado.categorias.has(e.categoria) && ver.has(e.nivel) && e.anio_fin >= a && e.anio <= z,
  );
}

/** Los de la lista del rail: mismo filtro de capa, sin el filtro de zoom. */
export function eventosDelRail() {
  if (!estado.datos) return [];
  const q = estado.busqueda.trim().toLowerCase();
  return estado.datos.eventos.filter((e) => {
    if (!estado.categorias.has(e.categoria)) return false;
    if (!q) return true;
    return (`${e.titulo} ${e.resumen} ${e.anio}`).toLowerCase().includes(q);
  });
}

export function eventoPorId(id) {
  if (!estado.datos || !id) return null;
  return estado.datos.eventos.find((e) => e.id === id) || null;
}
