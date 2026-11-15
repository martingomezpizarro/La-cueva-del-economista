"""mis_resultados — Vectores de resultados que el usuario guarda desde una tabla o matriz.

Un vector de resultados NO es una serie de tiempo: son, por ejemplo, los coeficientes de largo
plazo del ITCRM en los 149 modelos que pasaron el filtro, o la fila de la matriz de Granger
de una variable. Se guardan con sus etiquetas y su procedencia (qué método, qué tabla, qué
filtro) para volver a graficarlos o compararlos.

Viven en `<CUEVA_DATA>/resultados/<id>.json`. Qué NO hace: no entra al catálogo de series
(los métodos de series de tiempo no tienen sentido sobre un vector sin fechas).
"""

from __future__ import annotations

import json
import math
import re
import unicodedata
from datetime import datetime

from cueva import config

MAX_VALORES = 200_000


class ResultadoInvalido(ValueError):
    """El vector no pasa la validación (el mensaje es para el usuario)."""


def carpeta():
    return config.ruta_datos() / "resultados"


def _id(nombre: str) -> str:
    base = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode()
    base = re.sub(r"[^A-Za-z0-9]+", "_", base).strip("_").lower()[:50] or "resultado"
    return f"res_{base}"


def guardar(nombre: str, valores: list, etiquetas: list | None = None, procedencia: str = "") -> dict:
    if not nombre.strip():
        raise ResultadoInvalido("Falta el nombre.")
    if not valores or len(valores) > MAX_VALORES:
        raise ResultadoInvalido(f"Hacen falta entre 1 y {MAX_VALORES} valores.")
    if etiquetas is not None and len(etiquetas) != len(valores):
        raise ResultadoInvalido("Etiquetas y valores tienen que tener el mismo largo.")
    limpios = []
    for v in valores:
        if v is None or (isinstance(v, float) and not math.isfinite(v)):
            limpios.append(None)
        elif isinstance(v, (int, float)) and not isinstance(v, bool):
            limpios.append(float(v))
        else:
            raise ResultadoInvalido("Los valores tienen que ser números.")
    if all(v is None for v in limpios):
        raise ResultadoInvalido("No hay ningún valor numérico.")
    rid = _id(nombre)
    doc = {
        "id": rid,
        "nombre": nombre.strip()[:120],
        "procedencia": procedencia[:500],
        "creado": datetime.now().isoformat(timespec="seconds"),
        "etiquetas": [str(e)[:80] for e in etiquetas] if etiquetas is not None else None,
        "valores": limpios,
    }
    carpeta().mkdir(parents=True, exist_ok=True)
    (carpeta() / f"{rid}.json").write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    return {"id": rid, "n": len(limpios)}


def listar() -> list[dict]:
    if not carpeta().exists():
        return []
    out = []
    for f in sorted(carpeta().glob("res_*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        out.append({k: d[k] for k in ("id", "nombre", "procedencia", "creado")} | {"n": len(d["valores"])})
    return out


def obtener(rid: str) -> dict:
    if not re.match(r"^res_[a-z0-9_]{1,50}$", rid):
        raise ResultadoInvalido("Id inválido.")
    f = carpeta() / f"{rid}.json"
    if not f.exists():
        raise KeyError(rid)
    return json.loads(f.read_text(encoding="utf-8"))
