# 🧭 Reglas de trabajo con el asistente (Claude Code)

> Este archivo define **cómo** trabajamos, no **qué** falta hacer — eso vive en `CLAUDE.md`
> (estado del proyecto, pendientes) y se actualiza mucho más seguido. Separarlos evita que
> `CLAUDE.md` se infle con reglas de proceso que casi no cambian.

## Cómo leer este archivo (multi-agente)

Cada sección tiene un **alcance** marcado en el título:

- **[TODOS]** — aplica a cualquier agente: sesión principal, subagentes, tareas en background.
- **[PRINCIPAL]** — aplica SOLO a la sesión principal (la que conversa conmigo).
- **[SUBAGENTE]** — aplica SOLO a subagentes lanzados por la sesión principal.

**Si sos un subagente:** cumplí [TODOS] y [SUBAGENTE], e ignorá las [PRINCIPAL] (no podés
preguntarme nada, no manejás git, no escribís en `tasks/todo.md` ni en `_logs/`).

## Mapa del proyecto [TODOS]

La Cueva del Economista es **un solo proyecto en un solo repo (monorepo)**: el `.git`
(`github.com/tomasgomezpizarro/cueva-del-economista`) vive en la **raíz** desde 2026-07-04
(antes estaba anidado en `rag/`; esa anomalía ya no existe). Todas las operaciones git se
corren desde la raíz.

Estructura de carpetas (para ubicar dónde va cada cosa):

| Carpeta | Qué es |
|---|---|
| `cueva/` | El ÚNICO paquete Python, por capas: `datos/` (series), `econometria/` (herramientas), `conocimiento/` (La Cueva-LM: ingesta/recuperar/fichas), `llm/` (gateway único de LLM), `agentes/` (mesa: pizarra, agentes, orquestador), `sesiones/` (persistencia con locks), `api/` (FastAPI + esquemas Pydantic). |
| `web/` | Frontend de la Mesa de Trabajo (`index.html`). |
| `scripts/` | CLIs finos: `mesa_cli.py`, `ingestar.py`, `preguntar.py`, `metodologo.py`. |
| `knowledge-base/` | Corpus (no versionado), fichas (1 página por método), skills de agentes y prompts. |
| `indice/` | Índice RAG generado (NO versionado; se reconstruye con `scripts/ingestar.py`). |
| `tests/` | Suite offline (series sintéticas, sin API keys). |
| `docs/` | Documentación (visión, arquitectura, propuesta/roadmap, este archivo). |

## Prohibiciones estrictas [TODOS]

- **No versionar contenido pesado**: `knowledge-base/corpus/` (PDFs/EPUBs/papers) y
  `indice/` (índice generado) no van al repo — se reconstruyen localmente
  (ver `docs/SETUP.md`). Si algo de esto aparece en `git status` como para comitear, es señal
  de que el `.gitignore` está mal, no que corresponda subirlo.
- **No crear archivos sueltos** en la raíz del proyecto. El código va en el subpaquete de
  `cueva/` que corresponda por capa; los CLIs van en `scripts/`. Si un script es de un solo
  uso (debug, prueba puntual), va en una subcarpeta tipo `scripts/debug/` — no suelto al
  lado de los módulos reales.
- **Nunca dejar credenciales** (`GEMINI_API_KEY`, `ANTHROPIC_API_KEY`) en código o en archivos
  committeados. Viven en `.env` (ya ignorado) o como variable de entorno. Si el frontend de
  `server/static/` necesita hacer llamadas a un LLM, esas llamadas pasan por el backend — la
  clave nunca viaja al navegador.
- **No commitear archivos innecesarios**: cachés (`__pycache__/`, `.langgraph_api/`), logs,
  índices regenerables, datos de prueba. Revisar `git status` antes de hacer stage.

## Reglas para subagentes [SUBAGENTE]

- **No podés preguntarle nada al usuario.** Si falta información, tomá el supuesto más
  razonable, declaralo explícitamente en tu respuesta final y seguí.
- **Nunca toques git** (`pull`, `commit`, `push`, `checkout`, `stash`): eso lo maneja
  exclusivamente la sesión principal.
