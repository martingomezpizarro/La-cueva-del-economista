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

## Mapa de archivos

```
config.py              rutas a datos (autodetecta Trabajo Final + MATRIZ ARG) y modelo/clave
mesa/
  modelos.py           Proyecto, Mensaje, Hallazgo, FASES
  pizarra.py           el blackboard compartido
  llm.py               wrapper de Claude + modo offline
  rag_cliente.py       consulta a La Cueva-LM (índice existente)
  agentes.py           clase base + Metodólogo, Crítico, Intérprete, Bibliógrafo
  orquestador.py       conduce la conversación (generador que streamea)
econ/
  series.py            catálogo unificado de series + carga/panel
  herramientas.py      ADF/KPSS, Granger, OLS, VAR, VECM, GARCH (registro híbrido)
server/
  app.py               FastAPI (endpoints + SSE)
  static/index.html    UI de la Mesa de Trabajo
mesa_cli.py            correr una sesión desde la terminal
```

## Próximos pasos sugeridos

- **Bibliógrafo del usuario**: endpoint para subir PDFs propios → `rag/ingest.py` → reindex, y
  que el Bibliógrafo los priorice en sus búsquedas.
- **Tool-use real de Claude**: dejar que el agente elija y parametrice la herramienta (function
  calling) en lugar del guion por fase.
- **Persistencia de sesiones**: guardar/recuperar pizarras (`Pizarra.guardar`) y un historial.
- **Integrar el visualizador**: embeber `visualizador.html` del Trabajo Final como pestaña para
  ver y transformar las series que la mesa está discutiendo.
```
