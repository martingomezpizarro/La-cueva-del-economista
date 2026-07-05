"""Test de la mesa completa en modo offline (determinista, $0, sin red).

Es el smoke test de integración que corre en CI: valida orquestación, herramientas
reales sobre series sintéticas, y la regresión del bug B1 (con un par cointegrado la
mesa DEBE ver el resultado de Johansen y elegir VECM en la modelización).
"""

from cueva.agentes import Orquestador, Proyecto, investigar


def _proyecto_cointegrado():
    return Proyecto(
        titulo="Test cointegración",
        pregunta="¿coint_x explica a coint_y en el largo plazo?",
        series=["coint_x", "coint_y"],
        serie_dependiente="coint_y",
        frecuencia="mensual",
    )


def test_mesa_completa_offline(sin_llm, carpeta_series):
    piz = investigar(_proyecto_cointegrado())

    # corrió las 6 fases y fijó un hallazgo por fase
    fases_hallazgos = [h.fase for h in piz.hallazgos]
    assert fases_hallazgos == [
        "encuadre",
        "exploratorio",
        "control",
        "modelizacion",
        "interpretacion",
        "conclusiones",
    ]

    # en modo offline los agentes lo dicen (degradación visible, no silencio)
    agentes = [m for m in piz.mensajes if m.autor in ("metodologo", "critico", "interprete", "bibliografo")]
    assert agentes and all(m.estado == "offline" for m in agentes)

    # el presupuesto quedó registrado (0 llamadas reales)
    assert piz.uso_llm["llamadas"] == 0


def test_evidencia_vecm_no_se_pierde(sin_llm, carpeta_series):
    """Regresión del bug B1: el resultado de Johansen debe quedar en la pizarra…"""
    piz = investigar(_proyecto_cointegrado())
    evidencia_control = [
        r for m in piz.mensajes if m.autor == "herramientas" and m.fase == "control" for r in m.herramientas
    ]
    vecm = [r for r in evidencia_control if r.get("herramienta") == "vecm"]
    assert vecm, "la prueba de cointegración desapareció de la evidencia (bug B1)"
    assert vecm[0]["rango_cointegracion"] >= 1


def test_con_cointegracion_la_mesa_elige_vecm(sin_llm, carpeta_series):
    """…y la modelización debe estimar VECM (no caer a OLS/VAR)."""
    piz = investigar(_proyecto_cointegrado())
    evidencia_modelizacion = [
        r
        for m in piz.mensajes
        if m.autor == "herramientas" and m.fase == "modelizacion"
        for r in m.herramientas
    ]
    assert evidencia_modelizacion, "la modelización no ejecutó ninguna herramienta"
    assert evidencia_modelizacion[0]["herramienta"] == "vecm"


def test_sin_cointegracion_no_fuerza_vecm(sin_llm, carpeta_series):
    """Con dos caminatas INDEPENDIENTES (rango de Johansen = 0) la modelización usa OLS/VAR.

    Nota: no sirve mezclar una I(1) con una I(0) — si una variable ya es estacionaria,
    Johansen encuentra rango ≥ 1 trivialmente (esa dirección estacionaria existe)."""
    piz = investigar(
        Proyecto(
            titulo="Sin relación",
            pregunta="¿algo?",
            series=["caminata", "caminata2"],
            serie_dependiente="caminata",
        )
    )
    evidencia = [
        r
        for m in piz.mensajes
        if m.autor == "herramientas" and m.fase == "modelizacion"
        for r in m.herramientas
    ]
    assert evidencia
    assert evidencia[0]["herramienta"] in ("ols", "var")


def test_modo_lider_revisar(sin_llm, carpeta_series):
    orq = Orquestador(_proyecto_cointegrado())
    orq.piz.agregar_nota("elegí las series y quiero modelar ya")
    mensajes = list(orq.revisar("el usuario quiere saltear el control de series"))
    assert mensajes and mensajes[0].autor == "lider"


def test_pipeline_equipo_completo_offline(sin_llm, carpeta_series):
    """El guion de 10 especialistas (ex grafo_cueva.py) corre como dato del orquestador."""
    piz = investigar(_proyecto_cointegrado(), pipeline="equipo_completo")
    autores = {m.autor for m in piz.mensajes}
    assert {"lider", "curador_datos", "multivariados", "interprete"} <= autores
    assert [h.fase for h in piz.hallazgos] == [
        "encuadre",
        "exploratorio",
        "control",
        "modelizacion",
        "interpretacion",
        "conclusiones",
    ]


def test_pipeline_desconocido():
    import pytest

    with pytest.raises(ValueError):
        Orquestador(_proyecto_cointegrado(), pipeline="inventado")


def test_transcript_de_la_mesa(sin_llm, carpeta_series):
    """Cada sesión deja su transcript JSONL auditable (también en modo offline)."""
    import json
    import os
    from pathlib import Path

    orq = Orquestador(_proyecto_cointegrado())
    for _ in orq.correr():
        pass
    ruta = Path(os.environ["CUEVA_DATA"]) / "proyectos" / f"{orq.piz.id}.transcript.jsonl"
    assert ruta.exists()
    lineas = [json.loads(x) for x in ruta.read_text(encoding="utf-8").splitlines()]
    assert len(lineas) >= 10  # un evento por turno de agente + hallazgos
    assert all("system" in ln and "respuesta" in ln for ln in lineas)


def test_handoff_tipado(sin_llm, carpeta_series):
    """El handoff es un campo de primera clase del mensaje (bug B9)."""
    from cueva.agentes.agentes import _HANDOFF_RE

    m = _HANDOFF_RE.search("Mi análisis...\nHANDOFF: critico :: ¿ves riesgo de espuria?")
    assert m and m.group(1) == "critico"
