# Módulo Línea de Tiempo

> El **módulo 1** de la plataforma: la historia económica y social de Argentina, 1880 → hoy.
>
> - **Parte I — Qué es** (§1-7): comportamiento de la pantalla, decidido sobre el mockup entre el
>   2026-08-28 y el 2026-09-12.
> - **Parte II — Cómo se construye** (§8-13): datos, código, fases, cómo cargar lo que ya hay.
> - **Registro de decisiones** (§14): toda decisión nueva sobre el módulo se anota ahí.
>
> Contexto general: `docs/PLATAFORMA.md`. Fuentes históricas evaluadas:
> `docs/FUENTES_EVENTOS_HISTORICOS.md`. Hasta dónde llegan las series: `docs/FUENTES_SERIES_LARGAS.md`.
> Referencia visual: `docs/mockup/cueva-mockup.html`, pestaña «Línea de Tiempo».

---

# Parte I — Qué es

## 1. Alcance

**Es** una vista de consulta y narración: leer la historia económica argentina cruzando series
largas con eventos, gobiernos, autoridades económicas y bibliografía.

**No es** un banco de trabajo. Las acciones que operan sobre un proyecto («llevar a la mesa»,
«crear dummy») **se sacaron deliberadamente**: pertenecen a la Mesa de Trabajo. Mezclar consulta
y operación vuelve ambigua la pregunta "¿esto que toco modifica mi trabajo?".

