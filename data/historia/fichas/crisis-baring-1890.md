---
id: crisis-baring-1890

series: [tcr, infl, deuda, pbipc]

cifras:
  - id: emision85
    v: "58,6 mill. m$n"
    et: "Billetes emitidos, decretos de enero-marzo de 1885"
    serie: null
    anio: 1885
    fuente: "Decretos 9, 15, 21, 23 y 31/1/1885 y 21/3/1885, en BEHP pp. 145-156; Martí (2005: 76)"
  - id: respaldo85
    v: "37 %"
    et: "Reservas metálicas sobre billetes emitidos, 1885"
    serie: null
    anio: 1885
    fuente: "Gómez (2012), cuadro II.4"
  - id: emision86
    v: "88,3 mill. m$n"
    et: "Billetes emitidos, diciembre de 1886 (+51% en menos de dos años)"
    serie: null
    anio: 1886
    fuente: "Decreto del 24/12/1886, art. 2, en BEHP pp. 184-185"
  - id: emision89
    v: "+73 %"
    et: "Crecimiento de la emisión autorizada, marzo 1888 - marzo 1889"
    serie: null
    anio: 1889
    fuente: "BEHP pp. 80-81"
  - id: deudagasto
    v: "630 %"
    et: "Deuda pública sobre gasto, 1890 (era 270% en 1884-1887)"
    serie: deuda
    anio: 1890
    fuente: "della Paolera y Taylor (2003: 95)"
  - id: deficit89
    v: "48,1 mill. m$n"
    et: "Déficit presupuestario corregido, 1889"
    serie: null
    anio: 1889
    fuente: "della Paolera y Taylor (2003: 102)"
  - id: reservas89
    v: "6 mill. $ oro"
    et: "Reservas del Banco Nacional, diciembre de 1889: 10,4% del stock de marzo"
    serie: null
    anio: 1889
    fuente: "della Paolera y Taylor (2003: 72)"
  - id: tc91
    v: "3,40 m$n por $ oro"
    et: "Tipo de cambio 1891 (era 1,48 en 1888)"
    serie: tcr
    anio: 1891
    fuente: "della Paolera y Taylor (2003: 104)"
  - id: riesgo91
    v: "4,67 %"
    et: "Spread sobre el Consol británico, 1891: el máximo del período"
    serie: null
    anio: 1891
    fuente: "della Paolera y Taylor (2003: 104)"
  - id: infl91
    v: "56,2 %"
    et: "Inflación anual 1891"
    serie: infl
    anio: 1891
    fuente: "della Paolera y Taylor (2003: 104)"
  - id: acumulada
    v: "163,7 %"
    et: "Inflación acumulada 1889-1891 (depreciación acumulada: 152,7%)"
    serie: infl
    anio: 1891
    fuente: "della Paolera y Taylor (2003: 105)"
  - id: emprestito91
    v: "£ 15 millones"
    et: "Empréstito de Consolidación al 6%, enero de 1891"
    serie: null
    anio: 1891
    fuente: "Williams (1920: 144-145)"
  - id: interno91
    v: "28,5 de 100 mill."
    et: "Recaudación del empréstito interno destinado al redescuento"
    serie: null
    anio: 1891
    fuente: "Terry (1893: 192-193)"

fuentes_primarias:
  - tipo: ley
    ref: "Ley de Bancos Nacionales Garantidos del 3/11/1887 (BEHP, pp. 206-217)"
    url: ""
  - tipo: ley
    ref: "Ley 2741 del 7/10/1890, creación de la Caja de Conversión (Anales, complemento 1920-1940, pp. 212-214)"
    url: ""

medios: []

relacionados: [bancos-garantidos-1887, caja-conversion-1890, banco-nacion-1891, ley-conversion-1899]
redactor: "Claude (borrador) — pendiente de revisión humana"
revisado: 2026-09-13
verificado: false
---

## Contexto

En 1890 y 1891 la Argentina atravesó la que probablemente fue **la primera crisis de los
mercados emergentes**: se cerraron a la vez el crédito externo y el interno, el público sustituyó
moneda doméstica por oro, las corridas cambiarias arrastraron a los depósitos y el sistema
bancario quebró. La crisis llevó el nombre del acreedor —la casa Baring Brothers & Co. de
Londres, con una cartera cargada de títulos argentinos— y no el del deudor, lo que ya dice algo
sobre desde dónde se escribió esa historia [@gomez-2012-baring].

