# 🕳️📊 La Cueva del Economista

Plataforma web para economistas y estudiantes de economía (Argentina) que unifica las
series de tiempo económicas argentinas y permite realizar todo tipo de análisis
econométrico de series de tiempo, **con agentes de IA actuando como profesores incansables
detrás de cada investigación**: recomiendan métodos, advierten errores teóricos, ayudan a
interpretar resultados — todo fundamentado en bibliografía real.

## Estado

🚧 Etapa temprana. Primer hito en construcción: **el motor de conocimiento ("La Cueva-LM")**
— nuestro propio sistema tipo NotebookLM, integrable, que los agentes pueden consultar.

## Estructura

```
cueva-del-economista/
├── docs/
│   ├── VISION.md            # qué es y a dónde va
│   └── PLAN_AGENTES.md      # diseño de los agentes-profesores
├── knowledge-base/          # la base de conocimiento (corpus + fichas)
│   ├── corpus/              # PDFs/papers por tema (no se versionan, son pesados)
│   └── fichas/              # fichas "cara-al-agente": reglas y errores típicos
└── rag/                     # motor de recuperación + respuesta fundamentada
    ├── ingest.py            # PDF → fragmentos → índice
    └── ask.py               # pregunta → pasajes citados → respuesta fundamentada
```

## Probar el prototipo

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r rag/requirements.txt
python rag/ingest.py knowledge-base/corpus          # ingiere TODO el corpus (PDF, .py, .ipynb, .md)
python rag/ask.py "¿Para qué sirve el test de Dickey-Fuller aumentado?"
python rag/ask.py "¿Cómo estimo un VECM en Python con statsmodels?"
```

- Recuperación **multilingüe**: preguntás en español, recupera bibliografía/código en inglés.
- Ingiere **teoría (PDF) y código (.py/.ipynb)**: la IA aprende a programar con ejemplos reales.
- Con `ANTHROPIC_API_KEY`, Claude redacta la respuesta fundamentada y citada.
- Para cargar más material, ver `knowledge-base/GUIA_CARGA.md`.

Reusa código del repo de investigación de riesgo país (motor de datos y econometría).
