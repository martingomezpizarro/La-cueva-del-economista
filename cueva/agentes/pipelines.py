"""pipelines — los guiones de la mesa como DATO, no como código.

Un pipeline es una lista de turnos: en qué fase habla qué agente, con qué tarea, si
recibe la evidencia econométrica de la fase y si puede PEDIR herramientas (function
calling). Editar/agregar un guion no requiere tocar el orquestador.

- "clasica": la mesa de 4 profesores; tool-use del Metodólogo (modelización) y del
  Crítico (auditoría de la interpretación).
- "equipo_completo": los 10 especialistas de knowledge-base/skills/ (reemplaza al viejo
  pipeline LangGraph de grafo_cueva.py, retirado en fase 2); tool-use en los turnos de
  multivariados, volatilidad, controles_causal y robustez.

Regla de consistencia (la vigila un test): un turno con `herramientas: True` solo tiene
sentido si el agente declara en su skill herramientas que EXISTEN en el REGISTRO.
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
            "evidencia": True,
            "herramientas": True,
            "tarea": "Auditá la interpretación: ¿la evidencia la sostiene o se está sobre-leyendo? "
            "Si falta un diagnóstico (autocorrelación, estabilidad, espuria), PEDILO con tus "
            "herramientas antes de dar el veredicto.",
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
            "herramientas": True,
            "tarea": "Con los tests de estacionariedad y Johansen, decidí el modelo (niveles/diferencias/VECM) y justificá. "
            "Si te falta un test (otra serie, otra diferencia), PEDILO con tus herramientas.",
        },
        {
            "fase": "control",
            "agente": "critico",
            "evidencia": True,
            "tarea": "Auditá lo dicho hasta acá: buscá raíz unitaria ignorada, espuria, quiebres o autocorrelación, y proponé cómo mitigar.",
        },
        {
            "fase": "modelizacion",
            "agente": "volatilidad",
            "evidencia": True,
            "herramientas": True,
            "tarea": "Evaluá si hay heterocedasticidad/volatilidad condicional relevante en la dependiente: "
            "PEDÍ arch_lm para testear efectos ARCH y, solo si los hay, un GARCH.",
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
            "herramientas": True,
            "tarea": "Con Granger y el marco causal, distinguí precedencia predictiva de causalidad y advertí qué controles "
            "harían falta. Si falta el test de Granger de algún par relevante, PEDILO.",
        },
        {
            "fase": "modelizacion",
            "agente": "robustez",
            "evidencia": True,
            "herramientas": True,
            "tarea": "Revisá la robustez de los resultados: probá al menos UNA especificación alternativa con tus "
            "herramientas (ols/diagnosticos) y señalá fragilidades y riesgo de ajuste múltiple.",
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
