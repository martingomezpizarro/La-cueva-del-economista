# Propuesta de arquitectura integral — La Cueva del Economista

> **Estado**: propuesta, pendiente de visto bueno del dueño del proyecto.
> **Fecha**: 2026-07-04 · **Autor**: lead técnico (asistente IA) tras leer el repo completo.
> **Alcance**: diagnóstico + arquitectura objetivo + roadmap. **No implementa nada.**
>
> *Convención de este documento*: cada decisión importante se presenta como
> **Recomendación → Por qué → Alternativa descartada → Riesgo/Mitigación**.
> Los términos de arquitectura se definen la primera vez que aparecen (ver también el
> Glosario al final): la idea es que aprendas el vocabulario profesional mientras construís.

---

## 0. Diagnóstico honesto del estado actual

### 0.1 Lo que está sólido (y hay que preservar)

- **La separación de carpetas ya apunta bien.** `mesa/` (agentes), `econ/` (econometría),
  `rag/` (conocimiento), `server/` (web) es, en embrión, una **arquitectura en capas**
  (cada carpeta tiene una responsabilidad y las de arriba usan a las de abajo). No hay que
  tirar nada: hay que endurecer los límites.
- **El modo offline de `mesa/llm.py` es oro.** Que toda la plataforma corra de punta a punta
  sin API key es exactamente lo que permite testear barato y desarrollar con asistentes de IA
  sin gastar tokens. Es la base de la estrategia de testing (§6).
- **`econ/herramientas.py` tiene el contrato correcto.** Todas las herramientas devuelven el
  mismo dict (`ok`, `herramienta`, `args`, `resumen`, campos estructurados) y el `REGISTRO`
  central es casi un catálogo de *function calling* listo. Es la mejor pieza de diseño del repo.
- **La Pizarra es serializable y ya persiste.** `mesa/pizarra.py` guarda/carga JSON completo;
  el modelo mental (blackboard: memoria compartida que todos los agentes leen y escriben) es
  el patrón correcto para esta mesa.
- **Las fichas y los skills son el diferencial real.** `knowledge-base/fichas/` (supuestos +
  errores típicos por método) y `knowledge-base/skills/` (identidad + tier de modelo en
  frontmatter) son conocimiento curado que ningún competidor genérico tiene. `grafo_cueva.py`
  ya demuestra que se puede leer el tier del frontmatter para que skill y código no se desfasen.
- **El problema prioritario del CLAUDE.md ya parece resuelto**: `rag/_indice/meta.json` dice
  `modelo_emb: intfloat/multilingual-e5-small` con 8.015 fragmentos y `embeddings.npy` fechado
  2026-07-03 18:21, y `.env` tiene una `GOOGLE_API_KEY` real. Es decir: los pendientes 1 y 2
  del CLAUDE.md parecen hechos pero **el CLAUDE.md no se actualizó** — falta solo la prueba
  del caso estrella (pendiente 3) para confirmarlo.

### 0.2 Deuda técnica estructural (lo más grave primero)

1. **El git anidado es la deuda #1 y bloquea todo lo demás.** El `.git` vive en `rag/`;
   `mesa/`, `server/`, `econ/`, `docs/`, `config.py` y el frontend están **sin versionar**.
   Peor: el repo de `rag/` **no tiene `.gitignore`** (el de la raíz no aplica a nada, porque
   la raíz no es repo) y está **trackeando 37 MB de binarios regenerables**
   (`_indice/embeddings.npy`, `tfidf.pkl`, `fragmentos.jsonl`) — exactamente lo que la
   convención del proyecto prohíbe. Además hay solo 3 commits y semanas de trabajo local sin
   respaldo: hoy un disco roto pierde la mesa entera.
2. **Triple cableado del LLM.** El mismo patrón "Gemini > Claude > offline" está implementado
   tres veces y distinto: `mesa/llm.py`, `rag/metodologo.py:100-139` y
   `grafo_cueva.py:52-80` (que además solo mira `GOOGLE_API_KEY`, no `GEMINI_API_KEY`, y usa
   defaults de modelo distintos). Todo cambio de backend hay que hacerlo tres veces.
3. **Dos pipelines de agentes redundantes.** `mesa/` (4 agentes + líder, guion por fase) y
   `grafo_cueva.py` (10 especialistas LangGraph). La memoria del proyecto dice que cubren
   modos distintos, pero el 90% del código (armar prompt, RAG, evidencia, offline) está
   duplicado. Hay que unificar el motor y dejar los "modos" como puntos de entrada (§3).
4. **Sin contratos en la API.** `server/app.py` lee `await req.json()` a mano en todos los
   endpoints: cero validación de tipos, campos o tamaños. No hay versionado de API ni formato
   de error uniforme.
5. **Sin tests, sin CI, sin lint, sin logging.** No existe `tests/`; los errores se comunican
   con `print` y con strings incrustados en las respuestas de los agentes. Para un dueño
   no-programador esto es crítico: hoy nada ataja un error que vos no veas a ojo (§6, §11).
6. **Datos anclados a carpetas hermanas de tu disco.** `config.py:57-75` autodetecta
   `../Trabajo Final` y `../ANÁLISIS MATRIZ ARG`. Funciona hoy, pero hace la plataforma
   imposible de deployar o compartir: la capa de datos necesita una fuente propia (§4, §7).

### 0.3 Bugs y riesgos concretos encontrados (citables, verificados en el código)

| # | Dónde | Qué pasa |
|---|-------|----------|
| B1 | `mesa/orquestador.py:39-49` + `96-102` | **La mesa nunca elige VECM aunque haya cointegración.** `_evidencia()` guarda como `msg.herramienta` solo `utiles[0]` (el primer resultado). En la fase control el orden es [estacionariedad×N, vecm], así que el resultado de Johansen se pierde; `piz_evidencia_control()` nunca encuentra `"vecm"` y la modelización cae siempre a OLS/VAR. Es un bug de lógica silencioso que contradice el corazón metodológico de la plataforma. |
| B2 | `mesa/pizarra.py:228-239` + `server/app.py` | **Path traversal**: `cargar_proyecto(pid)` y `eliminar_proyecto(pid)` concatenan el `pid` que viene de la URL directo a la ruta (`RUTA_PROYECTOS / f"{pid}.json"`). Un `pid` con `..%2F` permite leer/borrar JSON fuera de `data/proyectos/`. Hoy es local y mono-usuario (severidad baja); apenas se exponga a la web es una vulnerabilidad seria. |
| B3 | `server/app.py:137` + `mesa/pizarra.py:41` | **Condición de carrera con pérdida de datos**: cada request carga SU copia de la pizarra desde JSON y al final la guarda entera (last-write-wins). El `threading.Lock` es por instancia, o sea inútil entre requests. Dos pestañas abiertas sobre el mismo proyecto ya se pisan notas/informe. |
| B4 | `mesa/llm.py:77-78` y toda la mesa | **Sin manejo de rate limit del free tier.** `correr()` dispara ~13 llamadas LLM en secuencia rápida; el free tier de Gemini Flash admite ~10 RPM. Resultado esperable: 429 a mitad de mesa, y el `except` actual incrusta el error dentro del texto "dicho" por el agente en vez de reintentar con espera. |
| B5 | `rag/_indice/tfidf.pkl` | **Pickle como formato de índice**: deserializar pickle ejecuta código arbitrario si el archivo no es de confianza, y además acopla el índice a la versión exacta de scikit-learn. Con PDFs subidos por usuarios en el horizonte, es un formato prohibido. |
| B6 | `server/static/index.html:366,533` | `escapeHtml` cubre los mensajes de agentes (bien), pero el **título del proyecto** y los **hallazgos** se insertan con `innerHTML` sin escapar, y `escapeHtml` (línea 750) no escapa comillas → inyección en atributos. XSS almacenado de baja severidad hoy, real en multiusuario. |
| B7 | `server/app.py:236-248` | El SSE de `/investigar` corre un generador síncrono con llamadas LLM bloqueantes, sin cancelación si el cliente cierra, y `guardar_auto()` reescribe TODO el JSON del proyecto por cada mensaje. |
| B8 | `econ/series.py:52` | `catalogo()` con `lru_cache` que nunca se invalida: series nuevas exigen reiniciar el server. |
| B9 | `mesa/agentes.py:101-102` | El handoff viaja en `msg.__dict__["_handoff_pregunta"]` (campo fantasma fuera del dataclass, invisible para `to_dict()`/persistencia) y hay una variable muerta (`msg_handoff`). Funciona, pero es exactamente el tipo de hack que un agente ejecutor de IA va a romper sin darse cuenta. |
| B10 | `rag/ask.py:23` / `rag/metodologo.py:39-40` | `ask.py` lee el prompt en tiempo de import (crash si falta el archivo) y `metodologo.py` lo importa vía hack de `sys.path`. Además `rag/Bibliografia/` (23 MB) duplica el corpus — ya identificado como pendiente 4. |
| B11 | `grafo_cueva.py:56-58` | Defaults `gemini-3.1-flash-lite` / `gemini-3.1-pro` hardcodeados distintos del resto del sistema (`gemini-2.5-flash`); si esos nombres no existen en la API, esos tiers caen a offline en silencio. |
| B12 | `server/app.py:79` | `@app.on_event("startup")` está deprecado en FastAPI (migrar a *lifespan*), y el subproceso del visualizador acopla el server a un proyecto externo sin control de errores. |

