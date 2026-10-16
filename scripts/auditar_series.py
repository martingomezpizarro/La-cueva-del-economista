"""auditar_series.py — radiografía del catálogo de series.

Recorre `cueva/datos/catalogo.json`, busca cada archivo en las carpetas de datos
configuradas y reporta, por serie: si el archivo existe, si la columna de valor
existe, el rango temporal REAL, cuántas observaciones tiene y si la serie ya
declara procedencia (bloque `proc`).

Salida: `docs/INVENTARIO_SERIES.md` (tabla legible) + `docs/inventario_series.csv`
(la misma info, para trabajar con ella). No modifica el catálogo.

Uso:
    python scripts/auditar_series.py
    python scripts/auditar_series.py --solo-sin-fuente
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import pandas as pd

from cueva import config
from cueva.fuentes import unidades

RAIZ = Path(__file__).resolve().parent.parent
CATALOGO = RAIZ / "cueva" / "datos" / "catalogo.json"
SALIDA_MD = RAIZ / "docs" / "INVENTARIO_SERIES.md"
SALIDA_CSV = RAIZ / "docs" / "inventario_series.csv"

# El orden es el del cuadro que se mira: qué serie es, de dónde sale el dato, desde
# cuándo hasta cuándo, cada cuánto, quién la publica, qué mide y en qué está medida.
COLUMNAS = [
    "serie", "id", "familia", "grupo", "subgrupo",
    "base", "origen", "final", "frecuencia",
    "fuente", "descripcion",
    "magnitud", "escala", "moneda",
    "unidad_texto", "base_indice", "precios",
    "n_obs", "faltantes", "confianza", "estado",
    "col_fecha", "col_valor", "id_externo", "existe",
]


def _carpetas_datos() -> list[Path]:
    """Carpetas donde buscar los CSV, en orden de prioridad."""
    carpetas = [RAIZ / "data" / "series"]
    tf = config.carpeta_trabajo_final()
    if tf:
        carpetas.append(tf / "data" / "Variables Finales")
    return [c for c in carpetas if c.exists()]


_CACHE_RUTA: dict[str, Path | None] = {}
_CACHE_DF: dict[Path, pd.DataFrame | None] = {}


def _buscar(archivo: str, carpetas: list[Path]) -> Path | None:
    """Ruta del CSV/XLSX. Cacheada: el catálogo tiene 739 entradas sobre ~100 archivos."""
    if archivo in _CACHE_RUTA:
        return _CACHE_RUTA[archivo]
    hallada = None
    for carpeta in carpetas:
        directo = carpeta / archivo
        if directo.exists():
            hallada = directo
            break
        hallada = next(iter(carpeta.rglob(archivo)), None)
        if hallada:
            break
    _CACHE_RUTA[archivo] = hallada
    return hallada


def _abrir(ruta: Path):
    """Lee el archivo una sola vez por corrida (muchas series comparten archivo)."""
    if ruta in _CACHE_DF:
        return _CACHE_DF[ruta]
    try:
        if ruta.suffix.lower() in {".xlsx", ".xls", ".xlsm"}:
            df = pd.read_excel(ruta)
        else:
            df = pd.read_csv(ruta)
    except Exception:
        df = None
    _CACHE_DF[ruta] = df
    return df


def _descender(items: list, camino: str):
    """Recorre items y sus `children`. El catálogo anida hasta 5 niveles: el balance
    de pagos, los vencimientos de deuda y el esquema fiscal cuelgan sus aperturas
    de la serie agregada. Si no se desciende, esas series quedan invisibles."""
    for item in items:
        yield camino, item
        hijos = item.get("children") or []
        if hijos:
            yield from _descender(hijos, f"{camino} › {item.get('label', item['id'])}")


def _iter_series(catalogo: dict):
    """Aplana el catálogo a (familia, grupo, camino, item, fuente_de_datos).

    Desde la reestructura de Actividad (2026-08-29) un bloque puede traer `grupo` y `subgrupo`
    por separado; los que no los traen usan `sub` para los dos, así el resto del catálogo sigue
    andando sin tocarlo."""
    for fam in catalogo["familias"]:
        bloques = [(s.get("grupo", s["sub"]), s.get("subgrupo", s["sub"]), s["items"])
                   for s in fam.get("subs", [])]
        if fam.get("items"):
            bloques.append(("—", "—", fam["items"]))
        for grupo, sub, items in bloques:
            for camino, item in _descender(items, sub):
                # Una serie puede tener varias fuentes de datos (una por frecuencia).
                fuentes = item.get("sources") or ([item] if item.get("file") else [None])
                for fd in fuentes:
                    yield fam["grp"], grupo, camino, item, fd


def _radiografia(ruta: Path | None, col_fecha: str, col_valor: str) -> dict:
    if ruta is None:
        return {"existe": False, "n_obs": 0, "origen": "", "final": "", "faltantes": ""}
    df = _abrir(ruta)
    if df is None:  # archivo ilegible: se reporta, no se rompe la auditoría
        return {"existe": True, "n_obs": 0, "origen": "", "final": "", "faltantes": "ilegible"}
    if col_valor not in df.columns:
        return {
            "existe": True, "n_obs": len(df), "origen": "", "final": "",
            "faltantes": f"falta la columna '{col_valor}'",
        }
    serie = df[[c for c in (col_fecha, col_valor) if c in df.columns]].dropna()
    origen = final = ""
    if col_fecha in df.columns and len(serie):
        fechas = pd.to_datetime(serie[col_fecha], errors="coerce", format="mixed").dropna()
        if len(fechas):
            origen, final = str(fechas.min().date()), str(fechas.max().date())
    return {
        "existe": True,
        "n_obs": int(df[col_valor].notna().sum()),
        "origen": origen,
        "final": final,
        "faltantes": int(df[col_valor].isna().sum()),
    }


def auditar() -> list[dict]:
    catalogo = json.loads(CATALOGO.read_text(encoding="utf-8"))
    carpetas = _carpetas_datos()
    filas: list[dict] = []
    for familia, grupo, sub, item, fd in _iter_series(catalogo):
        # La procedencia de la fuente de datos concreta manda sobre la de la serie:
        # el PBI mensual por Kalman no tiene el mismo origen que el trimestral del INDEC.
        proc = (fd or {}).get("proc") or item.get("proc") or {}
        u = unidades.interpretar(item.get("unit", ""))
        fila = {
            "serie": item.get("label", ""),
            "id": item["id"],
            "familia": familia,
            "grupo": grupo,
            "subgrupo": sub,
            "base": (fd or {}).get("file", ""),
            "frecuencia": (fd or {}).get("freq") or item.get("freq", ""),
            "fuente": proc.get("fuente", ""),
            "descripcion": (proc.get("definicion", "") or "").replace("\n", " ").strip(),
            "magnitud": u.magnitud,
            "escala": u.escala,
            "moneda": u.moneda or "",
            "unidad_texto": u.texto,
            "base_indice": u.base or "",
            "precios": u.precios or "",
            "col_fecha": (fd or {}).get("dateCol", ""),
            "col_valor": (fd or {}).get("valCol", ""),
            "id_externo": proc.get("id_externo", ""),
            "confianza": proc.get("confianza", ""),
        }
        if not fila["base"]:
            fila.update({"existe": "", "n_obs": "", "origen": "", "final": "", "faltantes": ""})
            fila["estado"] = "sin archivo (nodo agrupador o dummy)"
        else:
            ruta = _buscar(fila["base"], carpetas)
            fila.update(_radiografia(ruta, fila["col_fecha"], fila["col_valor"]))
            if not fila["existe"]:
                script = proc.get("script", "")
                fila["estado"] = (
                    f"pendiente de descarga ({script})" if script
                    else "ARCHIVO NO ENCONTRADO"
                )
            elif not fila["n_obs"]:
                fila["estado"] = "vacía o columna equivocada"
            elif not proc:
                fila["estado"] = "ok, sin procedencia documentada"
            else:
                fila["estado"] = "ok"
        filas.append(fila)
    return filas


def escribir(filas: list[dict], solo_sin_fuente: bool = False) -> None:
    SALIDA_CSV.parent.mkdir(parents=True, exist_ok=True)
    with SALIDA_CSV.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNAS)
        w.writeheader()
        w.writerows(filas)

    vistas = [f for f in filas if not solo_sin_fuente or not f["fuente"]]
    total = len(filas)
    con_fuente = sum(1 for f in filas if f["fuente"])
    no_encontrados = [f for f in filas if f["estado"] == "ARCHIVO NO ENCONTRADO"]
    pendientes = [f for f in filas if f["estado"].startswith("pendiente de descarga")]

    lineas = [
        "# Inventario de series — La Cueva del Economista",
        "",
        "> Generado por `python scripts/auditar_series.py`. **No editar a mano.**",
        "> La fuente de verdad es `cueva/datos/catalogo.json`; el esquema está en `docs/DATOS.md`.",
        "",
        "## Resumen",
        "",
        f"- Entradas del catálogo (serie × frecuencia): **{total}**",
        f"- Con procedencia documentada (`proc.fuente`): **{con_fuente}** ({con_fuente * 100 // max(total, 1)} %)",
        f"- Pendientes de descarga (tienen script que las repone): **{len(pendientes)}**",
        f"- Archivos referenciados que no se encontraron ni tienen script: **{len(no_encontrados)}**",
        "",
        "## Series",
        "",
        "| Serie | Base | Origen | Final | Frec. | Fuente | Descripción | Magnitud | Escala | Moneda |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for f in vistas:
        desc = f["descripcion"]
        lineas.append(
            "| {serie} | `{base}` | {origen} | {final} | {frecuencia} | {fuente} "
            "| {desc} | {magnitud} | {escala} | {moneda} |".format(
                **f, desc=(desc[:110] + "…") if len(desc) > 110 else desc)
        )
    if no_encontrados:
        lineas += ["", "## Archivos no encontrados", ""]
        for f in sorted({x["base"] for x in no_encontrados}):
            lineas.append(f"- `{f}`")
    lineas.append("")
    SALIDA_MD.write_text("\n".join(lineas), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--solo-sin-fuente", action="store_true",
                    help="En el markdown, listar solo las series sin procedencia documentada.")
    args = ap.parse_args()
    filas = auditar()
    escribir(filas, solo_sin_fuente=args.solo_sin_fuente)
    print(f"{len(filas)} entradas auditadas -> {SALIDA_MD.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
