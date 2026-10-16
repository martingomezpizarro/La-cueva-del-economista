# Datos: de dónde sale cada serie y cómo se repone

Este documento es el contrato de los datos de La Cueva. Si alguien quiere replicar un
resultado —o discutirlo— tiene que poder llegar, desde el número que ve en pantalla,
hasta la planilla del organismo que lo publicó. Eso es lo que ordena todo lo que sigue.

Regla de oro: **una serie sin procedencia declarada no es una serie, es un número suelto.**

---

## 1. Las tres piezas

| Archivo | Qué es | Quién lo edita |
|---|---|---|
| `cueva/datos/catalogo.json` | La taxonomía y la procedencia: qué series existen, cómo se llaman, en qué unidad están y de dónde salen. **Fuente única de verdad.** | Una persona, a mano, o `scripts/completar_procedencia.py` |
| `cueva/fuentes/registro.json` | El padrón de organismos: BCRA, INDEC, MECON… con su sitio, su API, su licencia y si el dato puede republicarse. | Una persona, a mano |
| `cueva/fuentes/bcra_variables.json` | Diccionario de las ~185 variables de la API del BCRA, con la definición metodológica del propio Banco. | `scripts/actualizar_bcra.py --indice` |

Todo lo demás se **deriva**: el árbol del explorador, el inventario, los CSV descargados.
Nada de eso se edita a mano.

---

## 2. El bloque `proc` de cada serie

Cada serie del catálogo lleva un bloque `proc` (procedencia). Ejemplo real:

```json
{
  "id": "res_brutas",
  "label": "Reservas Brutas BCRA",
  "unit": "Mill. USD",
  "freq": "D",
  "file": "001_reservas_brutas.csv",
  "dateCol": "fecha",
  "valCol": "valor",
  "proc": {
    "fuente": "bcra",
    "id_externo": "1",
    "endpoint": "/estadisticas/v4.0/monetarias/1",
    "definicion": "Saldo diario de reservas internacionales publicado por Comunicación «C»…",
    "script": "scripts/actualizar_bcra.py",
    "confianza": "alta",
    "verificado": "2026-08-27"
  }
}
```

### Campos

| Campo | Obligatorio | Qué dice |
|---|---|---|
| `fuente` | **sí** | Clave del organismo en `cueva/fuentes/registro.json` |
| `definicion` | sí (salvo derivadas obvias) | Qué mide la serie, en una o dos oraciones. Cuando el organismo la define, se usa **su** texto, no una paráfrasis |
| `confianza` | **sí** | `alta` · `media` · `baja` · `verificada` (ver §4) |
| `id_externo` | si existe | Identificador en la fuente: `idVariable` del BCRA, ticker de Yahoo, código de serie del BCRP |
| `endpoint` | si es API | Ruta exacta que devuelve el dato |
| `url_humana` | si no es API | Página donde una persona baja la planilla |
| `insumo_original` | si hubo conversión | Nombre del archivo tal como lo publica el organismo |
| `script` | si se repone solo | Script que vuelve a generar el archivo |
| `insumos` | **sí, si `fuente == "propia"`** | Series de las que se construye |
| `transformacion` | **sí, si `fuente == "propia"`** | La cuenta, en castellano. Si no se puede escribir, la serie no es replicable |
| `documentacion` | opcional | Nota metodológica larga, cuando la hay |
| `notas` | opcional | Advertencias de uso: empalmes, quiebres, estimaciones |
| `verificado` | sí | Fecha del último control |

### Series con más de una frecuencia

Cuando una serie tiene varias fuentes de datos (`sources`), **cada una lleva su propio
`proc`**, porque no comparten origen. El PBI constante es el caso testigo: el trimestral
es un dato del INDEC, el mensual es una estimación propia por filtro de Kalman.

```json
"sources": [
  {"freq": "M", "file": "pbi_constante_kalman.csv", "proc": {"fuente": "propia", "transformacion": "Mensualización por filtro de Kalman…"}},
  {"freq": "Q", "file": "pbi_constante_2004.csv",   "proc": {"fuente": "indec", "definicion": "PBI a precios constantes de 2004…"}}
]
```

