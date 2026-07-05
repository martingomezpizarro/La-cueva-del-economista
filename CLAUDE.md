# La Cueva del Economista — estado y contexto para el asistente

Plataforma de econometría de series de tiempo (visión completa en `docs/VISION.md`):
datos + motor de análisis + **agentes-profesores con RAG** (`docs/PLAN_AGENTES.md`).
La arquitectura objetivo y el roadmap aprobado viven en `docs/PROPUESTA_ARQUITECTURA.md`.
Responder siempre en español.

## Estado (actualizado 2026-07-04)

**Fases 0, 1 y 2 del roadmap COMPLETAS** (rescate + red de seguridad + agentes v2).

Fase 2 (agentes v2):
- **Los agentes se definen en `knowledge-base/skills/`** (frontmatter: `agente`, `rol`,
  `modelo` [tier barato/medio/claude], `sesgo_rag`, `herramientas` [lista blanca]; cuerpo =
  system prompt). Editar el markdown cambia al agente sin tocar Python. Plantel: 12 agentes
  (4 profesores + líder + 7 especialistas). Cargador: `cueva/agentes/skills.py`.
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

## Problema conocido (prioridad para fase 3)

La calidad del retrieval es floja: para "riesgo país + cointegración" trae resúmenes en
español (Sala-i-Martin, GARCH) en vez de los libros en inglés (Kirchgässner, Johansen), con
scores casi idénticos (~0.87). Además **Enders NO está en el corpus** (verificado: 24 fuentes
indexadas, sin Enders). Plan: evaluación con 20 preguntas doradas (`docs/PROPUESTA_ARQUITECTURA.md`
§7) + conseguir Enders + decidir TF-IDF/embeddings con datos.

## Pendientes en orden (fase 3 del roadmap aprobado)

1. Evaluación de retrieval: `tests/eval_rag.jsonl` con ~20 preguntas doradas + script que
   mida aciertos; decidir TF-IDF/embeddings con datos. Conseguir Enders para el corpus.
2. Ingesta incremental con manifiesto (`indice/manifest.json`: hash por archivo).
3. Subida de PDFs del usuario end-to-end (colección separada con provenance, checklist de
   seguridad de docs/PROPUESTA_ARQUITECTURA.md §5.3).
4. Después: fase 4 (web multiusuario: SQLite, job queue, auth, Docker), según el roadmap.

## Qué leer / qué no leer (economía de tokens)

- Leé siempre: este archivo, el módulo que toques, `cueva/api/esquemas.py` si tocás la API.
- NO leas: `.venv/`, `indice/`, `knowledge-base/corpus/`, `data/`, backups; `web/index.html`
  solo en tareas de frontend.
- Cada módulo de `cueva/` tiene docstring que dice qué hace y qué NO hace — leé eso antes
  que la implementación de otra capa.

## Convenciones

- Español en nombres, docstrings y comentarios. Imports absolutos `from cueva.x import y`.
- Corpus pesado, `indice/` y `data/proyectos/` NO se versionan.
- Fichas = ingrediente secreto: 1 página por método con supuestos y errores típicos
  (`knowledge-base/fichas/_plantilla_ficha.md`).
- Solo `cueva/llm/` habla con los SDKs de LLM. `econometria/` y `datos/` son puros (sin red).
- Sin `print` en el paquete (logging); sin `eval`/`exec`; errores como excepciones tipadas
  o `{"ok": False}`.
- Definition of Done: corre + tests + CI verde + sin secretos en el diff + docs al día.

## Reglas de proceso

Cómo trabajar conmigo (confirmaciones, estilo de respuesta, git, subagentes): `docs/WORKFLOW.md`.
Git: repo en la raíz; comitear solo con aprobación explícita; nunca push (lo maneja el usuario).
