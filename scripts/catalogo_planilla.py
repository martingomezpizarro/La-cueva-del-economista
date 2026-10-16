"""catalogo_planilla.py — el catálogo como planilla de trabajo para conseguir las series.

Genera `docs/catalogo_series.csv` (para subir a Google Sheets) y `docs/catalogo_series.xlsx`
(con formato, filtros y listas desplegables).

No es el inventario técnico —para eso está `cuadro_series.py`— sino la **hoja de campaña**:
una fila por serie, con lo que hace falta para decidir si se puede conseguir más historia,
de dónde, y en qué estado está la gestión. Las últimas columnas vienen vacías a propósito:
son para anotar a mano.

Uso:
    python scripts/catalogo_planilla.py
"""

from __future__ import annotations

import csv
import json

from auditar_series import RAIZ, auditar  # type: ignore

SERIES = RAIZ / "data" / "series"


def _en_data_series() -> set[str]:
    """Nombres de archivo que el catálogo puede usar, dentro de data/series.

    Una serie cuyo archivo no está ahí no se puede resolver en la plataforma, así que va sin
    Archivo, sin Columna y sin ID: el ID es lo que la plataforma usa para ir a buscar el dato.

    Las carpetas `<Familia>_Fuentes/` quedan afuera a propósito: guardan el crudo como lo publica
    el organismo (los .xls del INDEC, los CSV de datos.gob.ar), que es insumo de la ingesta, no
    algo que el catálogo lea. Contarlas daba por resuelto el ICA de Sector Externo, que todavía
    no está migrado."""
    return {r.name for r in SERIES.rglob("*")
            if r.is_file() and not any(p.name.endswith("_Fuentes") for p in r.parents)}

CSV = RAIZ / "docs" / "catalogo_series.csv"
XLSX = RAIZ / "docs" / "catalogo_series.xlsx"
REGISTRO = RAIZ / "cueva" / "fuentes" / "registro.json"

COLUMNAS = [
    "Familia", "Grupo", "Subgrupo", "Serie", "ID", "Archivo", "Columna", "Frec", "Desde", "Hasta", "Obs",
    "Unidad", "Fuente", "IdExt", "Confianza", "Estado",
    "¿Ampliable?", "Fuente alternativa", "Objetivo desde", "Notas", "Revisado",
]
# Las cinco últimas van vacías: son las columnas de trabajo.
A_MANO = 5


def filas() -> list[dict]:
    """Una fila por serie: si tiene varias frecuencias, se toma la más fina con datos."""
    orden = {"D": 0, "M": 1, "Q": 2, "A": 3}
    por_id: dict[str, dict] = {}
    for f in auditar():
        clave = f["id"]
        actual = por_id.get(clave)
        mejor = (
            actual is None
            or (bool(f["origen"]), -orden.get(f["frecuencia"], 9))
            > (bool(actual["origen"]), -orden.get(actual["frecuencia"], 9))
        )
        if mejor:
            por_id[clave] = f

    disponibles = _en_data_series()
    salida = []
    for f in por_id.values():
        resuelve = f["base"] in disponibles
        estado = f["estado"].split(" (")[0]
        salida.append({
            "Familia": f["familia"],
            "Grupo": f["grupo"],
            "Subgrupo": f["subgrupo"],
            "Serie": f["serie"],
            "ID": f["id"] if resuelve else "",
            "Archivo": f["base"] if resuelve else "",
            "Columna": f["col_valor"] if resuelve else "",
            "Frec": f["frecuencia"],
            "Desde": f["origen"],
            "Hasta": f["final"],
            "Obs": f["n_obs"],
            "Unidad": f["unidad_texto"],
            "Fuente": f["fuente"],
            "IdExt": f["id_externo"],
            "Confianza": f["confianza"],
            "Estado": estado,
            "¿Ampliable?": "",
            "Fuente alternativa": "",
            "Objetivo desde": "",
            "Notas": "",
            "Revisado": "",
        })
    salida.sort(key=lambda x: (x["Familia"], x["Grupo"], x["Subgrupo"], x["Serie"]))
    return salida


def escribir_csv(datos: list[dict]) -> None:
    CSV.parent.mkdir(parents=True, exist_ok=True)
    with CSV.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNAS)
        w.writeheader()
        w.writerows(datos)


def fuentes_conocidas() -> list[str]:
    d = json.loads(REGISTRO.read_text(encoding="utf-8"))["fuentes"]
    return sorted(d)


if __name__ == "__main__":
    datos = filas()
    escribir_csv(datos)
    print(f"{len(datos)} series -> {CSV.relative_to(RAIZ)}  ({CSV.stat().st_size // 1024} KB)")
