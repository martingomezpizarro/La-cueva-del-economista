# La Cueva del Economista — estado y contexto para el asistente

Plataforma de econometría de series de tiempo (visión completa en `docs/VISION.md`):
datos + motor de análisis + **agentes-profesores con RAG** (`docs/PLAN_AGENTES.md`).
La arquitectura objetivo y el roadmap aprobado viven en `docs/PROPUESTA_ARQUITECTURA.md`.
Responder siempre en español.

**Mapa de la plataforma (leer primero, 2026-09-12)**: `docs/PLATAFORMA.md` — las 4 fuentes del
backend, los 2 módulos del frontend, carpetas, API, decisiones y orden de construcción. Un documento
por módulo con spec + construcción + registro de decisiones: `docs/MODULO_LINEA_DE_TIEMPO.md`
(**en construcción primero**, fases T0-T6 en su §9) y `docs/MODULO_MESA_DE_TRABAJO.md`. Referencia
visual: `docs/mockup/cueva-mockup.html` (publicado como artifact; el documento manda sobre el mockup).

## Estado (actualizado 2026-07-14)

**Sitio publicado, versión estática (sesión 2026-10-18)** — `docs/PUBLICAR_SITIO.md`.
`scripts/construir_sitio.py` → `_sitio/` congela la API de lectura (historia, fichas, datos del
explorador) en JSON e inyecta `web/estatico/estatico.js`, que traduce los `fetch` a esos
archivos y hace fallar con un mensaje claro lo que necesita Python (Estudio, Kalman, agentes).
`/` = Mesa (`web/estatico/mesa.html` + explorador en iframe), `/tiempo/<id>/` = permalinks.
`.github/workflows/pages.yml` publica en GitHub Pages en cada push a `main`, con el dominio
`cuevadeleconomista.martingomezpizarro.com.ar`. **Las series NO están en el repo**: se
publican con `--exportar-datos-explorador` → `data/publico/explorador_datos.json`, que se
corre en la máquina con la carpeta del Trabajo Final. Tests: `tests/test_sitio.py`.

**Una sola plataforma a la vista (sesión 2026-09-17).** La Mesa (`/`) y la Línea de Tiempo
(`/tiempo`) comparten cascarón:
- `web/index.html` carga `web/estilo/tokens.css` y tiene la **topbar del mockup**: marca,
  conmutador de módulos, Vista Rápida/Proyecto, chips de estado y botón de tema. **No se
  reescribió su CSS**: sus nombres viejos (`--bg`, `--panel`, `--panel2`, `--txt`, `--muted`,
  `--acc`…) quedaron como **alias puente** hacia los tokens, así lo que ya andaba siguió
  andando. Lo NUEVO se escribe con tokens directos (`--surface`, `--ink`, `--accent`…).
- **`web/estilo/tema.js`**: el tema es del usuario, no de la pantalla. Lo guarda en
  `localStorage` (clave `cueva_tema`) y lo comparten los dos módulos; se carga sin `defer` y
  antes del contenido para que no parpadee.
- ⚠ **`web/explorador.html` NO sigue el tema**: tiene su paleta oscura fija. Hasta que se
  porte (`MODULO_MESA_DE_TRABAJO` §8.2) la Mesa en claro muestra un iframe oscuro; en oscuro
  quedan coherentes.
- **La subnav de cinco vistas del mockup no se construyó**: Tests y Transformaciones todavía
  no existen como pantallas y tres pestañas vacías serían maqueta. Va cuando existan (§8.6).


**Línea de Tiempo: fase T0 construida y andando (sesión 2026-09-16).** Se abre en `/tiempo`.
- **`web/estilo/tokens.css`**: el sistema de diseño salió del mockup a un archivo propio (tokens
  claro/oscuro + primitivas: chip, btn, seg, note, rail, layer, panel). **La Mesa tiene que
  consumir ESTE archivo** cuando se la rehaga; no volver a copiar CSS del mockup.
