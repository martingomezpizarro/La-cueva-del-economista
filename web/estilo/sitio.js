/* sitio.js — datos institucionales de La Cueva del Economista, en UN solo lugar.
 *
 * Lo leen el pie de página (web/estilo/pie.js) y la página de términos
 * (web/terminos.html). Para cambiar el mail, los links de colaboración o la
 * fecha de actualización, se edita ESTE archivo y nada más.
 *
 * Un valor en null se muestra en pantalla como «[COMPLETAR]» a propósito:
 * es preferible un hueco visible a un dato inventado.
 */
window.CUEVA_SITIO = {
  proyecto: 'La Cueva del Economista',
  autor: 'Martín Gómez Pizarro',
  email: 'gomezpizarromartin@gmail.com',
  sitioPersonal: 'https://martingomezpizarro.com.ar',

  colaborar: {
    // Link a la página de Cafecito (ej.: https://cafecito.app/usuario)
    cafecito: null,                       // [COMPLETAR]
    // Segunda opción: alias de Mercado Pago, link de pago u otra.
    // tipo: 'alias' muestra el texto para copiar; tipo: 'link' muestra un botón.
    alternativa: { tipo: 'alias', etiqueta: 'Alias de Mercado Pago', valor: 'martingomezpizarro' },
  },

  // Licencia. Mientras no se defina una, rige «todos los derechos reservados»
  // sobre el código y los textos propios. Los datos de terceros conservan la suya.
  licencia: null,                         // ej.: 'Código bajo MIT · textos bajo CC BY 4.0'
  anioInicio: 2026,

  // Fecha de la última actualización del sitio (AAAA-MM-DD). Actualizar al publicar.
  actualizado: '2026-10-22',

  jurisdiccion: 'República Argentina',

  // Fuentes principales que se nombran en el pie y en los términos.
  // El detalle por serie (organismo, endpoint, transformación) vive en el bloque
  // `proc` del catálogo y en cueva/fuentes/registro.json.
  fuentesPrincipales: ['INDEC', 'BCRA', 'Ministerio de Economía', 'Banco Mundial', 'FRED', 'BIS'],
};