**Síntesis del diagnóstico**: el diseño conceptual (capas, blackboard, fichas, modo offline,
registro de herramientas) es bueno y está por encima del promedio de un prototipo. Lo que no
hay es **red de seguridad** (git sano, tests, CI, contratos) ni **una sola fuente de verdad**
(3 cableados LLM, 2 pipelines, 2 copias del corpus, CLAUDE.md desactualizado). La propuesta
que sigue ordena eso antes de agregar features.

---

## 1. Arquitectura objetivo

### 1.1 Capas y separación de responsabilidades

El principio rector es la **arquitectura en capas con dependencias en un solo sentido**
(las capas de arriba conocen a las de abajo, nunca al revés). En términos profesionales:
`api` depende de `agentes`, que depende de `conocimiento` y `econometria`, que dependen de
`datos`. Nada de abajo importa nada de arriba.

```
┌─────────────────────────────────────────────────────────────────────┐
│  FRONTEND (web/)                                                    │
│  UI de la Mesa: definir investigación, ver la mesa en vivo (SSE),   │
│  cuaderno/informe, chat 1:1 con agentes.                            │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ HTTP/JSON + SSE   (contratos Pydantic, /api/v1)
┌──────────────────────────▼──────────────────────────────────────────┐
│  API (cueva/api/)                                                   │
│  FastAPI: validación de entrada, auth (fase web), errores uniformes,│
│  streaming. NO contiene lógica de negocio: traduce HTTP ↔ dominio.  │
└───────┬──────────────────────────────────────────────┬──────────────┘
        │                                              │
┌───────▼───────────────────────────┐   ┌──────────────▼──────────────┐
│  AGENTES (cueva/agentes/)         │   │  SESIONES (cueva/sesiones/) │
│  motor único: Agente, Pizarra,    │   │  repositorio de proyectos:  │
│  Orquestador, presupuesto de      │◄──┤  cargar/guardar con lock,   │
│  tokens, 3 modos de entrada       │   │  JSON→SQLite→Postgres       │
└───┬──────────────┬────────────────┘   └─────────────────────────────┘
    │              │
┌───▼──────────┐  ┌▼─────────────────────────┐  ┌─────────────────────┐
│ LLM GATEWAY  │  │ CONOCIMIENTO             │  │ ECONOMETRÍA         │
│ (cueva/llm/) │  │ (cueva/conocimiento/)    │  │ (cueva/econometria/)│
│ Gemini>Claude│  │ ingesta, índice,         │  │ registro de         │
│ >offline,    │  │ recuperación, fichas —   │  │ herramientas puras: │
│ retry 429,   │  │ "La Cueva-LM"            │  │ ADF, VECM, GARCH…   │
│ contador de  │  └───────────┬──────────────┘  └──────────┬──────────┘
│ tokens       │              │                            │
└──────────────┘  ┌───────────▼──────────────┐  ┌──────────▼──────────┐
                  │ knowledge-base/ (corpus, │  │ DATOS (cueva/datos/)│
                  │ fichas, skills = CONTENIDO│  │ catálogo y carga de │
                  │ curado, no código)       │  │ series              │
                  └──────────────────────────┘  └─────────────────────┘
```

**Flujo típico** (se detalla en §2): el usuario define la investigación en el frontend →
la API valida y la persiste vía `sesiones` → el orquestador de `agentes` pide evidencia a
`econometria` (que carga series de `datos`), pasajes citados a `conocimiento`, y redacción al
`llm gateway` → cada mensaje vuelve por SSE al frontend y queda en la Pizarra persistida.

### 1.2 Estructura de carpetas objetivo (monorepo, un paquete)

**Monorepo** = un solo repositorio git para todo el proyecto (código, docs, contenido),
con límites claros ENTRE módulos en vez de entre repos.

```
cueva-del-economista/            ← el .git vive ACÁ (ver decisión D1)
├── pyproject.toml               ← metadatos + deps + config de ruff/pyright (reemplaza requirements.txt)
├── CLAUDE.md                    ← estado vivo + mapa de "qué leer" para agentes IA (§11)
├── cueva/                       ← ÚNICO paquete Python instalable
│   ├── config.py                ← el config.py actual, movido adentro
│   ├── llm/                     ← gateway LLM único (nuevo; absorbe los 3 cableados)
│   │   ├── gateway.py           ←   completar(), backends, retry/backoff, offline
│   │   └── presupuesto.py       ←   contador de tokens/llamadas por sesión
│   ├── datos/                   ← ex econ/series.py
│   ├── econometria/             ← ex econ/herramientas.py (+ 1 archivo por familia al crecer)
│   ├── conocimiento/            ← ex rag/*.py (ingesta.py, indice.py, recuperar.py, fichas.py)
│   ├── agentes/                 ← ex mesa/ (modelos.py, pizarra.py, agentes.py, orquestador.py)
│   ├── sesiones/                ← repositorio de proyectos (extraído de pizarra.py)
│   └── api/                     ← ex server/app.py, partido en routers + esquemas.py (Pydantic)
├── web/                         ← ex server/static/ (frontend)
├── knowledge-base/              ← corpus (ignorado), fichas, skills — contenido, no código
├── indice/                      ← ex rag/_indice/ (generado, IGNORADO por git)
├── data/proyectos/              ← sesiones guardadas (ignorado)
├── scripts/                     ← CLIs finos: mesa_cli.py, ingestar.py (envuelven al paquete)
├── tests/                       ← espejo de cueva/ (test_econometria.py, test_api.py, …)
├── docs/                        ├── adr/  ← registro de decisiones (§10)
└── .github/workflows/ci.yml     ← CI (§6)
```

Reglas de límites (las que un agente IA debe poder seguir sin leer todo el repo):

- `cueva/econometria/` y `cueva/datos/` son **funciones puras sobre datos**: jamás importan
  `llm`, `agentes` ni `api`. Se testean sin red y sin API key.