- **`cueva/datos/historia.py`** (puro, no toca la red): presidencias · eventos · vocabulario ·
  fichas · `referencias.bib` · `gobierno_en()` · `validar()`. El **markdown de las fichas se
  renderiza acá, en el servidor**, a HTML saneado — el frontend nunca interpreta texto libre
  (escapa todo y después resuelve `{{c:cifra}}` y `[@cita]`). Dependencia nueva: **pyyaml**.
- **API**: `GET /tiempo` · `GET /tiempo/{evento_id}` (permalink) · `GET /api/v1/historia` (todo
  en una respuesta) · `GET /api/v1/historia/eventos/{id}`. Estáticos nuevos: **`/web`** (CSS y
  módulos ES de toda la plataforma) y `/historia-medios`.
- **`web/tiempo/`**, ES modules sin build: `estado.js` (estado único) · `grafico.js` (motor SVG
  portado del mockup) · `ficha.js` (panel inferior) · `app.js` (arranque y rails).
- **Lo que se ve**: banda de 60 gobiernos, regímenes en carriles (empaquetados por intervalo
  dentro de cada subtipo), episodios como barras, hitos como pines, **un carril por capa de
  eventos**, filtro de detalle por zoom, brush, tarjetita, rail de capas con conteos calculados
  y las 9 fichas con cifras enlazadas, citas y bibliografía formateada desde el .bib.
- **El área del gráfico está declarada VACÍA a propósito**: no hay `series.json` (fase T3) y no
  se dibuja ninguna curva inventada. Cuando se construyan las series, ojo con los ids que las
  fichas ya declaran (`infl`, `tcr`, `deuda`, `pbipc`, `apertura`, `toi`, `salario`, `poblacion`):
  o `series.json` los respeta o hay que corregir las fichas en la misma pasada.
- Tests: `tests/test_historia.py` (17) y 3 nuevos en `tests/test_api.py`. Ruff en verde.
- **Pendiente inmediato**: T1 (`ministros_economia.csv`, `autoridades_monetarias.csv` — la UI ya
  tiene las capas y las muestra como «falta»), normalizar `eventos_semilla_1936_2025.csv`, y T3.
- ⚠ **9 tests rojos preexistentes** (`test_skills.py`, `test_agentes_offline.py`,
  `test_conocimiento.py`): son del traslado de `knowledge-base/` a `RAG/`, no de este módulo.


**Fases 0, 1, 2 y 3 del roadmap COMPLETAS** (rescate + red de seguridad + agentes v2 + conocimiento).

**Procedencia de las series + API del BCRA (sesión 2026-08-27):**
- **Cada serie declara de dónde sale.** `cueva/datos/catalogo.json` sumó un bloque `proc`
  por serie (y por fuente de datos, cuando una serie tiene varias frecuencias con orígenes
  distintos): `fuente`, `definicion`, `id_externo`, `endpoint`/`url_humana`, `script`,
  `insumos`+`transformacion` (obligatorios si `fuente == "propia"`), `confianza` y
  `verificado`. **739/739 entradas con procedencia.** El contrato completo está en
  `docs/DATOS.md` — leerlo antes de tocar datos.
- **Capa nueva `cueva/fuentes/`**: adaptadores de organismos. Es la ÚNICA parte de la
  capa de datos que toca la red (`cueva/datos/` y `cueva/econometria/` siguen puras).
  Contiene `registro.json` (padrón de 12 organismos con sitio, API, licencia y si el dato
  se puede republicar), `registro.py` (lectura tipada) y `bcra.py` (cliente de la API).
- **API del BCRA, Estadísticas Monetarias v4.0** (`https://api.bcra.gob.ar`, sin clave):
  **1610 variables**. El **2026-08-21 el BCRA sumó dos categorías con serie histórica
  larga**: «Agregados monetarios y sus componentes» (28 series mensuales, Base Monetaria /
  M1 / M2 / M3 y componentes, **desde 1940-06-30**) y «Activos y Pasivos del BCRA»
  (reservas a fin de mes **desde 1940-02-29**, id 1605). Las 29 ya están en el catálogo,
  en «Monetario y Cambiario», pendientes de bajar.
  OJO con las unidades: el bloque histórico viene en **miles de ARS** y las series diarias
  equivalentes en **millones de ARS**; no son empalmables sin convertir.
