"""Tests del gateway LLM: modo offline, backoff ante 429 y presupuesto (sin red)."""

import pytest

from cueva.llm import ContadorTokens, completar
from cueva.llm import gateway as G


def test_offline_sin_claves(sin_llm):
    r = completar("Sos el Metodólogo.", "¿Qué método uso?")
    assert r.estado == "offline"
    assert r.backend == "offline"
    assert "MODO OFFLINE" in r.texto
    assert "Metodólogo" in r.texto  # la maqueta identifica el rol


def test_offline_rescata_citas(sin_llm):
    r = completar("Sos el Crítico.", "[Enders p.69] la raíz unitaria...\n[Tsay p.12] otra cosa")
    assert "[Enders p.69]" in r.texto


def test_backoff_reintenta_429(monkeypatch):
    """Dos 429 seguidos y después éxito: el gateway debe reintentar y terminar ok."""
    monkeypatch.setenv("GEMINI_API_KEY", "clave-de-prueba")
    intentos = {"n": 0}

    def falso_llamar(back, system, messages, max_tokens, temperatura):
        intentos["n"] += 1
        if intentos["n"] < 3:
            raise RuntimeError("429 RESOURCE_EXHAUSTED: quota exceeded")
        return G.Respuesta(texto="listo", backend=back, modelo="fake", tokens_entrada=10, tokens_salida=5)

    monkeypatch.setattr(G, "_llamar", falso_llamar)
    monkeypatch.setattr(G.time, "sleep", lambda s: None)

    contador = ContadorTokens()
    r = completar("sys", "hola", contador=contador)
    assert r.estado == "ok"
    assert r.intentos == 3
    assert contador.llamadas == 1
    assert contador.tokens_entrada == 10


def test_error_definitivo_degrada_a_offline(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "clave-de-prueba")

    def falso_llamar(*a, **k):
        raise ValueError("API key not valid")  # no transitorio → sin reintentos

    monkeypatch.setattr(G, "_llamar", falso_llamar)
    contador = ContadorTokens()
    r = completar("sys", "hola", contador=contador)
    assert r.estado == "error"
    assert "MODO OFFLINE" in r.texto
    assert contador.errores == 1


def test_presupuesto_agotado(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "clave-de-prueba")
    contador = ContadorTokens(limite_llamadas=0)
    r = completar("sys", "hola", contador=contador)
    assert r.estado == "presupuesto"
    assert "PRESUPUESTO AGOTADO" in r.texto


@pytest.mark.parametrize(
    "mensaje,esperado",
    [
        ("429 too many requests", True),
        ("RESOURCE_EXHAUSTED", True),
        ("503 service unavailable", True),
        ("API key not valid", False),
    ],
)
def test_clasificacion_transitorios(mensaje, esperado):
    assert G._es_transitorio(RuntimeError(mensaje)) is esperado
