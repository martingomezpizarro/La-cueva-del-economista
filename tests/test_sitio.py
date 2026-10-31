"""Sitio estático (GitHub Pages): el build arma las dos pantallas y la API congelada."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import construir_sitio as CS  # noqa: E402


@pytest.fixture()
def sitio(tmp_path):
    datos = tmp_path / "datos.json"
    datos.write_text(json.dumps({"serie.csv": {"fecha": ["2020-01-01"], "valor": [1.0]}}), encoding="utf-8")
    salida = tmp_path / "sitio"
    resumen = CS.construir(salida, "ejemplo.com.ar", datos)
    return salida, resumen


def test_arma_las_dos_pantallas_con_estatico_inyectado(sitio):
    salida, _ = sitio
    for pagina in ("index.html", "tiempo/index.html", "explorador/index.html", "404.html"):
        html = (salida / pagina).read_text(encoding="utf-8")
        assert CS.INYECCION in html, pagina
        # antes que cualquier otro script: si no, el primer fetch se escapa a la API inexistente
        assert html.index(CS.INYECCION) < html.index("<script", html.index(CS.INYECCION) + 1)
    assert (salida / "web" / "estatico" / "estatico.js").exists()
    assert (salida / "vendor" / "plotly.min.js").exists()


def test_congela_la_historia_y_un_permalink_por_evento(sitio):
    salida, resumen = sitio
    historia = json.loads((salida / "api/v1/historia.json").read_text(encoding="utf-8"))
    ids = [e["id"] for e in historia["eventos"]]
    assert resumen["eventos"] == len(ids) > 0
    for eid in ids:
        assert (salida / "api/v1/historia/eventos" / f"{eid}.json").exists()
        assert (salida / "tiempo" / eid / "index.html").exists()


def test_publica_las_series_pedidas_y_el_dominio(sitio):
    salida, resumen = sitio
    datos = json.loads((salida / "api/v1/explorador/datos.json").read_text(encoding="utf-8"))
    assert list(datos) == ["serie.csv"] and resumen["archivos_de_series"] == 1
    assert "Todavía no se publicaron" not in (salida / "index.html").read_text(encoding="utf-8")
    assert (salida / "CNAME").read_text() == "ejemplo.com.ar\n"
    assert (salida / ".nojekyll").exists()


def test_sin_series_avisa_en_la_mesa(tmp_path):
    vacio = tmp_path / "vacio.json"
    vacio.write_text("{}", encoding="utf-8")
    CS.construir(tmp_path / "s", "", vacio)
    assert "Todavía no se publicaron" in (tmp_path / "s" / "index.html").read_text(encoding="utf-8")
    assert not (tmp_path / "s" / "CNAME").exists()