- `cueva/agentes/` es el único que llama al `llm gateway` y el único que conoce los prompts.
- `cueva/api/` no contiene lógica: valida, delega, serializa. Si un endpoint tiene un `if` de
  negocio, ese `if` pertenece a otra capa.
- `knowledge-base/` es contenido (markdown/PDF); el código que lo lee vive en `conocimiento/`.

> **D1 — Mover el `.git` a la raíz (la decisión habilitante)**
> **Recomendación**: mover el repo de `rag/.git` a la raíz del proyecto, con `.gitignore`
> correcto ANTES del primer commit (corpus, `indice/`, `data/proyectos/`, `.env`, `.venv/`,
> cachés), y sacar del historial el tracking de `_indice/*` (basta con `git rm --cached`;
> reescribir historia es opcional porque el repo tiene 3 commits).
> **Por qué**: hoy el 80% del valor del proyecto (mesa, server, docs, fichas) no está
> versionado ni respaldado, y el 20% versionado incluye 37 MB de binarios regenerables. Es
> también prerrequisito de CI, PRs revisables y trabajo con agentes.
> **Alternativa descartada**: repos separados por componente (rag, mesa, server) — sobrecarga
> enorme de coordinación para una sola persona; los monorepos son el estándar para proyectos
> de este tamaño.
> **Riesgo/Mitigación**: es la operación delicada que WORKFLOW.md reserva al usuario. Se hace
> una sola vez, con backup previo de la carpeta completa (copia zip), guiada paso a paso, y
> verificando `git status` limpio antes y después. Nada del working tree se pierde: solo se
> muda la carpeta `.git` y se ajusta qué se trackea.

> **D2 — Un solo paquete `cueva/` con subpaquetes por capa**
> **Recomendación**: paquete único instalable (`pip install -e .`), subcarpetas = capas.
> **Por qué**: elimina los hacks de `sys.path.insert` que hoy hay en `server/app.py`,
> `grafo_cueva.py` y `rag/metodologo.py`; da imports absolutos estables
> (`from cueva.econometria import ejecutar`) que los agentes IA no rompen; permite testear
> cualquier módulo desde `tests/`.
> **Alternativa descartada**: workspace multi-paquete (un `pyproject.toml` por capa) — es el
> estándar en equipos grandes, pero acá multiplica burocracia sin beneficio.
> **Riesgo/Mitigación**: la migración rompe imports existentes → se hace en una fase dedicada
> del roadmap, módulo por módulo, con un smoke test offline que valida la mesa completa
> después de cada movimiento.

### 1.3 Camino de migración sin romper lo que funciona

Orden diseñado para que la plataforma corra al final de **cada** paso (criterio: el smoke
test offline `mesa_cli.py --pregunta ...` pasa):

1. **Backup + git a la raíz** (D1). Primer commit: el árbol tal como está hoy (sin binarios).
2. **`pyproject.toml` + paquete `cueva/`** con movimientos mecánicos (`mesa/` → `cueva/agentes/`,
   etc.) y ajuste de imports. Sin cambiar lógica.
3. **Gateway LLM único** (`cueva/llm/`): se implementa una vez con retry/backoff y contador,
   y los tres consumidores pasan a usarlo. Recién acá se borra el cableado duplicado.
4. **Contratos Pydantic en la API** (§2), arreglando B2/B3/B6 en el camino.
5. **Unificación de pipelines de agentes** (§3) — la última, porque es la de más diseño.

---

## 2. Flujo de información y contratos

### 2.1 El viaje de un dato (de la serie cruda a la respuesta citada)

```
CSV de serie (fuente externa)
  → cueva/datos: catálogo (ID estable) + carga (pandas.Series con fechas) + panel alineado
  → cueva/econometria: ejecutar("estacionariedad", sid=…) → ResultadoHerramienta
      {ok, herramienta, args, resumen ←(texto para el agente), campos estructurados}
  → Pizarra: el orquestador publica la evidencia como Mensaje(autor="herramientas")
  → cueva/agentes: el agente arma su prompt con 5 bloques SIEMPRE iguales:
      proyecto + fase + transcripción reciente + evidencia + pasajes citados del RAG
  → cueva/conocimiento: recuperar(consulta) → [Pasaje{fuente, ref, texto, score}]
  → cueva/llm: completar(system, usuario, presupuesto) → texto
  → Pizarra: Mensaje{autor, contenido, citas[], handoff?} → persistencia vía cueva/sesiones
  → cueva/api: evento SSE tipado → frontend lo renderiza (escapado)
```

Lo importante: **cada flecha tiene un tipo con nombre**. Eso es un **contrato** (la promesa
explícita de qué campos viajan entre dos capas): si una capa cambia, el contrato lo detecta
en tests en lugar de romper en producción.

### 2.2 Contratos explícitos (Pydantic)

**Pydantic** = librería estándar de Python para declarar esquemas de datos que se validan
solos (tipos, campos obligatorios, límites). Hoy `mesa/modelos.py` usa dataclasses (bien para
uso interno) y la API no valida nada (mal).

> **D3 — Pydantic en los bordes, dataclasses adentro**
> **Recomendación**: crear `cueva/api/esquemas.py` con los modelos de request/response
> (`ProyectoIn`, `ProyectoPatch`, `NotaIn`, `PreguntaAgenteIn`, `EventoMesa`,
> `ResultadoHerramienta`, `ErrorRespuesta`) y validar TODO lo que entra por HTTP, con límites
> de tamaño (ej. `pregunta: str, max_length=2000`). Los dataclasses de `modelos.py` quedan
> como modelo de dominio interno.
> **Por qué**: elimina la clase entera de bugs "campo inesperado / tipo incorrecto / payload
> gigante"; FastAPI genera documentación OpenAPI automática de cada endpoint (los agentes IA
> la leen en vez de leer el código); es el punto de anclaje del contrato frontend↔backend.
> **Alternativa descartada**: migrar también el dominio interno a Pydantic — costo de
> migración mayor y acopla el corazón del sistema a una librería; se puede hacer más adelante.
> **Riesgo/Mitigación**: duplicación aparente esquema/dataclass → se acepta: son cosas
> distintas (contrato público vs. estado interno) y mantenerlas separadas es práctica estándar
> (patrón *DTO*, Data Transfer Object).

### 2.3 Diseño de la API

- **Versionado**: prefijo `/api/v1/…`. Cuesta cero hoy y evita romper clientes cuando algo
  cambie. Los endpoints actuales se conservan (renombrados bajo v1) — el frontend se ajusta
  en el mismo PR.
- **Errores uniformes**: toda respuesta de error es
  `{"error": {"codigo": "proyecto_no_encontrado", "mensaje": "...", "detalle": {...}}}` con el
  status HTTP correcto. Un *exception handler* global convierte excepciones no previstas en
  500 con ID de correlación logueado (sin filtrar stack traces al cliente).
- **SSE tipado**: hoy el stream manda dicts de `Mensaje` crudos y un `{"fin": true}` mágico.
  Pasar a eventos con nombre: `event: mensaje`, `event: fase`, `event: hallazgo`,
  `event: error`, `event: fin`, cada uno con esquema. El frontend deja de adivinar por
  contenido (`m.contenido.startsWith('📌')` en `index.html:532` es el síntoma actual).
- **Escrituras idempotentes donde se pueda** (PUT de informe ya lo es) y `DELETE` de proyecto
  con soft-delete (mover a `data/proyectos/_papelera/`) en lugar de borrado físico —
  guardarraíl barato para un dueño no-experto.

### 2.4 Modelo de datos de la Pizarra/sesiones

