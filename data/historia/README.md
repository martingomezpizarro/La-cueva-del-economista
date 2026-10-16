# `data/historia/` — los datos del módulo Línea de Tiempo

Contrato completo: `docs/MODULO_LINEA_DE_TIEMPO.md`, Parte II.
Cómo se presentan estos datos en pantalla: `docs/PRESENTACION_DATOS_HISTORIA.md`.

Archivos chicos, curados, editados a mano o por script. **Se versionan en git**, salvo `_crudo/`.

```
data/historia/
├── README.md                       este archivo
├── vocabulario.json                valores permitidos (categorías, subtipos, niveles…)
├── presidencias.csv                ✅ 60 períodos 1880-hoy
├── eventos.csv                     ✅ 63 eventos 1880-1935
├── eventos_semilla_1936_2025.csv   ⚠  38 eventos del mockup, SIN normalizar
├── ministros_economia.csv          ❌
├── autoridades_monetarias.csv      ❌
├── fichas/                         ✅ 9 fichas completas
│   ├── _plantilla.md
│   ├── garantias-ferroviarias-1886.md   ferrocarriles, garantías y deuda
│   ├── bancos-garantidos-1887.md        la ley que explica 1890
│   ├── crisis-baring-1890.md
│   ├── ley-conversion-1899.md
│   ├── ley-saenz-pena-1912.md           apertura política y radicalismo
│   ├── gran-guerra-1914.md
│   ├── crack-1929.md                    la Depresión y sus canales
│   ├── control-cambios-1931.md          las tres etapas del control
│   └── creacion-bcra-1935.md
├── series.json                     ❌ catálogo cerrado de series troncales
├── series/<id>.csv                 ❌
├── medios/                         ❌
└── _crudo/gomez-2018/              ✅ transcripciones de Gómez (2018) + FUENTES.md
```

---

## Estado al 2026-09-13

**Primera carga del tramo 1880-1935** (fase T2, carril 📚), hecha íntegramente contra la
bibliografía de `RAG/corpus/14_historia/`.

- **63 eventos**: 47 hitos, 8 regímenes, 8 episodios.
  Por década: 1880s 13 · 1890s 11 · 1900s 2 · 1910s 13 · 1920s 9 · 1930s 15.
  Por capa: monetario 36 · fiscal 10 · crisis 6 · político 4 · internacional 4 · externo 3.
- **Todas las filas** llevan `refs` (claves de `RAG/referencias.bib`) o `fuente` (norma o base),
  y varias llevan las dos.
- **Todas nacen `verificado=no`.** La columna `nota` marca lo que hay que controlar.
- **9 fichas completas**, todas marcadas `verificado: false` y firmadas como borrador.
- **`referencias.bib`**: 53 entradas. Las 11 que tienen `file` apuntan a PDFs que ya están en el
  corpus y se pueden ingestar hoy.

### Lo que hay que verificar antes de pasar a `verificado=si`

Está todo anotado en la columna `nota` de `eventos.csv`. Lo más importante:

Tres de las cuatro fechas dudosas de la primera pasada ya se contrastaron contra una segunda
fuente el 2026-09-13, y la nota de cada fila lo dice. **Aun así siguen en `verificado=no`**: la
regla del proyecto es que `verificado=si` lo pone una persona, no un chequeo automático ni un
agente.

| Fila | Estado |
|---|---|
| `ley-monetaria-1881` | ✅ es la **Ley 1130** del 5/11/1881 (Infoleg id 48867) |
| `abandono-libra-1931` | ✅ **Gold Standard (Amendment) Act, 21/9/1931** (Hansard, HC Deb 21 Sep 1931) |
| `roca-runciman-1933` | ✅ **1/5/1933** (Archivo Histórico de Cancillería) |
| `creacion-bcra-1935` | ⚠ sanción 21/3/1935 y BO 5/4/1935 confirmados (Infoleg id 294177). **La inauguración (31/5/1935) y el inicio de operaciones (6/6/1935) siguen sin confirmar** contra la Memoria Anual del primer ejercicio |

