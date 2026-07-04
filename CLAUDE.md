# La Cueva del Economista — estado y contexto para el asistente

Plataforma de econometría de series de tiempo (visión completa en `docs/VISION.md`):
datos + motor de análisis + **agentes-profesores con RAG** (`docs/PLAN_AGENTES.md`).
Responder siempre en español.

## Estado (actualizado 2026-07-03)

**Fase 1 lista — motor de conocimiento "La Cueva-LM":**
- `rag/ingest.py` ingiere PDFs/código/md de `knowledge-base/corpus/` → índice en `rag/_indice/` (8.015 fragmentos, hoy solo TF-IDF).
- `rag/ask.py` = consulta suelta con pasajes citados.
- ~19 textos en `corpus/` por categoría; 10 fichas en `knowledge-base/fichas/`; 10 skills de agentes escritos en `knowledge-base/skills/` (aún sin cablear).

**Fase 2 recién iniciada — primer agente:**
- `rag/metodologo.py` = agente Metodólogo v1 (creado 2026-07-03). Recibe el contexto del
  análisis, recupera pasajes (reusa `ask.py`) + top-3 fichas por solapamiento de vocabulario,
  y redacta recomendación estructurada (diagnóstico → método → supuestos → errores típicos →
  plan). Flag `-i` = modo conversación.
- Backends LLM (elige el primero disponible): Gemini free tier vía `GEMINI_API_KEY`
  (`google-genai`, default `gemini-2.5-flash`, override `CUEVA_MODELO_GEMINI`) > Claude vía
  `ANTHROPIC_API_KEY`. **Decisión del usuario: NO usar API de Anthropic (costo); Gemini gratis.**

## Problema conocido (prioridad 1)

La recuperación TF-IDF falla con preguntas en español sobre corpus en inglés: en la prueba
del caso riesgo país trajo `utils.py` y Sala-i-Martin en vez de Enders/cointegración
(las fichas sí las eligió bien). Solución ya programada en `ingest.py`, falta activarla:

```
pip install sentence-transformers   # baja torch ~2GB, ojo espacio en disco
python rag/ingest.py knowledge-base/corpus
```

Esto además re-indexa los PDFs que se movieron a `corpus/` DESPUÉS del último índice.

## Pendientes en orden

1. Probar `metodologo.py` con `GEMINI_API_KEY` real (la última corrida usó el placeholder "tu_clave").
2. Instalar sentence-transformers + re-ingestar (embeddings multilingües e5-small).
3. Repetir la prueba caso estrella: `python rag/metodologo.py "Quiero explicar el riesgo país argentino (EMBI, mensual) con reservas del BCRA y tipo de cambio real. Objetivo: relación de largo plazo" -i` → debe recomendar raíz unitaria → cointegración (VECM/ARDL) citando bibliografía real.
4. Borrar `rag/Bibliografia/` (duplica los PDFs de `corpus/`) una vez validado el índice; libera GB.
5. Commitear (último commit: 13-jun; hay mucho trabajo local sin versionar).
6. Siguientes agentes: Intérprete y Crítico (mismo patrón que metodologo.py, prompts nuevos en `rag/prompts/`), luego orquestación (LangGraph) cableando `knowledge-base/skills/`.

## Convenciones

- Corpus pesado NO se versiona; el índice `rag/_indice/` tampoco.
- Fichas = ingrediente secreto: 1 página por método con supuestos y errores típicos (`_plantilla_ficha.md`).
- No leer/gastar tokens en `.venv/`.

## Reglas de proceso

Cómo trabajar conmigo (confirmaciones, estilo de respuesta, git, subagentes): `docs/WORKFLOW.md`.
Nota clave de ahí: el `.git` real vive en `rag/`, no en la raíz — toda operación git se corre parada en `rag/`.
