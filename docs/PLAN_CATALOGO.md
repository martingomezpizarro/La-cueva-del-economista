# Plan: rehacer el catálogo de series y poder curarlo a mano

Objetivo: pasar de un catálogo que **solo se edita en JSON a ciego** a uno que se pueda
**mirar, corregir y auditar visualmente**, sin perder la trazabilidad que ya se ganó.

Alcance acordado (2026-08-27): rehacer la taxonomía · limpiar duplicados y basura ·
completar las fichas · **auditar que los datos sean correctos**. La descarga masiva desde
las fuentes queda fuera por ahora.

---

## 1. Diagnóstico

### 1.1 El catálogo es más grande de lo que decía

La primera auditoría reportó 356 series. Estaba mal: **no descendía por `children`**, y ahí
vive un tercer, cuarto y quinto nivel de anidamiento (el balance de pagos, el esquema
fiscal y los vencimientos de deuda cuelgan sus aperturas de la serie agregada). Corregido:

| | Antes (mal) | Real |
|---|---|---|
| Series | 356 | **582** |
| Entradas (serie × frecuencia) | 494 | **739** |
| Sin procedencia | 0 | **226** (ya cargadas) |

Reparto por nivel: 356 en el primero, 94 en el segundo, 120 en el tercero, 7 en el cuarto,
5 en el quinto.

**La lección importa más que el número**: una estructura que anida de tres formas distintas
esconde series. Si a mí se me pasaron 226, a cualquier consumidor del catálogo también.

### 1.2 Los datos están mejor de lo que parecía

Una primera pasada marcó 90 «saltos de escala». Falsos positivos: en series que cambian de
signo (saldo comercial, brecha, variaciones) el ratio entre observaciones consecutivas
explota sin que pase nada raro. Filtrando esas, queda **un solo salto genuino**
(`ica_iauto`, 20,9× — importación de vehículos, plausible).

Estado real de los datos:

| Hallazgo | Cuántos | Qué es |
|---|---|---|
| Series OK | 609 entradas | leen bien, rango razonable |
| Pendientes de descarga | 113 | **84** apuntan a `vencimientos_1y_nuevo.csv`, que no existe; 29 son las nuevas del BCRA |
| Columna existe pero está vacía | 17 | todas de `vencimientos_2y_nuevo.csv`, 71 filas nulas |
| Huecos internos | 9 | faltantes en el medio de la serie |
| Desactualizadas (< 2025) | 4 | `pbi_pc_usd`, `fis_prima2`, `fis_fin2`, `wgi_polstab` |
| Serie constante / vacía | 1 | `dummy_gobiernos_var` |
| Duplicados exactos (mismo archivo + columna) | **0** | no hay basura duplicada |
| IDs repetidos | **0** | la identidad es sólida |

O sea: **el problema no son los datos, es la estructura y los nombres.**

### 1.3 Los nombres no identifican la serie

48 etiquetas viven en más de un subgrupo. «Brasil» es a la vez un socio comercial en
*Sector Externo* y un componente del ITCRM en *Monetario y Cambiario*. Dentro de su árbol
se entiende; en un buscador, en un gráfico o en la cita de un informe, no.

### 1.4 La taxonomía está desbalanceada

| Familia | Subgrupos | Series | Subgrupos de 1 |
|---|---|---|---|
| Actividad y Cuentas Nacionales | 12 | 103 | 0 |
| Sector Externo | 11 | 85 | 0 |
| Monetario y Cambiario | 11 | 54 | 3 |
| Contexto Global y Riesgo | 6 | 30 | 2 |
| Finanzas Públicas | 4 | 27 | 1 |
| Deuda y Riesgo Soberano | 8 | 24 | 4 |
| Expectativas y Confianza | 6 | 18 | 0 |
| Dummies y Variables Estructurales | 0 | 13 | — |
| **Precios e Inflación** | **1** | **2** | 0 |

Dos cosas saltan. **Precios e Inflación tiene 2 series** en una plataforma de historia
económica argentina — y ahora el BCRA publica inflación mensual desde 1943. Y hay **10
subgrupos de una sola serie**, que son ruido de navegación.

### 1.5 Por qué hoy no se puede editar visualmente