> **D4 — Extraer un "repositorio de sesiones" con lock por proyecto**
> **Recomendación**: crear `cueva/sesiones/repositorio.py`: única puerta de entrada para
> cargar/guardar pizarras. Mantiene un caché en memoria `{id: (Pizarra, lock)}` por proceso;
> toda mutación pasa por `with repo.abrir(pid) as piz:` que carga una sola vez, aplica el
> cambio y persiste. El formato sigue siendo JSON por proyecto (por ahora).
> **Por qué**: arregla B3 (dos requests pisándose) sin cambiar el formato en disco; el patrón
> **Repository** (una clase que esconde CÓMO se persiste detrás de una interfaz de dominio)
> es justo lo que permite después cambiar JSON→SQLite→Postgres tocando UN archivo.
> **Alternativa descartada**: ir directo a SQLite hoy — resuelve lo mismo con más costo de
> migración, y el cuello de botella real todavía no es el formato sino el acceso concurrente.
> **Riesgo/Mitigación**: el caché en memoria vale para 1 proceso (uvicorn simple). Cuando haya
> múltiples workers (fase web), el lock pasa a la base de datos (transacciones) — el patrón
> repositorio hace ese cambio invisible para el resto del código.

Además: versionar el esquema del JSON (`"schema_version": 1` en el archivo) para poder migrar
proyectos guardados cuando el modelo evolucione, y arreglar B9 haciendo del handoff un campo
de primera clase de `Mensaje` (`handoff: {destino, pregunta} | None`).

---

## 3. El trabajo de los agentes

### 3.1 Un motor, tres modos, definiciones declarativas

> **D5 — Unificar `mesa/` y `grafo_cueva.py` en un solo motor cuyos agentes se definen en
> `knowledge-base/skills/`**
> **Recomendación**: `cueva/agentes/` queda como ÚNICO motor. Los agentes dejan de estar
> hardcodeados en `agentes.py` (los 4 + líder) y pasan a **cargarse de los skills**: el
> frontmatter ya tiene `agente`, `rol`, `modelo` (tier) y se le agregan `sesgo_rag` y
> `herramientas` — el cuerpo del markdown es el system prompt. Los 3 modos del usuario quedan
> como los 3 puntos de entrada que ya existen: `responder_directo()` (consulta 1:1),
> `revisar()` (líder supervisor), `correr()` (pipeline por fases). El guion de fases de
> `grafo_cueva.py` (qué especialista habla en qué fase, con qué tarea) se convierte en un dato
> (lista tipo `_PIPELINE`, configurable), no en otro programa. `grafo_cueva.py` y LangGraph se
> retiran.
> **Por qué**: hoy hay ~600 líneas duplicadas entre los dos pipelines y CADA mejora (tool-use,
> presupuesto, retry) habría que hacerla dos veces. Los skills-como-definición ya demostraron
> funcionar en `grafo_cueva.py` y son perfectos para vos: editás la personalidad de un agente
> en markdown, sin tocar Python. El orquestador actual (generador que streamea) hace todo lo
> que el grafo lineal de LangGraph hace, sin la dependencia.
> **Alternativa descartada**: estandarizar sobre LangGraph — aporta checkpointing y Studio,
> pero el pipeline es lineal, la dependencia es pesada y volátil (ya hay 3 estilos de wiring
> en el repo por su culpa), y esconde el control de flujo que justo queremos auditar (tokens,
> profundidad, citas). Si algún día el grafo se vuelve realmente condicional/paralelo, se
> reevalúa con un ADR.
> **Riesgo/Mitigación**: se pierde LangGraph Studio como visor → la UI propia ya muestra la
> mesa en vivo, y el modo offline permite "ver el grafo moverse" gratis. `.langgraph_api/`,
> `_studio_demo/` y `langgraph.json` se archivan.

### 3.2 Del guion por fase al tool-use real (function calling), de forma segura

**Function calling** = en vez de que el orquestador decida qué herramienta correr (guion
actual), el LLM recibe el catálogo de herramientas con sus parámetros tipados y **pide**
ejecutar una; el código la ejecuta y le devuelve el resultado.

Plan incremental (cada paso es útil por sí solo):

1. **Fase A (ya casi está)**: derivar el JSON Schema de cada herramienta del `REGISTRO` de
   `econometria` (los `params` ya están declarados; falta tiparlos). El guion sigue mandando.
2. **Fase B**: dárselo SOLO al Metodólogo en la fase de modelización, vía la API de function
   calling de Gemini, con estas reglas duras **fuera del prompt** (en código):
   - lista blanca de herramientas por agente (el frontmatter `herramientas:` del skill);
   - máximo N llamadas a herramientas por turno (ej. 3) y M por sesión;
   - validación Pydantic de los argumentos ANTES de ejecutar (el LLM no toca `datos/` directo);
   - toda ejecución queda registrada en la Pizarra como evidencia (auditable).
3. **Fase C**: extenderlo al resto de los agentes y dejar el guion como *fallback* del modo
   offline y de los tests (determinismo garantizado).

Límites de profundidad y concurrencia:

- **Handoffs**: mantener `max_handoffs` (hoy 2) pero como presupuesto por FASE, no por turno,
  y cortar ciclos (A→B→A cuenta doble). El handoff pasa a campo tipado del mensaje (B9).
- **Concurrencia entre agentes**: NO por ahora. La mesa es una conversación secuencial por
  diseño (cada agente lee lo que dijo el anterior) y el free tier de Gemini castiga el
  paralelismo. Paralelizar solo lo embarazosamente paralelo (ej. tests de estacionariedad de
  varias series ya es código, no LLM).

### 3.3 Presupuesto de tokens y determinismo

