# La plataforma — documento maestro

> **Qué es este archivo**: el mapa de cómo está organizada La Cueva del Economista, de punta a
> punta: para qué existe, qué partes tiene, dónde vive cada una en el repo, qué está hecho y qué
> falta. Es la puerta de entrada: cada sección apunta al documento que tiene el detalle.
>
> **Cómo se mantiene**: el diseño se decide sobre el **mockup** (§8) y se registra acá y en el
> documento del módulo. Si una decisión cambia en el mockup y no se anota, no está decidida.
>
> Última actualización: 2026-09-12.

---

## 0. Mapa de documentos

| Pregunta | Documento |
|---|---|
| ¿Por qué existe la plataforma? | este archivo §1 · `docs/VISION.md` (visión original) |
| ¿Cómo se organiza entera? | **este archivo** |
| ¿Qué hace la Línea de Tiempo y cómo se construye? | `docs/MODULO_LINEA_DE_TIEMPO.md` |
| ¿Qué hace la Mesa de Trabajo? | `docs/MODULO_MESA_DE_TRABAJO.md` |
| ¿Cómo se ve? (referencia visual navegable) | `docs/mockup/cueva-mockup.html` · §8 |
| ¿De dónde sale cada serie? | `docs/DATOS.md` |
| ¿Qué fuentes históricas hay (presidencias, crisis)? | `docs/FUENTES_EVENTOS_HISTORICOS.md` |
| ¿Hasta dónde atrás llegan las series? | `docs/FUENTES_SERIES_LARGAS.md` |
| ¿Qué está mal organizado hoy y en qué orden se arregla? | `docs/AUDITORIA_2026-08.md` |
| ¿Cuál es la arquitectura técnica objetivo (escala, seguridad, costos)? | `docs/PROPUESTA_ARQUITECTURA.md` |
| ¿Cómo funcionan los agentes por dentro? | `docs/ARQUITECTURA.md` · `knowledge-base/skills/README.md` |
| ¿Cómo trabajamos (git, confirmaciones, estilo)? | `docs/WORKFLOW.md` |

---

## 1. Por qué y para qué

### 1.1 Motivaciones

1. **La IA potencia el análisis econométrico**: detecta patrones que a una persona le llevaría
   mucho tiempo ver.
2. **Conocer la historia económica argentina completa.**
3. **Hacer trabajos econométricos rápido y profesionalmente.**

### 1.2 Objetivos — dos productos

| # | Producto | Para quién | Módulo |
|---|---|---|---|
| 1 | Plataforma online donde un economista que investiga Argentina hace **todas las etapas** de un trabajo econométrico (exploración, construcción de series, tests, hipótesis, modelos, informe) de forma ágil, ordenada y profesional, **acompañado por un copiloto de IA** que detecta patrones, controla y cita bibliografía y ayuda a redactar | investigadores, tesistas | **Mesa de Trabajo** |
| 2 | **Línea de tiempo económica y social de Argentina, 1880 → hoy** | cualquiera que quiera entender la historia económica argentina; y el investigador, como contexto | **Línea de Tiempo** |

Los dos productos comparten el mismo backend. Esa es la razón de ser una sola plataforma y no
dos: el evento histórico que se lee en la Línea de Tiempo es el mismo que explica el quiebre
estructural que aparece en la Mesa.

### 1.3 Principios que atraviesan todo

- **Todo dato declara de dónde sale.** Serie, evento, cifra, foto o cita sin fuente no entra.
  Es el contrato `proc` de las series extendido a todo lo demás.