- **Dos trampas de la API, ya documentadas y testeadas**: (1) los campos del índice son
  `periodicidad`/`unidadExpresion`/`moneda`/`tipoSerie`/`primerFechaInformada`/
  `ultFechaInformada`, NO `frecuencia`/`unidad`/`fechaInicio`/`fechaFin`; (2)
  `metadata.resultset.count` es lo que queda DESDE el offset, no el total — la paginación
  corta por página corta.
- **OJO — el catálogo anida hasta 5 niveles vía `children`** (balance de pagos, esquema
  fiscal, vencimientos de deuda): son **582 series / 739 entradas**, no las 356 del primer
  nivel. Todo lo que recorra el catálogo TIENE que descender por `children` o se le
  esconden 226 series. Ya pasó una vez.
- **Plan de rehacer el catálogo + editor visual `/catalogo`**: `docs/PLAN_CATALOGO.md`
  (fase 0 normalizar el modelo → 1 servirlo por API → 2 editor → 3 curaduría).
- **Cronología histórica (2026-08-27)**: `data/historia/presidencias.csv` — 60 períodos
  desde 1880-10-12 (55 presidencias + 5 juntas militares), línea de tiempo SIN huecos ni
  solapamientos, protegida por `tests/test_historia.py`. Se genera con
  `scripts/construir_presidencias.py`; todas las filas están `verificado=no` a la espera del
  control contra Casa Rosada. Fuentes evaluadas y modelo de datos en
  `docs/FUENTES_EVENTOS_HISTORICOS.md`. Pendiente: correr `scripts/bajar_crisis_rr.py`
  (crisis y defaults desde 1800, base de Reinhart & Rogoff; hbs.edu bloqueado en el sandbox).
  Las dummies actuales (`dummy_gob`, `dummy_cepo`, `dummy_elec`) arrancan en 1999 y una
  columna por presidente NO escala a 1880: se van a GENERAR desde estas tablas.
- **Duplicados y nombres (investigación 2026-08-27, SIN aplicar)**:
  `docs/INFORME_DUPLICADOS_Y_NOMBRES.md`. 82 etiquetas ambiguas (281 series) → 0 con
  `scripts/normalizar_nombres_series.py --aplicar` (366 renombres por regla; NO toca ids).
  De las 100 series multi-frecuencia: **48 unificables a mensual** (EMAE/ICA: el trimestral
  y el anual son agregación verificada del mensual, error < 0,03 %) con
  `scripts/unificar_frecuencias.py --aplicar`; **44 NO se tocan** porque su mensual es una
  ESTIMACIÓN Kalman propia y el dato nativo es el trimestral del INDEC — borrarlo sería
  cambiar el dato oficial por la estimación. Pendiente de mirar: `ica_icmb` y `sc_asia`.
- **33 series del BCRA agregadas al catálogo (2026-08-28)**, `scripts/agregar_series_bcra_api.py`:
  11 tasas de interés (el catálogo NO tenía ninguna; plazo fijo 30d desde 1985), inflación
  mensual desde 1943 e interanual desde 1944, CER/UVA/UVI/ICL, agregados diarios desde 1996,
  balance del BCRA (LELIQ, pases, LEBAC, adelantos transitorios) y TC minorista. 6 subgrupos
  nuevos. **615 series / 772 entradas**; *Precios e Inflación* pasó de 2 a 8 series.
  Pendientes de bajar: `python scripts/actualizar_bcra.py --series --ids 12,7,35,8,44,13,14,11,43,30,31,32,40,27,28,15,16,17,18,19,25,22,23,24,26,4,1247,1260,1258,1261,1264,1267,1268`
- **Planilla de campaña** (`scripts/catalogo_planilla.py` → `docs/catalogo_series.csv`; el
  .xlsx con formato se arma aparte y va gitignorado): una fila por serie (615) con 5 columnas
  vacías para completar a mano — ¿Ampliable?, Fuente alternativa, Objetivo desde, Notas,
  Revisado. Cinco hojas: Cómo usar · Catálogo · Resumen (con COUNTIF, se recalcula) · Fuentes
  (24) · Prioridades. Pensada para subir a Google Sheets. Si se regenera, las columnas de
  trabajo vuelven vacías: guardar copia antes de editar.
