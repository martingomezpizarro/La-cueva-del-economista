# Arquitectura — La Mesa de Trabajo

La **Mesa de Trabajo** es el corazón de La Cueva del Economista: una red de agentes-profesores
que conversan entre sí, consultan la bibliografía (La Cueva-LM) y ejecutan econometría real
sobre las series, para acompañar una investigación de punta a punta (salvo la escritura final).

## Las tres capas

```
┌──────────────────────────────────────────────────────────────────┐
│  UI  ·  server/static/index.html                                   │
│  Definís la investigación (pregunta, hipótesis, series) y mirás    │
│  a los agentes conversar EN VIVO (stream SSE).                     │
└──────────────────────────────────────────────────────────────────┘
            │  POST /api/investigar  (server/app.py, FastAPI)
            ▼
┌──────────────────────────────────────────────────────────────────┐
│  MESA  ·  mesa/                                                     │
│  ┌──────────────┐   lee/escribe   ┌───────────────────────────┐   │
│  │ Orquestador  │ ───────────────▶│  Pizarra (blackboard)     │   │
│  │ conduce las  │ ◀─────────────── │  proyecto + mensajes +    │   │
│  │ fases y los  │                  │  hallazgos compartidos    │   │
│  │ handoffs     │                  └───────────────────────────┘   │
│  └──────┬───────┘                                                  │
│         │ da turnos                                                 │
│         ▼                                                           │
│   🧭 Metodólogo   🔎 Crítico   📖 Intérprete   🗂️ Bibliógrafo       │
│         │ cada agente: lee la pizarra · consulta RAG · lee         │
│         │ evidencia de herramientas · puede HANDOFF a un colega    │
└─────────┼───────────────────────────┬──────────────────────────────┘
          ▼                           ▼
┌────────────────────┐     ┌─────────────────────────────────────────┐
│ La Cueva-LM (RAG)  │     │  Motor econométrico (econ/) — HÍBRIDO     │
│ rag/_indice + RAG  │     │  series.py: 820+ series (Trabajo Final +  │
│ mesa/rag_cliente   │     │  MATRIZ ARG)                              │
│ → pasajes citados  │     │  herramientas.py: ADF/KPSS, Granger, OLS, │
│                    │     │  VAR, VECM, GARCH  (se ejecutan de verdad)│
└────────────────────┘     └─────────────────────────────────────────┘
```

## Cómo "conversan" los agentes

El mecanismo que hace que los agentes hablen entre sí es la **Pizarra** + los **handoffs**:

1. Todos los agentes leen la **misma pizarra**: ven la pregunta, los mensajes previos de los
   demás y los hallazgos ya fijados. Por eso cada intervención responde a la conversación, no
   ocurre en el vacío.
2. Cuando un agente necesita algo de otro, cierra su mensaje con:
   `HANDOFF: <id_agente> :: <pregunta concreta>`.
   El orquestador lo detecta y **le da el turno al agente interpelado**, que responde mirando la
   pregunta. Esto encadena diálogos reales (con un límite de profundidad para que no se vaya de
   mano).
3. El **Orquestador** marca el ritmo: abre cada fase, ejecuta las herramientas de esa fase,
   reparte los turnos según un guion y al final **fija un hallazgo** que sintetiza lo discutido.

## El pipeline (fases)

| Fase | Qué se ejecuta | Quién habla |
|------|----------------|-------------|
| 🎯 Encuadre | — | Metodólogo propone método; Bibliógrafo trae antecedentes |
| 🔍 Exploratorio | `describir` por serie | Crítico mira forma/huecos/outliers |
| 🧪 Control | `estacionariedad` por serie + `vecm` (Johansen) | Crítico diagnostica; Metodólogo fija el método |
| 📐 Modelización | `ols` / `var` / `vecm` / `garch` según el control | Metodólogo evalúa la especificación |
| 📖 Interpretación | (lee la evidencia) | Intérprete traduce a economía; Crítico audita |
| 🏁 Conclusiones | (síntesis) | Intérprete responde la pregunta con límites |

## Modo híbrido (ejecución)

- Lo **estándar** se ejecuta de verdad (`econ/herramientas.py`): los tests y modelos corren
  sobre las series reales y los agentes leen el output como evidencia.
- Lo **no estándar** (algo fuera del registro de herramientas) no se inventa: el agente lo
  detecta, asesora cómo encararlo y, si hace falta, pide confirmación para programarlo a medida.

## Modo offline

Sin `ANTHROPIC_API_KEY` la plataforma **igual funciona de punta a punta**: la orquestación, el
RAG y la econometría corren; los agentes devuelven una *maqueta* de su intervención (marcada como
MODO OFFLINE) en lugar de la redacción real de Claude. Cargás la clave y los mismos turnos pasan
a ser respuestas fundamentadas reales. Ideal para desarrollar y testear sin gastar tokens.

## Mapa de archivos (desde 2026-07-04: paquete único `cueva/` por capas)

```
cueva/
  config.py            rutas a datos (autodetecta Trabajo Final + MATRIZ ARG) y modelo/clave
  llm/
    gateway.py         ÚNICO punto de salida a LLMs: Gemini > Claude > offline, backoff 429
    presupuesto.py     ContadorTokens por sesión (límite de llamadas + telemetría)
  datos/series.py      catálogo unificado de series + carga/panel (caché auto-invalidante)
  econometria/
    herramientas.py    ADF/KPSS, Granger, OLS, VAR, VECM, GARCH (registro híbrido)
  conocimiento/
    ingesta.py         corpus → indice/ (fragmentos + TF-IDF sin pickle + embeddings)
    recuperar.py       pregunta → pasajes citados
    fichas.py          fichas metodológicas (el ingrediente secreto)
  agentes/
    modelos.py         Proyecto, Mensaje (handoff tipado, estado), Hallazgo, FASES
    pizarra.py         el blackboard compartido (serializable, schema v2)
    agentes.py         clase base + Metodólogo, Crítico, Intérprete, Bibliógrafo, Líder
    orquestador.py     conduce la conversación (generador que streamea) + presupuesto
  sesiones/
    repositorio.py     cargar/guardar pizarras con lock por proyecto y borrado suave
  api/
    esquemas.py        contratos Pydantic de entrada (límites de tamaño)
    app.py             FastAPI /api/v1 (endpoints + SSE + errores uniformes)
web/index.html         UI de la Mesa de Trabajo
scripts/               mesa_cli.py · ingestar.py · preguntar.py · metodologo.py
tests/                 suite offline (series sintéticas; corre en CI sin claves)
```

## Próximos pasos (roadmap completo en docs/PROPUESTA_ARQUITECTURA.md)

- **Fase 2 — agentes v2**: definiciones de agentes desde `knowledge-base/skills/`
  (retira `grafo_cueva.py`/LangGraph), tool-use real (function calling) con lista blanca,
  SSE tipado, transcript por sesión.
- **Fase 3 — conocimiento**: ingesta incremental con manifiesto, subida de PDFs del usuario
  (colección separada con provenance), evaluación de retrieval con preguntas doradas.
- **Fase 4 — escala web**: SQLite tras el repositorio, job queue, auth, Docker + deploy.
