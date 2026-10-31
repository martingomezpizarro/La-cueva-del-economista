"""Explorar nativo: resolución contra data/series, ficha, datos y estado por familia.

Usa ids REALES del catálogo (res_brutas: diaria, stock; res_mensual: mensual) con archivos
sintéticos en carpetas temporales — nunca la data/series real de la máquina.
"""

from __future__ import annotations

import pandas as pd
import pytest

from cueva.datos import series as S


def _csv(ruta, fechas, valores):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"fecha": fechas, "valor": valores}).to_csv(ruta, index=False, encoding="utf-8-sig")


@pytest.fixture()
def data_series(tmp_path, monkeypatch):
    raiz = tmp_path / "series"
    dias = pd.date_range("2020-01-01", "2020-03-31", freq="D")
    _csv(raiz / "bcra" / "0001_reservas_internacionales.csv", dias, range(len(dias)))
    meses = pd.date_range("1940-02-29", periods=24, freq="ME")
    _csv(raiz / "bcra" / "1605_reservas_internacionales.csv", meses, [100.0 + i for i in range(24)])
    monkeypatch.setenv("CUEVA_SERIES", str(raiz))
    S.refrescar()
    yield raiz
    S.refrescar()


def test_data_series_manda_sobre_el_trabajo_final(data_series, carpeta_series, monkeypatch):
    # el mismo archivo también en la carpeta del TF: tiene que ganar data/series
    _csv(
        carpeta_series / "1605_reservas_internacionales.csv",
        pd.date_range("2000-01-31", periods=12, freq="ME"),
        [1.0] * 12,
    )
    monkeypatch.setenv("CUEVA_SERIES", str(data_series))
    S.refrescar()
    info = S.catalogo()["res_mensual"]
    assert info.origen == S.ORIGEN_DATA_SERIES
    assert "series" in info.archivo


def test_las_carpetas_de_fuentes_no_se_leen(tmp_path, monkeypatch):
    raiz = tmp_path / "series"
    _csv(
        raiz / "Monetario_Fuentes" / "1605_reservas_internacionales.csv",
        pd.date_range("1940-02-29", periods=24, freq="ME"),
        range(24),
    )
    monkeypatch.setenv("CUEVA_SERIES", str(raiz))
    S.refrescar()
    assert "res_mensual" not in S.catalogo()


def test_lo_diario_viaja_mensual_con_fin_de_periodo(data_series):
    d = S.datos_explorar("res_brutas")
    assert d["frecuencia_nativa"] == "diaria"
    assert d["frecuencia_entrega"] == "M"
    assert d["agregacion"] == "ult"  # reservas es un stock
    assert d["fechas"] == ["2020-01-31", "2020-02-29", "2020-03-31"]
    assert d["valores"] == [30.0, 59.0, 90.0]  # último día de cada mes
    assert d["archivo"] == "bcra/0001_reservas_internacionales.csv"
    assert d["proc"]["fuente"] == "bcra"


def test_rango_real_y_no_el_del_encabezado(data_series):
    d = S.datos_explorar("res_mensual")
    assert d["desde"] == "1940-02-29" and d["hasta"] == "1942-01-31"
    assert len(d["valores"]) == 24


@pytest.mark.parametrize(
    ("etiqueta", "unidad", "esperado"),
    [
        ("Inflación mensual", "% mensual", "comp"),
        ("Tasa de plazo fijo a 30 días", "% TNA", "prom"),
        ("Reservas Brutas BCRA", "Mill. USD", "ult"),
        ("EMAE nivel general", "2004=100", "prom"),
    ],
)
def test_regla_de_agregacion(etiqueta, unidad, esperado):
    assert S.tipo_agregacion(etiqueta, unidad) == esperado


def test_resumen_por_familia_cuenta_lo_conectado(data_series):
    fams = {f["familia"]: f for f in S.resumen_familias()}
    mon = fams["Monetario y Cambiario"]
    assert mon["conectadas"] == 2 and mon["total"] > 2
    assert sum(f["total"] for f in fams.values()) == len(S._cargar_definicion_curada())


def test_api_datos_de_serie(cliente, data_series):
    r = cliente.get("/api/v1/series/res_mensual/datos")
    assert r.status_code == 200
    assert r.json()["unidad"] == "Mill. USD"
    assert cliente.get("/api/v1/series/no_existe/datos").status_code == 404
    fams = cliente.get("/api/v1/series/familias").json()
    assert fams[0]["familia"]


def test_la_mesa_monta_explorar_nativo(cliente):
    html = cliente.get("/mesa").text
    assert "/web/mesa/explorar.js" in html and "/web/mesa/explorar.css" in html
    assert 'id="viz-frame"' not in html  # el explorador clásico ya no va embebido
    assert cliente.get("/web/mesa/explorar.js").status_code == 200
    assert cliente.get("/explorador").status_code in (200, 500)  # sigue existiendo su ruta