El `proc` de la serie describe **el dato observado**: entre varias fuentes se elige la que
no es una estimación propia.

---

## 3. Fuentes registradas

`cueva/fuentes/registro.json` — 12 organismos. Lo que importa de cada uno es cómo se
accede y si el archivo puede o no republicarse:

| Clave | Organismo | Acceso | ¿Se republica? |
|---|---|---|---|
| `bcra` | Banco Central de la República Argentina | API v4.0, sin clave | sí |
| `indec` | INDEC | API de datos.gob.ar + planillas | sí |
| `mecon` | Ministerio de Economía | API de datos.gob.ar | sí |
| `finanzas` | Secretaría de Finanzas | planillas (SIGADE, Boletín) | sí |
| `banco_mundial` | Banco Mundial (WDI) | API / `wbgapi` | sí (CC BY 4.0) |
| `ofr` | Office of Financial Research (EE.UU.) | API | sí (dominio público) |
| `argentinadatos` | ArgentinaDatos | API, sin clave | **no** (EMBI es de J.P. Morgan) |
| `bcrp` | Banco Central de Reserva del Perú | API | **no** (EMBI es de J.P. Morgan) |
| `utdt` | UTDT — Centro de Investigación en Finanzas | descarga manual | **no** |
| `yahoo` | Yahoo Finance | `yfinance` | **no** |
| `heritage` | Heritage Foundation | descarga | **no** |
| `propia` | Elaboración propia | script | sí |

Lo que no se republica se repone con su script y se verifica con el hash del
`MANIFEST.csv` del repositorio de replicación del Trabajo Final. El criterio completo,
fuente por fuente, está en `DATOS_LICENCIAS.md` de ese repositorio.

---

## 4. Confianza: qué tan firme es la atribución

| Valor | Qué significa |
|---|---|
| `alta` | El archivo vive en la carpeta del organismo o lo produce su script de descarga |
| `media` | Se dedujo del nombre y del contenido; falta confirmarlo contra la fuente |
| `baja` | Atribución tentativa; no citar sin revisar |
| `verificada` | **Una persona** abrió la fuente original y comprobó el dato |

`scripts/completar_procedencia.py` **nunca pisa** una serie marcada `verificada`. Esa marca
se pone a mano, y es la que convierte al catálogo en algo citable.

---

## 5. La API del BCRA

Estadísticas Monetarias **v4.0**, pública y sin clave: `https://api.bcra.gob.ar`

| Endpoint | Devuelve |
|---|---|
| `GET /estadisticas/v4.0/Monetarias` | Índice de variables (**1610** al 2026-08-27) |
| `GET /estadisticas/v4.0/Monetarias/{id}?Desde=&Hasta=&Limit=&Offset=` | La serie histórica (máx. 3000 obs. por pedido) |
| `GET /estadisticas/v4.0/Metodologia[/{id}]` | La definición metodológica oficial |

El índice acepta filtros: `Categoria`, `Periodicidad`, `Moneda`, `TipoSerie`,
`UnidadExpresion`, `IdVariable`. Filtrar en la API es mucho más barato que traer las
1610 y filtrar en casa.

Cliente: `cueva/fuentes/bcra.py`. Descarga: `scripts/actualizar_bcra.py`.

### Cobertura real (verificada contra la API el 2026-08-27)

El **2026-08-21 el BCRA incorporó dos categorías nuevas** y con eso la API pasó a tener
serie histórica larga de verdad:

| Categoría | Series | Arranca | Periodicidad |
|---|---|---|---|
| **Agregados monetarios y sus componentes** | 28 | **1940-06-30** | mensual |
| **Activos y Pasivos del BCRA** | 29 | **1940-02-29** (reservas, id 1605) | diaria y mensual |
| Principales Variables | 30 | 1943-03-31 (inflación mensual) | diaria y mensual |
| Series.xlsm | 168 | 2003-01-02 | diaria |
| Préstamos / Depósitos por tipo de titular | cientos | 1989-12-31 | mensual |
| Depósitos por cuenta | cientos | — | mensual |