- **Series largas: hasta dónde se puede ir atrás** — `docs/FUENTES_SERIES_LARGAS.md`. Lo
  esencial: las reservas ya están en su máximo oficial (id 1605, 1940-02; **el BCRA se creó
  en 1935**, antes son reservas de la Caja de Conversión y NO se empalman). El TC oficial no
  es problema de fuente sino de EMPALME: la Com. A3500 es de 2002 y hubo cinco cambios de
  moneda desde 1880 — la serie larga se construye desde Ferreres. Los depósitos en USD no
  existen antes de 1977 y fueron pesificados en 2002 (quiebre estructural). El ITCRM tiene
  alternativa MUCHO más larga: **Bruegel REER índice estrecho, MENSUAL desde 1960** (37
  años más que el BCRA, licencia libre con cita); el BIS vía FRED (1994) queda segundo.
  Caja de Conversión 1901-1935: Instituto de Economía Bancaria + Memoria de la Caja de
  Conversión 1933, reconstruidas por Salama (UNLP doc. 28) — transcripción manual, y su
  advertencia de que no son un balance completo va a `proc.notas`.
  Los depósitos/préstamos en USD son insumo de dos ratios que FALTAN en el catálogo:
  **dolarización de depósitos** (sustitución de moneda) y **descalce de monedas** (por qué
  una devaluación es contractiva). Registro ampliado a 20 fuentes (FRED, BIS, FMI/IFS,
  Ferreres, Della Paolera & Taylor).
- **Cobertura del BCRA** (`scripts/cobertura_bcra.py`, ver `docs/DATOS.md` §10): cruza el
  rango real en disco contra el que publica la API. Resultado: 5 series se estiran
  (REM +12,3 años, reservas +7,0, depósitos +3,0 — y las 4 están 89 días atrasadas), 29
  históricas por bajar enteras, 19 del BCRA sin `idVariable` (las 15 del ITCRM no salen de
  la API sino de planillas), y ~36 variables que la API tiene y el catálogo NO: **11 tasas
  de interés** (el catálogo no tiene ninguna; plazo fijo 30 días desde 1985), inflación
  desde 1943, CER/UVA/UVI/ICL, agregados diarios desde 1996 e instrumentos del BCRA.
  El snapshot local es PARCIAL (69 de 1610): falta correr `--indice`.
- **Grilla de revisión** (`scripts/cuadro_revision.py` → `docs/cuadro_revision.html`,
  publicada como artifact con la capacidad `artifact`): el catálogo con la MISMA jerarquía
  que el árbol del visualizador del TF (familia con color › subgrupo › sub-subgrupo › serie,
  carpetas con «Total»), colapsable y con avance por grupo. Se editan nombre, descripción,
  fuente y unidad (magnitud/escala/moneda por desplegable del vocabulario); base, origen,
  final y frecuencia NO se editan porque salen del archivo. Tres veredictos: está bien →
  `verificada`; tiene un problema → nota en `proc.revision` y NO se sella; sin revisar.
  El regreso al catálogo es explícito: `scripts/aplicar_revision.py --desde <html> [--aplicar]`,
  que simula por defecto, rearma la unidad desde `unidades.json` y AVISA en vez de inventar
  si la combinación no existe. CSS y JS en `web/cuadro/revision.{css,js}`. 9 tests en
  `tests/test_revision.py`.
- **Cuadro de series**: `python scripts/cuadro_series.py` genera `docs/cuadro_series.html`
  (página navegable: buscar, filtrar, ordenar, ficha por serie) + el CSV + el markdown.
  Columnas: serie · base · origen · final · frecuencia · fuente · descripción · magnitud ·
  escala · moneda. El HTML es derivado y va gitignorado; el CSS/JS viven en `web/cuadro/`.