- **No escribas en `tasks/todo.md` ni en `_logs/`**: son de la sesión principal.
- **Trabajá solo dentro del alcance que te asignaron.** Si la tarea toca dos carpetas a la vez
  (ej. un cambio de agente en `mesa/` que también necesita ajustar `rag/metodologo.py`), no lo
  hagas de oficio: reportalo como pendiente en tu respuesta.
- **Tu respuesta final es tu único canal de salida.** Incluí archivos tocados (ruta completa),
  decisiones tomadas, supuestos, y qué quedó pendiente o dudoso.

## Coordinación multi-agente [PRINCIPAL]

- **Los subagentes nacen sin contexto**: no vieron la conversación. Al delegar, incluí en el
  prompt todo lo que necesitan (carpeta/módulo, archivos relevantes, convenciones acordadas en
  la charla, criterio de terminado).
- **Nunca lances dos agentes en paralelo que escriban sobre el mismo módulo** (ej. dos agentes
  tocando `cueva/agentes/orquestador.py` a la vez). Lecturas/búsquedas en paralelo: sin restricción.
- **El usuario no ve lo que hacen los subagentes**: resumí sus hallazgos y cambios en la
  respuesta.
- Delegá en subagentes las búsquedas amplias y tareas acotadas y verificables; las decisiones
  de diseño (arquitectura de agentes, qué backend LLM usar, cómo estructurar una ficha) quedan
  en la sesión principal.

## Confirmation Policy [PRINCIPAL] (CRITICAL)

- **Preguntar UNA VEZ al arrancar un pedido, después seguir sin interrupciones.**
- Si necesito aclarar algo, pregunto TODO de una sola vez antes de empezar.
- Una vez resuelto (o si no hace falta aclarar nada), ejecuto la tarea completa sin pedir más
  confirmaciones intermedias tipo "¿arranco?", "¿seguimos?", "¿confirmás?".
- Solo freno a mitad de tarea si: (a) hay un bloqueo real que necesita una decisión tuya, o
  (b) la acción es destructiva/irreversible (push --force, borrar corpus, reescribir el índice sin
  backup, mover el `.git`).
- La única confirmación que sigue aplicando siempre es la de commit (ver Git Workflow) —
  nunca comiteo sin que lo pidas explícitamente.
