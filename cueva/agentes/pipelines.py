"""pipelines — los guiones de la mesa como DATO, no como código.

Un pipeline es una lista de turnos: en qué fase habla qué agente, con qué tarea, si
recibe la evidencia econométrica de la fase y si puede PEDIR herramientas (function
calling). Editar/agregar un guion no requiere tocar el orquestador.

- "clasica": la mesa de 4 profesores + Metodólogo con tool-use en modelización.
- "equipo_completo": los 10 especialistas de knowledge-base/skills/ (reemplaza al viejo
  pipeline LangGraph de grafo_cueva.py, retirado en fase 2).
"""

from __future__ import annotations

# Cada turno: fase (de modelos.FASES) · agente (id de skills) · tarea · flags
PIPELINES: dict[str, list[dict]] = {
    "clasica": [
        {
            "fase": "encuadre",
            "agente": "metodologo",
            "tarea": "Aterrizá la pregunta en un diseño econométrico: ¿qué familia de modelos es candidata "
            "y por qué? Nombrá los 2-3 supuestos críticos a verificar antes de avanzar.",
        },
        {
            "fase": "encuadre",
            "agente": "bibliografo",
            "tarea": "¿Qué antecedentes o definiciones de la bibliografía respaldan o matizan el enfoque propuesto?",
        },
        {
            "fase": "exploratorio",
            "agente": "critico",
            "evidencia": True,
            "tarea": "Mirá la evidencia descriptiva: forma, escala, posibles huecos/outliers/estacionalidad. "
            "¿Qué hay que tratar antes de testear o modelar?",
        },
        {
            "fase": "control",
            "agente": "critico",
            "evidencia": True,
            "tarea": "Leé los tests de estacionariedad y la prueba de cointegración. ¿Qué órdenes de integración hay? "
            "¿Riesgo de regresión espuria? ¿Hace falta diferenciar o usar marco de cointegración?",
        },
        {
            "fase": "control",
            "agente": "metodologo",
            "tarea": "Dado el control de series, fijá el método a estimar (en niveles, diferencias, VECM/ARDL) "
            "y justificá el orden de los pasos.",
        },
        {
            "fase": "modelizacion",
            "agente": "metodologo",
            "evidencia": True,
            "herramientas": True,
            "tarea": "Comentá la estimación obtenida: ¿el modelo quedó bien especificado? ¿qué validar todavía? "
            "Si te falta evidencia (otro test, otra especificación), PEDILA con tus herramientas.",
        },
        {
            "fase": "interpretacion",
            "agente": "interprete",
            "evidencia": True,
            "tarea": "Traducí los resultados a economía: signo, magnitud y significancia de lo relevante, "
            "conectándolo con la pregunta y las hipótesis. Citá la bibliografía que respalda la lectura.",
        },
        {
            "fase": "interpretacion",
            "agente": "critico",
            "tarea": "Auditá la interpretación: ¿la evidencia la sostiene o se está sobre-leyendo? "
            "¿algún diagnóstico pendiente (autocorrelación, estabilidad, espuria) que la debilite?",
        },
        {
            "fase": "conclusiones",
            "agente": "interprete",
            "tarea": "Redactá una respuesta provisoria a la pregunta de investigación a partir de los hallazgos "
            "fijados, separando lo que la evidencia sostiene de lo conjetural, y nombrando límites.",
        },
    ],
    "equipo_completo": [
        {
            "fase": "encuadre",
            "agente": "lider",
            "tarea": "Confirmá la pregunta, ordená objetivos e hipótesis y proponé el método candidato y el orden de trabajo.",
        },
        {
            "fase": "exploratorio",
            "agente": "curador_datos",
            "evidencia": True,
            "tarea": "Revisá la calidad y forma de las series (rango, escala, huecos, outliers) y advertí qué cuidar antes de modelar.",
        },
        {
            "fase": "exploratorio",
            "agente": "transformaciones",
            "evidencia": True,
            "tarea": "Recomendá las transformaciones necesarias (log, diferencias, desestacionalizar, deflactar, frecuencia) según la evidencia.",
        },
        {
            "fase": "control",
            "agente": "multivariados",
            "evidencia": True,
            "tarea": "Con los tests de estacionariedad y Johansen, decidí el modelo (niveles/diferencias/VECM) y justificá.",
        },
        {
            "fase": "control",
            "agente": "critico",
            "tarea": "Auditá lo dicho hasta acá: buscá raíz unitaria ignorada, espuria, quiebres o autocorrelación, y proponé cómo mitigar.",
        },
        {
            "fase": "modelizacion",
            "agente": "volatilidad",
            "evidencia": True,
            "tarea": "Evaluá si hay heterocedasticidad/volatilidad condicional relevante (GARCH) en la dependiente y qué implica.",
        },
        {
            "fase": "modelizacion",
            "agente": "pronostico_ml",
            "tarea": "Proponé un esquema de pronóstico y su evaluación fuera de muestra (benchmark naive, ARIMA/ETS, ML) si la pregunta lo amerita.",
        },
        {
            "fase": "modelizacion",
            "agente": "controles_causal",
            "evidencia": True,
            "tarea": "Con Granger y el marco causal, distinguí precedencia predictiva de causalidad y advertí qué controles harían falta.",
        },
        {
            "fase": "modelizacion",
            "agente": "robustez",
            "evidencia": True,
            "tarea": "Revisá la robustez de los resultados (especificaciones alternativas, sensibilidad, ajuste múltiple) y señalá fragilidades.",
        },
        {
            "fase": "interpretacion",
            "agente": "interprete",
            "evidencia": True,
            "tarea": "Traducí la evidencia y los modelos a economía clara: signos, magnitudes, largo plazo y conexión con la hipótesis.",
        },
        {
            "fase": "conclusiones",
            "agente": "lider",
            "tarea": "Sintetizá la respuesta a la pregunta de investigación, los límites del análisis y el próximo paso concreto.",
        },
    ],
}


def turnos_de(pipeline: str, fase: str) -> list[dict]:
    return [t for t in PIPELINES.get(pipeline, []) if t["fase"] == fase]
