"""La Mesa de investigación (portada del mockup «La Cueva») y su catálogo vivo."""

import json

from cueva.datos import catalogo_mesa as CM


def _cat(js: str) -> dict:
    assert js.startswith("const CAT = ") and js.rstrip().endswith(";")
    return json.loads(js[len("const CAT = ") :].rstrip().rstrip(";"))


def test_la_mesa_y_el_inicio_son_la_pagina_del_mockup(cliente):
    for ruta in ("/", "/mesa"):
        html = cliente.get(ruta).text
        assert "/api/v1/mesa/catalogo.js" in html
        assert "const CAT = {" not in html  # los datos ya no van embebidos
        for pieza in (
            'id="v-mesa"',
            'id="v-proyecto"',
            'id="v-documento"',
            'id="v-inicio"',
            'id="bandeja"',
            'id="reg-lista"',
            'id="ec-f"',
            'id="code"',
            'id="lin"',
            'id="herr-lista"',
            'id="proy-lista"',
        ):
            assert pieza in html, f"falta {pieza} en {ruta}"
    assert cliente.get("/portada").status_code == 200
    assert cliente.get("/mesa/anterior").status_code == 200


def test_catalogo_vivo_con_el_formato_del_mockup(cliente):
    r = cliente.get("/api/v1/mesa/catalogo.js")
    assert r.status_code == 200 and "javascript" in r.headers["content-type"]
    cat = _cat(r.text)
    assert set(cat) == {"calendarios", "series", "arbol", "generado"}
    for fila in cat["arbol"]:
        assert len(fila) == 9 and fila[7] in ("datos", "falta", "terminal")


def test_armar_alinea_las_series_al_calendario():
    terminal = [
        {
            "id": "KO",
            "nombre": "KO — Coca-Cola",
            "freq": "diaria",
            "unidad": "USD",
            "fuente": "Terminal · Yahoo",
            "familia": "Mercado de Capitales",
            "grupo": "Precio ajustado (USD)",
            "subgrupo": "ETF",
            "puntos": [("2026-01-02", 60.0), ("2026-01-06", 61.0)],
        },
        {
            "id": "PEP",
            "nombre": "PEP — PepsiCo",
            "freq": "diaria",
            "unidad": "USD",
            "fuente": "Terminal · Yahoo",
            "familia": "Mercado de Capitales",
            "grupo": "Precio ajustado (USD)",
            "subgrupo": "ETF",
            "puntos": [("2026-01-05", 150.0), ("2026-01-06", 151.0)],
        },
        {
            "id": "MELI",
            "nombre": "MELI",
            "freq": "diaria",
            "unidad": "USD",
            "fuente": "Terminal · Yahoo",
            "familia": "Mercado de Capitales",
            "grupo": "Precio ajustado (USD)",
            "subgrupo": "",
        },
    ]
    cat = CM.armar(terminal)
    cal = cat["calendarios"]["diaria"]
    ko, pep = cat["series"]["KO"], cat["series"]["PEP"]
    assert [cal[ko["i0"] + i] for i, v in enumerate(ko["y"]) if v is not None] == ["2026-01-02", "2026-01-06"]
    assert ko["y"] == [60.0, None, 61.0]  # el 05 es de PEP: hueco en KO
    assert cal[pep["i0"]] == "2026-01-05"
    estados = {f[6]: f[7] for f in cat["arbol"]}
    assert estados["KO"] == "datos" and estados["MELI"] == "terminal"


def _serie(nombre, n=180, semilla=1):
    import numpy as np
    import pandas as pd

    f = pd.date_range("2008-01-31", periods=n, freq="ME")
    y = 100 * np.exp(np.cumsum(np.random.default_rng(semilla).normal(0.003, 0.02, n)))
    return {"nombre": nombre, "fechas": [str(d.date()) for d in f], "valores": y.tolist()}


def test_metodo_del_servidor_sobre_fichas_con_datos(cliente):
    """Las fichas de la Mesa (catálogo, Terminal o transformadas) llegan con sus datos y
    cualquier método del catálogo corre sobre ellas."""
    r = cliente.post(
        "/api/v1/mesa/metodo",
        json={"metodo": "filtro_hamilton", "args": {"sid": "@a"}, "series": {"a": _serie("ko")}},
    )
    j = r.json()
    assert r.status_code == 200 and j["ok"] is True
    assert "ko" in j["resumen"] and "m:" not in j["resumen"]
    assert j["series_salida"] and any(b["tipo"] == "lineas" for b in j["bloques"])


def test_herramientas_viejas_tambien_ven_las_fichas(cliente):
    r = cliente.post(
        "/api/v1/mesa/metodo",
        json={
            "metodo": "correlaciones",
            "args": {"sids": ["@a", "@b"]},
            "series": {"a": _serie("ko"), "b": _serie("pep", semilla=2)},
        },
    )
    j = r.json()
    assert j["ok"] is True and "ko" in j["resumen"] and "m:" not in str(j)


def test_ficha_que_no_vino(cliente):
    r = cliente.post("/api/v1/mesa/metodo", json={"metodo": "filtro_hamilton", "args": {"sid": "@x"}})
    assert r.status_code == 422


def test_la_mesa_carga_los_metodos_del_servidor(cliente):
    assert "/web/cueva/metodos_servidor.js" in cliente.get("/mesa").text
    assert cliente.get("/web/cueva/metodos_servidor.js").status_code == 200
