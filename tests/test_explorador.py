"""Tests del explorador nativo y del banco de trabajo (pestaña Estudio).

Cubre: el payload de datos columnares (ex EMBEDDED), las herramientas nuevas/ampliadas
(transformaciones, OLS con rezagos, correlaciones, ARIMA), los estudios persistidos con
resultado completo y la creación de proyecto con semilla (promover Vista Rápida).
"""

from __future__ import annotations

import pytest

from cueva.datos import explorador_datos
from cueva.econometria import herramientas as H


@pytest.fixture()
def catalogo_sintetico(carpeta_series, monkeypatch):
    """Hace que el catálogo curado apunte a una serie sintética del fixture."""
    hojas = [
        {
            "id": "caminata",
            "etiqueta": "Caminata sintética",
            "unidad": "",
            "grupo": "Test",
            "subgrupo": "Sintéticas",
            "fuentes": [{"freq": "M", "file": "caminata.csv", "dateCol": "fecha", "valCol": "valor"}],
        }
    ]
    monkeypatch.setattr(explorador_datos, "_cargar_definicion_curada", lambda: hojas)
    explorador_datos.refrescar()
    yield
    explorador_datos.refrescar()


# ── payload de datos del explorador (el viejo EMBEDDED, servido en vivo) ────


def test_payload_explorador_incluye_archivos_del_catalogo(catalogo_sintetico):
    datos = explorador_datos.payload()
    assert "caminata.csv" in datos
    cols = datos["caminata.csv"]
    assert set(cols) == {"fecha", "valor"}
    assert len(cols["fecha"]) == len(cols["valor"]) == 150
    assert isinstance(cols["valor"][0], float)


def test_payload_explorador_sin_carpeta_tf(monkeypatch):
    # sin carpeta de datos, el payload es vacío (la SPA cae al fallback estático)
    monkeypatch.setattr(explorador_datos, "_carpeta_vars", lambda: None)
    explorador_datos.refrescar()
    assert explorador_datos.payload() == {}
    explorador_datos.refrescar()


def test_endpoint_datos_explorador(cliente):
    r = cliente.get("/api/v1/explorador/datos")
    assert r.status_code == 200
    assert isinstance(r.json(), dict)


def test_explorador_html_servido(cliente):
    r = cliente.get("/explorador")
    assert r.status_code == 200
    assert "Estudio" in r.text  # la pestaña del banco de trabajo está en la SPA
    assert "/api/v1/explorador/datos" in r.text  # y pide los datos a la API


# ── transformaciones como parámetro (pendiente P2 de la auditoría) ──────────


def test_transformacion_dif_vuelve_estacionaria_la_caminata(carpeta_series):
    nivel = H.estacionariedad("caminata")
    dif = H.estacionariedad("caminata", transf="dif")
    assert nivel["ok"] and dif["ok"]
    assert "NO estacionaria" in nivel["conclusion"]
    assert dif["conclusion"] == "estacionaria"
    assert dif["args"]["transf"] == "dif"


def test_transformacion_desconocida_es_error_legible(carpeta_series):
    r = H.describir("caminata", transf="cuadrada")
    assert r["ok"] is False
    assert "Transformación desconocida" in r["resumen"]


def test_describir_trae_grafico_y_percentiles(carpeta_series):
    r = H.describir("caminata")
    assert r["ok"]
    assert r["stats"]["p25"] <= r["stats"]["mediana"] <= r["stats"]["p75"]
    g = r["grafico"]
    assert g["tipo"] == "linea" and len(g["fechas"]) > 100


# ── OLS completo: rezagos, tabla de coeficientes y gráfico ──────────────────


def test_ols_con_rezagos_y_grafico(carpeta_series):
    r = H.ols("coint_y", ["coint_x"], rezagos=1, rezagos_dep=1)
    assert r["ok"]
    variables = {f["variable"] for f in r["tabla_coeficientes"]}
    assert {"const", "coint_x", "coint_x_L1", "coint_y_L1"} <= variables
    g = r["grafico"]
    assert g["tipo"] == "ajuste"
    assert len(g["observado"]) == len(g["ajustado"]) == len(g["residuos"]) == len(g["fechas"])
    assert r["n"] == len(g["observado"])


# ── correlaciones y ARIMA (herramientas nuevas del banco de trabajo) ────────


def test_correlaciones_cointegradas_alta(carpeta_series):
    r = H.correlaciones(["coint_x", "coint_y"])
    assert r["ok"]
    assert r["matriz"]["coint_x"]["coint_y"] > 0.9
    assert r["grafico"]["tipo"] == "matriz_corr"


def test_arima_pronostica_el_horizonte_pedido(carpeta_series):
    r = H.arima("ar_uno", horizonte=6)
    assert r["ok"], r["resumen"]
    p = r["pronostico"]
    assert len(p["fechas"]) == len(p["media"]) == 6
    assert all(li <= m <= ls for li, m, ls in zip(p["li_95"], p["media"], p["ls_95"], strict=True))


# ── estudios persistidos con resultado + borrado ────────────────────────────


def test_herramienta_con_proyecto_persiste_resultado_completo(cliente):
    pid = cliente.post("/api/v1/proyectos", json={"titulo": "Con estudios"}).json()["id"]
    r = cliente.post(
        "/api/v1/herramienta",
        json={"nombre": "describir", "args": {"sid": "caminata"}, "proyecto_id": pid},
    ).json()
    assert r["ok"] and "estudio_id" in r

    piz = cliente.get(f"/api/v1/proyectos/{pid}").json()
    assert len(piz["estudios"]) == 1
    est = piz["estudios"][0]
    assert est["id"] == r["estudio_id"]
    assert est["resultado"]["stats"]["n"] == 150  # evidencia completa, no solo el resumen

    # borrar el estudio
    assert cliente.delete(f"/api/v1/proyectos/{pid}/estudios/{est['id']}").json() == {"ok": True}
    assert cliente.get(f"/api/v1/proyectos/{pid}").json()["estudios"] == []
    # borrarlo de nuevo → 404
    assert cliente.delete(f"/api/v1/proyectos/{pid}/estudios/{est['id']}").status_code == 404


# ── promover Vista Rápida: crear proyecto con semilla ───────────────────────


def test_crear_proyecto_con_semilla_de_vista_rapida(cliente):
    cuerpo = {
        "titulo": "Promovida",
        "series": ["caminata", "ar_uno"],
        "serie_dependiente": "caminata",
        "frecuencia": "mensual",
        "estudios": [
            {
                "herramienta": "estacionariedad",
                "args": {"sid": "caminata", "transf": "dif"},
                "resumen": "caminata (Δ): estacionaria",
                "resultado": {"ok": True, "conclusion": "estacionaria"},
            }
        ],
    }
    r = cliente.post("/api/v1/proyectos", json=cuerpo)
    assert r.status_code == 200
    d = r.json()
    assert d["proyecto"]["titulo"] == "Promovida"
    assert d["proyecto"]["series"] == ["caminata", "ar_uno"]
    assert d["proyecto"]["serie_dependiente"] == "caminata"
    assert len(d["estudios"]) == 1
    assert d["estudios"][0]["herramienta"] == "estacionariedad"
    assert d["estudios"][0]["resultado"]["conclusion"] == "estacionaria"
    assert d["estudios"][0]["id"]  # recibió id propio al registrarse
