"""Tests de La Cueva-LM con un índice temporal (TF-IDF sin pickle, sin torch)."""

from cueva.conocimiento import buscar, contexto_citado, indice_disponible


def test_indice_disponible(indice_temporal):
    assert indice_disponible()
    # el índice nuevo NO contiene pickle
    assert not list(indice_temporal.glob("*.pkl"))
    assert (indice_temporal / "tfidf.json").exists()
    assert (indice_temporal / "tfidf_matriz.npz").exists()


def test_buscar_recupera_lo_relevante(indice_temporal):
    pasajes = buscar("cointegracion johansen relacion de largo plazo", k=3)
    assert pasajes, "debería recuperar pasajes"
    assert pasajes[0].fuente == "cointegracion"

    pasajes = buscar("volatilidad condicional garch", k=3)
    assert pasajes[0].fuente == "volatilidad"


def test_contexto_citado_formatea(indice_temporal):
    texto, citas = contexto_citado("modelo VECM series integradas", k=2)
    assert texto.startswith("[")
    assert citas and all(isinstance(c, str) for c in citas)


def test_sin_indice_devuelve_vacio(tmp_path, monkeypatch):
    from cueva.conocimiento import recuperar

    monkeypatch.setenv("CUEVA_INDICE", str(tmp_path / "no_existe"))
    recuperar.limpiar_cache()
    try:
        assert not indice_disponible()
        assert buscar("lo que sea") == []
        assert contexto_citado("lo que sea") == ("", [])
    finally:
        recuperar.limpiar_cache()


def test_fichas_relevantes_reales():
    """Las fichas del repo (knowledge-base/fichas/) se eligen por vocabulario."""
    from cueva.conocimiento import fichas_relevantes

    fichas = fichas_relevantes("cointegración relación de largo plazo entre series", n=3)
    assert fichas, "debería encontrar fichas"
    assert any("cointegracion" in nombre for nombre, _ in fichas)
