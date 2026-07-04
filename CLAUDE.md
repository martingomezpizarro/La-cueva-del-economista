# La Cueva del Economista — estado y contexto para el asistente

Plataforma de econometría de series de tiempo (visión completa en `docs/VISION.md`):
datos + motor de análisis + **agentes-profesores con RAG** (`docs/PLAN_AGENTES.md`).
La arquitectura objetivo y el roadmap aprobado viven en `docs/PROPUESTA_ARQUITECTURA.md`.
Responder siempre en español.

## Estado (actualizado 2026-07-04)

**Fases 0 y 1 del roadmap COMPLETAS** (rescate + red de seguridad):

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
  (`Orquestador.revisar`), pipeline (`Orquestador.correr`). `grafo_cueva.py` (LangGraph)
  sigue funcionando pero se retira en fase 2 (unificación por skills).

## Problema conocido (prioridad para fase 3)

La calidad del retrieval es floja: para "riesgo país + cointegración" trae resúmenes en
español (Sala-i-Martin, GARCH) en vez de los libros en inglés (Kirchgässner, Johansen), con
scores casi idénticos (~0.87). Además **Enders NO está en el corpus** (verificado: 24 fuentes
indexadas, sin Enders). Plan: evaluación con 20 preguntas doradas (`docs/PROPUESTA_ARQUITECTURA.md`
§7) + conseguir Enders + decidir TF-IDF/embeddings con datos.

## Pendientes en orden (fase 2 del roadmap aprobado)

1. Unificar motor de agentes: definiciones desde `knowledge-base/skills/` (frontmatter =
   tier/sesgo/herramientas; cuerpo = system prompt); retirar `grafo_cueva.py` + LangGraph.
2. Tool-use real (function calling de Gemini) para el Metodólogo, con lista blanca y límites.
3. SSE tipado (eventos con nombre) + transcript JSONL por sesión.
4. Después: fase 3 (conocimiento: ingesta incremental con manifiesto, PDFs del usuario,
   eval de retrieval) y fase 4 (web multiusuario), según el roadmap.

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