El mecanismo se arma en la década previa, y es institucional antes que coyuntural. La
convertibilidad instaurada con la ley monetaria de 1881 duró apenas diecisiete meses: en enero
de 1885 los decretos que suspendieron la conversión dejaron {{c:emision85}} en circulación con un
respaldo de {{c:respaldo85}}. La circular del 9 de marzo de ese año permitió **movilizar el encaje
metálico**, y con eso desapareció el costo principal de emitir: el rendimiento de la emisión pasó de
`i(B−R)` a `i(B+R)`. Para diciembre de 1886 la emisión ya era de {{c:emision86}}.

La Ley de Bancos Nacionales Garantidos de 1887 fue el paso decisivo. Copiaba la *National
Currency Act* estadounidense de 1862, pero con dos diferencias que la volvían otra cosa: los bonos
de garantía **se creaban especialmente** para respaldar cada emisión —en Estados Unidos venían de
un mercado secundario activo—, y el sistema funcionaba como un "patrón oro de mano única", que
expandía la base con la entrada de oro pero no la contraía con su salida [@dellapaolera-taylor-2003,
pp. 68-72]. Las provincias se endeudaron en Londres al 6% para comprar bonos nacionales que
rendían 4,5%, y con los billetes resultantes —un pasivo que no pagaba interés— prestaban a
interés. Era un arbitraje. La emisión autorizada creció {{c:emision89}} en un solo año.

Del otro lado, la política fiscal. Los ingresos venían del comercio exterior (dos tercios, aranceles
a la importación) y los gastos siempre los excedieron. Desde 1888, cuando las autoridades
decidieron acelerar la inversión pública, el déficit se disparó: {{c:deficit89}} en 1889, y la deuda
pública pasó de 270% del gasto en 1884-1887 a {{c:deudagasto}} en 1890.

Sobre las causas hay tres lecturas y la ficha no las zanja. **Williams** y **Ford** las ubican en el
lado real —la interrupción del flujo de capitales y el saldo negativo de la balanza de pagos—,
aunque discrepan sobre el mecanismo de ajuste (precio en Williams, ingreso en Ford).
**Cortés Conde** las ubica en el lado monetario: el saldo negativo de la cuenta capital lo produjo
la fuga de capitales, no el corte de préstamos nuevos [@cortesconde-1989, pp. 216-217].
**della Paolera y Taylor** proponen la síntesis que este relato sigue: la causa fue la
*inconsistencia* entre la política monetaria y la fiscal, que terminó reasignando casi todo el
metálico del sistema bancario hacia el público.

## Cronología

- **1885-01-09** — Decretos de enero y marzo suspenden la convertibilidad por dos años y dan
  curso legal a los billetes de banco. En circulación: {{c:emision85}}, con {{c:respaldo85}} de respaldo.
- **1885-03-09** — Una circular autoriza a movilizar el encaje metálico. Emitir deja de tener costo.
- **1887-11-03** — Ley de Bancos Nacionales Garantidos. Se pasa de una pluralidad de bancos
  autorizados a un sistema de banca libre con emisión garantida por bonos oro.
- **1888-03-01** — Los siete viejos bancos de emisión ya están incorporados a la ley.
- **1889-03-01** — La emisión autorizada creció {{c:emision89}} en un año.
- **1889** — El gobierno propone pagar en pesos papel parte de la deuda contraída en oro:
  default parcial. Se cierra el mercado internacional de títulos.
- **1889-03-14** — Ante la salida de oro (3 millones a Montevideo y 5 a Europa sólo en febrero)
  se prohíbe negociarlo en la Bolsa. La salida continúa: el 4 de mayo la demanda de oro en el
  Banco Nacional es de 10 millones en un día.
- **1889-12** — Las reservas del Banco Nacional caen a {{c:reservas89}}. Salta la prima del oro y
  estalla la crisis. El tipo de cambio pasa de 1,48 a 1,80 y la inflación de 0% a 19,8%.
- **1890-01** — Primera corrida sobre los depósitos del Banco Nacional y del Banco de la
  Provincia de Buenos Aires. El gobierno autoriza billetes de vieja emisión: en marzo y abril hay
  35,1 millones de m$n circulando sin respaldo en títulos.
