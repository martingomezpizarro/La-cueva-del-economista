# La Cueva del Economista — estado y contexto para el asistente

Plataforma de econometría de series de tiempo (visión completa en `docs/VISION.md`):
datos + motor de análisis + **agentes-profesores con RAG** (`docs/PLAN_AGENTES.md`).
La arquitectura objetivo y el roadmap aprobado viven en `docs/PROPUESTA_ARQUITECTURA.md`.
Responder siempre en español.

## Estado (actualizado 2026-07-05)

**Fases 0, 1, 2 y 3 del roadmap COMPLETAS** (rescate + red de seguridad + agentes v2 + conocimiento).

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
- 70 tests en verde (aislados: los tests jamás tocan el índice real).

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
4. Datos: empaquetar las series (hoy carpetas hermanas) como dataset propio.
Paralelo (conocimiento): conseguir Enders; iterar retrieval midiendo con
`scripts/evaluar_rag.py` (baseline @3=14/20).

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
