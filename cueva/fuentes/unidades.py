"""unidades — traduce el `unit` de texto libre del catálogo a magnitud + escala + moneda.

QUÉ HACE: `"Miles de ARS"` → `Unidad(magnitud="moneda", escala="miles", moneda="ARS")`.
El vocabulario cerrado vive en `unidades.json`; para agregar una unidad se edita ese
archivo, no este módulo.

QUÉ NO HACE: no convierte valores entre escalas ni deflacta. Solo describe.

POR QUÉ EXISTE: dos series pueden decir «base monetaria» y no ser comparables. El bloque
histórico del BCRA viene en MILES de ARS y la serie diaria equivalente en MILLONES. Con
`unit` como texto libre eso no se puede detectar; con magnitud/escala/moneda separadas, sí.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

RUTA = Path(__file__).with_name("unidades.json")


class UnidadDesconocida(KeyError):
    """El catálogo declara un `unit` que no está en el vocabulario."""


@dataclass(frozen=True)
class Unidad:
    """Una unidad descompuesta. `texto` conserva el original para no perder matices."""

    texto: str
    magnitud: str
    escala: str = "unidad"
    moneda: str | None = None
    precios: str | None = None   # "constantes" cuando la serie está a precios de una base
    base: str | None = None      # "2004=100", "dic-2016=100", "2004"
    rango: str | None = None     # para los scores
    por: str | None = None       # "PBI", "habitante"
    contra: str | None = None    # para tipos de cambio
    nota: str | None = None

    @property
    def factor(self) -> int:
        """Cuántas unidades vale un punto de esta escala. Útil para empalmar."""
        return _crudo()["escalas"].get(self.escala, 1)

    @property
    def es_monetaria(self) -> bool:
        return self.magnitud in {"moneda", "tipo_de_cambio"}

    def comparable_con(self, otra: Unidad) -> bool:
        """¿Se pueden graficar o empalmar juntas sin convertir nada?"""
        return (
            self.magnitud == otra.magnitud
            and self.escala == otra.escala
            and self.moneda == otra.moneda
            and self.base == otra.base
        )

    def como_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}


@lru_cache(maxsize=1)
def _crudo() -> dict[str, Any]:
    return json.loads(RUTA.read_text(encoding="utf-8"))


@lru_cache(maxsize=512)
def interpretar(texto: str, estricto: bool = False) -> Unidad:
    """Descompone un `unit` del catálogo.

    Sin `estricto`, un texto desconocido devuelve magnitud "desconocida" en vez de romper:
    la auditoría tiene que poder correr sobre un catálogo a medio curar y mostrar el hueco.
    Con `estricto=True` levanta `UnidadDesconocida` — así lo usa el test.
    """
    texto = (texto or "").strip()
    mapa = _crudo()["mapa"]
    if texto in mapa:
        return Unidad(texto=texto, **mapa[texto])
    if estricto:
        raise UnidadDesconocida(
            f"unidad '{texto}' fuera del vocabulario. Agregala a cueva/fuentes/unidades.json"
        )
    return Unidad(texto=texto, magnitud="desconocida")


def vocabulario() -> dict[str, Any]:
    """El vocabulario completo, para poblar los desplegables del editor."""
    d = _crudo()
    return {
        "magnitudes": d["magnitudes"],
        "escalas": d["escalas"],
        "monedas": d["monedas"],
        "textos": sorted(d["mapa"]),
    }