- **Unidades descompuestas** (`cueva/fuentes/unidades.py` + `unidades.json`): el `unit` de
  texto libre se traduce a magnitud + escala + moneda contra un vocabulario cerrado (34
  textos, 14 magnitudes). Es lo que deja ver que la base monetaria histórica (miles de ARS)
  y la diaria (millones) NO son comparables. Un `unit` nuevo sin dar de alta rompe el test.
- **Scripts nuevos**: `actualizar_bcra.py` (`--categorias` para detectar bloques nuevos del
  BCRA, `--indice` para el diccionario + metodología, `--series [--todas|--categoria|--ids]`
  para bajar a `data/series/bcra/`), `auditar_series.py` (radiografía de las 494 entradas →
  `docs/INVENTARIO_SERIES.md` + `inventario_series.csv`), `completar_procedencia.py` (carga
  `proc` desde una tabla de atribución basada en evidencia; nunca pisa lo que ya tiene
  procedencia propia) y `agregar_series_bcra_historicas.py` (el bloque de 1940).
- `tests/test_fuentes.py` (13 tests) falla si una serie no declara procedencia, si apunta a
  un organismo inexistente, si es propia y no dice de qué se construye, o si se rompe la
  paginación / el mapeo de campos del cliente del BCRA.
- Pendiente de esta línea: correr `--indice` y `--series` con red (desde el sandbox de
  Cowork `api.bcra.gob.ar` está bloqueado por la allowlist de egress); confirmar las 21
  series con `confianza: "media"`; definir el empalme histórico↔diario.

**Explorador NATIVO + Vista Rápida/Proyecto + banco de trabajo (sesión 2026-07-14):**
- **El visualizador del TF ya NO se embebe por iframe a :8765**: la SPA completa vive en
  `web/explorador.html` (servida en `GET /explorador`, ~7000 líneas) con Plotly/SheetJS
  vendorizados en `web/vendor/`. El server externo del TF quedó obsoleto para la plataforma.
- **Datos en vivo**: `cueva/datos/explorador_datos.py` arma el payload columnar
  `{archivo: {col: [...]}}` (el viejo `EMBEDDED`) desde el catálogo + deflactores
  (PBI/CER/TIP) + dummies + vencimientos xlsx transpuestos → `GET /api/v1/explorador/datos`
  (~6.6 MB, cacheado por mtime). Fallback: mount estático `/data` → carpeta de datos del TF.
- **Kalman nativo** (`cueva/econometria/kalman.py`, `POST /api/v1/explorador/kalman`) y
  **puente al análisis básico legacy** (`POST /api/v1/explorador/analisis-basico` corre el
  02a del TF por subprocess; reporte en `/explorador-reporte/`). El legacy se reemplazará
  por el banco de trabajo.
- **Vista Rápida vs Proyecto** (header de `web/index.html`): la Vista Rápida es un espacio
  efímero único (nada se persiste; estado en sessionStorage), SIN auto-crear proyectos
  basura. Los proyectos se crean/renombran CON NOMBRE (modal propio). Botón
  **"💾 Promover a proyecto"**: `POST /api/v1/proyectos` acepta semilla
  {series, serie_dependiente, frecuencia, estudios} y se lleva todo lo acumulado.
  En Vista Rápida el rail de drawers y el FAB de agentes quedan gateados (son del proyecto).
- **Banco de trabajo "⚗️ Estudio"** (pestaña nueva de la SPA): pasos declarativos
  herramienta+series+transformación+parámetros que corren EN EL SERVIDOR vía
  `POST /api/v1/herramienta`; tarjetas con resumen, tablas (coeficientes, diagnósticos)
  y gráficos Plotly (ajuste/residuos, pronóstico con IC, heatmap de correlaciones).
  En modo Proyecto cada paso persiste en `piz.estudios` **con `id` y `resultado` completo**
  (`DELETE /api/v1/proyectos/{id}/estudios/{eid}` para quitarlos); el shell y la SPA se
  hablan por postMessage (`cueva:contexto`, `cueva:estudios-cambiaron`, `cueva:vr-limpiar`).
