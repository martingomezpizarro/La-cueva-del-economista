"""Tests de la fase 3: ingesta incremental con manifiesto, colecciones con provenance
y subida segura de bibliografía del usuario."""

import json

import pytest

from cueva import config
from cueva.conocimiento import biblioteca, buscar, contexto_citado, ingesta, recuperar

TEXTO_COINT = (
    "La cointegracion de Johansen permite estimar un modelo VECM cuando las series "
    "comparten una relacion de largo plazo y son integradas de orden uno."
)
TEXTO_GARCH = (
    "El modelo GARCH captura la volatilidad condicional de los retornos financieros "
    "cuando hay heterocedasticidad y persistencia de los shocks."
)


def _docs(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "cointegracion.md").write_text("\n".join([TEXTO_COINT] * 130), encoding="utf-8")
    (docs / "volatilidad.md").write_text("\n".join([TEXTO_GARCH] * 130), encoding="utf-8")
    return docs


# ──────────────────────────────────────────────────────────────────────────
# Ingesta incremental + manifiesto
# ──────────────────────────────────────────────────────────────────────────
def test_manifiesto_y_reingesta_sin_cambios(tmp_path):
    docs = _docs(tmp_path)
    meta1 = ingesta.ingestar([docs], embeddings=False, verboso=False)
    manifest = json.loads((config.ruta_indice() / "manifest.json").read_text(encoding="utf-8"))
    assert len(manifest["archivos"]) == 2
    assert all("hash" in v and v["n_fragmentos"] > 0 for v in manifest["archivos"].values())

    # re-ingesta sin cambios: mismos fragmentos, nada nuevo
    meta2 = ingesta.ingestar([docs], embeddings=False, verboso=False)
    assert meta2["n"] == meta1["n"]


def test_incremental_solo_procesa_lo_cambiado(tmp_path):
    docs = _docs(tmp_path)
    ingesta.ingestar([docs], embeddings=False, verboso=False)

    # se agrega un archivo nuevo → solo ese se suma; los previos se reutilizan
    (docs / "kalman.md").write_text(
        "\n".join(["El filtro de Kalman estima el estado latente de un modelo estructural."] * 130),
        encoding="utf-8",
    )
    meta = ingesta.ingestar([docs], embeddings=False, verboso=False)
    manifest = json.loads((config.ruta_indice() / "manifest.json").read_text(encoding="utf-8"))
    assert len(manifest["archivos"]) == 3
    assert meta["n"] > 0
    recuperar.limpiar_cache()
    assert buscar("filtro de kalman estado latente", k=2)[0].fuente == "kalman"


def test_incremental_descarta_lo_borrado(tmp_path):
    docs = _docs(tmp_path)
    ingesta.ingestar([docs], embeddings=False, verboso=False)
    (docs / "volatilidad.md").unlink()
    ingesta.ingestar([docs], embeddings=False, verboso=False)
    recuperar.limpiar_cache()
    fuentes = {
        json.loads(line)["fuente"]
        for line in (config.ruta_indice() / "fragmentos.jsonl").read_text(encoding="utf-8").splitlines()
    }
    assert "volatilidad" not in fuentes
    assert "cointegracion" in fuentes


# ──────────────────────────────────────────────────────────────────────────
# Colecciones (provenance) y prioridad de la biblioteca del usuario
# ──────────────────────────────────────────────────────────────────────────
def test_colecciones_separadas_y_citas_marcadas(tmp_path):
    docs = _docs(tmp_path)
    ingesta.ingestar([docs], embeddings=False, verboso=False)
    propio = tmp_path / "mi_tesis.md"
    propio.write_text(
        "\n".join([TEXTO_COINT + " Aplicado al riesgo pais argentino."] * 130), encoding="utf-8"
    )
    ingesta.ingestar([propio], coleccion="usuario", embeddings=False, verboso=False)
    recuperar.limpiar_cache()

    solo_usuario = buscar("riesgo pais argentino", k=5, coleccion="usuario")
    assert solo_usuario and all(p.coleccion == "usuario" for p in solo_usuario)
    assert "biblioteca del usuario" in solo_usuario[0].cita

    # prioridad del Bibliógrafo: lo del usuario va primero
    texto, citas = contexto_citado("riesgo pais argentino", k=4, prioridad_usuario=True)
    assert "biblioteca del usuario" in citas[0]


# ──────────────────────────────────────────────────────────────────────────
# Subida segura (checklist §5.3)
# ──────────────────────────────────────────────────────────────────────────
def test_validaciones_de_subida():
    with pytest.raises(biblioteca.ArchivoInvalido, match="Extensión"):
        biblioteca.validar("malware.exe", b"MZ...")
    with pytest.raises(biblioteca.ArchivoInvalido, match="vacío"):
        biblioteca.validar("nota.md", b"")
    with pytest.raises(biblioteca.ArchivoInvalido, match="firma"):
        biblioteca.validar("falso.pdf", b"no soy un pdf")
    assert biblioteca.validar("paper.pdf", b"%PDF-1.7 ...") == ".pdf"


def test_tamano_maximo(monkeypatch):
    monkeypatch.setattr(biblioteca, "MAX_BYTES", 100)
    with pytest.raises(biblioteca.ArchivoInvalido, match="grande"):
        biblioteca.validar("nota.md", b"x" * 101)


def test_subir_e_indexar_nombre_regenerado(tmp_path):
    contenido = "\n".join([TEXTO_COINT] * 130).encode("utf-8")
    r = biblioteca.guardar_e_indexar("Mi Tesis (borrador FINAL) ..md", contenido)
    assert r["ok"] and r["coleccion"] == "usuario" and r["fragmentos"] > 0
    # nombre regenerado: slug + hash, sin espacios ni caracteres raros del original
    assert " " not in r["archivo"] and "(" not in r["archivo"]
    assert (biblioteca.ruta_biblioteca() / r["archivo"]).exists()
    assert biblioteca.listar()[0]["indexado"]


# ──────────────────────────────────────────────────────────────────────────
# API HTTP
# ──────────────────────────────────────────────────────────────────────────
def test_api_subida(cliente):
    contenido = "\n".join([TEXTO_COINT] * 130).encode("utf-8")
    r = cliente.post("/api/v1/biblioteca", files={"archivo": ("mi paper.md", contenido, "text/markdown")})
    assert r.status_code == 200
    assert r.json()["fragmentos"] > 0

    lista = cliente.get("/api/v1/biblioteca").json()
    assert len(lista) == 1 and lista[0]["indexado"]

    # extensión prohibida → 422 con envelope
    r = cliente.post(
        "/api/v1/biblioteca", files={"archivo": ("script.exe", b"MZ", "application/octet-stream")}
    )
    assert r.status_code == 422

    # pdf falso → 422
    r = cliente.post("/api/v1/biblioteca", files={"archivo": ("falso.pdf", b"hola", "application/pdf")})
    assert r.status_code == 422
