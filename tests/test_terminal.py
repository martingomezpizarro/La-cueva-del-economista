"""La pestaña Terminal: se monta si el repo de la Terminal está en la compu; si no, avisa."""

import importlib
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from cueva.api import terminal as pestana

PUENTE_FALSO = """
from fastapi import FastAPI
PREFIJO = "/terminal"
def disponible():
    return False
def montar(app_padre, prefijo=PREFIJO, barra_cueva=True):
    sub = FastAPI()
    @sub.get("/api/estado")
    def estado():
        return {"ok": True, "barra": barra_cueva}
    app_padre.mount(prefijo, sub)
"""


@pytest.fixture(autouse=True)
def limpiar(monkeypatch):
    for nombre in [m for m in sys.modules if m == "terminal" or m.startswith("terminal.")]:
        monkeypatch.delitem(sys.modules, nombre)
    monkeypatch.setattr(pestana, "ESTADO", {"disponible": False, "motivo": "sin intentar", "carpeta": None})
    yield
    for nombre in [m for m in sys.modules if m == "terminal" or m.startswith("terminal.")]:
        sys.modules.pop(nombre, None)


def test_sin_la_terminal_la_pestana_explica_por_que(monkeypatch, tmp_path):
    monkeypatch.setattr(pestana.config, "carpeta_terminal", lambda: None)
    monkeypatch.setattr(pestana.importlib, "import_module", _falla_import("terminal"))
    app = FastAPI()
    estado = pestana.montar(app)
    assert estado["disponible"] is False
    r = TestClient(app).get("/terminal/matriz")
    assert r.status_code == 503
    assert "no está en esta compu" in r.text and "barra.js" in r.text


def test_falta_una_dependencia_de_la_terminal(monkeypatch):
    monkeypatch.setattr(pestana.config, "carpeta_terminal", lambda: None)
    monkeypatch.setattr(pestana.importlib, "import_module", _falla_import("duckdb"))
    app = FastAPI()
    assert "duckdb" in pestana.montar(app)["motivo"]


def test_con_la_terminal_se_monta_con_la_barra(monkeypatch, tmp_path):
    paquete = tmp_path / "terminal"
    paquete.mkdir()
    (paquete / "__init__.py").write_text("")
    (paquete / "puente.py").write_text(PUENTE_FALSO)
    monkeypatch.setattr(pestana.config, "carpeta_terminal", lambda: tmp_path)
    monkeypatch.setattr(sys, "path", list(sys.path))
    importlib.invalidate_caches()
    app = FastAPI()
    assert pestana.montar(app)["disponible"] is True
    assert TestClient(app).get("/terminal/api/estado").json() == {"ok": True, "barra": True}


def _falla_import(nombre):
    def importar(_):
        raise ModuleNotFoundError(f"No module named '{nombre}'", name=nombre)

    return importar
