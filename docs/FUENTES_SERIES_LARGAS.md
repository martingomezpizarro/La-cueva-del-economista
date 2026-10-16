# Series largas: hasta dónde se puede ir hacia atrás, y con qué fuente

Registro del 2026-08-28. Para tres series el BCRA no es el techo, y para otra la limitación
no es de fuente sino histórica. Conviene tener claro cuál es cuál antes de salir a buscar.

---

## 1. Reservas internacionales

**Ya tenemos la serie oficial más larga que existe**: `idVariable 1605`, mensual, desde
**febrero de 1940**. Está en el catálogo como `res_mensual`, pendiente de bajar.

Y hay un techo que no es de fuente sino institucional: **el BCRA se creó en 1935**. Antes
de esa fecha no existen «reservas del Banco Central» — existían las reservas de la **Caja
de Conversión** (1899-1929), que son otra cosa: respaldo metálico de la emisión bajo patrón
oro. Empalmarlas sin decirlo sería un error conceptual, no un empalme.

| Fuente | Qué da | Cobertura | Cómo se accede |
|---|---|---|---|
| **BCRA API id 1605** | Reservas a fin de mes | **1940-02 → hoy** | ya conectada |
| **BCRA API id 1** | Reservas diarias | 1996-01 → hoy | ya conectada |
| **FMI — IFS** | Reservas, mensual, comparable entre países | 1948 → hoy | `data.imf.org/ifs`, con API |
| **Della Paolera & Taylor**, *Straining at the Anchor* | Oro y respaldo de la Caja de Conversión | 1880-1935 | libro, series en apéndice |
| **Instituto de Economía Bancaria (UBA)** | Circulación, existencias de oro y balance de pagos | **1901-1935** | *La Economía Argentina a través de sus índices más representativos* |
| **Memoria de la Caja de Conversión (1933)** | Respaldo oro de la emisión | hasta 1933 | fuente primaria de época |
| **Salama (UNLP, doc. 28)** | Reconstruye las series y marca sus límites | 1920-1935 | `depeco.econo.unlp.edu.ar` |
| **Ferreres**, *Dos siglos* | Serie anual empalmada | 1810-2010 | libro / `dossiglos.fundacionnorteysur.org.ar` |

**Conclusión:** bajar la id 1605 y quedarse ahí. Para el período de la Caja de Conversión,
una serie SEPARADA y rotulada como tal, no un empalme.

**Cómo conseguirla, en concreto.** La compilación del Instituto de Economía Bancaria
(1901-1935) es la vía más directa: es contemporánea a los hechos y trae circulación, oro
y balance de pagos juntos. Salama la reconstruye en el documento 28 de la UNLP y **advierte
que las series no constituyen un balance completo** — esa advertencia hay que trasladarla a
`proc.notas`, no dejarla en el camino. Las fuentes primarias que respaldan todo son la
*Memoria de la Caja de Conversión de 1933* y las *Memorias del Banco de la Nación* de 1929,
1932 y 1934. Es transcripción manual y verificación contra dos fuentes: no hay descarga.

Y una lectura que vale la pena para el uso que le querés dar: bajo patrón oro, el respaldo
metálico **sí** funciona como medida de liquidez sistémica, porque la emisión estaba atada
a él por ley. Es un indicador distinto de las reservas post-1935, donde ya hay política
monetaria discrecional. Son dos regímenes, no dos tramos de una serie.

---

## 2. Tipo de cambio oficial

Acá el problema no es la fuente: **la Comunicación A 3500 es de 2002**. Antes de esa fecha
no existe «el A3500», existe otro régimen cambiario. Y entre 1880 y hoy Argentina cambió
**cinco veces de moneda** —peso moneda nacional, ley 18.188, peso argentino, austral, peso
convertible— y tuvo largos períodos de **tipos de cambio múltiples** (el dólar MUC de los
ochenta, entre otros).

Una serie larga de tipo de cambio no se «consigue»: **se construye**, empalmando con los
coeficientes de conversión y eligiendo qué tipo se toma cuando hubo varios. Eso es una
decisión metodológica que hay que dejar escrita.

| Fuente | Qué da | Cobertura |
|---|---|---|
| **BCRA API id 5** | Mayorista de referencia (A3500) | 2002-03 → hoy |
| **BCRA API id 4** | Minorista promedio vendedor | 2010-06 → hoy |
| **FMI — IFS** | TC oficial, mensual | 1948 → hoy |
| **Banco Mundial** `PA.NUS.FCRF` | TC oficial, promedio anual | 1960 → hoy |
| **Ferreres** | Serie empalmada con cambios de moneda | 1810-2010 |
| **Della Paolera & Taylor** | Peso oro y peso papel, con el premio del oro | 1880-1935 |

**Conclusión:** el empalme largo sale de Ferreres, y la parte 1880-1935 de Della Paolera &
Taylor. Ambas se transcriben, y el criterio de empalme va documentado en la serie.

---

## 3. Depósitos y préstamos en dólares

Otra limitación histórica, no de fuente. Los depósitos en dólares en el sistema local
**recién se vuelven relevantes con la reforma financiera de 1977**, y masivos con la
convertibilidad (1991). Y en **2002 fueron pesificados**: la serie tiene un quiebre
estructural que ninguna fuente puede suavizar.

| Fuente | Cobertura |
|---|---|
| **BCRA `Series.xlsm`** (ids 107, 108 y 118-125) | 2002-12 → hoy, diaria |
| **BCRA — Boletín Estadístico** (planillas) | años noventa, mensual |

### A qué variable macro hacen referencia

