"""Tests de cueva.datos: catálogo, carga, panel y refresco del caché (bug B8)."""

import pandas as pd

from cueva.datos import series as S
from tests.conftest import N_OBS, _guardar


def test_catalogo_detecta_series(carpeta_series):
    cat = S.catalogo()
    assert set(cat) == {"caminata", "caminata2", "ar_uno", "coint_x", "coint_y"}
    info = cat["caminata"]
    assert info.n == N_OBS
    assert info.origen == "Trabajo Final"


def test_cargar_devuelve_serie_fechada(carpeta_series):
    s = S.cargar("caminata", freq="mensual")
    assert isinstance(s, pd.Series)
    assert isinstance(s.index, pd.DatetimeIndex)
    assert len(s) == N_OBS


def test_panel_alinea(carpeta_series):
    df = S.panel(["coint_x", "coint_y"], freq="mensual")
    assert list(df.columns) == ["coint_x", "coint_y"]
    assert len(df.dropna()) == N_OBS


def test_serie_desconocida(carpeta_series):
    import pytest

    with pytest.raises(KeyError):
        S.cargar("no_existe")


def test_cache_detecta_archivos_nuevos(carpeta_series):
    """B8: agregar un CSV nuevo no debe exigir reiniciar el proceso."""
    assert "nueva" not in S.catalogo()
    _guardar(carpeta_series, "nueva", list(range(20)))
    assert "nueva" in S.catalogo()


def test_listar_filtra(carpeta_series):
    assert [s["id"] for s in S.listar(filtro="coint")] == ["coint_x", "coint_y"]


# ── Catálogo curado (catalogo.json). No tocan disco de datos: leen el JSON del paquete. ──


def test_catalogo_curado_integridad():
    """El catálogo curado (fuente única) parsea, cubre las 9 familias y tiene ids únicos."""
    hojas = S._cargar_definicion_curada()
    assert len(hojas) > 500  # ~553 hojas migradas del visualizador
    ids = [h["id"] for h in hojas]
    assert len(ids) == len(set(ids)), "ids duplicados en catalogo.json"
    for h in hojas:
        assert h["grupo"], h  # toda hoja cuelga de una familia (el subgrupo puede faltar)
        assert h["fuentes"], h  # y tiene al menos una fuente
    # salvo las dummies (items a nivel familia), el resto cuelga de un subgrupo
    sin_sub = [h["id"] for h in hojas if not h["subgrupo"]]
    assert all(h["grupo"] == "Dummies y Variables Estructurales" for h in hojas if not h["subgrupo"]), sin_sub
    familias = {h["grupo"] for h in hojas}
    assert len(familias) == 9
    assert "Sector Externo" in familias and "Deuda y Riesgo Soberano" in familias


def test_fuente_para_freq_elige_la_mas_cercana():
    """Con varias fuentes, cargar elige la de frecuencia más próxima a la pedida."""
    info = S.SerieInfo(
        id="x",
        nombre="X",
        origen="Trabajo Final",
        archivo="m.csv",
        col_fecha="fecha",
        col_valor="y",
        n=10,
        desde="",
        hasta="",
        fuentes=[
            {"freq": "M", "path": "mensual.csv", "dateCol": "fecha", "valCol": "y"},
            {"freq": "Q", "path": "trim.csv", "dateCol": "fecha", "valCol": "y"},
        ],
    )
    assert S._fuente_para_freq(info, "mensual")["path"] == "mensual.csv"
    assert S._fuente_para_freq(info, "trimestral")["path"] == "trim.csv"
    assert S._fuente_para_freq(info, "anual")["path"] == "trim.csv"  # Q es la más cercana a A
