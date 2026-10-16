"""catalogo_planilla_merge.py — regenera la hoja de campaña sin perder la cobertura ya medida.

`catalogo_planilla.py` mide Desde / Hasta / Obs leyendo los archivos en disco. Si se corre
en una máquina que no ve la carpeta del Trabajo Final, esas tres columnas vuelven vacías
para las series que viven allá. Este script vuelve a escribir `docs/catalogo_series.csv`
tomando la medición nueva cuando existe y, si no, la de la planilla anterior
(`docs/catalogo_series.xlsx`, hoja «Catálogo»).

    python scripts/catalogo_planilla_merge.py
"""

from __future__ import annotations

import csv
from pathlib import Path

import openpyxl

RAIZ = Path(__file__).resolve().parent.parent
CSV = RAIZ / "docs" / "catalogo_series.csv"
XLSX_PREVIO = RAIZ / "docs" / "catalogo_series.xlsx"
COBERTURA = ["Frec", "Desde", "Hasta", "Obs", "Estado"]


def previo() -> dict[str, dict]:
    wb = openpyxl.load_workbook(XLSX_PREVIO, read_only=True, data_only=True)
    hoja = wb["Catálogo"]
    filas = hoja.iter_rows(values_only=True)
    cab = [str(c) if c is not None else "" for c in next(filas)]
    out = {}
    for fila in filas:
        d = dict(zip(cab, ["" if v is None else str(v) for v in fila]))
        for clave in _claves(d):
            out.setdefault(clave, d)
    return out


def _claves(f: dict) -> list[str]:
    """Un ID ya no alcanza: las series cuyo archivo no está en data/series van sin ID, y los ids
    de Actividad se renombraron a <prefijo><columna>. La ubicación completa las identifica igual."""
    claves = []
    if f.get("ID"):
        claves.append("id:" + f["ID"])
    claves.append("|".join(f.get(c, "") for c in
                          ("Familia", "Grupo", "Subgrupo", "Serie", "Unidad")))
    return claves


def main() -> None:
    with CSV.open(encoding="utf-8", newline="") as fh:
        filas = list(csv.DictReader(fh))
        cab = list(filas[0])

    viejo = previo()
    recuperadas = 0
    for f in filas:
        v = next((viejo[k] for k in _claves(f) if k in viejo), None)
        if v and not str(f["Estado"]).startswith("ok") and str(v.get("Estado", "")).startswith("ok"):
            for c in COBERTURA:
                if v.get(c):
                    f[c] = v[c]
            recuperadas += 1

    with CSV.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cab)
        w.writeheader()
        w.writerows(filas)

    con_datos = sum(1 for f in filas if str(f["Estado"]).startswith("ok"))
    print(f"{len(filas)} series · {con_datos} con datos · {recuperadas} recuperadas de la planilla previa")
    print(f"-> {CSV.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