`catalogo.json` es la fuente de verdad, pero `scripts/generar_arbol_visualizador.py` lo
**hornea** como `const CATALOG` dentro de `web/explorador.html` (7.204 líneas). Hay dos
copias del catálogo y un paso de build entre editar y ver. Cualquier editor en vivo choca
contra eso.

---

## 2. La idea: normalizar antes de construir

No se puede construir un editor visual sobre un modelo que anida de tres formas distintas.
El orden es: **primero el modelo, después el transporte, después la interfaz, y recién ahí
la curaduría.** Saltearse el primer paso significa construir la interfaz dos veces.

---

## Fase 0 — Normalizar el modelo *(base de todo)*

**Problema.** Hoy una serie puede declararse de tres maneras: con `file` directo, con
`sources` (una por frecuencia), o colgada de `children` de otra serie. La jerarquía tiene
niveles variables. `unit` es texto libre.

**Qué se hace.**

1. **Una sola forma de declarar dónde está el dato**: siempre `sources: [{freq, file, dateCol, valCol, proc}]`, aunque haya una sola. Se elimina `file`/`dateCol`/`valCol` sueltos en el item.
2. **Jerarquía de profundidad fija**: `familia › subgrupo › serie`. Lo que hoy cuelga de `children` pasa a ser serie de pleno derecho, con un campo `parte_de: "<id del agregado>"` que preserva la relación todo/parte sin anidar. El balance de pagos sigue siendo navegable como árbol, pero el árbol se **deriva** de `parte_de`, no de la estructura del archivo.
3. **`id` global, estable y explícito**: el id es el contrato. Se congela y se agrega `alias: []` para los nombres viejos, de modo que renombrar no rompa nada.
4. **Unidades de un vocabulario cerrado** (`cueva/fuentes/unidades.json`): magnitud, escala y moneda separadas — `{magnitud: "moneda", escala: "miles", moneda: "ARS"}` en vez de `"Miles de ARS"`. Sin esto no se puede comparar ni empalmar automáticamente (el bloque histórico del BCRA viene en miles de ARS y el diario en millones).
5. **Contrato Pydantic** en `cueva/api/esquemas.py`: `SerieCatalogo`, `FuenteDeDatos`, `Procedencia`. El catálogo se valida al cargar y al guardar. Un catálogo inválido no se escribe.
6. **Migración con script** (`scripts/migrar_catalogo_v2.py`) + `version: 2` en el JSON, reversible, con test que compara serie por serie que no se perdió ninguna.

**Terminado cuando**: las 582 series pasan el contrato, `pytest` verde, el explorador
sigue mostrando lo mismo que antes.

---

## Fase 1 — El catálogo se sirve por API *(quita el horneado)*

1. `GET /api/v1/catalogo` — el árbol completo, validado, con `ETag` por hash del archivo.
2. `GET /api/v1/catalogo/{id}` — una serie con su ficha, su cobertura real y sus alias.
3. `explorador.html` pide el catálogo al arrancar en vez de traerlo horneado. Se borran los marcadores `__CATALOG_INICIO__` y el paso de build queda **solo** para el standalone del Trabajo Final.
4. Caché por mtime, igual que `/api/v1/explorador/datos`.

**Terminado cuando**: se puede editar el JSON, recargar el navegador y ver el cambio, sin
correr ningún script.

---

## Fase 2 — El editor: página `/catalogo`

Página propia (`web/catalogo.html`), no una pestaña dentro de las 7.204 líneas del
explorador. Tres paneles:

**Izquierda — el árbol.** Familias › subgrupos › series, arrastrable. Mover una serie de
subgrupo, reordenar, crear/renombrar/fusionar subgrupos. Cada nodo con un semáforo del
estado de auditoría: verde (verificada), amarillo (confianza media), rojo (dato con
problema), gris (pendiente de descarga).

**Centro — la ficha.** Formulario sobre el bloque `proc`: etiqueta, unidad (desplegable del
vocabulario cerrado), definición, fuente (desplegable del registro de organismos),
identificador externo, endpoint o URL, insumos y transformación si es propia, notas. Con
el texto metodológico oficial del BCRA al lado cuando la serie viene de ahí, para copiar o
contrastar.