Del bloque de 1940 salen **Base Monetaria, Circulación Monetaria, M1, M2 y M3** (en
moneda local y en moneda local + extranjera), más sus componentes: cuentas corrientes,
cajas de ahorro, plazos fijos y otros depósitos, abiertos por sector público/privado y
por moneda. Están todos en el catálogo, en la familia «Monetario y Cambiario».

Ojo con las unidades: el bloque histórico viene **en miles de ARS**, mientras que las
series diarias equivalentes vienen **en millones de ARS**. No son empalmables sin
convertir.

### Dos trampas del contrato de la API

1. **Los nombres de campo del índice** son `periodicidad`, `unidadExpresion`, `moneda`,
   `tipoSerie`, `primerFechaInformada` y `ultFechaInformada`. No `frecuencia`, `unidad`,
   `fechaInicio` ni `fechaFin`.
2. **`metadata.resultset.count` no es el total del catálogo**: es cuántos registros
   quedan desde el `Offset` pedido. Con `Offset=0` da 1610; con `Offset=1400` da 210.
   Por eso la paginación se corta cuando una página vuelve corta, no comparando contra
   `count`.

### Dos detalles operativos

- El BCRA **controla el tráfico por IP**. El cliente espacia los pedidos y siempre filtra
  por fechas; conviene no paralelizar la descarga.
- La **cadena TLS suele venir incompleta**. Si el certificado no valida:
  `python scripts/actualizar_bcra.py --series --sin-verificar-tls`.

### Cómo detectar que el BCRA publicó algo nuevo

```bash
python scripts/actualizar_bcra.py --categorias
```

Lista cuántas variables hay por categoría. Si aparece una categoría que no estaba, ahí
hay series nuevas para incorporar. Así se encontró el bloque de 1940.

---

## 6. Dónde viven los archivos

```
data/series/<organismo>/     ← dataset propio de La Cueva (lo que bajan los scripts)
    bcra/
        _index.csv           ← resumen: id, archivo, unidad, n_obs, rango, fecha de consulta
        001_reservas_internacionales.csv
docs/
    DATOS.md                 ← este documento
    INVENTARIO_SERIES.md     ← generado; no editar
    inventario_series.csv    ← lo mismo, para trabajar con ello
```

Además, el catálogo sigue leyendo los CSV históricos de la carpeta del Trabajo Final
(`data/Variables Finales`), que se ubica sola o se fija con `CUEVA_TRABAJO_FINAL`.
La búsqueda de un archivo va primero a `data/series/` y después a esa carpeta: a medida
que una serie se migra al dataset propio, deja de depender del repo vecino sin tocar
ninguna otra cosa.

---

## 7. Cómo agregar una serie

1. **Conseguir el dato.** Si la fuente tiene API, escribir el adaptador en
   `cueva/fuentes/` (es la única capa de datos que puede tocar la red). Si no, dejar el
   script de descarga y anotar la URL humana.
2. **Registrar el organismo** en `cueva/fuentes/registro.json`, si es nuevo.
3. **Agregar la serie** a `cueva/datos/catalogo.json`, con su `proc` completo.
4. **Auditar**: `python scripts/auditar_series.py` — tiene que salir `ok`.
5. **Regenerar el árbol**: `python scripts/generar_arbol_visualizador.py`.
6. **Correr los tests**: `pytest tests/test_fuentes.py tests/test_datos.py`.

Los tests fallan si una serie no declara procedencia, si apunta a un organismo que no
existe, o si es de elaboración propia y no dice de qué se construye. Es a propósito.

---

## 8. El cuadro de series

```bash
python scripts/cuadro_series.py
```

Genera tres salidas de una vez, todas derivadas del catálogo (ninguna se edita a mano):

| Archivo | Para qué |
|---|---|
| `docs/cuadro_series.html` | La página navegable: buscar, filtrar por familia/fuente/frecuencia/magnitud/moneda/estado, ordenar por columna y abrir la ficha completa de cada serie |
| `docs/inventario_series.csv` | Lo mismo en tabla, para trabajar con ello |
| `docs/INVENTARIO_SERIES.md` | El cuadro en markdown, versionable y diffeable |