Lo que queda abierto:

1. **Inauguración y primer día de operaciones del BCRA** (ver arriba). Las Memorias del BCRA están
   digitalizadas en su repositorio.
2. **Cinco entradas de `referencias.bib`** tienen `note` con datos por confirmar (editorial,
   revista o páginas): `quinteroramos-1970`, `arnaudo-1987`, `sember-2012`, `prados-arrarte-1944`,
   `beveraggi-1954`.
3. **Las 63 filas, una por una**, contra la bibliografía. El chequeo automático
   (`python scripts/chequear_historia.py`) verifica estructura, vocabulario y referencias
   cruzadas — **no** verifica que el hecho sea cierto.

### Segunda tanda (misma fecha)

A pedido, se agregaron **seis eventos ancla** y **seis fichas** sobre los ejes que faltaban:

| Ficha | Qué cubre | Fuente principal |
|---|---|---|
| `garantias-ferroviarias-1886` | los contratos ferroviarios y la deuda que generaron: 350 mill. $ oro en garantías entre 1886 y 1889 | Llach (2007) |
| `bancos-garantidos-1887` | la ley que hizo posible 1890 | Gómez (2012) · della Paolera-Taylor |
| `ley-saenz-pena-1912` | la apertura política y la llegada del radicalismo | Resico (2010) |
| `gran-guerra-1914` | el paquete de emergencia y la primera banca central | Gómez (2018), cap. III |
| `crack-1929` | la Depresión y sus canales de transmisión | O'Connell (1984) |
| `control-cambios-1931` | las tres etapas del control, 1931-1935 | Gómez (2018), cap. V |

Eventos nuevos: `garantias-ferroviarias-1886`, `venta-ferrocarriles-estado-1888`,
`ley-saenz-pena-1912`, `llegada-del-radicalismo-1916`, `gran-guerra-1914`, `boom-posguerra-1919`.
Subtipo nuevo: `reforma_electoral`.

Dos correcciones de encuadre que salieron al escribir:

- **El período no recibió inflación importada, recibió deflación.** El único shock inflacionario de
  origen externo del tramo es el boom de posguerra de 1919-1921 (`boom-posguerra-1919`); las
  hiperinflaciones europeas de esos años se observaron desde acá, no se padecieron.
- **El PBI no muestra la Gran Depresión.** Entre 1925-29 y 1930-34 el PBI *sube* 2%, mientras el
  ingreso nacional bruto cae 9,4% y el per cápita 20%. La diferencia son los términos del
  intercambio y la rigidez del servicio de la deuda. Si la línea de tiempo grafica sólo PBI per
  cápita, induce una lectura falsa del período.

### Una corrección al mockup

La semilla del mockup fecha la **Caja de Conversión en 1899**. Es un error de dos eventos
distintos fundidos en uno:

- la Caja de Conversión se crea el **7 de octubre de 1890** (Ley 2741), en plena crisis de Baring,
  y durante nueve años emite sin convertir;
- lo que ocurre el **31 de octubre de 1899** (Ley 3871) es el **retorno a la convertibilidad**, a
  2,27 m$n por peso oro.

`eventos.csv` tiene las dos filas separadas (`caja-conversion-1890` y `ley-conversion-1899`) y la
nota lo explica.

---

## Las tres decisiones de método que conviene no perder

### 1. Dos fechas por régimen: la legal y la efectiva

Gómez (2018) fecha los cambios de régimen **por comportamiento observado, no por la norma**, y la
diferencia no es menor:

| Régimen | Fecha legal | Fecha efectiva |
|---|---|---|
| Patrón oro de la Caja de Conversión | 1899-10-31 (Ley 3871) | **1902-10** (primer saldo del Fondo) |
| Banca central | 1935-03-21 (Ley 12.155) | **1931-04-25** (primer redescuento de la Caja) |