- **Honestidad visible.** Lo que falta se muestra como faltante (banda "sin cobertura", "ficha
  pendiente", "sin verificar", "eje recortado"). Nunca se rellena para que se vea lindo.
- **El número vive una sola vez.** Una cifra se define en un lugar, con su fuente, y se
  referencia desde el relato, el gráfico y el informe.
- **Reproducible.** Toda serie derivada guarda su receta; todo paso de análisis guarda sus
  argumentos y su resultado completo.
- **Consulta y operación no se mezclan.** La Línea de Tiempo se lee; la Mesa se opera.

---

## 2. La plataforma en una imagen

```
                        ┌────────────────── FRONTEND ──────────────────┐
                        │                                              │
                        │   ① LÍNEA DE TIEMPO         ② MESA DE TRABAJO│
                        │   consulta y narración      Explorar         │
                        │   1880 → hoy                Análisis:        │
                        │                              Tests           │
                        │                              Transformaciones│
                        │                              Modelado        │
                        │                             Laboratorio      │
                        │                                              │
                        │        ◉ Copiloto IA (botón flotante)        │
                        └───────────────────────┬──────────────────────┘
                                                │  API /api/v1
                        ┌───────────────────────┴──────────────────────┐
                        │                   BACKEND                    │
                        │                                              │
                        │  1 DATOS HISTÓRICOS     2 BIBLIOGRAFÍA       │
                        │    1.1 series             2.1 econométrica   │
                        │    1.2 eventos,           2.2 económica      │
                        │        gobiernos,         (propia / externa) │
                        │        ministros, BCRA                       │
                        │                                              │
                        │  3 STACK ECONOMÉTRICO   4 AGENTES DE IA      │
                        │    herramientas Python    skills, pipelines, │
                        │                           modelos, tools     │
                        └──────────────────────────────────────────────┘
```

Quién usa qué:

| Fuente del backend | Línea de Tiempo | Mesa de Trabajo |
|---|---|---|
| 1.1 Series | 10 series troncales anuales (catálogo cerrado) | catálogo completo (615 series) |
| 1.2 Eventos y gobiernos | **es su contenido principal** | contexto; dummies generadas desde acá |
| 2 Bibliografía | citas de las fichas de eventos | citas del informe; RAG de los agentes |
| 3 Stack econométrico | — (solo transformaciones de visualización) | Tests, Transformaciones, Modelado |
| 4 Agentes | a futuro: preguntar sobre un evento | copiloto en todas las pantallas |

---

## 3. Backend — las cuatro fuentes

Para cada una: **qué es · dónde vive · contrato · estado**.

### 3.1 Fuente 1.1 — Series económicas

| | |
|---|---|
| **Qué es** | Series de tiempo argentinas con su procedencia |
| **Datos** | `data/series/<familia>/` (CSV tidy) · `data/series/<familia>_Fuentes/` (crudos del organismo) · `data/series/bcra/` |
| **Catálogo** | `cueva/datos/catalogo.json` — fuente única de la taxonomía (9 familias → subgrupo → serie) |
| **Código** | `cueva/datos/series.py` (lectura, pura) · `cueva/fuentes/` (adaptadores por organismo: la **única** capa que sale a la red) · `cueva/fuentes/unidades.py` (magnitud + escala + moneda) |
| **Contrato** | bloque `proc` por serie: `fuente`, `definicion`, `id_externo`, `endpoint`, `script`, `insumos`+`transformacion` si es propia, `confianza`, `verificado` — ver `docs/DATOS.md` |
| **Estado** | ✅ 615 series / 772 entradas, todas con `proc`. ✅ API del BCRA conectada. ⏳ Falta bajar las históricas de 1940 y las 33 del BCRA; normalizar nombres; empalme histórico↔diario |
| **Regla** | Se llena con scripts, no a mano. Un archivo que no está en `data/series/` no se cataloga |

### 3.2 Fuente 1.2 — Eventos, gobiernos y autoridades

| | |
|---|---|
| **Qué es** | La cronología: presidencias, ministros de Economía, autoridades monetarias (Caja de Conversión 1890-1935, BCRA 1935→), eventos económicos/sociales/políticos, fichas narrativas y las series largas 1880→ |
| **Datos** | `data/historia/` — estructura completa en `docs/MODULO_LINEA_DE_TIEMPO.md` §8 |
| **Código** | `cueva/datos/historia.py` *(a crear)*: lectura y validación, pura |
| **Contrato** | cada fila lleva `fuente` y `verificado`; los gobiernos no se guardan en los eventos, **se derivan por fecha** |
| **Estado** | ✅ `presidencias.csv`: 60 períodos 1880-hoy, sin huecos ni solapamientos (`tests/test_historia.py`), todos `verificado=no`. ⏳ Script de crisis Reinhart-Rogoff listo sin correr. ❌ Ministros, autoridades monetarias, eventos, fichas, series largas |
| **Regla** | Las dummies (`dummy_gob`, `dummy_cepo`, `dummy_elec`) se **generan** desde estas tablas; no se mantienen a mano |

### 3.3 Fuente 2 — Bibliografía

| | |
|---|---|
| **Qué es** | 2.1 bibliografía econométrica · 2.2 bibliografía económica (incluye historia económica) — cada una puede ser **propia** (del usuario) o **externa** (corpus curado) |
| **Datos** | `knowledge-base/corpus/<tema>/` (PDFs, **no se versiona**) · `data/biblioteca/` (subidas del usuario) · `indice/` (índice RAG, no se versiona) |
| **Registro** | `knowledge-base/referencias.bib` *(a crear)*: la ficha bibliográfica de cada obra, con su clave de cita. **Sí se versiona** — es liviano y es lo que las fichas y el informe citan |
| **Código** | `cueva/conocimiento/` (ingesta incremental con manifiesto, recuperación por embeddings, biblioteca del usuario) |
| **Contrato** | cada fragmento lleva `coleccion` (`corpus` \| `usuario`); cada cita que llega al usuario tiene que ser **localizable** en el corpus o marcarse como no verificada |
| **Estado** | ✅ corpus econométrico en 12 carpetas temáticas, RAG medido (aciertos@3 = 70 %). ❌ No hay corpus de **historia económica** ni separación econométrica/económica en las colecciones. ❌ No hay registro de referencias con claves |

### 3.4 Fuente 3 — Stack econométrico

| | |
|---|---|
| **Qué es** | Las herramientas de análisis que corren **en el servidor** |
| **Código** | `cueva/econometria/herramientas.py` (registro de 11 herramientas: `describir`, `estacionariedad`, `granger`, `ols`, `var`, `vecm`, `garch`, `arch_lm`, `diagnosticos`, `correlaciones`, `arima`) · `cueva/econometria/kalman.py` |
| **Contrato** | herramienta + series + transformación (`nivel`/`log`/`dif`/`dif2`/`dif_log`/`pct`) + parámetros → resultado con resumen, tablas y gráfico. Un único punto de entrada: `POST /api/v1/herramienta` |
| **Estado** | ✅ funcionando y testeado. ⏳ Partir el archivo (916 líneas) en transformaciones / pruebas / modelos. ⚠ ADF, PP y OLS también están en JS en `web/explorador.html`: **dos motores que pueden dar números distintos** — se borra el de JS |
| **Regla** | `econometria/` es pura: lee de disco y nada más. Sin `eval`/`exec` |

### 3.5 Fuente 4 — Agentes de IA

| | |
|---|---|
| **Qué es** | Agentes-profesores que ven lo que el usuario hace, consultan la bibliografía y ejecutan herramientas |
| **Definición** | `knowledge-base/skills/<agente>.md` — frontmatter (`agente`, `rol`, `modelo`, `sesgo_rag`, `herramientas`, `prioriza_usuario`) + cuerpo = system prompt. Editar el markdown cambia al agente sin tocar Python |
| **Plantel (12)** | `lider` · `curador_datos` · `metodologo` · `critico` · `interprete` · `bibliografo` · `transformaciones` · `multivariados` · `volatilidad` · `controles_causal` · `robustez` · `pronostico_ml` |
| **Código** | `cueva/agentes/` (skills, pipelines como dato, orquestador, pizarra) · `cueva/llm/gateway.py` (**único** que habla con los SDKs: Gemini > Claude > offline) |
| **Modos** | 1:1 (chat con un agente) · supervisor (el líder revisa) · pipeline (`clasica` = Metodólogo, Bibliógrafo, Crítico, Intérprete · `equipo_completo` = el Líder y los especialistas) |
| **Estado** | ✅ tool-use real, SSE tipado, transcript por sesión. ❌ **Los agentes no ven los estudios ni el informe** (`piz.estudios` se guarda pero no entra al prompt) — falta `ContextoDelCopiloto` (`AUDITORIA` §2.2) |

---

## 4. Frontend — los dos módulos

### 4.1 Estructura de navegación

```
Topbar:  [marca]  [ Línea de Tiempo | Mesa de Trabajo ]      [proyecto] [series] [fuentes] [tema]

Línea de Tiempo
  ├── rail izquierdo: capas (instituciones · eventos · series históricas n/4)
  ├── centro: gráfico 1880→hoy + panel Δ i.a. + barra de rango + ficha del evento (panel inferior)
  └── rail derecho: evento seleccionado + lista de todos los eventos

Mesa de Trabajo
  ├── Explorar         jugar con series: comparar, deflactar, reescalar — solo visual + estadísticos
  ├── Análisis
  │     ├── Tests            comportamiento de las series (raíz unitaria, quiebres, correlograma…)
  │     ├── Transformaciones construir series desde otras, con receta
  │     └── Modelado         el Estudio: pasos declarativos (VECM, Granger, diagnósticos…)
  └── Laboratorio      pregunta, hipótesis con evidencia, informe por secciones, bibliografía citada

Transversal:  ◉ botón flotante "IA" → tarjeta de chat con el listado de agentes
```

Detalle de cada pantalla: `docs/MODULO_LINEA_DE_TIEMPO.md` y `docs/MODULO_MESA_DE_TRABAJO.md`.

### 4.2 Copiloto flotante (transversal)

Decidido en el mockup el 2026-08-29. El copiloto **no ocupa un panel fijo**: estorbaba y le
quitaba ~330 px a todas las pantallas.

- Botón circular **IA**, abajo a la derecha, **arrastrable** a cualquier lugar (si el puntero se
  mueve menos de 5 px se toma como clic). Muestra un contador de mensajes sin leer.
- Al tocarlo abre una **tarjeta de ~1/4 de pantalla** que se ubica sola junto al botón; se mueve
  desde el encabezado, se redimensiona desde la esquina y se cierra con minimizar o `Esc`.
- **Vista 1 — listado de agentes** agrupado: *Mesas* (pipelines `clasica` y `equipo_completo`) ·
  *Dirección* (Líder) · *Profesores* (los 4 de la mesa clásica: Metodólogo, Bibliógrafo, Crítico,
  Intérprete) · *Especialistas* (los 7 restantes). Cada uno con inicial de color, qué hace y qué
  herramientas tiene habilitadas.
- **Vista 2 — chat** con el agente elegido (o la mesa), sugerencias contextuales y composer.
  Flecha para volver al listado.
- El listado **se genera desde `knowledge-base/skills/`**, no se escribe a mano en el frontend.
- En Vista Rápida (sin proyecto) el copiloto queda gateado, igual que hoy.

### 4.3 Sistema de diseño — "pizarrón y tiza"

| Token | Claro (papel) | Oscuro (pizarrón) | Uso |
|---|---|---|---|
| `--ground` | `#EEF1EC` | `#101715` | fondo de la app |
| `--surface` | `#FAFBF8` | `#18211E` | tarjetas, paneles |
| `--ink` | `#14201C` | `#E7EDE9` | texto principal |
| `--accent` | `#8A6410` | `#E9C46A` | tiza ámbar: selección, acción primaria, cifras |
| `--ok` / `--crit` | `#2F7D52` / `#A32F4C` | `#7BC49A` / `#E0708A` | positivo/negativo, constitucional/de facto |
| `--s1…--s5` | — | — | colores de series (máx. 5 simultáneas) |

- **Tipografías**: Fraunces (títulos) · IBM Plex Sans (interfaz) · IBM Plex Mono (**todo número**,
  con cifras tabulares).
- **Tema**: claro y oscuro con tokens; `:root` = claro, se redefinen solo los tokens en oscuro.
- **Destino en el repo**: `web/estilo/tokens.css`, importado por **todas** las pantallas (hoy
  `index.html` y `explorador.html` tienen temas distintos — deuda D5 de la auditoría).

### 4.4 Convenciones de interacción (valen para todo gráfico)

| Gesto | Efecto |
|---|---|
| Rueda | zoom en X centrado en el cursor |
| Arrastrar | desplazar |
| Doble clic | volver al rango completo |
| Pasar el mouse | línea vertical + tarjetita con **nombre, fecha, valor y unidad** por serie |
| Barra de rango inferior | ventana arrastrable y estirable sobre todo el dominio |
| Botones rápidos | Mesa: `1M · 3M · 6M · YTD · 1A · 5A · Todo` · Línea de Tiempo: períodos históricos |

Y dos reglas de honestidad gráfica: **un eje recortado se declara** en su etiqueta, y **comparar
unidades distintas fuerza base 100 con aviso**.

---

## 5. Estructura de carpetas

Estado real al 2026-09-12. ✅ existe · ⏳ parcial · ❌ a crear.

```
La Cueva del Economista/
├── cueva/                              paquete Python único, por capas
│   ├── datos/          ✅  lectura pura de disco
│   │   ├── catalogo.json       ✅  taxonomía + proc de las 615 series
│   │   ├── series.py           ✅
│   │   ├── explorador_datos.py ✅
│   │   └── historia.py         ❌  cronología: lectura + validación
│   ├── fuentes/        ✅  ÚNICA capa que sale a la red (bcra.py, registro, unidades)
│   ├── econometria/    ⏳  herramientas.py (partir), kalman.py
│   ├── conocimiento/   ✅  RAG: ingesta, recuperar, biblioteca, fichas
│   ├── llm/            ✅  ÚNICA capa que habla con SDKs de LLM
│   ├── agentes/        ⏳  falta contexto.py (lo que el agente ve)
│   ├── investigacion/  ❌  dominio del Laboratorio: Hipotesis, Estudio, Seccion, Cita
│   ├── sesiones/       ✅  persistencia de proyectos
│   └── api/            ⏳  app.py (partir en routers/: explorador, catalogo, proyectos, mesa, historia)
│
├── data/                               DATOS (fuente 1)
│   ├── series/         ✅  CSV por familia + crudos + bcra/   (CSV ignorados por git)
│   ├── historia/       ⏳  presidencias.csv ✅ · resto ❌ — ver MODULO_LINEA_DE_TIEMPO §8
│   ├── biblioteca/     ✅  PDFs subidos por el usuario (ignorado)
│   └── proyectos/      ✅  proyectos y transcripts (ignorado)
│
├── knowledge-base/                     BIBLIOGRAFÍA + AGENTES (fuentes 2 y 4)
│   ├── corpus/         ✅  PDFs por tema (ignorado) — falta carpeta de historia económica
│   ├── referencias.bib ❌  registro de obras con clave de cita (versionado)
│   ├── fichas/         ✅  1 página por método
│   └── skills/         ✅  definición de los 12 agentes
│
├── web/                                FRONTEND
│   ├── index.html      ✅  shell (Vista Rápida / Proyecto)
│   ├── explorador.html ✅  SPA de la Mesa (~7000 líneas, a partir en módulos)
│   ├── estilo/tokens.css ❌  sistema de diseño compartido
│   ├── tiempo/         ❌  módulo Línea de Tiempo (index.html + tiempo.js + tiempo.css)
│   ├── cuadro/         ✅  CSS/JS de los cuadros de catálogo
│   └── vendor/         ✅  Plotly, SheetJS
│
├── scripts/            ✅  CLIs de ingesta, auditoría y construcción (no importables)
├── tests/              ✅  pytest — cada contrato de datos tiene su test
└── docs/
    ├── PLATAFORMA.md           este archivo
    ├── MODULO_LINEA_DE_TIEMPO.md
    ├── MODULO_MESA_DE_TRABAJO.md
    └── mockup/cueva-mockup.html   referencia visual (§8)
```

**Reglas de dependencia** (no negociables): `datos` y `econometria` no importan de capas
superiores ni salen a la red · solo `fuentes` usa la red · solo `llm` habla con LLMs · `api`
solo orquesta, sin lógica de dominio · nada suelto en la raíz del repo.

---

## 6. API

| Endpoint | Estado | Para qué |
|---|---|---|
| `GET /` · `GET /explorador` | ✅ | shell y SPA de la Mesa |
| `GET /api/v1/series` | ✅ | catálogo |
| `GET /api/v1/explorador/datos` | ✅ | payload columnar de series |
| `POST /api/v1/herramienta` · `GET /api/v1/herramientas` | ✅ | stack econométrico |
| `GET/POST /api/v1/biblioteca` | ✅ | bibliografía propia |
| `/api/v1/proyectos/…` | ✅ | proyectos, estudios, notas, informe |
| `POST /api/v1/proyectos/{pid}/agente/{agente_id}` · `/investigar` | ✅ | chat 1:1 y mesa |
| `GET /tiempo` | ❌ | página de la Línea de Tiempo |
| `GET /api/v1/historia` | ❌ | todo lo que la Línea de Tiempo necesita al abrir |
| `GET /api/v1/historia/eventos/{id}` | ❌ | ficha completa (se pide al abrirla) |
| `GET /api/v1/agentes` | ❌ | plantel desde los skills (alimenta el listado del copiloto) |

Contratos en `cueva/api/esquemas.py` (Pydantic). Errores uniformes. Detalle de los endpoints de
historia en `docs/MODULO_LINEA_DE_TIEMPO.md` §10.

---

## 7. Orden de construcción

Decisión del 2026-09-12: **se empieza por la Línea de Tiempo**, porque ya hay bibliografía y datos
para avanzar, porque es la que menos depende de piezas que faltan (no necesita proyectos,
agentes ni el Laboratorio) y porque obliga a resolver primero dos cimientos que después usa la
Mesa: `tokens.css` y el registro de referencias.

| Frente | Qué | Documento | Depende de |
|---|---|---|---|
| **A — Línea de Tiempo** | fases T0-T6 | `MODULO_LINEA_DE_TIEMPO.md` §9 | nada |
| B — Datos de la Mesa | bajar series pendientes, nombres, empalmes | `DATOS.md`, `PLAN_CATALOGO.md` | — |
| C — Proyecto de investigación | `investigacion/`, `ContextoDelCopiloto`, informe con citas | `AUDITORIA` §4 camino B | `referencias.bib` (de A) |
| D — Frontend unificado | tokens, borrar econometría JS, módulos ES, copiloto flotante | `AUDITORIA` §2.3 | `tokens.css` (de A) |
| E — Escala web | SQLite, auth, Docker, deploy | `PROPUESTA_ARQUITECTURA.md` fase 4 | C y D |

El frente A tiene dos carriles que corren **en paralelo**: el de **datos** (curar, transcribir,
verificar — manual, lo lleva el investigador) y el de **código** (esquemas, tests, API, pantalla).
El código se construye contra los datos que ya existen y crece a medida que se cargan.

---

## 8. El mockup: cómo se sigue diseñando

- **Link**: https://claude.ai/code/artifact/93e690be-30cc-46fa-b4ba-38cbd8c4cf97 (privado)
- **Copia en el repo**: `docs/mockup/cueva-mockup.html` — un solo archivo, se abre con doble clic.
  Es la fuente para republicar: la carpeta temporal donde se armó originalmente se borra sola.
- **Qué es**: una maqueta navegable con datos **ilustrativos**. Los números de sus series son
  sintéticos; las presidencias y los 49 eventos son una semilla sin verificar.
- **Qué no es**: código de producción. Se porta la interacción y el diseño, no el archivo.

**Ciclo de trabajo**:

```
 idea / pedido  →  se prueba en el mockup  →  se acepta  →  se anota en el doc del módulo
                                                              (sección "Registro de decisiones")
                                                                     ↓
                                                         se construye en el repo real
```

Regla: **el documento manda sobre el mockup**. Si difieren, lo que dice el documento es lo
decidido y el mockup está atrasado (o es una propuesta sin aceptar todavía).

**Diferencias conocidas entre el mockup y la realidad** (para no copiarlas):

| En el mockup | En la realidad |
|---|---|
| Series del explorador y de la Línea de Tiempo con valores sintéticos | Datos reales desde `data/series/` y `data/historia/` |
| Presidencias: 40 bloques agrupados | 60 períodos en `presidencias.csv` |
| 49 eventos semilla sin fuente | Cada evento con `refs` o `fuente` (`MODULO_LINEA_DE_TIEMPO` §8.2) |
| Tests y modelos con resultados de ejemplo | Todo corre en el servidor vía `POST /api/v1/herramienta` |
| Listado de agentes escrito en el HTML | Se genera desde `knowledge-base/skills/` (`GET /api/v1/agentes`) |

(El 2026-09-12 se alinearon con la realidad el conteo de series del topbar y el plantel de agentes
del copiloto: los 12 skills reales y la mesa clásica correcta.)

---

## 9. Decisiones

### 9.1 Tomadas

| Fecha | Decisión | Dónde se argumenta |
|---|---|---|
| 2026-07-04 | Paquete único `cueva/` por capas; gateway LLM único | `ARQUITECTURA.md` |
| 2026-07-04 | Agentes definidos por skills en markdown; pipelines como dato | `ARQUITECTURA.md` |
| 2026-07-14 | El explorador es nativo (adiós iframe al TF) | `CLAUDE.md` |
| 2026-08-27 | Toda serie declara `proc`; solo `cueva/fuentes/` sale a la red | `DATOS.md` |
| 2026-08-27 | Gobiernos y eventos como tablas; las dummies se generan | `FUENTES_EVENTOS_HISTORICOS.md` |
| 2026-08-28 | Línea de Tiempo = consulta; sin "llevar a la mesa" ni "crear dummy" | `MODULO_LINEA_DE_TIEMPO.md` §1 |
| 2026-08-28 | 10 series troncales anuales, máx. 4 simultáneas, 3 modos de escala + panel Δ | `MODULO_LINEA_DE_TIEMPO.md` §2-3 |
| 2026-08-28 | Ficha del evento en panel inferior; cifras enlazadas al gráfico | `MODULO_LINEA_DE_TIEMPO.md` §5 |
| 2026-08-29 | Todo dato del catálogo vive en `data/series/` | `data/series/README.md` |
| 2026-08-29 | Explorador con la estructura del visualizador del TF; sidebar de series editable | `MODULO_MESA_DE_TRABAJO.md` §2 |
| 2026-08-29 | Comparar: spread A−B, cuadro, correlación y dispersión | `MODULO_MESA_DE_TRABAJO.md` §2.6 |
| 2026-08-29 | Copiloto como botón flotante movible, no como panel fijo | este archivo §4.2 |
| 2026-09-12 | Se construye primero la Línea de Tiempo | este archivo §7 |
| 2026-09-12 | Los datos de historia viven en `data/historia/`, no dentro de `cueva/` | `MODULO_LINEA_DE_TIEMPO.md` §8 |
| 2026-09-12 | Fichas de evento en markdown con frontmatter (no JSON) | `MODULO_LINEA_DE_TIEMPO.md` §5.2 |
| 2026-09-12 | Registro único de bibliografía en `knowledge-base/referencias.bib` | `MODULO_LINEA_DE_TIEMPO.md` §8.4 |

### 9.2 Abiertas

| # | Pregunta | Impacto | Quién decide |
|---|---|---|---|
| 1 | ¿Se agrega más adelante un puente explícito Mesa → "importar evento como dummy"? | Medio: la dirección del puente importa (desde donde se opera) | usuario |
| 2 | ¿Hasta dónde escribe el copiloto: secciones completas o párrafo por párrafo con aceptación? | Alto: cambia el modelo de datos del informe | usuario |
| 3 | ¿El orden de transformaciones (deflactar → variación → log → diferenciar) es fijo o configurable? | Medio | usuario |
| 4 | ¿Cuántos eventos llevan ficha completa y quién las redacta? | Alto en trabajo manual | usuario — propuesta: 12 estructurales |
| 5 | ¿Los datos van versionados en el repo, en un repo aparte o por descarga con manifiesto? | Alto al desplegar | usuario — hoy: CSV de series ignorados, tablas de historia versionadas |
| 6 | ¿Colección separada para historia económica en el RAG? | Medio: evita que la historia contamine respuestas de método | técnica — propuesta en `MODULO_LINEA_DE_TIEMPO.md` §8.4 |

---

## 10. Glosario mínimo

| Término | Qué significa acá |
|---|---|
| **`proc`** | bloque de procedencia de una serie: de dónde sale, cómo se construye, qué tan confiable es |
| **Serie troncal** | una de las 10 series anuales largas de la Línea de Tiempo |
| **Ficha** (de evento) | relato completo de un evento: cronología, cifras enlazadas, citas, medios, bibliografía |
| **Ficha** (de método) | 1 página por método econométrico en `knowledge-base/fichas/` — no confundir |
| **Cifra enlazada** | número dentro de un relato que al tocarlo lleva a ese valor en el gráfico |
| **Estudio** | la lista de pasos de análisis de un proyecto, cada uno con su resultado guardado |
| **Paso** | herramienta + series + transformación + parámetros, ejecutado en el servidor |
| **Receta** | cómo se construyó una serie derivada, guardada junto a ella |
| **Vista Rápida** | espacio efímero de la Mesa, sin proyecto; se puede promover a proyecto |
| **Skill** | markdown que define a un agente: rol, modelo, herramientas permitidas y prompt |
| **Pipeline** | secuencia de agentes definida como dato (`clasica`, `equipo_completo`) |