> Abierto: si más adelante se agrega un puente, se ofrece **desde la Mesa** ("importar evento
> como dummy"), no desde acá. El puente sale de donde se opera, no de donde se consulta.

### 1.1 La pantalla

```
┌─ CAPAS ──────────┬─ GRÁFICO ─────────────────────────────────────────┬─ EVENTOS ─────────┐
│ Instituciones    │ [Comparar en: Índice 100 | Log | Paneles] [Δ i.a.]│ Evento            │
│  ☑ Presidencias  │ [Período: Todo | Agroexp. | Sustitución | …]      │ seleccionado      │
│  ☐ Ministros     │ ──────────────────────────────────────────────── │  fecha · título   │
│  ☐ BCRA          │ banda de presidencias (color = constitucional/    │  resumen          │
│ Eventos          │   de facto)                                       │  [Ver ficha]      │
│  ☑ Monetarios    │ banda de eventos (pines / barras / regímenes)     │                   │
│  ☑ Crisis        │ ┌──────────────────────────────────────────────┐ │ Todos los eventos │
│  ☑ Externos …    │ │ series troncales (hasta 4)                    │ │  1890 Baring      │
│ Series (n/4)     │ └──────────────────────────────────────────────┘ │  1891 Banco Nac.  │
│  ☑ PBI pc        │ ┌ Δ interanual ────────────────────────────────┐ │  …                │
│  ☐ Inflación …   │ └──────────────────────────────────────────────┘ │                   │
│                  │ ═══ barra de rango (brush) ═══                    │                   │
│ notas de         ├───────────────────────────────────────────────────┤                   │
│ cobertura        │ FICHA DEL EVENTO (panel inferior, ≈46 % alto)     │                   │
│                  │  relato + cronología │ cifras · foto · citas · bib │                   │
└──────────────────┴───────────────────────────────────────────────────┴───────────────────┘
```

---

## 2. Series troncales: catálogo cerrado, anual

El módulo **no** usa el catálogo completo de la Mesa (615 series). Usa un **catálogo cerrado de
series troncales, todas anuales**.

**Criterios de inclusión** (los tres a la vez):
1. cuenta algo estructural de la historia larga;
2. es empalmable hasta ~1880 (o su inicio real es en sí mismo un dato);
3. tiene una fuente histórica reconocida.

**Propuesta inicial** (a confirmar contra los datos disponibles — decisión abierta §13.1):

| id | Serie | Unidad | Tipo | Desde (objetivo) | Fuente probable |
|---|---|---|---|---|---|
| `pbipc` | PBI per cápita | índice 1880=100 | nivel | 1880 | Ferreres · Maddison Project |
| `inflacion` | Inflación anual | % anual | tasa | 1900 | Ferreres · BCRA (1943→) · INDEC |
| `tcr` | Tipo de cambio real | índice | nivel | 1913 | Ferreres · Bruegel REER (1960→) · BCRA |
| `deuda` | Deuda pública / PBI | % del PBI | tasa | 1880 | MECON · Reinhart-Rogoff |
| `resultado_primario` | Resultado primario / PBI | % del PBI | tasa | 1900 | MECON · Hacienda |
| `apertura` | Apertura comercial (X+M)/PBI | % del PBI | tasa | 1880 | INDEC · MOxLAD |
| `toi` | Términos de intercambio | índice | nivel | 1880 | INDEC · MOxLAD |
| `salario_real` | Salario real | índice | nivel | 1880 | Ferreres · INDEC |
| `desempleo` | Desempleo | % de la PEA | tasa | 1974 | INDEC · EPH |
| `poblacion` | Población | millones | nivel | 1880 | INDEC · censos |

**Máximo 4 series simultáneas.** Más de cuatro curvas sobre 145 años es ilegible. La UI muestra
`n/4` y deshabilita el resto al llegar al tope.

### 2.1 `tipo`: nivel vs tasa

Cada serie declara si es un **nivel** (índice, monto, población) o una **tasa** (ya en %). No es
cosmético: decide qué transformación es válida.

- Poner en **base 100** algo que ya es un porcentaje no significa nada → la UI avisa.
- La **variación** de un nivel es un cambio porcentual; la de una tasa, una diferencia en
  **puntos porcentuales**. El panel Δ las calcula distinto y lo dice en la etiqueta.

### 2.2 Cobertura honesta

Lo que la serie no cubre se pinta como **banda gris "sin cobertura"**, calculada desde los datos
reales (no declarada a mano). Los tramos empalmados se distinguen: la tarjetita del mouse dice de
qué fuente sale **ese año** (§8.5).

---

## 3. Escalas

El problema: nominalidades y órdenes de magnitud incompatibles (inflación de 3.079 % contra deuda
de 78 % del PBI). Ningún modo único lo resuelve.

| Modo | Qué hace | Cuándo |
|---|---|---|
| **Índice 100** (default) | base 100 en el **primer año visible** (se re-ancla al hacer zoom) | comparar trayectorias heterogéneas |
| **Log** | nivel real en escala logarítmica | series que crecen multiplicativamente |
| **Paneles** | un panel por serie, cada uno con su eje y escala real | cuando normalizar mentiría |
| **Δ i.a.** (panel inferior, independiente) | variación interanual | dinámica de corto plazo |

**Δ interanual es un panel aparte, no un modo**: se ve el nivel y su variación a la vez.
- una serie → barras con signo (verde/rojo); varias → líneas;
- eje recortado al percentil 94 × 2,4 para que la hiperinflación (+2.900 p.p.) no aplaste el
  resto; **el recorte se declara** en la etiqueta del panel.

---

## 4. Navegación

- **Rueda**: zoom en X centrado en el cursor. **Arrastrar**: desplazar. **Doble clic**: 1880-hoy.
- **Barra de rango** (brush): silueta de la primera serie activa con las crisis marcadas; la
  ventana se arrastra entera o se estira desde los bordes.
- **Períodos**: Todo · Agroexportador (1880-1930) · Sustitución (1930-1976) · Apertura
  (1976-2001) · Post-convertibilidad (2001-hoy).
- Ventana mínima: 6 años. Ticks adaptativos (20 → 10 → 5 → 2 → 1 año).

### 4.1 Tarjetita del mouse

Línea vertical, punto resaltado sobre cada serie y una caja con **año**, y por serie **nombre,
valor, unidad** y **fuente del tramo**. Si el año tiene un evento, se nombra al pie. Sobre el
panel Δ cambia a las unidades de la variación (% o p.p.). Sobre la banda de presidencias muestra
el gobierno con sus fechas.

---

## 5. La ficha del evento

### 5.1 Dónde va

**Panel inferior que sube y comprime el gráfico** (≈46 % de la altura), no un modal ni el panel
lateral.

El argumento decisivo son las **cifras enlazadas**: si tocar un número lleva a ese valor en el
gráfico, el gráfico tiene que seguir visible. Un modal lo taparía; el panel lateral (296 px) no
da ancho para cronología, cifras, imagen y bibliografía.

- **panel lateral derecho** → índice: evento seleccionado en resumen + lista de todos;
- **panel inferior** → la ficha completa en dos columnas (relato | evidencia);
- **gráfico** → siempre visible arriba, encuadrado en el período del evento.

Se abre con doble clic en el pin o con «Ver ficha». Con la ficha abierta, seleccionar otro evento
la actualiza en vez de cerrarla.

### 5.2 Qué contiene

| Columna | Bloque | Contenido |
|---|---|---|
| Relato | encabezado | título, fechas, categoría, gobierno (derivado), estado editorial |
| Relato | contexto | 1-3 párrafos |
| Relato | cronología | lista fechada; los números son **cifras enlazadas** |
| Relato | qué mirar | qué debería moverse en las series y por qué (§6.3) |
| Evidencia | cifras clave | cada cifra con etiqueta, fuente y «ver en el gráfico» |
| Evidencia | medios | foto con epígrafe, crédito y licencia |
| Evidencia | citas | textuales, con obra y página |
| Evidencia | fuentes primarias | ley, decreto, comunicación, discurso — con enlace |
| Evidencia | bibliografía | obras citadas, formateadas desde `referencias.bib` |
| Evidencia | relacionados | eventos vinculados, clickeables |

El formato de archivo está en §8.3.

### 5.3 Cifra enlazada

Al tocarla:
1. si declara `serie` y esa serie **no está activa**, se activa (liberando lugar si hay 4);
2. el gráfico hace zoom al año de la cifra;
3. se resalta el punto con año y valor;
4. el resaltado se apaga solo a los ~2,6 s.

Una cifra sin `serie` (ej. "Decreto 1570/2001") se muestra igual pero como *sin serie* — no
finge un vínculo que no existe.

### 5.4 Estado editorial

Toda ficha muestra su estado en el encabezado: `verificada 2026-08-28` o `sin verificar`. Los
eventos sin ficha muestran "ficha pendiente de redacción" en vez de un vacío.

---

## 6. Propuestas incorporadas al diseño

Ordenadas por valor/costo. Todas tienen lugar en el modelo de datos de la Parte II; se construyen
en las fases que indica §9.

### 6.1 Duración y jerarquía de eventos *(fase T2)*

El Rodrigazo es un día, la hiperinflación 18 meses, la Convertibilidad casi 11 años:

- **régimen** — banda de fondo detrás del gráfico (Caja de Conversión, Convertibilidad, cepo);
- **episodio** — barra con ancho en la banda de eventos (Tequila, hiperinflación);
- **hito** — pin puntual (una ley, un anuncio).

**El detalle se filtra por zoom**: a 145 años se ven regímenes; al acercarse aparecen episodios y
después hitos. Como un mapa.

### 6.2 Evento ↔ quiebre estadístico *(fase T5)*

Registrar si hay un **quiebre estructural detectado** (Bai-Perron, Chow) cerca de la fecha y en
qué series. Convierte la infografía en insumo econométrico y es el puente natural con la Mesa.

### 6.3 "Qué mirar" *(fase T4)*

Por evento, qué debería moverse y por qué: "tras una devaluación real esperá que el TCR salte y el
salario real caiga el mismo año". Es el gesto de agente-profesor aplicado a la historia.

### 6.4 Fuentes primarias *(fase T4)*

Enlace al documento original: ley, decreto, comunicación del BCRA, discurso. Barato de cargar,
sube mucho la autoridad.

### 6.5 Contexto internacional *(fase T5)*

Capa opcional con crisis globales (1873, 1890, 1929, 1973, 1982, 2008, 2020) para ver a simple
vista **qué fue local y qué importado**.

### 6.6 Permalink y exportación *(fase T5)*

URL por evento (`/tiempo/corralito-default-2001`) para citarla; exportar la ficha (cifras + citas
+ bibliografía) al proyecto de la Mesa.

### 6.7 ⚠ Derechos de imagen *(regla desde T4)*

Las fotos de archivo argentino **no** son libres por defecto:
- preferir Wikimedia Commons, Archivo General de la Nación y material con licencia declarada;
- Télam, Clarín y La Nación requieren permiso explícito;
- **siempre** `credito`, `licencia` y `url_origen` por imagen — el test lo exige.

Sin licencia clara, placeholder. Un marco vacío con su crédito es mejor que un problema legal.

---

## 7. Lo que el módulo NO hace

- No corre econometría: el Δ i.a. y los modos de escala son transformaciones de visualización.
- No crea ni modifica proyectos.
- No usa series que no estén en su catálogo cerrado.
- No inventa: sin fuente, no hay evento; sin licencia, no hay foto; sin serie, la cifra lo dice.

---

# Parte II — Cómo se construye

## 8. Datos: `data/historia/`

**Todo lo del módulo vive en `data/historia/`**, fuera del paquete `cueva/` (el código lee de ahí;
los datos no se mezclan con el código). Son archivos chicos, curados y editados a mano o por
script: **se versionan en git**, salvo `_crudo/`.

```
data/historia/
├── README.md                      qué hay y cómo se llena (versión corta de esta Parte II)
├── vocabulario.json               valores permitidos: categorías, subtipos, niveles, tipos de gobierno…
│
├── presidencias.csv               ✅ 60 períodos 1880-hoy
├── ministros_economia.csv         ❌
├── autoridades_monetarias.csv     ❌ Caja de Conversión / BCRA
│
├── eventos.csv                    ❌ índice de TODOS los eventos, una fila cada uno
├── fichas/
│   ├── _plantilla.md              ❌ copiar para empezar una ficha
│   └── <id-evento>.md             ❌ solo los eventos con ficha completa
│
├── series.json                    ❌ catálogo cerrado de series troncales (con tramos y procedencia)
├── series/<id>.csv                ❌ una serie anual por archivo
│
├── medios/                        ❌ imágenes con licencia (≤ 500 KB c/u)
└── _crudo/<fuente>/               ✅ (ignorado) archivos originales tal como se bajaron
```

Y fuera de `data/`, porque la usa toda la plataforma:

```
knowledge-base/referencias.bib     ❌ registro único de obras citables
knowledge-base/corpus/13_historia_economica_argentina/   ❌ PDFs (ignorado)
```

### 8.1 Instituciones

Las tres tablas comparten forma: **un período por fila**, fechas ISO `AAAA-MM-DD`, `fuente` y
`verificado` en cada fila.

**`presidencias.csv`** — ya existe, no cambia:

```
orden,nombre,desde,hasta,tipo,fuerza_politica,acceso,salida,fuente,verificado,nota
```

**`ministros_economia.csv`**:

```
orden,nombre,desde,hasta,cargo,interino,fuente,verificado,nota
```

- `cargo`: la denominación **de la época** (Ministro de Hacienda, Ministro de Economía, Ministro
  de Economía y Obras y Servicios Públicos…). La capa se llama "Ministros de Economía" pero el
  dato no reescribe la historia.
- Hubo períodos con **dos carteras económicas a la vez** (Hacienda y Economía por separado): se
  permite solapamiento **solo entre cargos distintos**.
- `interino`: `si` | `no`.

**`autoridades_monetarias.csv`**:

```
orden,institucion,cargo,nombre,desde,hasta,fuente,verificado,nota
```

- `institucion`: vocabulario cerrado (`caja_conversion`, `bcra`, y los que surjan al investigar
  el período previo — se dan de alta en `vocabulario.json`).
- Las reservas de la Caja de Conversión y las del BCRA **no se empalman** (`FUENTES_SERIES_LARGAS`);
  las autoridades tampoco se presentan como una sola línea: la capa marca el cambio de institución.

**Regla**: el gobierno de un evento **no se guarda**: se deriva por fecha. Guardarlo duplicaría el
dato y se desincronizaría al corregir una fecha de traspaso.

### 8.2 `eventos.csv` — el índice

Una fila por evento, tenga o no ficha.

```
id,titulo,categoria,subtipo,nivel,desde,hasta,precision,resumen,refs,fuente,ficha,verificado,nota
```

| Campo | Regla | Ejemplo |
|---|---|---|
| `id` | slug único, minúsculas y guiones, termina en el año de inicio | `corralito-default-2001` |
| `titulo` | corto, como se ve en el pin | `Corralito y default` |
| `categoria` | la **capa** de la UI (vocabulario) | `crisis` |
| `subtipo` | clasificación fina (vocabulario) | `default` |
| `nivel` | `hito` \| `episodio` \| `regimen` | `episodio` |
| `desde` | ISO `AAAA-MM-DD` | `2001-12-01` |
| `hasta` | ISO o vacío si es puntual; ≥ `desde` | `2002-01-06` |
| `precision` | `dia` \| `mes` \| `anio` — si solo se sabe el año, `desde=AAAA-01-01` y `precision=anio` | `dia` |
| `resumen` | 1-2 líneas para el panel lateral | |
| `refs` | claves de `referencias.bib` separadas por `;` | `damill-frenkel-2003;gerchunoff-llach-2018` |
| `fuente` | fuente no bibliográfica (norma, base de datos) si la hay | `Decreto 1570/2001` |
| `ficha` | `si` si existe `fichas/<id>.md` | `si` |
| `verificado` | `si` \| `no` | `no` |
| `nota` | discusiones, fechas en disputa | |

**Toda fila tiene `refs` o `fuente`** (o ambas). Un evento sin ninguna no pasa el test.

**Vocabulario inicial** (vive en `vocabulario.json`; agregar un valor = editar ese archivo):

- `categoria`: `monetario` · `fiscal` · `externo` · `crisis` · `politico` · `social` ·
  `internacional` (la capa de contexto de §6.5)
- `subtipo`: `default` · `reestructuracion_deuda` · `crisis_bancaria` · `crisis_cambiaria` ·
  `hiperinflacion` · `plan_estabilizacion` · `regimen_cambiario` · `control_cambios` ·
  `cambio_moneda` · `creacion_institucion` · `reforma_fiscal` · `acuerdo_fmi` · `shock_externo` ·
  `guerra` · `golpe` · `eleccion` · `reforma_constitucional` · `conflicto_social` · `pandemia` ·
  `norma` · `otro`

> ⚠ `scripts/bajar_crisis_rr.py` hoy escribe `eventos.csv` con otras columnas (`fecha_inicio`,
> `fecha_fin`, `ambito`, `tipo`…). **No se corrió nunca**, así que adaptarlo a este esquema es
> parte de la fase T2 y no rompe nada.

### 8.3 `fichas/<id>.md` — la ficha completa

**Markdown con frontmatter**, no JSON: una ficha es sobre todo prosa, y escribir un relato largo
dentro de un JSON (comillas escapadas, sin saltos de línea) es un castigo. Es el mismo formato que
ya usan los skills de los agentes.

Lo que ya está en `eventos.csv` (título, fechas, categoría, nivel) **no se repite** en la ficha.

```markdown
---
id: corralito-default-2001
series: [pbipc, desempleo, deuda, salario_real]

cifras:
  - id: tope
    v: "250 USD semanales"
    et: "Tope de extracción del corralito"
    serie: null
    anio: 2001
    fuente: "Decreto 1570/2001"
  - id: desempleo02
    v: "21,5 %"
    et: "Desempleo, mayo 2002"
    serie: desempleo
    anio: 2002
    fuente: "INDEC — EPH"

fuentes_primarias:
  - tipo: decreto
    ref: "Decreto 1570/2001"
    url: "https://…"

medios:
  - tipo: foto
    archivo: medios/corralito-cacerolazo.jpg
    epigrafe: "Cacerolazo frente al Congreso, 20 de diciembre de 2001"
    credito: "Archivo General de la Nación"
    licencia: "CC BY-SA 4.0"
    url_origen: "https://…"

relacionados: [fin-convertibilidad-2002, canje-deuda-2005]
redactor: "…"
revisado: 2026-09-12
verificado: false
---

## Contexto

Uno a tres párrafos. Las citas bibliográficas van con clave: [@damill-frenkel-2003, p. 47].

## Cronología

- **2001-12-01** — Cavallo anuncia el límite de retiro de {{c:tope}}.
- **2001-12-19** — …

## Qué mirar

Qué debería moverse en las series troncales y por qué.

## Citas

> "Texto textual de la cita."
> — [@damill-frenkel-2003, p. 47]
```

Tres convenciones:

| Sintaxis | Qué hace | Por qué así |
|---|---|---|
| `{{c:tope}}` | inserta la cifra `tope` como número clickeable | el número vive **una vez**, con fuente y serie. Se referencia por **nombre**, no por posición: reordenar la lista no rompe el relato |
| `[@clave, p. 47]` | cita a una obra de `referencias.bib` | es la sintaxis de Pandoc: se exporta tal cual a LaTeX y Word cuando la ficha pase a un informe |
| `serie: null` | cifra sin vínculo | la UI lo muestra como "sin serie" en vez de fingir un enlace |

Dependencia nueva: **`pyyaml`** (solo `yaml.safe_load`) para leer el frontmatter anidado. El parser
de los skills es por regex y no soporta listas de objetos.

### 8.4 Bibliografía: `referencias.bib` y el corpus de historia

**`knowledge-base/referencias.bib`** es el registro único de obras citables de **toda** la
plataforma (fichas de eventos, informe del Laboratorio, respuestas de los agentes). BibTeX porque
es el estándar del oficio y el Laboratorio exporta a LaTeX.

```bibtex
@book{gerchunoff-llach-2018,
  author    = {Gerchunoff, Pablo and Llach, Lucas},
  title     = {El ciclo de la ilusión y el desencanto},
  publisher = {Crítica},
  year      = {2018},
  edition   = {edición actualizada},
  keywords  = {historia_economica},
  file      = {13_historia_economica_argentina/gerchunoff_llach_2018.pdf}
}
```

- **Clave**: `apellido-anio` (dos autores `a-b-anio`; tres o más `a-etal-anio`; si choca, `2018a`).
- `file` apunta al PDF dentro de `knowledge-base/corpus/` **si lo tenemos**. Sin `file`, la obra se
  puede citar pero el Bibliógrafo no puede verificar la cita contra el texto → se muestra como
  "cita no verificable".
- `keywords`: `historia_economica`, `econometria`, `argentina`… — sirve para filtrar.
- Los datos del catálogo que sean obras (Ferreres, Maddison) también van acá, así una serie y un
  evento citan la misma entrada.

**Corpus**: los PDFs de historia económica van a
`knowledge-base/corpus/13_historia_economica_argentina/` (ignorado por git, como el resto del
corpus). Hoy las colecciones del RAG son `corpus` y `usuario`: la historia quedaría mezclada con
la econometría. Propuesta técnica (decisión §13.5): agregar el campo `tema` al fragmento, derivado
de la carpeta, para que el Metodólogo no traiga a Gerchunoff cuando le preguntan por
cointegración, y la ficha no traiga a Enders.

### 8.5 Series troncales: `series.json` + `series/<id>.csv`

Una serie larga argentina **nunca sale de una sola fuente**: es un empalme. El formato lo hace
visible en vez de esconderlo.

**`series/<id>.csv`** — un año por fila, y cada año dice de qué tramo sale:

```
anio,valor,tramo
1880,100.0,ferreres
1881,103.2,ferreres
…
1993,412.7,indec
```

**`series.json`** — el catálogo cerrado:

```jsonc
{
  "series": [
    {
      "id": "inflacion",
      "nombre": "Inflación anual",
      "unidad": "% anual",
      "tipo": "tasa",                      // nivel | tasa
      "agregacion_anual": "dic_dic",       // dic_dic | promedio | fin_periodo | suma — OBLIGATORIO
      "base": null,                        // "1880=100" si es índice
      "tramos": [
        {"id": "ferreres", "desde": 1900, "hasta": 1942,
         "ref": "ferreres-2010", "detalle": "cuadro X, IPC Capital Federal",
         "archivo_crudo": "_crudo/ferreres/precios.xlsx"},
        {"id": "bcra", "desde": 1943, "hasta": 2025,
         "ref": null, "fuente": "BCRA API v4.0, id 27",
         "archivo_crudo": "_crudo/bcra/27.csv"}
      ],
      "empalme": "Sin empalme: los tramos no se superponen; se comprobó que 1943 no tiene salto.",
      "script": "scripts/historia_serie.py inflacion",
      "confianza": "media",                // alta | media | baja
      "verificado": false,
      "notas": "1914-1917 sin dato mensual; el anual de Ferreres es estimación."
    }
  ]
}
```

- **`agregacion_anual` es obligatorio** porque cambia el número: la inflación de 1989 dic-dic
  (4.923 %) y promedio anual (3.079 %) son dos datos distintos y los dos son "la inflación de 1989".
- **`empalme`** describe el método (retropolación por tasas, coeficiente de enlace en el año de
  superposición, ninguno). Sin descripción, no hay serie.
- Los crudos quedan en `_crudo/` **sin tocar**; el CSV final lo produce un script, así se puede
  rehacer.

### 8.6 Medios

`data/historia/medios/<id-evento>-<descripcion>.jpg`, máximo 500 KB (redimensionar antes). Toda
imagen referenciada por una ficha lleva `credito`, `licencia` y `url_origen`. Una imagen en la
carpeta que ninguna ficha usa es un error del test (evita basura con licencia dudosa en el repo).

---

## 9. Fases de construcción

Cada fase termina en algo **que se ve funcionando** y deja los tests en verde. Dos carriles en
paralelo: 📚 **datos** (curar, transcribir, verificar — lo lleva el investigador) y 🔧 **código**.

### T0 — Cimientos *(🔧)* — ✅ **hecho el 2026-09-16**

- ✅ `web/estilo/tokens.css` extraído del mockup (tokens + primitivas compartidas: chip, btn,
  seg, note, rail, layer; lo va a reusar la Mesa).
- ✅ `data/historia/README.md`, `vocabulario.json`, `fichas/_plantilla.md` (ya existían).
- ✅ `cueva/datos/historia.py`: lee y valida presidencias, eventos, vocabulario, fichas
  (frontmatter YAML + markdown → **HTML saneado en el servidor**) y `referencias.bib`;
  `gobierno_en()` y `validar()`.
- ✅ `GET /api/v1/historia`, `GET /api/v1/historia/eventos/{id}`, `GET /tiempo` y
  `GET /tiempo/{evento_id}` (permalink); estáticos en `/web` y `/historia-medios`.
- ✅ `web/tiempo/` en módulos ES sin build: `estado.js` · `grafico.js` · `ficha.js` · `app.js`.

**Listo**: se abre `/tiempo`, se recorren los 60 gobiernos reales, los 63 eventos del tramo
1880-1935 en sus tres niveles y las 9 fichas completas. 17 tests en `tests/test_historia.py`
(datos + render + payload) y 3 nuevos en `tests/test_api.py`; ruff en verde.

> Se adelantó parte de **T2** (eventos, filtro por zoom, conteos calculados) y de **T4** (panel
> de ficha con cifras enlazadas, citas, bibliografía y estado editorial) porque los datos ya
> estaban cargados. Queda pendiente de T2 correr `bajar_crisis_rr.py`, y de T4 los medios.

### T1 — Instituciones *(📚 + 🔧)*

- 📚 Verificar las 60 presidencias contra Casa Rosada (`verificado=si`; resolver las dos notas en
  disputa: Ortiz→Castillo, fin del mandato de CFK).
- 📚 Cargar `ministros_economia.csv` y `autoridades_monetarias.csv`.
- 🔧 Capas conmutables en el rail; tests de no-solapamiento por cargo.

**Listo cuando**: las tres capas se prenden y apagan con datos reales y cada fila tiene fuente.

### T2 — Referencias y eventos *(📚 + 🔧)*

- 📚 Crear `referencias.bib` con la bibliografía que ya hay; PDFs al corpus de historia; ingestar.
- 📚 `eventos.csv`: empezar por los **49 eventos semilla del mockup** (con `verificado=no`) y ir
  completando `refs` desde la bibliografía; sumar los que falten.
- 🔧 Adaptar y correr `scripts/bajar_crisis_rr.py` (crisis y defaults desde 1800, fechados).
- 🔧 Pines, barras de episodio y bandas de régimen; **filtro por zoom** (§6.1); rail con evento
  seleccionado y lista; conmutadores por categoría con conteos **calculados**.

**Listo cuando**: todos los eventos se ven en su nivel, cada uno tiene `refs` o `fuente`, y los
conteos del rail salen de los datos.

### T3 — Series troncales *(📚 + 🔧, de a una)*

- 📚 Por serie: juntar crudos, decidir tramos y empalme, llenar su entrada en `series.json`.
- 🔧 Script que produce `series/<id>.csv` desde los crudos; test del contrato.
- 🔧 Gráfico: Índice 100 / Log / Paneles, panel Δ i.a., brush, tarjetita con **tramo**, banda
  "sin cobertura" calculada, máximo 4.

**Orden sugerido**: primero las series para las que ya hay datos; después las de fuente única
larga (población, PBI per cápita de Maddison); al final las de empalme difícil (TCR, salario real).

**Listo cuando** (por serie): procedencia completa, empalme descrito, test en verde, cobertura
visible y honesta.

### T4 — Fichas *(📚 + 🔧)*

- 📚 Redactar las fichas de los **eventos estructurales** (propuesta §13.2).
- 🔧 Panel inferior en dos columnas; render de markdown; cifras enlazadas (§5.3); citas formateadas
  desde `referencias.bib`; medios con crédito; fuentes primarias; "qué mirar"; relacionados.
- 🔧 `GET /api/v1/historia/eventos/{id}`.

**Listo cuando**: una ficha completa se lee de punta a punta y cada número lleva a su valor.

### T5 — Profundidad *(🔧 + 📚)*

- Contexto internacional (§6.5) · evento ↔ quiebre (§6.2, usa las herramientas de la Mesa) ·
  permalink y exportación (§6.6) · botón Exportar (PNG/CSV del gráfico).

### T6 — Puentes con el resto de la plataforma *(🔧)*

- **Dummies generadas** desde las tablas (reemplazan `dummy_gob`/`dummy_cepo`/`dummy_elec`; criterio
  ya acordado: no se pisan hasta reproducir exactamente sus valores en el tramo común).
- El copiloto puede **responder sobre un evento** usando la ficha y el corpus de historia.
- La Mesa puede importar un evento como dummy (si se decide §13.3).

---

## 10. Código

### 10.1 Backend

**`cueva/datos/historia.py`** — puro (lee disco, no sale a la red):

```python
def cargar_presidencias() -> list[Periodo]: ...
def cargar_ministros() -> list[Periodo]: ...
def cargar_autoridades() -> list[Periodo]: ...
def cargar_eventos() -> list[Evento]: ...
def cargar_ficha(evento_id: str) -> Ficha: ...          # frontmatter + cuerpo + cifras resueltas
def cargar_series() -> list[SerieHistorica]: ...        # series.json + datos
def gobierno_en(fecha: date) -> Periodo: ...            # la derivación de §8.1
def validar() -> list[str]: ...                         # lo que usan los tests y un script de chequeo
```

Errores como excepciones tipadas (`EventoNoEncontrado`), ids validados contra
`^[a-z0-9-]+$` antes de tocar el disco (el mismo cuidado que ya se tuvo con path traversal en
proyectos).

**Endpoints** (contratos Pydantic en `cueva/api/esquemas.py`; router propio `api/routers/historia.py`
cuando se parta `app.py`):

| Endpoint | Devuelve |
|---|---|
| `GET /tiempo` · `GET /tiempo/{evento_id}` | la página (el segundo abre con la ficha — permalink) |
| `GET /api/v1/historia` | todo lo necesario al abrir, en una sola respuesta |
| `GET /api/v1/historia/eventos/{id}` | la ficha completa, se pide al abrirla |

`GET /api/v1/historia` (estimado < 200 KB: son ~60+60+40 períodos, unos cientos de eventos y 10
series de 145 puntos):

```jsonc
{
  "rango": {"desde": 1880, "hasta": 2026},
  "presidencias": [{"orden": 1, "nombre": "Julio Argentino Roca", "desde": "1880-10-12",
                    "hasta": "1886-10-12", "tipo": "constitucional", "verificado": false}],
  "ministros": [],
  "autoridades": [],
  "eventos": [{"id": "crisis-baring-1890", "titulo": "Crisis de Baring", "categoria": "crisis",
               "subtipo": "default", "nivel": "episodio", "desde": "1890-07-01", "hasta": "1891-12-31",
               "precision": "mes", "resumen": "…", "ficha": true, "verificado": false}],
  "series": [{"id": "pbipc", "nombre": "PBI per cápita", "unidad": "índice 1880=100", "tipo": "nivel",
              "tramos": [{"id": "maddison", "desde": 1880, "hasta": 2022}],
              "datos": [[1880, 100.0, "maddison"]]}],
  "vocabulario": {"categorias": {"crisis": {"etiqueta": "Crisis", "color": "--s3"}}}
}
```

### 10.2 Frontend

```
web/estilo/tokens.css      sistema de diseño compartido (lo usa también la Mesa después)
web/tiempo/index.html      estructura de la pantalla (§1.1)
web/tiempo/tiempo.css
web/tiempo/grafico.js      motor SVG: escalas, bandas, pines, series, Δ, brush, zoom, tarjetita
web/tiempo/ficha.js        panel inferior, cifras enlazadas
web/tiempo/estado.js       estado único de la pantalla (rango, modo, capas, series activas, evento)
web/tiempo/app.js          arranque: pide /api/v1/historia y conecta todo
```

- **ES modules nativos, sin build** (`<script type="module">`), como recomienda la auditoría.
- **SVG propio, no Plotly.** Bandas de gobierno, pines con jerarquía, bandas de régimen y cifras
  que manejan el zoom son justamente lo que en Plotly se vuelve incómodo; el motor del mockup ya
  resuelve esas interacciones y es la especificación viva. Se **porta y ordena** en módulos, no se
  copia el archivo.
- Markdown de las fichas: se renderiza **en el servidor** a HTML saneado, así el frontend no
  interpreta texto libre (evita XSS por contenido de fichas).

### 10.3 Tests — `tests/test_historia.py`

Los datos se testean como código. Además de lo que ya chequea sobre presidencias:

| Archivo | Qué falla |
|---|---|
| todas las tablas | fecha inválida · `hasta < desde` · `verificado` fuera de `si`/`no` · fila sin `fuente` |
| `ministros_economia.csv` | solapamiento dentro del mismo `cargo` |
| `autoridades_monetarias.csv` | solapamiento dentro de la misma `institucion` · institución fuera del vocabulario |
| `eventos.csv` | id duplicado o mal formado · categoría/subtipo/nivel fuera del vocabulario · sin `refs` ni `fuente` · clave de `refs` inexistente en `referencias.bib` · `ficha=si` sin archivo |
| `fichas/*.md` | ficha sin fila en `eventos.csv` · `{{c:x}}` que no existe en `cifras` · cifra sin `fuente` · `serie` que no está en `series.json` · `[@clave]` inexistente · medio sin `credito`/`licencia`/`url_origen` · archivo de medio inexistente · `relacionados` inexistentes |
| `series.json` + `series/*.csv` | serie sin `tipo`, `agregacion_anual`, `empalme` o tramos · año repetido · `tramo` del CSV que no está declarado · tramos que se superponen sin empalme descrito |
| `medios/` | imagen que ninguna ficha usa · imagen > 500 KB |

---

## 11. Cómo cargar lo que ya tenés

Recetas para el carril 📚. Ninguna requiere programar.

### A. Un libro o paper de historia económica (PDF)

1. Copiar el PDF a `knowledge-base/corpus/13_historia_economica_argentina/`, con nombre
   `apellido_anio.pdf`.
2. Agregar su entrada a `knowledge-base/referencias.bib` (plantilla en §8.4) con `file` apuntando
   al PDF.
3. Reindexar: `python scripts/ingestar.py knowledge-base/corpus` (solo procesa lo nuevo).

> `knowledge-base/GUIA_CARGA.md` todavía muestra comandos viejos (`rag/ingest.py`): el correcto es
> el de arriba.

### B. Una obra que no tenemos en PDF (pero se va a citar)

Solo el paso 2, sin `file`. Queda citable; las citas a esa obra se marcan "no verificable".

### C. Un evento que aparece en la bibliografía

1. Agregar una fila a `data/historia/eventos.csv` (Excel o Google Sheets sirven; guardar como
   **CSV UTF-8**).
2. `refs` con la clave de la obra; si hay norma, `fuente` con su número.
3. `verificado=no` hasta contrastarlo con una segunda fuente o con la norma original.

### D. Una tabla de datos (Ferreres, un anuario, una planilla)

1. Guardar el archivo **tal como vino** en `data/historia/_crudo/<fuente>/`. No editarlo.
2. Anotar en la conversación de trabajo: qué serie es, qué cuadro/hoja, qué unidad, cómo se
   agrega al año. Con eso se escribe su entrada en `series.json` y el script que la convierte.
3. Si hay que **transcribir a mano** (una tabla de un libro escaneado), se transcribe a un CSV en
   `_crudo/<fuente>/` con la página en el nombre (`ferreres_p412.csv`) y se trata igual que un crudo.

### E. Una ficha completa

1. Copiar `data/historia/fichas/_plantilla.md` a `fichas/<id-del-evento>.md`.
2. Llenar frontmatter y secciones. Los números importantes van como cifras (`{{c:nombre}}`).
3. En `eventos.csv`, poner `ficha=si`.

### F. Una foto

1. Buscar primero en Wikimedia Commons o el Archivo General de la Nación.
2. Guardar en `data/historia/medios/` (≤ 500 KB).
3. Registrarla en la ficha con `credito`, `licencia` y `url_origen`. Sin los tres, no se usa.

---

## 12. Riesgos conocidos

| Riesgo | Mitigación |
|---|---|
| **Extracción automática con errores** (ya pasó: faltaban Milei, Puerta y Camaño) | toda fila nace `verificado=no`; la UI lo muestra |
| **Empalmes silenciosos** que fabrican tendencias | `tramo` por año + `empalme` obligatorio |
| **Dos "inflaciones de 1989"** según cómo se agregue | `agregacion_anual` obligatorio |
| **Cambios de moneda** (5 desde 1880) en series nominales | las troncales son reales, índices o ratios; ninguna nominal en pesos |
| **Derechos de imagen** | §6.7 + test de medios |
| **Redactar fichas es mucho trabajo** | empezar por pocas (§13.2); los demás eventos viven con resumen |
| **Historia contaminando el RAG de método** (y viceversa) | campo `tema` en fragmentos (§8.4) |

---

## 13. Decisiones abiertas

1. **Lista final de series troncales.** La tabla de §2 es una propuesta: se confirma contra los
   datos que efectivamente hay y los que se pueden conseguir. Al construir T0 quedó claro que
   las **fichas ya declaran series** (`pbipc`, `infl`, `tcr`, `deuda`, `apertura`, `toi`,
   `salario`, `poblacion`): esos ids son el pedido concreto del tramo 1880-1935 y conviene que
   `series.json` los respete o que las fichas se corrijan a la vez. Ojo con `infl` vs
   `inflacion` y `salario` vs `salario_real`.
2. **Cuántas fichas completas y quién redacta.** Propuesta: ~12 estructurales (1890, 1930, 1935,
   1946, 1975, 1976, 1989, 1991, 2001, 2002, 2018, 2023) y el resto con resumen. ¿Manuscrito, o
   borrador del copiloto con verificación humana? Si es lo segundo, `verificado` es el control
   central.
3. **Puente con la Mesa** ("importar evento como dummy"): ¿se hace en T6 o no?
4. **Qué pasa antes de 1880.** El script de Reinhart-Rogoff trae crisis desde 1800. ¿Se descartan,
   o el eje permite ir hacia atrás con cobertura declarada?
5. **Campo `tema` en el RAG** para separar historia de econometría (técnica, recomendada).

---

## 14. Registro de decisiones

| Fecha | Decisión | Motivo |
|---|---|---|
| 2026-08-28 | Sin «llevar a la mesa» ni «crear dummy» | consulta y operación separadas |
| 2026-08-28 | Catálogo cerrado de series anuales, máx. 4 | legibilidad sobre 145 años |
| 2026-08-28 | Índice 100 / Log / Paneles + panel Δ i.a. independiente | escalas incompatibles; nivel y variación a la vez |
| 2026-08-28 | Tarjetita con serie, año y valor | pedido del usuario |
| 2026-08-28 | Ficha en panel inferior, cifras enlazadas | el gráfico tiene que seguir visible |
| 2026-08-28 | Propuestas §6.1-6.7 incorporadas al diseño | completitud; cada una con fase asignada |
| 2026-09-12 | Datos en `data/historia/`, no en `cueva/datos/historia/` | los datos no viven dentro del paquete de código; sigue a `data/series/` |
| 2026-09-12 | Eventos: índice CSV + ficha markdown solo para los que la tienen | la mayoría de los eventos son una fila; la prosa larga no cabe en JSON |
| 2026-09-12 | Cifras referenciadas por nombre (`{{c:tope}}`), no por posición | reordenar no rompe el relato |
| 2026-09-12 | Citas con sintaxis Pandoc contra `referencias.bib` | estándar académico, exportable a LaTeX y Word |
| 2026-09-12 | Gobierno de un evento derivado por fecha, no guardado | una sola fuente de verdad |
| 2026-09-12 | Series troncales con `tramo` por año y `agregacion_anual` obligatoria | los empalmes y la agregación cambian el dato |
| 2026-09-12 | Motor gráfico SVG propio, ES modules sin build | bandas, jerarquía y zoom semántico; lo pide la auditoría |
| 2026-09-12 | Se construye en fases T0-T6, empezando por presidencias reales | la primera pantalla funciona con datos que ya existen |
| 2026-09-16 | El área del gráfico queda **declarada vacía** hasta T3, y su alto se le devuelve a los carriles de eventos | sin series troncales, rellenar el espacio con algo sería inventar; la cobertura honesta se muestra, no se disimula |
| 2026-09-16 | Los eventos se leen como **partitura: un carril por capa**, con rótulos en dos filas y halo | es lo que hoy tiene datos con fuente; a 55 años y 63 eventos una sola banda de pines es ilegible |
| 2026-09-16 | Los regímenes se **empaquetan por intervalos** dentro de cada subtipo, no una fila por subtipo | «Bancos Nacionales Garantidos» (1887-1890) corre por dentro de la inconvertibilidad (1885-1899) y comparte subtipo: con una fila fija se pisaban |
| 2026-09-16 | Con la ficha abierta los rótulos pasan a **una sola fila** | el carril comprimido (34 px) no da para dos sin que un rótulo invada el carril de al lado |
| 2026-09-16 | `/web` sirve los estáticos de toda la plataforma; `tokens.css` es el sistema de diseño compartido | la Mesa va a consumir los mismos tokens; un solo lugar donde cambiar el tema |
| 2026-09-16 | `pyyaml` pasa a dependencia del proyecto | el frontmatter de las fichas tiene listas de objetos; el parser por regex de los skills no alcanza |
