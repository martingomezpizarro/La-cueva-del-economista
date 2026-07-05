"""Tests del bucle de function calling del gateway (sin red: backend simulado)."""

from cueva.llm import ContadorTokens, conversar_con_herramientas
from cueva.llm import gateway as G

DECL = [
    {
        "name": "estacionariedad",
        "description": "ADF/KPSS",
        "parameters_json_schema": {"type": "object", "properties": {"sid": {"type": "string"}}},
    }
]


def _respuesta_texto(texto="listo, con la evidencia pedida concluyo X"):
    return G.Respuesta(texto=texto, backend="gemini", modelo="fake", tokens_entrada=10, tokens_salida=5)


def _respuesta_con_llamada(nombre="estacionariedad", args=None):
    return G.Respuesta(
        texto="",
        backend="gemini",
        modelo="fake",
        tokens_entrada=10,
        tokens_salida=5,
        llamadas_funcion=[{"name": nombre, "args": args or {"sid": "caminata"}}],
        _partes_crudas=[],
    )


def test_bucle_pide_ejecuta_y_responde(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "clave-de-prueba")
    secuencia = [_respuesta_con_llamada(), _respuesta_texto()]
    monkeypatch.setattr(G, "_llamar", lambda *a, **k: secuencia.pop(0))

    ejecutadas = []

    def ejecutar_fn(nombre, args):
        ejecutadas.append((nombre, args))
        return {"ok": True, "herramienta": nombre, "resumen": "ADF p=0.9 → I(1)"}

    contador = ContadorTokens()
    r, resultados = conversar_con_herramientas(
        "sys",
        [{"role": "user", "content": "analizá"}],
        declaraciones=DECL,
        ejecutar_fn=ejecutar_fn,
        contador=contador,
    )
    assert r.estado == "ok"
    assert "concluyo" in r.texto
    assert ejecutadas == [("estacionariedad", {"sid": "caminata"})]
    assert len(resultados) == 1
    assert contador.llamadas == 2  # una ronda con pedido + una con respuesta final


def test_tope_de_herramientas(monkeypatch):
    """El modelo pide sin parar: el gateway corta en max_herramientas y fuerza texto."""
    monkeypatch.setenv("GEMINI_API_KEY", "clave-de-prueba")

    def siempre_pide(back, system, contents, max_tokens, temperatura, **kwargs):
        # cuando ya no se le ofrecen herramientas, el modelo responde texto
        if not kwargs.get("herramientas"):
            return _respuesta_texto("me quedo con lo que tengo")
        return _respuesta_con_llamada()

    monkeypatch.setattr(G, "_llamar", siempre_pide)

    n = {"ejecutadas": 0}

    def ejecutar_fn(nombre, args):
        n["ejecutadas"] += 1
        return {"ok": True, "resumen": "r"}

    r, resultados = conversar_con_herramientas(
        "sys",
        [{"role": "user", "content": "x"}],
        declaraciones=DECL,
        ejecutar_fn=ejecutar_fn,
        max_herramientas=2,
    )
    assert n["ejecutadas"] == 2  # tope duro
    assert r.estado == "ok" and r.texto


def test_offline_no_usa_herramientas(sin_llm):
    r, resultados = conversar_con_herramientas(
        "sys",
        [{"role": "user", "content": "x"}],
        declaraciones=DECL,
        ejecutar_fn=lambda *a: {"ok": True},
    )
    assert r.estado == "offline"
    assert resultados == []


def test_transcript_registra_las_llamadas(tmp_path, sin_llm):
    from cueva.llm import Transcript, completar

    t = Transcript(tmp_path / "t.jsonl")
    completar("sys", "hola", transcript=t)
    completar("sys", "chau", transcript=t)

    import json

    lineas = [json.loads(x) for x in (tmp_path / "t.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(lineas) == 2
    assert lineas[0]["estado"] == "offline"
    assert lineas[0]["usuario"] == "hola"