**Derecha — el dato.** Y este es el panel que hace que la curaduría sea posible: mini
gráfico de la serie, rango real, cantidad de observaciones, huecos marcados, últimos y
primeros valores en tabla. **No se puede verificar una serie sin verla.** Un botón
«verificado» que sella `confianza: "verificada"` con fecha — y que solo se habilita si
mirás el gráfico.

**Cómo escribe, sin romper nada.**

- `PUT /api/v1/catalogo/{id}` y `POST /api/v1/catalogo/mover`, validados contra Pydantic.
- Escritura atómica (archivo temporal + `replace`), nunca a medias.
- **Copia de seguridad antes de cada escritura** en `data/catalogo_backups/`, con las últimas 20.
- Optimistic locking con el `ETag`: si el JSON cambió por fuera, el editor avisa en vez de pisar.
- **Renombrar un `id` agrega un alias, nunca lo borra**: los proyectos guardados referencian series por id, y romperlos es la forma más fácil de arruinar meses de trabajo.

**Terminado cuando**: se puede reorganizar una familia entera, escribir cinco fichas y
sellar cinco series como verificadas, sin abrir el JSON.

---

## Fase 3 — La curaduría (el trabajo de fondo, ya con herramienta)

Recién acá se toca el contenido. En este orden:

1. **Reparar lo roto** *(rápido y concreto)*: reponer `vencimientos_1y_nuevo.csv` (84 series lo esperan), revisar las 17 columnas vacías de `vencimientos_2y_nuevo.csv` — decidir si son ceros legítimos o un bug del parser —, actualizar las 4 series desactualizadas y resolver `dummy_gobiernos_var`.
2. **Bajar el bloque histórico del BCRA** (29 series desde 1940) y decidir el criterio de empalme con las diarias modernas — que están en otra escala.
3. **Rehacer la taxonomía**: partir *Precios e Inflación* en una familia de verdad (IPC, mayoristas, costos, deflactores, inflación histórica desde 1943), disolver los 10 subgrupos de una sola serie, y revisar si *Monetario y Cambiario* debería separar lo monetario de lo cambiario ahora que el bloque monetario creció.
4. **Desambiguar los 48 nombres**: la etiqueta tiene que entenderse fuera de su árbol. «Brasil» pasa a «ITCRM bilateral — Brasil» y «Saldo comercial — Brasil».
5. **Completar las 43 fichas sin definición** y confirmar las **39 series con confianza `media`**, pasándolas a `verificada` una por una con el gráfico a la vista.
6. **Auditar el dato serie por serie**, familia por familia, sellando a medida. Esta es la parte larga y no hay atajo: es mirar cada serie.

---

## Orden y por qué

| Fase | Qué desbloquea | Riesgo si se saltea |
|---|---|---|
| 0 · Modelo | Que exista algo editable de forma uniforme | Se construye el editor dos veces |
| 1 · API | Ver el cambio al recargar | Se cura a ciegas contra una copia horneada |
| 2 · Editor | Curar sin abrir el JSON | 582 series a mano en un archivo de 400 KB |
| 3 · Curaduría | El catálogo citable | — |

Las fases 0 a 2 son de infraestructura y tienen final claro. La 3 es una campaña que se
puede hacer de a ratos, familia por familia, y que el semáforo del editor deja medir.

---

## Riesgos, dichos de frente

- **Romper los proyectos guardados.** Referencian series por `id`. Mitigación: alias obligatorios, nunca borrar un id, y un test que verifique que todo id citado en `data/proyectos/` sigue resolviendo.
- **La reorganización de la taxonomía es opinión, no técnica.** Conviene decidirla con criterio de historia económica y dejarla escrita en `docs/DATOS.md`, no que emerja de arrastrar cajas.
- **El editor puede corromper el catálogo.** Mitigación: validación en el servidor, escritura atómica, backups y `ETag`. Nunca confiar en la validación del navegador.
- **La fase 3 no termina nunca si no se acota.** Sugerencia: una familia por sesión, sellando `verificada` a medida, y el porcentaje de series verificadas como métrica visible en el editor.
- **`web/explorador.html` tiene 7.204 líneas.** Por eso el editor va aparte. Lo único que se toca ahí es de dónde lee el catálogo.

---

## Lo que se puede empezar hoy

La fase 0 no depende de nada y es la que más rinde: el contrato Pydantic y la migración a
`version: 2` ya harían que ninguna serie vuelva a esconderse.
