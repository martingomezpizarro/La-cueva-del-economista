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


def test_diagnosticos_limpios_dan_verde(carpeta_series):
    """coint_y = 2 + 0.8·coint_x + ruido iid POR CONSTRUCCIÓN → la batería no debe ver nada."""
    r = ejecutar("diagnosticos", dep="coint_y", indeps=["coint_x"])
    assert r["ok"]
    assert r["semaforo"] == "verde"
    assert r["banderas"] == []
    assert set(r["pvalores"]) == {
        "autocorrelación (Ljung-Box)",
        "autocorrelación (Breusch-Godfrey)",
        "heterocedasticidad (ARCH-LM)",
        "no normalidad (Jarque-Bera)",
        "especificación (RESET Ramsey)",
        "inestabilidad (CUSUM-OLS)",
    }


def test_diagnosticos_cazan_la_espuria(carpeta_series):
    """caminata ~ caminata2 son random walks INDEPENDIENTES: los residuos quedan I(1) y la
    batería tiene que gritar autocorrelación (el semáforo del Crítico en rojo)."""
    r = ejecutar("diagnosticos", dep="caminata", indeps=["caminata2"])
    assert r["ok"]
    assert r["semaforo"] == "rojo"
    assert "autocorrelación (Ljung-Box)" in r["banderas"]
    assert "autocorrelación (Breusch-Godfrey)" in r["banderas"]


def test_arch_lm_sin_efectos_arch(carpeta_series):
    """Los incrementos de la caminata son homocedásticos por construcción → sin efectos ARCH
    (la evidencia que le dice al especialista en volatilidad que un GARCH NO se justifica)."""
    r = ejecutar("arch_lm", sid="caminata")
    assert r["ok"]
    assert r["hay_arch"] is False
    assert r["p_valor"] > 0.05


def test_herramienta_desconocida_es_modo_asesor():
    r = ejecutar("magia_negra")
    assert not r["ok"]
    assert r.get("no_estandar") is True


def test_argumentos_invalidos_no_rompen(carpeta_series):
    r = ejecutar("estacionariedad", sid="caminata", argumento_falso=1)
    assert not r["ok"]
    assert "Argumentos inválidos" in r["resumen"]