- **Herramientas ampliadas** (11): transformaciones como parámetro común
  (`transf`: nivel/log/dif/dif2/dif_log/pct — P2 de la auditoría, HECHO), `ols` con
  rezagos de X e Y (estilo ARDL) + tabla de coeficientes + gráfico, y nuevas
  `correlaciones` (matriz Pearson) y `arima` (pronóstico auto por AIC con IC 95%).
- El drawer "Elegir series" ahora tabula por **familia** del catálogo (adiós pestaña
  MATRIZ ARG vacía) y filtra client-side sobre el catálogo completo.
- `scripts/generar_arbol_visualizador.py` inyecta el CATALOG en **ambos** destinos:
  `web/explorador.html` (principal) y el template del TF (opcional, para su standalone).
- 91 tests en verde (12 nuevos en `tests/test_explorador.py`).
- Pendiente de esta línea: punto 3 (que los agentes VEAN estudios/series en sus prompts —
  ojo: `piz.estudios` se persiste pero aún NO se inyecta en los prompts) y punto 4
  (fijar al informe, screenshots en notas).

**Agentes con herramientas coherentes (auditoría 2026-07-06, P0+P1 ejecutados):**
- **Skills sincerados**: la lista blanca de cada skill es SUBCONJUNTO del REGISTRO (lo vigila
  `test_herramientas_de_skills_existen_en_registro`); lo que la plataforma no ejecuta va en el
  cuerpo como "asesorás sin ejecutar" (nunca en el frontmatter, para que el agente no alucine
  evidencia). `declaraciones_herramientas` loguea warning si algo se descarta.
- **Herramientas nuevas** (`cueva/econometria/herramientas.py`, 9 en total): `diagnosticos`
  (batería sobre residuos OLS: Ljung-Box, Breusch-Godfrey, ARCH-LM, Jarque-Bera, RESET, CUSUM →
  semáforo verde/amarillo/rojo — el Crítico con dientes) y `arch_lm` (¿se justifica un GARCH?).
- **Tool-use en 6 turnos** (antes 1): Metodólogo y Crítico en `clasica`; multivariados, volatilidad,
  controles_causal y robustez en `equipo_completo`. `LIMITE_LLAMADAS_MESA` 40→60.
- **Granger se corre en modelización** (dep vs 2 indeps) — antes el turno causal leía evidencia
  que no existía. De paso se cazó bug latente: `p_por_lag` con claves numpy.int64 rompía la
  persistencia de la pizarra la primera vez que granger corría en la mesa.
- **Handoffs dinámicos**: las REGLAS ofrecen todo el plantel (menos uno mismo), ya no los 4
  cableados; `AGENTES_IDS` incluye a los 7 especialistas (tienen chat 1:1).
- **Degradación visible**: turno que pedía tool-use con backend sin function calling (Claude)
  sale con `estado="sin_herramientas"`, no un "ok" mentiroso.
- Pendiente P2/P3 (decidido en la auditoría): transformaciones como parámetro de las herramientas,
  `catalogo_series` para el Curador, pronóstico ARIMA/ETS/DM, tool-use en `responder_directo`.

**Organización de series (catálogo curado, fuente única):**
- `cueva/datos/catalogo.json` es LA fuente de verdad de la taxonomía: **9 familias**
  (grupo → subgrupo → serie) con `id`, `label`, `unit` y fuentes por frecuencia (M/Q/A).
  553 hojas migradas del árbol viejo del visualizador (20 grupos → 9 familias; se colapsaron
  los grupos de 1 serie, se movió Índice Líder a Actividad y las expectativas de inflación a
  Expectativas y Confianza). Para reorganizar: **editar el JSON**, no Python ni el template.
- `series.py` consume el JSON (aporta `grupo`/`subgrupo`/`unidad`/`etiqueta`); el escaneo de
  carpetas quedó como *fallback* solo para archivos que el catálogo NO cura (sintéticos de test,
  subidas, CSVs por curar). Un archivo referenciado por el catálogo es "territorio curado": el
  escaneo no vuelve a explotar sus columnas (adiós slugs crípticos de los INDEC anuales).