Columnas del cuadro: **serie · base (archivo) · origen (primer dato) · final (último dato) ·
frecuencia · fuente · descripción · magnitud · escala · moneda**. La ficha desplegable suma
identificador, columnas de fecha y valor, cantidad de observaciones, confianza, unidad
declarada e id en la fuente.

Cada fila lleva una barra de color a la izquierda con el estado: verde verificable, ámbar
por bajar, naranja sin datos, rojo archivo ausente.

### Las unidades, descompuestas

`unit` en el catálogo es texto libre (`"Miles de ARS"`). `cueva/fuentes/unidades.py` lo
traduce a **magnitud + escala + moneda** contra el vocabulario cerrado de
`cueva/fuentes/unidades.json` (34 textos mapeados, 14 magnitudes).

Sin esa descomposición no se puede detectar el problema más caro que tenemos: la base
monetaria histórica del BCRA viene en **miles** de ARS y la diaria en **millones**. Como
texto libre son dos cadenas distintas y nada más; descompuestas, `comparable_con()`
devuelve `False` y el factor dice que hay 1000 de diferencia.

Si el catálogo estrena una unidad que no está en el vocabulario, `tests/test_fuentes.py`
falla. Es a propósito: una unidad sin declarar es una serie que no se puede empalmar.

---

## 9. La grilla de revisión

```bash
python scripts/cuadro_revision.py       # genera docs/cuadro_revision.html
```

Es la herramienta para **controlar el catálogo serie por serie**. A diferencia del cuadro
del §8, que es de lectura, acá se corrige.

### Cómo está armada

El árbol replica la jerarquía del **visualizador del Trabajo Final**, que es la que ya
conocés de leer: familia (con su color) › subgrupo › sub-subgrupo › serie, y las series
con apertura cuelgan de una carpeta con su «Total» en itálica. Cada nodo se colapsa, y
cada uno muestra su avance: `12/47 revisadas` y una barrita.

Cada fila trae las columnas del cuadro —serie, base, origen, final, frecuencia, fuente,
descripción— y al hacer click se abre la ficha con los campos editables.

### Qué se puede editar y qué no

| Editable | Por qué |
|---|---|
| Nombre, descripción, fuente, magnitud, escala, moneda, nota | Son decisiones de curaduría |
| **Base, origen, final, frecuencia, observaciones** | **No.** Salen del archivo en disco: si están mal, lo que hay que arreglar es el dato, no la ficha |

La magnitud, la escala y la moneda son desplegables del vocabulario cerrado. No se escribe
una unidad a mano.

### Los tres veredictos

- **Está bien** → la serie queda `verificada`.
- **Tiene un problema** → se anota qué pasa y **no se toca el dato**. La serie NO queda
  verificada: un problema registrado no es un problema resuelto.
- **Dejar sin revisar** → vuelve a pendiente.

Si además editaste algún campo, el estado pasa solo a *corregida*.

### Cómo vuelven las correcciones al catálogo

No vuelven solas, y es a propósito: el catálogo se toca con un diff a la vista.

```bash
python scripts/aplicar_revision.py --desde docs/cuadro_revision.html   # simula
python scripts/aplicar_revision.py --desde docs/cuadro_revision.html --aplicar
```

El script traduce magnitud + escala + moneda de vuelta a un `unit` del vocabulario. **Si
la combinación corregida no existe en `unidades.json`, avisa y no la escribe** — no
inventa unidades. Un id que ya no está en el catálogo también avisa en vez de romper.

Las series que quedan `verificada` son las únicas que `completar_procedencia.py` nunca
pisa. Esa marca es lo que convierte al catálogo en algo citable.

---

## 10. Qué puede completar la API del BCRA

```bash
python scripts/cobertura_bcra.py --csv docs/cobertura_bcra.csv
```

Cruza el rango REAL de cada serie en disco contra el rango que publica la API y dice qué
se gana. Tres respuestas:

### 10.1 Series que se estiran (5 con datos + 29 por bajar)

