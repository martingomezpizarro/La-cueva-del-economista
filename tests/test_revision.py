"""Tests del circuito de revisión: grilla → correcciones → catálogo.

Lo que se prueba es que aplicar una revisión no rompa ni invente nada. En particular:
una unidad corregida tiene que salir del vocabulario cerrado, nunca construirse a mano.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))


def _cargar(nombre: str):
    ruta = RAIZ / "scripts" / f"{nombre}.py"
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


@pytest.fixture(scope="module")
def app():
    return _cargar("aplicar_revision")


@pytest.fixture
def catalogo():
    return {"familias": [{"grp": "Prueba", "clr": "#000", "subs": [{"sub": "S", "items": [
        {"id": "uno", "label": "Serie Uno", "unit": "Miles de ARS", "file": "a.csv",
         "proc": {"fuente": "bcra", "definicion": "vieja", "confianza": "alta"}},
        {"id": "dos", "label": "Serie Dos", "unit": "Mill. USD", "file": "b.csv",
         "proc": {"fuente": "indec", "confianza": "media"},
         "children": [{"id": "hijo", "label": "Hijo", "unit": "Mill. USD", "file": "c.csv",
                       "proc": {"fuente": "indec", "confianza": "media"}}]},
    ]}]}]}


def test_ok_sella_la_serie_como_verificada(app, catalogo):
    app.aplicar(catalogo, {"uno": {"estado": "ok", "campos": {}}})
    proc = catalogo["familias"][0]["subs"][0]["items"][0]["proc"]
    assert proc["confianza"] == "verificada"
    assert proc["verificado"]


def test_corregir_la_descripcion_la_escribe_y_sella(app, catalogo):
    app.aplicar(catalogo, {"uno": {"estado": "corregida", "campos": {"desc": "nueva"}}})
    proc = catalogo["familias"][0]["subs"][0]["items"][0]["proc"]
    assert proc["definicion"] == "nueva"
    assert proc["confianza"] == "verificada"


def test_la_unidad_se_rearma_desde_el_vocabulario(app, catalogo):
    """magnitud + escala + moneda vuelven a un texto que ya existe en unidades.json."""
    app.aplicar(catalogo, {"uno": {"estado": "corregida",
                                   "campos": {"mag": "moneda", "esc": "millones", "mon": "ARS"}}})
    assert catalogo["familias"][0]["subs"][0]["items"][0]["unit"] == "Mill. ARS"


def test_una_combinacion_inexistente_avisa_y_no_inventa_unidad(app, catalogo):
    diff, avisos = app.aplicar(catalogo, {"uno": {"estado": "corregida",
                                                  "campos": {"mag": "ratio", "esc": "millones", "mon": "ARS"}}})
    assert catalogo["familias"][0]["subs"][0]["items"][0]["unit"] == "Miles de ARS", "no debía cambiar"
    assert any("no existe en" in a for a in avisos)


def test_problema_no_toca_los_datos_ni_sella(app, catalogo):
    app.aplicar(catalogo, {"uno": {"estado": "problema", "campos": {"nota": "falta un mes"}}})
    proc = catalogo["familias"][0]["subs"][0]["items"][0]["proc"]
    assert "falta un mes" in proc["revision"]
    assert proc["confianza"] == "alta", "una serie con problema NO se marca verificada"
    assert proc["definicion"] == "vieja"


def test_pendiente_se_ignora(app, catalogo):
    diff, _ = app.aplicar(catalogo, {"uno": {"estado": "pendiente", "campos": {}}})
    assert diff == []


def test_un_id_que_ya_no_existe_avisa_en_vez_de_romper(app, catalogo):
    _, avisos = app.aplicar(catalogo, {"fantasma": {"estado": "ok", "campos": {}}})
    assert any("no está en el catálogo" in a for a in avisos)


def test_llega_a_las_series_anidadas(app, catalogo):
    """El catálogo anida vía `children`: la revisión tiene que alcanzar el fondo."""
    app.aplicar(catalogo, {"hijo": {"estado": "ok", "campos": {}}})
    hijo = catalogo["familias"][0]["subs"][0]["items"][1]["children"][0]
    assert hijo["proc"]["confianza"] == "verificada"


def test_la_grilla_publicada_trae_el_bloque_de_revision(app):
    grilla = RAIZ / "docs" / "cuadro_revision.html"
    if not grilla.exists():
        pytest.skip("falta docs/cuadro_revision.html (correr scripts/cuadro_revision.py)")
    assert isinstance(app.leer_revision(grilla), dict)