- ANÁLISIS MATRIZ ARG **excluido** (sus 9 CSVs duplicaban EMAE/ICA ya presentes, mejor abiertos,
  en el Trabajo Final).
- El árbol del visualizador se **deriva** del JSON: `python scripts/generar_arbol_visualizador.py`
  inyecta el `const CATALOG` (estilo comillas simples, compatible con el generador de TF) entre
  marcadores `/*__CATALOG_INICIO__*/…/*__CATALOG_FIN__*/` en `visualizador_template.html`; después,
  en la carpeta de TF, `python notebooks/generar_visualizador.py` embebe los datos.
- El drawer "Elegir series" de `web/index.html` ya tabula por familia/subgrupo del catálogo
  (resuelto 2026-07-14; la pestaña "MATRIZ ARG" vacía se eliminó).

Fase 3 (conocimiento):
- **Ingesta incremental con manifiesto** (`indice/manifest.json`: hash SHA-256 por archivo):
  re-ingestar solo procesa lo nuevo/cambiado, reusa embeddings de lo que no cambió y
  descarta lo borrado. `scripts/ingestar.py` (flag `--completo` para reconstruir).
- **Colecciones con provenance**: cada fragmento lleva `coleccion` ("corpus" | "usuario");
  las citas de la biblioteca del usuario van marcadas y el Bibliógrafo la prioriza
  (`prioriza_usuario: si` en su skill).
- **Subida de bibliografía del usuario**: `POST /api/v1/biblioteca` (y GET para listar)
  con checklist de seguridad (extensión, 30 MB máx., firma %PDF, nombre regenerado);
  UI en el drawer "Bibliografía propia". Archivos en `<CUEVA_DATA>/biblioteca/`.
- **Evaluación de retrieval**: `tests/eval_rag.jsonl` (20 preguntas doradas) +
  `scripts/evaluar_rag.py` (aciertos@1/3/5, `--modo tfidf|embeddings` para comparar).
- 79 tests en verde (aislados: los tests jamás tocan el índice real).

Fase 2 (agentes v2):

Fase 2 (agentes v2):
- **Los agentes se definen en `knowledge-base/skills/`** (frontmatter: `agente`, `rol`,
  `modelo` [tier barato/medio/claude], `sesgo_rag`, `herramientas` [lista blanca],
  `prioriza_usuario`; cuerpo = system prompt). Editar el markdown cambia al agente sin
  tocar Python. Plantel: 12 agentes. Cargador: `cueva/agentes/skills.py`.
- **El guion es un dato** (`cueva/agentes/pipelines.py`): pipelines `clasica` (4 profesores)
  y `equipo_completo` (10 especialistas). `grafo_cueva.py` + LangGraph RETIRADOS.
- **Tool-use real (function calling de Gemini)**: el Metodólogo PIDE herramientas en la
  modelización; lista blanca del skill ∩ REGISTRO, tope de 3 por turno, argumentos saneados,
  cada ejecución queda como evidencia en la pizarra. Probado contra la API real.
- **SSE tipado** (`event: mensaje|fin|error`) + **transcript JSONL** por sesión
  (`data/proyectos/{id}.transcript.jsonl`) + uso de tokens visible en la UI al cerrar la mesa.
- 62 tests en verde.

Fases 0-1 (resumen):

- **El `.git` vive en la raíz** (la anomalía del git anidado en `rag/` quedó resuelta).
  Todo el proyecto está versionado; corpus, `indice/` y `data/proyectos/` van ignorados.
- **Paquete único `cueva/`** con capas: `datos` → `econometria`/`conocimiento`/`llm` →
  `agentes`/`sesiones` → `api`. Los viejos `mesa/`, `econ/`, `server/`, `rag/` ya no existen.
- **Gateway LLM único** (`cueva/llm/gateway.py`): Gemini free > Claude > offline, con backoff
  ante 429 y `ContadorTokens` por sesión (el triple cableado anterior se eliminó).
- **API `/api/v1`** con contratos Pydantic (`cueva/api/esquemas.py`), errores uniformes y
  frontend en `web/index.html`.
