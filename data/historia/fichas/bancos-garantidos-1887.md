---
id: bancos-garantidos-1887

series: [deuda, infl, tcr]

cifras:
  - id: capitalMin
    v: "250.000 m$n"
    et: "Capital realizado mínimo para poder emitir billetes"
    serie: null
    anio: 1887
    fuente: "Ley del 3/11/1887, art. 5 (BEHP, pp. 206-209)"
  - id: aforo
    v: "85 %"
    et: "Precio en oro de los títulos que respaldaban cada emisión"
    serie: null
    anio: 1887
    fuente: "Ley del 3/11/1887, art. 7 (BEHP, pp. 206-209)"
  - id: interes
    v: "4,5 % + 1 %"
    et: "Interés y amortización anual de los Bonos Oro Nacionales"
    serie: null
    anio: 1887
    fuente: "Ley del 3/11/1887 (BEHP, pp. 206-209)"
  - id: encaje
    v: "10 %"
    et: "Reserva de oro exigida sobre la emisión — y era movilizable"
    serie: null
    anio: 1887
    fuente: "Ley del 3/11/1887, art. 14 (BEHP, p. 213)"
  - id: cupo
    v: "40 mill. m$n"
    et: "Cupo de emisión para bancos nuevos: 15 para nueve provincias del Interior, 25 para el resto"
    serie: null
    anio: 1887
    fuente: "Ley del 3/11/1887, art. 32 (BEHP, pp. 213-214)"
  - id: emision88
    v: "88,3 mill. m$n"
    et: "Emisión autorizada al 1 de marzo de 1888, con los siete viejos bancos ya incorporados"
    serie: null
    anio: 1888
    fuente: "Decretos 16 y 29/2/1888 (BEHP, pp. 230-246)"
  - id: salto89
    v: "+67,7 mill. m$n"
    et: "Emisión adicional al 1 de marzo de 1889: un 73% de aumento en un año"
    serie: null
    anio: 1889
    fuente: "BEHP, pp. 80-81"
  - id: respaldo89
    v: "57,6 mill. $ oro"
    et: "Respaldo en oro de esa emisión adicional (85% marginal)"
    serie: null
    anio: 1889
    fuente: "BEHP, pp. 80-81"
  - id: arbitraje
    v: "6 % contra 4,5 %"
    et: "Costo del crédito de Londres frente al rendimiento de los Bonos Oro Nacionales"
    serie: null
    anio: 1888
    fuente: "Cortés Conde (1989: 184)"
  - id: impuesto
    v: "2 % sobre depósitos"
    et: "Impuesto propuesto en mayo de 1889 a los bancos que no se adhirieran"
    serie: null
    anio: 1889
    fuente: "Williams (1920: 85)"
  - id: privados89
    v: "+6,1 mill. m$n"
    et: "Emisión de los siete bancos privados incorporados entre mayo y julio de 1889"
    serie: null
    anio: 1889
    fuente: "Martí (2005: 80)"

fuentes_primarias:
  - tipo: ley
    ref: "Ley de Bancos Nacionales Garantidos del 3/11/1887 (BEHP, pp. 206-217)"
    url: ""
  - tipo: decreto
    ref: "Decreto reglamentario del 18/11/1887 (BEHP, p. 224)"
    url: ""
  - tipo: decreto
    ref: "Decretos del 16 y 29/2/1888, incorporación de los viejos bancos de emisión (BEHP, pp. 230-246)"
    url: ""

medios: []

relacionados: [suspension-convertibilidad-1885, movilizacion-encaje-1885, expansion-emision-1888, default-parcial-1889, crisis-baring-1890, caja-conversion-1890, garantias-ferroviarias-1886]
redactor: "Claude (borrador) — pendiente de revisión humana"
revisado: 2026-09-13
verificado: false
---

## Contexto

La Ley de Bancos Nacionales Garantidos es el evento que explica la crisis de Baring, y por eso
merece ficha propia: sin entender qué permitía esta ley, 1890 parece un accidente. No lo fue.

