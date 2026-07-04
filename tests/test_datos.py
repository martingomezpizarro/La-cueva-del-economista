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