- **48 tests en verde** (`pytest`): econometría sobre series sintéticas con semilla, contratos
  de API, mesa completa offline. CI en `.github/workflows/ci.yml` (ruff + pytest, $0, sin claves).
- Bugs corregidos: evidencia del VECM que se perdía (B1), path traversal en ids (B2),
  requests concurrentes que se pisaban (B3), pickle en el índice (B5), XSS parcial (B6),
  caché de series sin invalidar (B8), handoff no tipado (B9), y un `np.False_ is False`
  que hacía inalcanzable la conclusión "NO estacionaria" en ADF/KPSS.
- Los 3 modos de agentes siguen: 1:1 (`Agente.responder_directo`), líder supervisor
  (`Orquestador.revisar`), pipeline (`Orquestador.correr`).

## Problema conocido (retrieval — ya MEDIDO, no resuelto del todo)

Baseline 2026-07-05 (`scripts/evaluar_rag.py` sobre las 20 preguntas doradas):
- **embeddings: aciertos@3 = 14/20 (70%)** · @1 = 8/20 · @5 = 16/20
- **TF-IDF: aciertos@3 = 1/20 (5%)** → decisión tomada con datos: embeddings es la
  recuperación primaria; TF-IDF queda solo como fallback sin sentence-transformers.
Patrón de fallo: los resúmenes en español (`sala_i_martin`, `utils`, `specification_curve`)
acaparan las consultas genéricas (regresión espuria, DiD, transformaciones, estacionalidad).
Además **Enders NO está en el corpus** (24 fuentes; conseguirlo suma para cointegración).
Ideas para iterar (medir antes/después con el script): penalizar/borrar `utils.py` del
corpus, probar e5-base, y chunking por sección en vez de por página.

## Pendientes en orden (fase 4 del roadmap aprobado)

1. SQLite detrás del repositorio de sesiones + job queue (la mesa y la indexación de
   subidas salen del request).
2. Auth de usuarios + rate limiting + checklist de seguridad web (PROPUESTA §5).
3. Dockerfile + compose + deploy a un PaaS.
4. Datos: empaquetar las series (hoy carpetas hermanas) como dataset propio en
   `data/series/<organismo>/` — la búsqueda de archivos ya lo prioriza sobre la carpeta
   del Trabajo Final, así que se puede migrar serie por serie sin romper nada.
Paralelo (conocimiento): conseguir Enders; iterar retrieval midiendo con
`scripts/evaluar_rag.py` (baseline @3=14/20).

## Qué leer / qué no leer (economía de tokens)

- Leé siempre: este archivo, el módulo que toques, `cueva/api/esquemas.py` si tocás la API,
  `docs/DATOS.md` si tocás series o fuentes.
- NO leas: `.venv/`, `indice/`, `knowledge-base/corpus/`, `data/`, backups; `web/index.html`
  solo en tareas de frontend.
- Cada módulo de `cueva/` tiene docstring que dice qué hace y qué NO hace — leé eso antes
  que la implementación de otra capa.

## Convenciones

- Español en nombres, docstrings y comentarios. Imports absolutos `from cueva.x import y`.
- Corpus pesado, `indice/` y `data/proyectos/` NO se versionan.
- Fichas = ingrediente secreto: 1 página por método con supuestos y errores típicos
  (`knowledge-base/fichas/_plantilla_ficha.md`).
- Solo `cueva/llm/` habla con los SDKs de LLM y solo `cueva/fuentes/` sale a buscar datos
  a la red. `econometria/` y `datos/` son puros: leen de disco y nada más.
- Sin `print` en el paquete (logging); sin `eval`/`exec`; errores como excepciones tipadas
  o `{"ok": False}`.
- Definition of Done: corre + tests + CI verde + sin secretos en el diff + docs al día.

## Reglas de proceso

Cómo trabajar conmigo (confirmaciones, estilo de respuesta, git, subagentes): `docs/WORKFLOW.md`.
Git: repo en la raíz; comitear solo con aprobación explícita; nunca push (lo maneja el usuario).
