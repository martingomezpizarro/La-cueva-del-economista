"""Tests de cueva.econometria sobre series sintéticas de propiedades CONOCIDAS.

Estos tests convierten el conocimiento econométrico en guardarraíl: si un refactor
rompe la lectura de un test o la elección de modelo, acá se ve en rojo.
"""

from cueva.econometria import ejecutar


def test_estacionariedad_random_walk_es_i1(carpeta_series):
    r = ejecutar("estacionariedad", sid="caminata")
    assert r["ok"]
    assert "NO estacionaria" in r["conclusion"]


def test_estacionariedad_ar1_es_estacionaria(carpeta_series):
    r = ejecutar("estacionariedad", sid="ar_uno")
    assert r["ok"]
    assert r["conclusion"] == "estacionaria"


def test_random_walk_diferenciada_es_estacionaria(carpeta_series):
    r = ejecutar("estacionariedad", sid="caminata", dif=1)
    assert r["ok"]
    assert r["conclusion"] == "estacionaria"


def test_vecm_detecta_cointegracion(carpeta_series):
    """El par (coint_x, coint_y) cointegra POR CONSTRUCCIÓN → Johansen debe verlo."""
    r = ejecutar("vecm", sids=["coint_x", "coint_y"])
    assert r["ok"]
    assert r["rango_cointegracion"] >= 1


def test_ols_devuelve_contrato(carpeta_series):
    r = ejecutar("ols", dep="coint_y", indeps=["coint_x"])
    assert r["ok"]
    assert 0 <= r["r2"] <= 1
    assert "coint_x" in r["coeficientes"]


def test_describir(carpeta_series):
    r = ejecutar("describir", sid="ar_uno")
    assert r["ok"]
    assert r["stats"]["n"] > 0


def test_herramienta_desconocida_es_modo_asesor():
    r = ejecutar("magia_negra")
    assert not r["ok"]
    assert r.get("no_estandar") is True


def test_argumentos_invalidos_no_rompen(carpeta_series):
    r = ejecutar("estacionariedad", sid="caminata", argumento_falso=1)
    assert not r["ok"]
    assert "Argumentos inválidos" in r["resumen"]