El diseño venía de afuera y era respetable: estaba inspirado en la **National Currency Act**
estadounidense de 1862. Cualquier banco con {{c:capitalMin}} de capital realizado podía emitir
billetes, siempre que comprara fondos públicos nacionales por el monto total a emitir. La Oficina
Inspectora —que la ley creaba— le entregaba billetes por una suma igual a los títulos comprados,
y esos títulos quedaban en garantía. Se pasaba de una pluralidad de bancos autorizados por el
Estado a un sistema de **banca libre**.

Pero había dos diferencias con el modelo estadounidense que lo volvían otra cosa.

**Primera: de dónde salían los bonos.** En Estados Unidos los bonos elegibles venían de un mercado
secundario activo. En la Argentina **se creaban especialmente** para respaldar cada nueva emisión.
Eso significa que emitir dinero *fabricaba deuda pública*, en vez de apoyarse en deuda que ya
existía. Cada peso nuevo en circulación agrandaba el pasivo del Estado.

**Segunda: el mecanismo sólo funcionaba en un sentido.** Los bancos estaban obligados a comprar
títulos en oro por el monto total de los billetes a emitir, de modo que la base monetaria se
expandía con el oro depositado en el Banco Nacional. Pero **no se contraía cuando las reservas
caían**. Della Paolera y Taylor lo bautizaron un *patrón oro de mano única*: el aforo era del
{{c:aforo}} sobre cada unidad adicional de emisión, y no había mecanismo simétrico de retiro.

A eso se sumaba algo que la ley heredaba de 1885: el encaje de {{c:encaje}} en oro sobre la
emisión **podía movilizarse** por medio de operaciones legítimas y usuales. Es decir, la reserva
podía prestarse. Lo que quedaba de la ortodoxia era formal.

### El arbitraje

Puesto todo junto, el negocio bancario de emisión se convirtió en una operación de arbitraje, y
así lo entendieron sus participantes. Los bancos provinciales recién creados —La Rioja, Catamarca,
San Luis, Corrientes— y algunos viejos, como el de Córdoba, **se endeudaron en el mercado de
Londres para comprar los Bonos Oro Nacionales** que la ley les exigía. El cálculo era simple:
{{c:arbitraje}}. Se pagaba el interés del préstamo externo con el de los bonos, se cobraba interés
por los créditos otorgados con los billetes emitidos, y esos billetes —que eran deuda del banco—
no pagaban interés alguno.

La fórmula del rendimiento de la emisión, que antes de 1885 era `rB = i(B−R)` y con el encaje
movilizable pasó a `rB = i(B+R)`, terminó siendo `rB = K + i·0,90·B − i*·T`, donde `i*` es la tasa
a la que las provincias conseguían fondos en Londres.

Y funcionó exactamente como estaba diseñado. La adhesión de los viejos bancos emisores fue
**absoluta**: los siete se incorporaron antes del 1 de marzo de 1888, con {{c:emision88}} de
emisión autorizada. Para los privados hizo falta un empujón: recién se sumaron cuando en mayo de
1889 el gobierno presentó al Congreso un proyecto de {{c:impuesto}} para los bancos comerciales que
no se adhirieran. Siete entidades de la Capital —el Francés del Río de la Plata, Londres y Río de
la Plata, el Nuevo Banco Italiano, De Italia y Río de la Plata, el Inglés de Río de Janeiro,
Carabassa y Del Comercio— entraron entre mayo y julio de ese año, sumando {{c:privados89}}.

Al 1 de marzo de 1889 la emisión adicional era de {{c:salto89}}, respaldada por {{c:respaldo89}}
en oro. En un año.

## Cronología

- **1885-01-09** — Los decretos de enero suspenden la convertibilidad e imponen tres restricciones
  a los bancos: no bajar las reservas, retener la mitad de las utilidades y no aumentar la emisión.
- **1885-03-09** — Una circular autoriza a movilizar el encaje. Cae la primera restricción.
- **1885-10-14** — La ley ratifica la inconvertibilidad, devuelve a los bancos la disposición de
  sus utilidades y libera al Banco Nacional del tope de emisión. Caen la segunda y la tercera.