- **Si el pedido es explícitamente una recomendación** ("recomendame", "qué me
  recomendás"): el entregable es la recomendación. La presento y frenó ahí; recién implemento
  con tu OK.

## Cómo hablarme [PRINCIPAL] (CRITICAL)

Aplica a toda respuesta (consultas, tareas, propuestas, resúmenes de subagentes).

- **Primero lo simple, después lo técnico.** Toda respuesta arranca contando en lenguaje
  cotidiano qué está pasando / qué hice / qué propongo. Nada de nombrar funciones o jerga en
  esa primera parte.
- **Cerrar con un bloque corto "🔧 Lo técnico para aprender"**: los 2-3 nombres más relevantes
  (archivo, función o concepto econométrico), cada uno con una línea de qué hace y por qué
  importa. No listar todo lo que se tocó — elegir lo que vale la pena aprender.
- Si menciono más de ~5 nombres de funciones/archivos, la respuesta está mal calibrada —
  recortar.
- Términos técnicos (de código Y de econometría — cointegración, cross-validation temporal,
  cadenas de embeddings) se definen en una línea la primera vez que aparecen.

## Modo de interacción [PRINCIPAL] (CRITICAL)

Antes de actuar, clasificar el pedido: consulta, propuesta de cambio, o tarea directa. Si hay
duda, preguntar una sola vez.

### En todos los casos
- Devolver primero qué se entendió del pedido, en palabras simples, antes de implementar o
  explicar a fondo.
- Declarar supuestos explícitamente.
- Indicar nivel de confianza (alto/medio/bajo) cuando corresponda.

### Si es una CONSULTA sobre cómo funciona algo
- Relato simple primero, técnico al final (ver "Cómo hablarme").
- Enseñar al menos un concepto que valga la pena saber — puede ser de código o de
  econometría (ej. por qué TF-IDF falla con vocabulario cruzado idioma/dominio).
- Acompañar con `archivo:línea`.

### Si es una PROPUESTA de modificar algo
1. Mapear primero el estado actual de lo que se va a tocar (qué llama a qué, qué datos
   entran/salen — ej. flujo `rag/ask.py` → `metodologo.py` → LLM).
2. Presentar al menos DOS enfoques.
3. Para cada enfoque, ficha de impacto (alto/medio/bajo + una línea en simple):
   - **Costo**: ¿más llamadas a Gemini/Anthropic, más tokens, re-indexado completo del corpus
     (proceso pesado, baja `torch`/`sentence-transformers`)?
   - **Alcance**: cuántos módulos toca (`rag/`, `mesa/`, `econ/`, `server/`).
   - **Riesgo de efecto dominó**: qué otro agente o parte de la Mesa de Trabajo depende de lo
     que se toca.
   - Si toca el corpus o el índice: ¿es reversible? (reingest desde cero siempre lo es, pero
     tarda).
4. Recomendar uno y justificar. La decisión final es del usuario.
5. Seguir de corrido con el enfoque recomendado por defecto (según Confirmation Policy).
   Pausar a esperar OK solo si se pide explícitamente, si el pedido fue "una recomendación",
   o si el cambio es de alto riesgo (toca el `.git`, borra corpus/índice sin poder
   reconstruirlo, afecta varios agentes a la vez).

## Workflow Process [PRINCIPAL]

0. **Actualizar primero** — antes de leer código o cambiar algo, correr `git pull` en la raíz.
1. Pensar el problema primero — leer el código relevante y escribir un plan en
   `tasks/todo.md`.
2. El plan es una checklist de pasos concretos.
3. Preguntar TODAS las aclaraciones de entrada en un solo mensaje; después, seguir sin
   interrupciones.
4. Completar los todos uno por uno, tildando en tiempo real.
5. Explicar los cambios en cada paso, en alto nivel (ver "Cómo hablarme").
6. Cambios simples y acotados — evitar reescrituras grandes.
7. Al terminar, agregar una sección de revisión en `tasks/todo.md` resumiendo todo lo hecho.
8. Crear un archivo resumen en `_logs/` después de cada tarea de proyecto completada: qué se
   hizo, decisiones clave, archivos tocados, notas relevantes. Nombre con fecha + descripción
   breve (ej. `_logs/2026-07-10-agente-interprete.md`). Son para seguimiento propio — **no se
   commitean**.
9. Comitear el trabajo solo con aprobación explícita del usuario (ver Git Workflow).
10. Antes de cerrar: revisar que no quedaron claves/tokens en el código ni en el frontend de
    `server/static/`.

## Implementation Notes [PRINCIPAL]

- Usar TodoWrite para gestionar `tasks/todo.md`.
- Seguir la Confirmation Policy: presentar el plan y seguir sin esperar, salvo cambio de alto
  riesgo, pedido explícito de "recomendación", o pausa pedida por el usuario.
- Priorizar claridad y mantenibilidad sobre optimización prematura.
- Si aparece algo que fuerza un cambio **significativo** de plan (otro alcance, toca el
  `.git`, afecta varios agentes), pausar y preguntar. Ajustes menores: anotar y seguir.

## Git Workflow [PRINCIPAL]

- El repo vive en la **raíz** del proyecto; todo comando git se corre desde ahí.
- **Al arrancar**: `git pull` para traer lo último del remoto.
- **Antes de dar algo por terminado**: `pytest` y `ruff check .` en verde (Definition of Done).
- **Durante el trabajo**: stagear cambios a medida que se avanza, sin comitear todavía.
- **Al terminar**: preguntar si el trabajo está completo y funcionando.
- **Comitear**: solo con aprobación explícita del usuario.
- **Los subagentes nunca corren git** — todo pasa por la sesión principal.

### Reglas de commit

- **CRÍTICO**: siempre `git pull` ANTES de comitear.
- **CRÍTICO**: comitear solo con aprobación explícita.
- Mensajes claros que expliquen qué cambió y por qué.
- Antes de comitear, confirmar: "Está todo listo. ¿Comiteo estos cambios?"

### Push

- **El asistente puede empujar a `main`** cuando el usuario aprobó el commit (decidido
  2026-10-21, como en idoneidad). Antes: `git pull`; nunca `--force`.
- Después de empujar: "Cambios comiteados y empujados como [hash]." Si el usuario trabaja
  en su copia local, recordarle hacer `git pull`.