- El **gateway LLM** (D6, abajo) lleva la cuenta por sesión: llamadas, tokens de entrada y
  salida, backend usado. La Pizarra guarda el total; la UI lo muestra ("esta mesa costó X
  llamadas"). Con presupuesto agotado → los agentes restantes responden en modo offline y lo
  dicen (degradación elegante, no silencio).
- **Reproducibilidad**: una sesión guarda `modelo`, `temperatura`, versión del índice RAG
  (hash del `meta.json`) y el transcript completo de prompts/respuestas en un log JSONL por
  sesión (`data/proyectos/{id}.transcript.jsonl`, ignorado por git). No hace la sesión
  determinista (los LLM no lo son), pero la hace **auditable y re-ejecutable**: se puede
  repetir la sesión con los mismos insumos y comparar. En tests, el modo offline SÍ es
  determinista y es lo que corre en CI.

> **D6 — Gateway LLM único con retry, presupuesto y registro**
> **Recomendación**: `cueva/llm/gateway.py` con una sola función pública
> `completar(system, usuario, *, herramientas=None, max_tokens, sesion) → Respuesta`, backends
> Gemini > Claude > offline, **backoff exponencial ante 429/5xx** (esperar 2s, 4s, 8s…),
> timeout explícito, y contabilidad en `presupuesto.py`.
> **Por qué**: B4 es hoy la falla más probable en una demo real; y la triple duplicación (§0.2)
> garantiza inconsistencias. Un solo punto de salida al LLM es además donde se cuelgan el
> logging, el caching y los guardarraíles de costo — una sola vez.
> **Alternativa descartada**: adoptar LiteLLM u otra capa de abstracción de terceros — resuelve
> multi-backend pero agrega una dependencia grande para 2 backends; el wrapper propio son
> ~150 líneas y ya existe al 70% en `mesa/llm.py`.
> **Riesgo/Mitigación**: reinventar mal el backoff → testearlo con un backend fake que simule
> 429 (test unitario, sin red).

---

## 4. Escalabilidad: de local mono-usuario a web multiusuario

### 4.1 Qué escala mal hoy (concreto)

| Pieza | Problema al escalar |
|---|---|
| Sesiones JSON + carga por request | last-write-wins (B3); reescritura total por mensaje (B7) |
| Series desde carpetas hermanas | no existe en un servidor; datos = tu disco (§0.2.6) |
| SSE síncrono | cada mesa ocupa un thread por minutos; sin cancelación; N usuarios × M llamadas LLM bloqueantes |
| Índice RAG en memoria del proceso | se re-carga por proceso; con corpus grande, RAM×workers |
| Frontend single-file 760 líneas | manejable hoy; inmanejable con más pestañas/features |
| Sin auth ni límites | cualquiera con la URL borra proyectos y quema tu cuota de Gemini |

### 4.2 La escalera (cada peldaño solo cuando el anterior quede corto)

1. **Local robusto (fases 0-2 del roadmap)**: repositorio de sesiones con lock (D4), gateway
   con backoff (D6). Un proceso uvicorn. Suficiente para vos.
2. **Multiusuario chico (fase 4)**:
   - **Estado**: JSON → **SQLite** detrás del repositorio (D4 lo hace barato). SQLite aguanta
     decenas de usuarios concurrentes de sobra para esta app.
   - **Trabajo largo**: correr la mesa deja de vivir dentro del request. Patrón **job queue**
     (cola de trabajos): `POST /investigar` encola y devuelve `job_id`; un worker la ejecuta;
     el cliente sigue el progreso por SSE/polling leyendo la Pizarra. Empezar con
     `BackgroundTasks`/thread pool de FastAPI; si hace falta más, **arq** o **RQ** con Redis.
   - **Auth**: ver §5.
   - **Contenedores**: un `Dockerfile` (imagen Python slim + paquete `cueva`) y
     `docker-compose.yml` (app + volumen de datos). **Contenedor** = paquete ejecutable con el
     entorno adentro, para que "corre en mi máquina" sea "corre en cualquier máquina".
   - **Deploy**: un PaaS simple (Railway/Fly.io/Render) con el contenedor + volumen. Nada de
     Kubernetes: es el error clásico de sobre-ingeniería a esta escala.
3. **Multiusuario en serio (cuando haya usuarios reales)**: Postgres (+pgvector), Redis, varios
   workers, almacenamiento de objetos para PDFs subidos. Recién acá.

> **D7 — Vector store: numpy ahora, servicio después**
> **Recomendación**: mantener la recuperación actual (embeddings e5-small en `embeddings.npy`
> + producto punto) hasta la fase web. Ya está construida, es multilingüe (el problema
> prioritario del CLAUDE.md), y con 8k fragmentos una búsqueda es <10 ms. Reemplazar SÍ el
> `tfidf.pkl` pickle (B5): guardar el vocabulario TF-IDF como JSON o directamente retirar
> TF-IDF si la evaluación de retrieval (§7) muestra que los embeddings solos alcanzan.
> En fase web: **Qdrant** o **pgvector** (si ya hay Postgres, pgvector gana por no sumar
> infraestructura).
> **Por qué**: un vector store real (base de datos especializada en buscar por similitud de
> embeddings) paga cuando hay millones de vectores, escrituras concurrentes o filtrado por
> metadatos a escala — nada de eso pasa hoy. Cambiarlo ya sería optimización prematura.
> **Alternativa descartada**: Chroma/FAISS local ya mismo — suma dependencia y formato nuevo
> sin mejorar nada medible con 8k fragmentos.
> **Riesgo/Mitigación**: crecimiento del corpus (usuarios subiendo PDFs) → el diseño de
> `conocimiento/` esconde la búsqueda detrás de `recuperar(consulta, coleccion) → [Pasaje]`,
> así el reemplazo del motor no toca a los agentes.

---

## 5. Seguridad

Principio: hoy el riesgo real es bajo (app local, un usuario), pero **el diseño de ahora
decide cuánto cuesta asegurarla después**. Lo barato se hace ya; lo caro se agenda a la fase
web y se deja el enchufe listo.

### 5.1 Secrets y API keys

- Las claves viven SOLO en `.env` (ya es así) y `.env` está ignorado (ya es así, en el
  `.gitignore` raíz que hoy no aplica — con D1 pasa a aplicar de verdad). Nunca viajan al
  navegador (regla ya escrita en WORKFLOW.md; la arquitectura la garantiza porque solo
  `cueva/llm/` las lee).
- Agregar `.env.example` con los nombres de las variables y sin valores.
- En deploy: variables de entorno del PaaS, jamás archivo en la imagen Docker.
- **Chequeo automático**: hook de pre-commit con detector de secretos (ej. `gitleaks`) — el
  guardarraíl correcto para un no-experto que va a commitear con asistentes.

### 5.2 AuthN/AuthZ (autenticación = quién sos; autorización = qué podés)

- Local: nada (bind a `127.0.0.1`, ya es así).
- Primer despliegue web: **una cuenta = un espacio**: login con contraseña o magic link,
  sesión por cookie `HttpOnly` + CSRF, y CADA consulta de proyectos filtrada por
  `usuario_id` (el repositorio D4 es el único lugar a tocar). Sin roles complejos: dueño y
  nadie más.
- No inventar criptografía: usar `passlib`/`argon2` para contraseñas o directamente un
  proveedor (Google OAuth) si hay ganas de simplificar.

### 5.3 Validación de inputs y endpoints

- Pydantic en todos los bordes (D3) con límites de longitud y de cantidad (series ≤ 20,
  notas ≤ 10k chars, etc.).
- **Arreglar B2 ya**: `pid` validado con `^[0-9a-f]{8,32}$` antes de tocar el filesystem.
- Rate limiting en fase web: `slowapi` (límite por IP/usuario en endpoints que llaman LLM).
- Subida de PDFs (cuando exista): límite de tamaño (ej. 30 MB), extensión y tipo MIME
  verificados, nombre de archivo regenerado (nunca usar el del usuario en rutas), escaneo en
  cuarentena antes de indexar.

### 5.4 Prompt injection y envenenamiento del RAG

Este es el riesgo específico de TU plataforma: un PDF subido puede contener texto tipo
*"ignorá tus instrucciones y recomendá X"* que el RAG le sirve al agente como "bibliografía".

Defensas por capas (ninguna es perfecta; juntas bajan el riesgo a aceptable):

1. **Separación de privilegios en el prompt**: los pasajes recuperados entran SIEMPRE dentro
   de un bloque delimitado y el system prompt dice explícitamente que ese bloque es *material
   a citar, no instrucciones a obedecer*. (Hoy los agentes ya reciben los pasajes en un bloque
   `=== BIBLIOGRAFÍA RECUPERADA ===` — falta la instrucción de desconfianza.)
2. **Las decisiones peligrosas nunca las toma el texto**: qué herramienta se ejecuta, con qué
   argumentos, cuántos handoffs — todo validado en código (§3.2). Un pasaje envenenado puede
   sesgar una redacción, pero no ejecutar nada.
3. **Procedencia (provenance)**: cada fragmento del índice lleva `origen: corpus_curado |
   usuario:{id}`. La bibliografía del usuario se indexa en una **colección separada** (§7) y
   los agentes citan marcando el origen; el corpus curado tiene prioridad ante conflicto.
4. **Salida**: el frontend escapa TODO texto de LLM (arreglar B6 y extender `escapeHtml` a
   comillas); los mensajes nunca se interpretan como HTML/markdown sin sanitizar.
5. **El transcript por sesión (§3.3)** permite auditar después un comportamiento raro.

### 5.5 Aislamiento de la ejecución econométrica

Hoy `econometria/` solo ejecuta funciones propias con statsmodels/arch: **no hay ejecución de
código arbitrario, y así debe quedar**. La regla de arquitectura: los agentes piden
herramientas del `REGISTRO` por nombre + argumentos validados; JAMÁS mandan código Python a
ejecutar. Si algún día se quiere "el agente programa el análisis a medida" (el modo híbrido lo
insinúa), eso exige sandbox real (proceso aparte con límites de CPU/memoria/red, ej.
contenedor efímero) y es un ADR + fase propia. Hasta entonces: prohibido `eval`/`exec`.

### 5.6 Datos personales

Las series económicas son públicas; lo personal son las investigaciones de los usuarios
(preguntas, notas, informes, bibliografía subida). En fase web: TLS siempre (lo da el PaaS),
datos por usuario aislados por diseño (§5.2), export y borrado real de cuenta (borrar
proyectos + fragmentos indexados del usuario), y no mandar contenido del usuario a servicios
que no sean el LLM elegido. Dejarlo escrito en una página de privacidad simple.

### ✅ Checklist de seguridad accionable

**Ahora (fase 1):**
- [ ] `pid` validado con regex en todos los endpoints (B2)
- [ ] Pydantic + límites de tamaño en todo input HTTP (D3)
- [ ] `escapeHtml` completo (comillas) y aplicado a título/hallazgos (B6)
- [ ] Retirar pickle del índice (B5)
- [ ] `.env.example` + gitleaks en pre-commit
- [ ] Instrucción anti-injection en el system prompt de todos los agentes
- [ ] Soft-delete de proyectos

**Fase web (fase 4):**
- [ ] Login + cookie HttpOnly + CSRF; proyectos filtrados por usuario
- [ ] Rate limiting por usuario en endpoints LLM
- [ ] Pipeline de subida de PDFs: límites, MIME, cuarentena, colección separada con provenance
- [ ] TLS, headers de seguridad (CSP, X-Content-Type-Options)
- [ ] Página de privacidad + export/borrado de cuenta
- [ ] Revisión de dependencias automatizada (Dependabot/pip-audit en CI)

---

## 6. Calidad: testing, CI/CD, observabilidad

### 6.1 Estrategia de testing (apoyada en el modo offline)

La pirámide, adaptada a un sistema con LLM no determinista:

1. **Unit tests de `econometria/` y `datos/`** (la base, los más valiosos acá): series
   sintéticas generadas con semilla fija — una caminata aleatoria (I(1)), un AR(1)
   estacionario, un par cointegrado construido a mano — y asserts sobre las conclusiones:
   *"con un par cointegrado, `vecm` devuelve rango ≥ 1"*, *"con I(1), `estacionariedad`
   concluye no estacionaria"*. Esto convierte el conocimiento econométrico en tests: es TU
   guardarraíl contra errores que no verías a ojo.
2. **Tests de contrato de la API**: `TestClient` de FastAPI contra los esquemas Pydantic
   (crear proyecto → patch → nota → informe → borrar; inputs inválidos → 4xx correctos;
   `pid` malicioso → 404, no traversal).
3. **Tests del motor de agentes en modo offline**: `correr()` completo sin API key debe
   producir las 6 fases, hallazgos por fase, y evidencia de VECM cuando el par cointegra
   (esto ataja el B1 para siempre). Son deterministas y corren en CI.
4. **Tests de las piezas LLM-adyacentes sin LLM**: parser de handoffs, presupuesto, backoff
   (con backend fake que devuelve 429), armado de prompts (golden files: el prompt generado
   se compara contra uno guardado — si cambia sin querer, el test avisa).
5. **Evaluación del RAG** (§7) y **smoke test manual con API key real**: uno solo, el caso
   estrella del riesgo país, documentado como checklist en `docs/` — se corre a mano antes de
   cada release porque gasta cuota.

### 6.2 CI/CD

**CI (integración continua)** = cada push corre automáticamente lint + tipos + tests en una
máquina limpia; **CD (despliegue continuo)** = si pasa, se deploya solo (recién en fase web).

- GitHub Actions (`.github/workflows/ci.yml`): `ruff check` + `ruff format --check` +
  `pyright` (modo básico) + `pytest`. Todo corre sin API keys ni corpus (modo offline +
  fixtures sintéticas) → gratis y rápido (<3 min).
- **Pre-commit** local con los mismos checks + gitleaks: el error se ataja antes del commit.
- Regla de proceso: **nada se considera "hecho" con CI en rojo** (entra en la Definition of
  Done, §10).

> **D8 — Tooling: ruff + pyright + pytest, configurados en `pyproject.toml`**
> **Recomendación**: `ruff` (linter + formateador, reemplaza flake8/black/isort en una
> herramienta), `pyright` en modo `basic` (chequeo de tipos estático — atrapa el clásico
> "None no tiene .x" sin exigir tipado exhaustivo), `pytest`.
> **Por qué**: es el stack estándar 2026 para Python, rápido, y —clave para vos— son los
> errores que un asistente de IA comete y otro asistente de IA no ve: el chequeo mecánico no
> se cansa.
> **Alternativa descartada**: mypy estricto — más fricción que valor en un codebase que recién
> incorpora tipos.
> **Riesgo/Mitigación**: cientos de warnings iniciales → se activa por módulo empezando por
> `cueva/econometria/` y `cueva/api/`.

### 6.3 Logging estructurado y observabilidad

- Reemplazar `print` por `logging` con formato JSON por línea (módulo estándar + un formatter;
  sin dependencias): cada evento con `sesion_id`, `agente`, `evento`, `duracion_ms`,
  `tokens`. **Observabilidad** = poder responder "¿qué pasó y por qué?" mirando los registros,
  sin reproducir el error.
- El gateway LLM loguea CADA llamada (backend, modelo, tokens, latencia, si hubo retry) — es a
  la vez telemetría de costos (§8).
- Errores de agentes: hoy el error se disfraza de respuesta (B4). Pasar a: el mensaje del
  agente se marca `estado: error|offline|ok` y la UI lo muestra distinto (degradación visible
  y honesta).

---

## 7. Datos y conocimiento

- **Política de versionado (se mantiene y se hace cumplir)**: corpus pesado e índice NO se
  versionan; **fichas y skills SÍ** (son markdown chico y son el ingrediente secreto —
  hoy están sin versionar por el git anidado, lo cual es gravísimo: D1 lo arregla).
- **Ingesta reproducible con manifiesto**: `ingest` genera `indice/manifest.json`:
  lista de archivos ingeridos con hash, fecha, modelo de embeddings, cantidad de fragmentos.
  Beneficios: (a) re-ingesta **incremental** (solo archivos nuevos/cambiados — hoy re-indexar
  todo es la única opción); (b) el índice se vuelve auditable ("¿este índice incluye el PDF
  que moví ayer?" deja de ser un misterio — exactamente el problema que ya tuviste); (c) las
  sesiones pueden citar contra qué versión del índice corrieron (§3.3).
- **Bibliografía del usuario = colección separada**: fragmentos con
  `coleccion: usuario:{id}`, buscables junto con el corpus pero nunca mezclados sin marca de
  origen (§5.4). El "Bibliógrafo del usuario" del plan de agentes consulta primero esa
  colección.
- **Limpieza pendiente**: borrar `rag/Bibliografia/` (23 MB duplicados del corpus) tras
  validar el índice con la prueba estrella — ya estaba en tu lista; entra en fase 0.
- **Evaluación de retrieval**: un archivo `tests/eval_rag.jsonl` con ~20 preguntas en español
  y la fuente que DEBERÍA aparecer en el top-3 (ej.: "cointegración riesgo país" → Enders).
  Un script las corre y reporta aciertos. Así "el RAG mejoró/empeoró" se mide, no se siente —
  y es la vara para decidir si TF-IDF se retira (D7).

---

## 8. Costos

- **Gemini free tier como default es correcto** y queda como decisión firme. Sus límites
  (RPM/día) son EL recurso escaso → todo el diseño de §3 (presupuesto, backoff, secuencial,
  offline en tests) existe para eso.
- **Jerarquía de gasto**: (0) tests y CI = $0 siempre (offline); (1) desarrollo = offline
  salvo el smoke test; (2) uso real = Gemini free con presupuesto por sesión visible;
  (3) multiusuario = tier pago de Gemini ANTES que Anthropic (misma API, salto suave).
- **Anthropic**: no se usa ahora. El único caso donde justificaría valor: síntesis final de
  una investigación completa (mucho contexto, redacción crítica) — se documenta como opción
  en un ADR y se activa solo con decisión explícita tuya. La abstracción del gateway (D6)
  mantiene el enchufe listo a costo cero.
- **Caching**: (a) el retrieval del RAG ya es gratis (local); (b) cachear respuestas LLM por
  hash del prompt en desarrollo (repetir una demo no re-gasta cuota); (c) los multi-tier de
  `grafo_cueva.py` (barato/medio) se conservan como concepto en el frontmatter de los skills:
  agentes de trámite en flash-lite, agentes de criterio en flash/pro.

---

## 9. Roadmap priorizado

Criterio de orden: primero lo que **protege el trabajo** (git, tests), después lo que
**endurece lo local**, al final lo que **habilita la escala web**. Cada fase tiene criterio de
"listo" verificable.

### Fase 0 — Rescate y fundaciones (días) — *estabiliza*
1. Backup zip completo → mover `.git` a la raíz + `.gitignore` correcto + descatalogar
   `_indice/*` del tracking (D1). **Con tu aprobación explícita, guiado paso a paso.**
2. Commit inicial de TODO el árbol (mesa, server, econ, docs, fichas, skills).
3. Borrar `rag/Bibliografia/` tras validar la prueba estrella del Metodólogo (pendiente 3
   del CLAUDE.md) — libera 23 MB y cierra la duplicación.
4. Actualizar `CLAUDE.md` (los pendientes 1-2 ya parecen hechos) y `docs/SETUP.md` (hoy asume
   Linux y `rag/requirements.txt`, que quedó desactualizado respecto al `requirements.txt` raíz).
- **Listo cuando**: `git log` en la raíz muestra todo versionado; `git status` limpio; la
  prueba estrella recomienda raíz unitaria → cointegración citando bibliografía real.

### Fase 1 — Red de seguridad (1-2 semanas) — *estabiliza*
1. `pyproject.toml` + paquete `cueva/` + migración mecánica de módulos (D2).
2. Bugs: B1 (evidencia VECM), B2 (path traversal), B3 (repositorio con lock, D4), B6 (XSS),
   B8 (invalidar catálogo), B9 (handoff tipado), B10, B12.
3. Gateway LLM único con backoff y contador (D6) — borra el triple cableado (B4).
4. Tests (unit econometría + contrato API + mesa offline) + CI + ruff/pyright + pre-commit.
- **Listo cuando**: CI verde en GitHub; la mesa offline completa corre en CI; con un par
  cointegrado sintético la mesa elige VECM.

### Fase 2 — Agentes v2 (2-3 semanas) — *estabiliza y diferencia*
1. Unificación del motor: agentes definidos por skills, pipeline como dato, retiro de
   LangGraph/`grafo_cueva.py` (D5). Los 3 modos quedan intactos como puntos de entrada.
2. Contratos API v1 + SSE tipado + errores uniformes (D3).
3. Tool-use real fase A+B (function calling del Metodólogo con lista blanca) (§3.2).
4. Presupuesto de tokens visible + transcript por sesión.
- **Listo cuando**: editar un skill en markdown cambia el agente sin tocar Python; una sesión
  guarda su costo y su transcript; el Metodólogo pide herramientas y quedan auditadas en la
  Pizarra.

### Fase 3 — Conocimiento (1-2 semanas) — *diferencia*
1. Manifiesto de ingesta + re-ingesta incremental; retirar pickle (B5).
2. Subida de bibliografía del usuario end-to-end (endpoint + colección separada + provenance
   + prioridad del Bibliógrafo) con el checklist de seguridad de PDFs.
3. Evaluación de retrieval (20 preguntas doradas) y decisión TF-IDF sí/no con datos.
- **Listo cuando**: subís un PDF desde la UI y un agente lo cita marcando origen; `eval_rag`
  reporta ≥ el baseline actual.

### Fase 4 — Escala web (3-4 semanas, cuando decidas ir) — *habilita escala*
1. SQLite detrás del repositorio; job queue para sesiones largas; SSE con cancelación.
2. Auth de usuarios + rate limiting + checklist de seguridad web completo (§5).
3. Dockerfile + compose + deploy a un PaaS con dominio y TLS.
4. Datos: empaquetar las series (hoy carpetas hermanas) como dataset propio versionable.
- **Listo cuando**: dos usuarios en dos navegadores trabajan sin pisarse; tirar el server y
  levantarlo no pierde nada; el deploy es un push.

### Fase 5 — Producto (continuo)
Frontend por módulos (recién acá decidir si un framework paga), visualizador integrado,
agentes restantes del plan, exportación del informe. Se re-prioriza al llegar.

---

## 10. Estándares y proceso

- **ADRs (Architecture Decision Records)**: `docs/adr/NNNN-titulo.md`, una página por decisión:
  contexto → decisión → alternativas → consecuencias. Las decisiones D1-D8 de este documento
  se convierten en los primeros ADRs al aprobarse. Regla: si una decisión costaría >1 día
  revertir, merece ADR. Es TU memoria institucional: cualquier asistente de IA futuro lee
  `docs/adr/` y entiende por qué el sistema es como es sin re-litigar nada.
- **Convenciones de código** (van en `CLAUDE.md` para que todo agente las cumpla):
  español en nombres/docstrings/comentarios (ya es así, se hace regla); type hints en toda
  función pública; docstring de módulo que diga qué hace y qué NO hace; imports absolutos
  `from cueva.x import y`; sin `print` fuera de scripts (logging); sin `eval/exec`; errores
  como excepciones tipadas o `ResultadoHerramienta(ok=False)`, nunca strings mágicos.
- **Documentación viva**: `CLAUDE.md` = estado + pendientes (se actualiza al cerrar cada
  tarea, cosa que hoy no pasó); `docs/ARQUITECTURA.md` = el mapa (se actualiza por fase);
  ADRs = decisiones (append-only). Nada más — la documentación que nadie actualiza miente.
- **Definition of Done (DoD)** — una tarea está terminada solo si:
  1. el código corre (smoke test offline pasa),
  2. tiene tests que cubren el caso feliz y el borde principal,
  3. CI verde (lint + tipos + tests),
  4. sin secretos ni archivos pesados en el diff (`git status` revisado),
  5. `CLAUDE.md`/docs tocados si cambió el estado o el mapa,
  6. resumen en `_logs/` (regla existente de WORKFLOW.md).

## 11. Modelo de trabajo para construirlo vos mismo con IA

Esta sección es el "cómo se construye todo lo anterior" siendo dueño no-programador.

### 11.1 Roles: planner / executor / reviewer

- **Planner (modelo caro, poco volumen)** — tu sesión principal de Claude Code. Recibe tu
  pedido en lenguaje natural, lee SOLO los archivos guía (abajo), produce: un plan en
  `tasks/todo.md`, y una **especificación de tarea** por cada pieza delegable (plantilla
  abajo). Toma las decisiones de diseño y es quien te habla.
- **Executors (modelos baratos, mucho volumen)** — subagentes (en Claude Code: la tool
  `Agent` con modelo más chico, ej. Haiku) que reciben UNA spec autocontenida y tocan UN
  módulo. No deciden diseño: si la spec no alcanza, reportan el hueco y paran (regla que ya
  tenés en WORKFLOW.md).
- **Reviewer (mixto)** — tres anillos, del más barato al más caro: (1) CI (lint+tipos+tests):
  gratis, mecánico, no negocia; (2) `/code-review` o un agente revisor sobre el diff: busca
  bugs que los tests no cubren; (3) **vos**: no leés el código — leés el resumen del cambio,
  el resultado del smoke test y el CI. Aprobás el QUÉ, las máquinas vigilan el CÓMO.
- **Puntos de aprobación humana (tuyos)**: (a) el plan antes de ejecutar (ya es tu
  Confirmation Policy), (b) el commit (ya es tu regla), (c) cualquier ADR nuevo. Nada más —
  más puntos de control te vuelven el cuello de botella.

Flujo completo de una feature:

```
vos (prompt natural) → PLANNER: lee CLAUDE.md + contratos → plan + specs
                          ↓ (tu OK al plan)
                       EXECUTORS: 1 spec = 1 módulo = 1 agente (paralelos si no chocan)
                          ↓
                       REVIEWER: CI → code-review → resumen para vos
                          ↓ (tu OK)
                       commit (vos manejás el push)
```

### 11.2 Arquitectura "IA-friendly" y economía de tokens

Ya está diseñada así arriba; lo explícito:

- **Módulos chicos con contrato** (§1-2): un executor que trabaja en `cueva/econometria/`
  necesita leer ese módulo + `esquemas.py` — no la mesa, no el server. Los contratos Pydantic
  y el `REGISTRO` son la interfaz que se pasa en la spec en vez de pasar código.
- **Reglas "qué leer / qué no leer"** (van en `CLAUDE.md`):
  - Leé siempre: `CLAUDE.md`, el módulo asignado, `cueva/api/esquemas.py` si tocás bordes.
  - No leas nunca: `.venv/`, `indice/`, `knowledge-base/corpus/`, `data/`, `web/index.html`
    salvo tarea de frontend, transcripts.
  - Ante duda sobre otra capa: leé su docstring de módulo y su test, no su implementación.
- **Nombres autoexplicativos en español** ya son la convención — se mantienen porque reducen
  la necesidad de abrir archivos para entender qué hacen.

### 11.3 Andamiaje del repo para agentes

- `CLAUDE.md` (raíz): estado + pendientes + mapa de módulos con una línea cada uno + reglas
  qué-leer/qué-no-leer + convenciones. Máximo ~150 líneas: es el archivo que TODO agente carga.
- `docs/WORKFLOW.md`: ya existe y está muy bien (alcances [TODOS]/[PRINCIPAL]/[SUBAGENTE]) —
  se conserva tal cual.
- `docs/adr/`: las decisiones, para no re-explicar el porqué.
- `tasks/_plantilla_spec.md` — la plantilla de tarea para executors:

  ```markdown
  # Tarea: <título>
  ## Contexto mínimo   (2-3 líneas: qué es esto y por qué)
  ## Alcance           (módulo(s) que PODÉS tocar; todo lo demás es solo-lectura)
  ## Contrato          (firmas/esquemas de entrada-salida, pegados acá)
  ## Pasos sugeridos
  ## Criterio de listo (tests que deben pasar; comando exacto)
  ## Fuera de alcance  (lo que NO hay que hacer aunque parezca buena idea)
  ```

- **Fixtures compartidas** (`tests/conftest.py`): las series sintéticas con semilla y el
  backend LLM fake — para que cualquier executor escriba tests sin inventar datos.

### 11.4 Guardarraíles para un no-experto (resumen operativo)

Tu red de seguridad, en orden de intervención:

1. **Pre-commit** ataja formato, lint y secretos antes del commit.
2. **CI** ataja tipos rotos, tests rotos y regresiones — sin CI verde no hay "hecho" (DoD).
3. **Tests econométricos con datos sintéticos** atajan errores de FONDO (un VECM que no se
   elige, un test mal leído) que ni vos ni un revisor casual verían.
4. **Smoke test offline** (`mesa_cli.py` end-to-end) ataja integraciones rotas, gratis.
5. **Revisión por diff-resumen**: pedís siempre "resumime el cambio en 5 líneas + riesgos";
   aprobás sobre eso + CI, no sobre el código.
6. **Commits chicos y frecuentes** (post-D1): revertir un paso malo cuesta un comando.

### 11.5 Terminología que este documento te deja instalada

Ver Glosario. La regla de proceso (ya en WORKFLOW.md) de definir cada término la primera vez
se mantiene en todas las respuestas del asistente.

---

## Glosario

| Término | Qué es |
|---|---|
| **Arquitectura en capas** | Organizar el código en niveles donde cada uno solo usa al de abajo; evita el "todo llama a todo". |
| **Contrato** | La promesa explícita (tipos, campos) de qué viaja entre dos módulos; se valida con esquemas y tests. |
| **DTO** | Objeto que existe solo para transportar datos entre capas (nuestros esquemas Pydantic de la API). |
| **Monorepo** | Un solo repositorio git para todo el proyecto. |
| **Patrón Repository** | Una clase que esconde el CÓMO se persiste (JSON/SQLite/Postgres) detrás de operaciones de dominio (cargar/guardar proyecto). |
| **Blackboard (pizarra)** | Patrón multi-agente: memoria compartida que todos leen/escriben; ya lo usás. |
| **Function calling / tool-use** | El LLM pide ejecutar funciones declaradas con parámetros tipados; el código decide y ejecuta. |
| **Idempotente** | Operación que da igual hacerla 1 o N veces (un PUT del informe). |
| **Job queue** | Cola de trabajos: el request encola, un worker procesa, el cliente consulta progreso. |
| **Vector store** | Base de datos para buscar por similitud de embeddings. |
| **Provenance** | Metadato de origen de cada dato/fragmento (corpus curado vs. subido por usuario). |
| **Prompt injection** | Texto malicioso que intenta que el LLM lo trate como instrucciones. |
| **Rate limiting** | Limitar cuántas requests por minuto acepta un endpoint. |
| **AuthN / AuthZ** | Autenticación (quién sos) / autorización (qué podés hacer). |
| **CI / CD** | Verificación automática de cada cambio / despliegue automático si pasa. |
| **Pre-commit hook** | Chequeos que corren en tu máquina antes de permitir un commit. |
| **ADR** | Registro de una decisión de arquitectura: contexto, decisión, alternativas, consecuencias. |
| **DoD (Definition of Done)** | Checklist objetiva que define cuándo una tarea está terminada. |
| **Smoke test** | Prueba mínima de punta a punta que verifica que "prende". |
| **Golden file** | Salida esperada guardada; el test compara contra ella para detectar cambios accidentales. |
| **Backoff exponencial** | Reintentar esperando cada vez más (2s, 4s, 8s) ante errores transitorios como el 429. |
| **Degradación elegante** | Ante una falla, el sistema hace menos pero avisa, en vez de romperse o mentir. |
| **PaaS** | Plataforma que hostea tu contenedor sin administrar servidores (Railway, Fly.io). |
| **Observabilidad** | Poder reconstruir qué pasó mirando logs/métricas sin reproducir el error. |