Esto es lo importante y es la razón de tenerlas. **No son series interesantes por su nivel,
sino porque son el insumo de dos ratios**:

**Dolarización de depósitos** = depósitos en USD / depósitos totales.
Es la medida estándar de *sustitución de moneda*: cuánto del ahorro doméstico rechaza el
peso como reserva de valor. En la literatura de riesgo país y de crisis emergentes es un
predictor de primer orden — Reinhart, Rogoff y Savastano lo trabajan en *Addicted to
Dollars*, y Levy Yeyati lo usa como indicador de fragilidad financiera.

**Descalce de monedas** (*currency mismatch*) = préstamos en USD / depósitos en USD, y
préstamos en USD sobre el crédito total.
Mide cuánto se le presta en dólares a deudores que generan pesos. Es el mecanismo por el
cual **una devaluación se vuelve contractiva en vez de expansiva**: destruye el patrimonio
de los deudores en moneda extranjera antes de mejorar las exportaciones. Es el canal de
balance de Calvo y Krugman, y el corazón de la crisis de 2001-2002.

Para un trabajo sobre riesgo país argentino, la dolarización de depósitos es además la base
del **run cambiario-bancario**: la corrida de 2001 se lee en esa serie antes que en el EMBI.

**Pendiente:** el catálogo tiene los cuatro niveles (`dep_usd_tot`, `dep_usd_res`,
`dep_usd_priv`, `prest_usd`) pero **ninguno de los dos ratios**. Habría que agregarlos como
series de elaboración propia, con sus insumos declarados.

---

## 4. ITCRM: qué hay además del BCRA

El ITCRM del BCRA arranca en **1997** y no se publica por la API. **1994 (BIS) no era el
techo**: hay una serie mensual que llega a **1960**.

| Fuente | Qué da | Cobertura | Licencia |
|---|---|---|---|
| **Bruegel — REER, índice estrecho** (Darvas) | TCR efectivo, 51 socios, deflactado por IPC | **1960 → hoy, MENSUAL** | **libre con cita** |
| Bruegel — índice amplio | 120 socios | 1993 → hoy, mensual | libre con cita |
| BIS — REER (`RBARBIS` vía FRED) | Canasta amplia, base 2020=100 | 1994-01 → hoy, mensual | cita obligatoria |
| FMI — IFS | REER y NEER | 1980 → hoy | cita |
| **Global Macro Database** | 46 variables macro empalmadas, 243 países | series desde 1086 | cita académica |

**La recomendación cambia al Bruegel**: mensual desde 1960 —**37 años más que el ITCRM del
BCRA**—, misma metodología para todos los países, y licencia que permite usarlo transformado
mientras se cite. Última actualización: agosto de 2026. Al bajarlo hay que verificar desde
cuándo arranca Argentina en concreto: la base declara 178 países pero no todos empiezan
en 1960.

Antes de 1960 sigue habiendo que construirlo (TC nominal × IPC socio / IPC local, ponderado
por comercio), y ahí conviene mirar la **Global Macro Database**, que ya empalmó 32 fuentes
históricas — con el cuidado de revisar QUÉ fuente primaria usó para Argentina en cada tramo:
es un agregador, no un relevamiento propio.

**Atajo para buscar:** el repositorio abierto `forex-centuries` reúne 27 de estas fuentes en
CSV normalizados (tipos de cambio de ~243 países desde 1106, inflación desde 1500, deuda
soberana desde 1800, regímenes cambiarios 1800-2021) con actualización semanal. Sirve para
**localizar** una serie rápido; la cita va siempre a la fuente primaria, nunca al repositorio.

## 5. ¿La API tiene los agregados monetarios en frecuencia mensual?

**Sí, y son los más largos que publica.** Es el bloque que el BCRA incorporó el 21 de
agosto de 2026:

| Agregado | Mensual (largo) | Diario |
|---|---|---|
| Base monetaria | id **1606**, desde **1940-06** | id 15, desde 1996-01 |
| Circulación monetaria | id **1607**, desde 1940-06 | id 16, desde 1996-01 |
| Billetes y monedas en poder del público | id **1608**, desde 1940-06 | id 17, desde 1996-01 |
| M1 | ids **1611** (ML+ME) y **1612** (ML), desde 1940-06 | — |
| M2 | ids **1617** (ML+ME) y **1618** (ML), desde 1940-06 | id 109, desde 2002-12 |
| M3 | ids **1623** (ML+ME) y **1624** (ML), desde 1940-06 | — |

Tres cosas antes de empalmarlos:

1. **Unidades distintas.** El bloque mensual va en **miles de ARS**; las series diarias, en
   **millones**. Factor 1000 de diferencia.
2. **No son el mismo concepto.** El M2 diario (id 109) es uno solo; el mensual distingue
   M2 en moneda local del M2 en moneda local + extranjera. Elegir cuál es «el M2» es una
   decisión, no un detalle.
3. **M1 y M3 solo existen en mensual.** No hay versión diaria.

Para trabajo histórico, la mensual gana por lejos: 1940 contra 1996, y encima trae M1 y M3
que en diario no existen.

---

## 6. Qué queda anotado para después

- Bajar `res_mensual` (id 1605) y dejar de usar la diaria para trabajo histórico.
- Construir el empalme largo de tipo de cambio desde Ferreres, con criterio escrito.
- Agregar los **ratios de dolarización y descalce** como series propias.
- Sumar el **BIS REER vía FRED** como la serie comparable internacionalmente.
- Decidir cuál M2 es el canónico del catálogo.
- Registrar FRED como fuente: da acceso a BIS, FMI y series de Argentina con una sola API.
