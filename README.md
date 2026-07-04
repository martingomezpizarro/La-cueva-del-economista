# 🕳️📊 La Cueva del Economista

Plataforma web para economistas y estudiantes de economía (Argentina) que unifica las series de
tiempo económicas argentinas y permite hacer **investigación econométrica de punta a punta**
(todo menos la escritura final), potenciada por una **red de agentes-profesores de IA** que
conversan entre sí, consultan bibliografía real y ejecutan la econometría.

## Las dos piezas

1. **La Cueva-LM** (motor de conocimiento, tipo NotebookLM propio e integrable): un RAG sobre el
   corpus de econometría + la bibliografía que sube el usuario. Da respuestas **fundamentadas y
   citadas**. Ver `rag/` y `docs/VISION.md`.
2. **La Mesa de Trabajo** (lo nuevo): la red de agentes orquestados que recorren una
   investigación —encuadre → exploratorio → control de series → modelización → interpretación →
   conclusiones— consultando La Cueva-LM y corriendo tests y modelos sobre **820+ series reales**
   del Trabajo Final y de ANÁLISIS MATRIZ ARG. Ver `docs/ARQUITECTURA.md`.

## Arrancar la Mesa de Trabajo

```bash
python3 -m venv .venv && . .venv/bin/activate    # en Windows: .venv\Scripts\activate
pip install -r requirements.txt

# (opcional, recomendado) respuestas reales de los agentes:
export ANTHROPIC_API_KEY="tu_clave"              # en Windows: set ANTHROPIC_API_KEY=...

uvicorn server.app:app --port 8800
# abrir http://localhost:8800
```

En la UI: definís título, pregunta de investigación e hipótesis, buscás y seleccionás las series
(marcás una como dependiente con ⭐), y **abrís la mesa**. Los agentes conversan en vivo, citan la
bibliografía y muestran la evidencia econométrica que van ejecutando.

> **Sin `ANTHROPIC_API_KEY` igual funciona**: la orquestación, el RAG y la econometría corren; los
> agentes muestran una *maqueta* de su intervención (modo offline). Cargás la clave y pasan a ser
> respuestas reales de Claude, sin tocar nada más.

### Detección de datos

`config.py` autodetecta las carpetas hermanas del Trabajo Final (`…/Trabajo/data/Variables
Finales`) y de ANÁLISIS MATRIZ ARG (`…/Series`). Si están en otro lado, sobreescribí con variables
de entorno `CUEVA_TRABAJO_FINAL` y `CUEVA_MATRIZ_ARG`, o un `cueva.local.toml`. Verificá con:

```bash
python mesa_cli.py --diag
```

## Desde la terminal (sin web)

```bash
python mesa_cli.py --series reservas                       # buscar series
python mesa_cli.py --pregunta "¿Los depósitos explican las reservas?" \
    --ids 001_reservas_brutas 021_dep_total --dep 001_reservas_brutas
```

## La Cueva-LM (RAG) por separado

```bash
python rag/ingest.py knowledge-base/corpus     # ingiere el corpus (PDF, .py, .ipynb, .md)
python rag/ask.py "¿Para qué sirve el test de Dickey-Fuller aumentado?"
```

Para cargar tu propia bibliografía, ver `knowledge-base/GUIA_CARGA.md`.

## Estructura

```
config.py              rutas a datos + modelo/clave de IA
mesa/                  la red de agentes (pizarra, agentes, orquestador, RAG, LLM)
econ/                  motor de datos + herramientas econométricas (modo híbrido)
server/                FastAPI + UI de la Mesa de Trabajo
mesa_cli.py            correr una sesión desde la terminal
rag/                   La Cueva-LM (motor de conocimiento)
knowledge-base/        corpus + fichas + bibliografía
docs/                  VISION.md · PLAN_AGENTES.md · ARQUITECTURA.md · SETUP.md
```

Reusa el motor de datos y econometría del proyecto de investigación de riesgo país (Trabajo Final).
