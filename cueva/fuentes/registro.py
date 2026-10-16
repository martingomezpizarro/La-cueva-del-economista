"""registro — lectura del registro de organismos (`registro.json`).

El JSON es la fuente de verdad: para agregar un organismo se edita ese archivo, no
este módulo. Acá solo se lo lee, se lo cachea y se lo expone tipado.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

RUTA_REGISTRO = Path(__file__).with_name("registro.json")


class OrganismoDesconocido(KeyError):
    """La serie declara un `proc.fuente` que no está en el registro."""


@dataclass(frozen=True)
class Organismo:
    """Una fuente institucional de datos, tal como la declara `registro.json`."""

    clave: str
    nombre: str
    sigla: str
    sitio: str
    acceso: str
    licencia: str
    redistribuible: bool
    datos: dict[str, Any]

    @property
    def api(self) -> dict[str, Any]:
        return self.datos.get("api") or {}

    def cita(self) -> str:
        """Línea de cita lista para pegar en un anexo de fuentes."""
        return f"{self.nombre} ({self.sigla}). {self.sitio}"


@lru_cache(maxsize=1)
def _crudo() -> dict[str, Any]:
    return json.loads(RUTA_REGISTRO.read_text(encoding="utf-8"))


def registro() -> dict[str, Organismo]:
    """Todos los organismos conocidos, indexados por clave."""
    return {clave: _armar(clave, d) for clave, d in _crudo()["fuentes"].items()}


def organismo(clave: str) -> Organismo:
    """Un organismo por su clave. Lanza `OrganismoDesconocido` si no existe."""
    fuentes = _crudo()["fuentes"]
    if clave not in fuentes:
        conocidas = ", ".join(sorted(fuentes))
        raise OrganismoDesconocido(f"fuente '{clave}' desconocida. Conocidas: {conocidas}")
    return _armar(clave, fuentes[clave])


def _armar(clave: str, d: dict[str, Any]) -> Organismo:
    return Organismo(
        clave=clave,
        nombre=d.get("nombre", clave),
        sigla=d.get("sigla", clave),
        sitio=d.get("sitio", ""),
        acceso=d.get("acceso", ""),
        licencia=d.get("licencia", ""),
        redistribuible=bool(d.get("redistribuible", False)),
        datos=d,
    )
