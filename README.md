# 🕳️📊 La Cueva del Economista

Plataforma web para economistas y estudiantes de economía (Argentina) que unifica las series de
tiempo económicas argentinas y permite hacer **investigación econométrica de punta a punta**
(todo menos la escritura final), potenciada por una **red de agentes-profesores de IA** que
conversan entre sí, consultan bibliografía real y ejecutan la econometría.

## Las dos piezas

1. **La Cueva-LM** (motor de conocimiento, tipo NotebookLM propio e integrable): un RAG sobre el
   corpus de econometría + la bibliografía que sube el usuario. Da respuestas **fundamentadas y
   citadas**. Ver `cueva/conocimiento/` y `docs/VISION.md`.
2. **La Mesa de Trabajo**: la red de agentes orquestados que recorren una investigación
   —encuadre → exploratorio → control de series → modelización → interpretación → conclusiones—
   consultando La Cueva-LM y corriendo tests y modelos sobre **820+ series reales**
   del Trabajo Final y de ANÁLISIS MATRIZ ARG. Ver `docs/ARQUITECTURA.md`.

## Arrancar la Mesa de Trabajo

```bash
python -m venv .venv && . .venv/bin/activate    # en Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# (opcional, recomendado) respuestas reales de los agentes — Gemini es GRATIS:
# clave en https://aistudio.google.com/apikey → guardala en .env como GEMINI_API_KEY=...

uvicorn cueva.api.app:app --port 8800
# abrir http://localhost:8800
```

En la UI: definís título, pregunta de investigación e hipótesis, buscás y seleccionás las series
(marcás una como dependiente con ⭐), y **abrís la mesa**. Los agentes conversan en vivo, citan la
bibliografía y muestran la evidencia econométrica que van ejecutando.

> **Sin API key igual funciona**: la orquestación, el RAG y la econometría corren; los
> agentes muestran una *maqueta* de su intervención (modo offline). Cargás la clave y pasan a ser
> respuestas reales, sin tocar nada más.

### Detección de datos

`cueva/config.py` autodetecta las carpetas hermanas del Trabajo Final (`…/Trabajo/data/Variables
Finales`) y de ANÁLISIS MATRIZ ARG (`…/Series`). Si están en otro lado, sobreescribí con variables
de entorno `CUEVA_TRABAJO_FINAL` y `CUEVA_MATRIZ_ARG`, o un `cueva.local.toml`. Verificá con:

```bash
python scripts/mesa_cli.py --diag
```

## Desde la terminal (sin web)

```bash
python scripts/mesa_cli.py --series reservas                       # buscar series
python scripts/mesa_cli.py --pregunta "¿Los depósitos explican las reservas?" \
    --ids 001_reservas_brutas 021_dep_total --dep 001_reservas_brutas
```

## La Cueva-LM (RAG) por separado

```bash
python scripts/ingestar.py knowledge-base/corpus   # ingiere el corpus (PDF, .py, .ipynb, .md)
python scripts/preguntar.py "¿Para qué sirve el test de Dickey-Fuller aumentado?"
python scripts/metodologo.py "Quiero explicar el EMBI con reservas y TCR" -i
```

Para cargar tu propia bibliografía, ver `knowledge-base/GUIA_CARGA.md`.

## Desarrollo

```bash
pytest              # 48 tests: econometría sintética, API, mesa offline — sin API key, $0
ruff check .        # lint
ruff format .       # formato
pre-commit install  # hooks de commit (formato + detector de secretos)
```

## Estructura (arquitectura en capas: api → agentes/sesiones → conocimiento/econometría/llm → datos)

```
cueva/                 ÚNICO paquete Python
  config.py            rutas a datos + modelo/clave de IA
  llm/                 gateway único de LLM (Gemini > Claude > offline, backoff, tokens)
  datos/               catálogo y carga de series
  econometria/         herramientas ejecutables (ADF/KPSS, Granger, OLS, VAR, VECM, GARCH)
  conocimiento/        La Cueva-LM: ingesta, índice, recuperación, fichas
  agentes/             la mesa: modelos, pizarra, agentes, orquestador
  sesiones/            persistencia de investigaciones (repositorio con locks)
  api/                 FastAPI /api/v1 (contratos Pydantic)
web/                   UI de la Mesa de Trabajo
scripts/               CLIs: mesa_cli, ingestar, preguntar, metodologo
knowledge-base/        corpus (no versionado) + fichas + skills + prompts
indice/                índice RAG generado (no versionado)
tests/                 suite offline (corre en CI sin claves)
docs/                  VISION · PLAN_AGENTES · ARQUITECTURA · SETUP · WORKFLOW · PROPUESTA_ARQUITECTURA
```

Reusa el motor de datos y econometría del proyecto de investigación de riesgo país (Trabajo Final).
