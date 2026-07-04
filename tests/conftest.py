"""Fixtures compartidas de la suite.

Principios:
  - CERO llamadas de red y CERO API keys: los tests corren en el modo offline del gateway.
  - Series SINTÉTICAS con semilla fija: sabemos POR CONSTRUCCIÓN si una serie es I(1),
    estacionaria o cointegrada, así los tests validan las conclusiones econométricas.
  - Todo el estado (datos, índice, proyectos) vive en carpetas temporales.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from cueva.datos import series as S
from cueva.sesiones import RepositorioProyectos

N_OBS = 150


def _guardar(carpeta, nombre, valores):
    fechas = pd.date_range("2005-01-31", periods=len(valores), freq="ME")
    pd.DataFrame({"fecha": fechas, "valor": valores}).to_csv(
        carpeta / f"{nombre}.csv", index=False, encoding="utf-8-sig"
    )


@pytest.fixture()
def carpeta_series(tmp_path, monkeypatch):
    """Carpeta de datos sintéticos con 5 series de propiedades conocidas (semilla 1,
    elegida verificando que ADF/KPSS/Johansen den resultados inequívocos):

    - `caminata`  : random walk pura → I(1), no estacionaria (ADF p≈0.91, KPSS p≈0.01).
    - `caminata2` : random walk INDEPENDIENTE → no cointegra con `caminata` (rango 0).
    - `ar_uno`    : AR(1) con φ=0.5  → estacionaria.
    - `coint_x`   : random walk (la tendencia común).
    - `coint_y`   : 2 + 0.8·coint_x + ruido estacionario → cointegrada con coint_x (rango 1).
    """
    rng = np.random.default_rng(1)
    tf = tmp_path / "trabajo"
    datos = tf / "data" / "Variables Finales"
    datos.mkdir(parents=True)

    caminata = np.cumsum(rng.normal(0, 1, N_OBS)) + 50
    caminata2 = np.cumsum(rng.normal(0, 1, N_OBS)) + 80
    x = np.cumsum(rng.normal(0, 1, N_OBS)) + 100
    y = 2 + 0.8 * x + rng.normal(0, 0.5, N_OBS)
    ar = np.zeros(N_OBS)
    for t in range(1, N_OBS):
        ar[t] = 0.5 * ar[t - 1] + rng.normal(0, 1)

    _guardar(datos, "caminata", caminata)
    _guardar(datos, "caminata2", caminata2)
    _guardar(datos, "ar_uno", ar)
    _guardar(datos, "coint_x", x)
    _guardar(datos, "coint_y", y)

    # aislar de las carpetas reales de la máquina
    monkeypatch.setenv("CUEVA_TRABAJO_FINAL", str(tf))
    monkeypatch.setenv("CUEVA_MATRIZ_ARG", str(tmp_path / "sin_matriz"))
    (tmp_path / "sin_matriz").mkdir()
    S.refrescar()
    yield datos
    S.refrescar()


@pytest.fixture()
def sin_llm(monkeypatch):
    """Garantiza modo offline: sin claves, el gateway responde maquetas deterministas."""
    for var in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "ANTHROPIC_API_KEY"):
        monkeypatch.delenv(var, raising=False)


@pytest.fixture()
def repo(tmp_path):
    return RepositorioProyectos(ruta=tmp_path / "proyectos")


@pytest.fixture()
def cliente(repo, sin_llm, carpeta_series):
    """TestClient de la API con repositorio temporal inyectado (dependency override)."""
    from fastapi.testclient import TestClient

    from cueva.api.app import crear_app, get_repo

    app = crear_app()
    app.dependency_overrides[get_repo] = lambda: repo
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def indice_temporal(tmp_path, monkeypatch):
    """Índice de La Cueva-LM chiquito y determinista (solo TF-IDF, sin torch)."""
    from cueva.conocimiento import ingesta, recuperar

    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "cointegracion.md").write_text(
        "\n".join(
            [
                "La cointegracion de Johansen permite estimar un modelo VECM cuando las "
                "series comparten una relacion de largo plazo y son integradas de orden uno."
            ]
            * 130
        ),
        encoding="utf-8",
    )
    (docs / "volatilidad.md").write_text(
        "\n".join(
            [
                "El modelo GARCH captura la volatilidad condicional de los retornos "
                "financieros cuando hay heterocedasticidad y persistencia de los shocks."
            ]
            * 130
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("CUEVA_INDICE", str(tmp_path / "indice"))
    recuperar.limpiar_cache()
    ingesta.ingestar([docs], embeddings=False, verboso=False)
    recuperar.limpiar_cache()
    yield tmp_path / "indice"
    recuperar.limpiar_cache()