- **1890-04-16** — Cambio de gabinete. José E. Uriburu asume Hacienda, propone subir 15% las
  tarifas y cobrar en oro la mitad de los impuestos aduaneros, y pide la renuncia del directorio
  del Banco Nacional. Juárez Celman primero acepta y después se retracta; Uriburu renuncia.
- **1890-06** — El Banco Nacional notifica a Baring Brothers la suspensión del pago trimestral
  del servicio de la deuda. Segunda corrida.
- **1890-08-05** — Renuncia Juárez Celman. Asume Carlos Pellegrini, con Vicente F. López en Hacienda.
- **1890-09-06** — Se autorizan 60 millones en billetes de tesorería para asistir a los dos bancos.
- **1890-10-07** — **Ley 2741: se crea la Caja de Conversión.** La emisión, que era un pasivo de
  los bancos garantidos, pasa a un organismo estatal.
- **1890-11** — Victorino de la Plaza viaja a Londres a negociar una moratoria. En medio de las
  negociaciones, Baring Brothers entra en cesación y el Banco de Inglaterra —apartándose de las
  reglas del patrón oro— sale al rescate.
- **1891-01-24** — Empréstito de Consolidación: {{c:emprestito91}} garantizados con la recaudación
  aduanera. A cambio, Argentina se compromete a no contraer deuda nueva y a no otorgar
  redescuentos durante tres años.
- **1891-04** — Sin prestamista de última instancia, tercera corrida. El empréstito interno de 100
  millones destinado al redescuento recauda {{c:interno91}}, y buena parte se pagó con cheques del
  mismo banco que se quería asistir. **El Banco Nacional y el Banco de la Provincia cierran sus puertas.**
- **1891-05** — La corrida alcanza a los bancos particulares, que cierran casi todos.
- **1891-10-16** — Ley 2841: se crea el Banco de la Nación Argentina sobre las ruinas del Banco Nacional.
- **1891-12-31** — Cierre del año: tipo de cambio {{c:tc91}}, inflación {{c:infl91}}, riesgo país
  {{c:riesgo91}}. Acumulado 1889-1891: {{c:acumulada}}.

## Qué mirar

La crisis es el caso de manual del **trilema macroeconómico**. Entre 1880 y 1889 Argentina eligió
cuenta de capital abierta más compromiso cambiario, resignando autonomía monetaria. Cuando el
techo de endeudamiento externo apareció (1889), las autoridades se desviaron hacia oferta
monetaria endógena para financiar el déficit, y el público anticipó correctamente el movimiento.
El resultado —fuga hacia el oro, agotamiento de reservas, salto cambiario— es el mismo que se
repite en 1975, 1989 y 2001.

En las series troncales lo que debería verse: un salto del **tipo de cambio real** en 1890-1891 y
una aceleración de la **inflación** que, entre 1889 y 1891, acumula 163,7%; un salto de la
**deuda / PBI**; y una caída del **PBI per cápita**. Y una comprobación de consistencia que vale la
pena: entre 1889 y 1891 la inflación observada acumulada (163,7%) y la *contrafactual* —la que
habría habido si todo el déficit se hubiera monetizado— (154,9%) casi coinciden. En plena crisis,
los billetes se emitieron con el único propósito de financiar el déficit fiscal.

## Citas

> "La falta de coordinación entre políticas monetarias y fiscales resultó en una casi completa
> reasignación de metálico del sistema bancario hacia el público y finalmente provocó la crisis
> de Baring."
> — [@dellapaolera-taylor-2003, pp. 35-36]

> "El público anticipó correctamente que la política monetaria de «flotación sucia» pronto se
> desviaría del anunciado objetivo de retomar la paridad en busca de ser una herramienta al
> servicio del derroche fiscal."
> — [@dellapaolera-taylor-2003, p. 105]

> "Con el interés de los Bonos Nacionales, a 4,5, se pagaba el de los préstamos externos (algo
> más caros, un 6%), y se obtenían billetes que se entregaba a los clientes por los créditos por
> los que se les cobraba interés, mientras que la deuda de los bancos (los billetes) no pagaba
> interés alguno."
> — [@cortesconde-1989, p. 184]

> "Provincias cuyos nombres jamás habían sonado en las Bolsas europeas, y que no tenían
> industria ni producción con que responder a tan cuantiosos préstamos, obtuvieron millones de
> pesos oro."
> — [@hansen-1916, pp. 422-423]