- **1886-12-24** — Un decreto prorroga la suspensión dos años más y autoriza aumentos de emisión
  a Buenos Aires, Santa Fe y Córdoba.
- **1887-11-03** — **Ley de Bancos Nacionales Garantidos.** Banca libre con emisión respaldada por
  bonos oro comprados al {{c:aforo}} de su valor, que rinden {{c:interes}}. Cupo de {{c:cupo}} para
  bancos nuevos.
- **1887-11-18** — Decreto reglamentario. Los bancos que no se incorporen pueden circular billetes
  inconvertibles sólo hasta treinta días después del 9 de enero de 1889.
- **1888-02-29** — Los siete viejos bancos de emisión ya están adentro: {{c:emision88}} autorizados,
  con curso legal en todo el país.
- **1888-07-19** — Ley especial: el Banco Provincial de Córdoba puede subir su emisión 4 millones
  para igualarla a su capital realizado.
- **1888-09-19 / 1888-11-06** — Nuevas autorizaciones de aumento: Buenos Aires de 34,4 a 50
  millones, Entre Ríos de 3 a 8,5, Santa Fe de 5 a 20, Córdoba de 8 a 17, Tucumán de 0,4 a 3,6,
  y el Banco Nacional hasta el doble de su capital.
- **1888 (ago-dic)** — Se incorporan diez bancos nuevos, casi todos mixtos con fuerte
  participación de los estados provinciales: Mendoza, San Juan, La Rioja, Santiago del Estero,
  Catamarca, San Luis, Corrientes, Salta y dos privados porteños.
- **1889-03-01** — {{c:salto89}} de emisión adicional en doce meses, con {{c:respaldo89}} de oro.
- **1889-05** — El proyecto de {{c:impuesto}} convence a los bancos privados de adherirse.
- **1889-12** — Las reservas del Banco Nacional caen a 6 millones de pesos oro. Estalla la crisis.
- **1890-10-07** — La Ley 2741 crea la Caja de Conversión y le saca la emisión a los bancos
  garantidos. El sistema dura tres años menos un mes.

## Qué mirar

El indicador que cuenta la historia no es monetario sino fiscal: **la deuda pública sobre el gasto**,
que pasa de 270% en 1884-1887 a 350% en 1887-1889 y a 630% en 1890. Ese salto es en buena medida
el sistema de bancos garantidos funcionando según lo previsto, porque emitir *creaba* deuda.

Lo contraintuitivo: durante 1888, el primer año pleno de la ley, la **inflación observada fue nula**
mientras la contrafactual —la que habría habido si todo el déficit se hubiera monetizado— fue del
7,9%, y el riesgo país siguió bajando hasta 2,18%. El sistema estaba expandiendo la base contra
reservas marginales conseguidas con deuda externa, así que el desequilibrio fiscal no aparecía en
los precios. Apareció después, todo junto. Es el patrón de un ancla que oculta el problema en vez
de resolverlo, y vale la pena tenerlo presente cuando se mire 1979 o 1998 en las mismas series.

## Citas

> "En los Estados Unidos los bonos elegibles provenían de mercados secundarios activos, mientras
> que en la Argentina los bonos eran especialmente creados para el fin de respaldar las nuevas
> emisiones."
> — [@dellapaolera-taylor-2003, p. 68]

> "Con el interés de los Bonos Nacionales, a 4,5, se pagaba el de los préstamos externos (algo más
> caros, un 6%), y se obtenían billetes que se entregaba a los clientes por los créditos por los
> que se les cobraba interés, mientras que la deuda de los bancos (los billetes) no pagaba interés
> alguno."
> — [@cortesconde-1989, p. 184]

> "Provincias cuyos nombres jamás habían sonado en las Bolsas europeas, y que no tenían industria
> ni producción con que responder a tan cuantiosos préstamos, obtuvieron millones de pesos oro."
> — [@hansen-1916, pp. 422-423]