| Serie | Hoy | Con la API | Gana |
|---|---|---|---|
| `rem_mens` / `rem_crec` (id 29) | 2016-06 → 2025-12 | 2004-01 → 2026-07 | **+12,3 años** atrás |
| `res_brutas` (id 1) | 2003-01 → 2026-05 | 1996-01 → 2026-08 | **+7,0 años** atrás |
| `dep_total` (id 21) | 2003-01 → 2026-05 | 1999-12 → 2026-08 | **+3,0 años** atrás |
| `tc_a3500` (id 5) | 2003-01 → 2026-06 | 2002-03 → 2026-08 | +0,8 años atrás |

Las cuatro además están **89 días desactualizadas**. Y las 29 series históricas del bloque
de 1940 todavía no tienen ningún dato en disco: se bajan enteras.

### 10.2 Series del BCRA sin `idVariable` (19)

No se pueden actualizar solas hasta emparejarlas con una variable de la API:

- **ITCRM (15 series)**: la API v4 **no publica el ITCRM** — sale de las planillas de
  Publicaciones Estadísticas. Conviene confirmarlo al correr `--indice` completo.
- **Depósitos y préstamos en USD (4)**: la categoría `Series.xlsm` tiene candidatos
  (ids 107, 108, 118-125). Hay que emparejarlos serie por serie.

### 10.3 Lo que la API tiene y el catálogo no

Acá está el hueco más grande, y no es de cobertura sino de contenido:

| Bloque | Cuántas | Desde | Estado en el catálogo |
|---|---|---|---|
| **Tasas de interés** | 11 | plazo fijo 30 días desde **1985**, BADLAR desde 1999 | **NINGUNA.** El catálogo no tiene una sola tasa argentina |
| **Inflación** | 2 | mensual desde **1943**, interanual desde 1944 | *Precios e Inflación* tiene 2 series |
| **Índices de ajuste** | 4 | CER desde 2002, UVA/UVI 2016, ICL 2020 | Ninguno |
| **Agregados diarios** | 8 | base monetaria y circulación desde 1996 | Solo los mensuales históricos |
| **Instrumentos del BCRA** | 9 | LELIQ, pases, LEBAC, adelantos transitorios | Ninguno |

Para una plataforma de econometría argentina, **no tener tasas de interés ni CER es el
agujero más caro**: son las variables que aparecen en casi cualquier modelo monetario o
financiero, y están a un `--ids` de distancia.

> El índice local es **parcial**: 69 variables verificadas de las 1610 que publica la API.
> Este cruce cubre «Principales Variables», las dos categorías históricas y lo esencial de
> «Activos y Pasivos del BCRA». Quedan sin revisar las 168 de `Series.xlsm` y las ~1370 de
> depósitos y préstamos por titular y por cuenta. Correr `--indice` completa el cuadro.

---

## 11. Estado (2026-08-28)

- **582 series** en el catálogo, **739 entradas** contando cada frecuencia por separado.
  (La primera auditoría decía 356: no descendía por `children`, donde vive un tercer,
  cuarto y quinto nivel. Todo lo que recorra el catálogo tiene que bajar hasta el fondo.)
- **739 de 739 con procedencia declarada.** 39 con confianza `media` (hay que
  confirmarlas contra la fuente); 29 marcadas a mano contra la API del BCRA.
- **609 entradas verificables, 113 por bajar, 17 con problema, 43 sin descripción.**
- 113 entradas **pendientes de descarga**: 84 esperan `vencimientos_1y_nuevo.csv`, que no
  existe, y 29 son las series históricas del BCRA. Todas tienen script que las repone.
  Ninguna referencia rota sin script.
- 17 entradas con la columna presente pero vacía, todas de `vencimientos_2y_nuevo.csv`.
- El snapshot `cueva/fuentes/bcra_variables.json` es **parcial a propósito**: tiene las
  29 variables históricas verificadas a mano, de las 1610 que publica la API, y el campo
  `metodologia` vacío. Correr `--indice` con red lo reemplaza por el diccionario completo.
- Pendiente de fondo: el plan completo para rehacer el catálogo y poder curarlo
  visualmente está en `docs/PLAN_CATALOGO.md`.