Por eso los **hitos** llevan la fecha de la norma y los **regímenes** la del comportamiento, con la
diferencia anotada en `nota`. Cuando la línea de tiempo periodice, tiene que poder mostrar las dos.

### 2. Los regímenes se superponen, y está bien

Tres filas de nivel `regimen` pueden cubrir el mismo año porque describen **dimensiones distintas**:

- convertibilidad (`patron-mixto-1883`, `inconvertibilidad-1885`, `patron-oro-1902`…),
- organización de la emisión (`bancos-garantidos-1887`),
- control de cambios (`regimen-control-cambios-1931`).

La UI tiene que separarlas en carriles por `subtipo`, no apilarlas. Está anotado en
`vocabulario.json → notas.regimenes_superpuestos`.

### 3. Sin fuente, no hay evento

Se dejaron **deliberadamente afuera** hechos canónicos del período que la bibliografía disponible
no fecha ni sostiene:

- la **Revolución del Parque** (julio de 1890) — el capítulo de Gómez menciona las manifestaciones
  de abril y la crisis política de junio-agosto, pero no la fecha la revolución;
- la **Campaña del Desierto** (1880, 30 millones de hectáreas), el primer frigorífico, el boom
  exportador de 1898 — todos documentados en `gomez-2012-crecimiento`, pero **fuera del alcance
  acordado el 2026-08-27** (quiebres de régimen económico + política + shocks externos; no
  social/estructural). Son material de primera para las fichas, no filas de `eventos.csv`.

Si el alcance se amplía, el capítulo de crecimiento tiene la superficie cultivada, la red
ferroviaria, los flujos migratorios y la población urbana/rural con fuente y cuadro.

---

## Vocabulario: qué se agregó

Dos subtipos nuevos respecto de la lista inicial de `docs/MODULO_LINEA_DE_TIEMPO.md` §8.2:

- **`crisis_politica`** — renuncias y crisis de gobierno que no son golpe ni elección
  (Juárez Celman, 1890).
- **`acuerdo_comercial`** — tratados bilaterales de comercio (Roca-Runciman, 1933).

Y un criterio para separar dos capas que se confunden fácil: **`internacional`** es para shocks de
origen externo con fecha propia (crack de 1929, salida británica del patrón oro en 1931);
**`externo`** queda para hechos argentinos del sector externo (arreglos de deuda, acuerdos
comerciales, canjes). El mockup ponía el crack de 1929 en "externo".

---

## `eventos_semilla_1936_2025.csv`

Los 38 eventos del mockup posteriores a 1935, **tal como estaban**: sólo año, título, categoría y
resumen. No son filas válidas de `eventos.csv` —les falta id, fecha ISO, nivel, precisión, refs y
fuente— y por eso viven en un archivo aparte, para no ensuciar el índice con datos sin procedencia.

Normalizarlos es una tarea propia: por cada uno hay que fijar la fecha exacta, el nivel
(hito / episodio / régimen) y al menos una referencia. Tres de ellos ya tienen ficha esbozada en
el mockup (Rodrigazo 1975, Convertibilidad 1991, Corralito 2001) y son el mejor punto de partida.

---

## Bibliografía: dónde vive

`docs/MODULO_LINEA_DE_TIEMPO.md` §8.4 la ubica en `knowledge-base/referencias.bib`. **Ese
directorio no existe en el repo**: el corpus vive en `RAG/`. El archivo se creó en
**`RAG/referencias.bib`** y las rutas de `file` son relativas a `RAG/corpus/`. Si se prefiere la
ruta del documento, hay que mover el corpus entero — conviene decidirlo una vez y anotarlo en el
registro de decisiones.

Para ingestar los PDFs ya referenciados:

```bash
python scripts/ingestar.py RAG/corpus
```
