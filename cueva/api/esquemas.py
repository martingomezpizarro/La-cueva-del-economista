"""esquemas — contratos Pydantic de la API (DTOs de entrada).

Todo lo que entra por HTTP se valida acá: tipos, campos obligatorios y LÍMITES de tamaño.
Un payload inválido devuelve 422 con el detalle, sin tocar el dominio.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Frecuencia = Literal["diaria", "mensual", "trimestral", "anual"]

# ID de proyecto: hex corto generado por el sistema (cierra el path traversal, bug B2)
PID_PATTERN = r"^[0-9a-f]{8,32}$"


class EstudioSemilla(BaseModel):
    """Un estudio corrido en la Vista Rápida que se lleva al proyecto al promoverla."""

    herramienta: str = Field(pattern=r"^[a-z_]{2,30}$")
    args: dict = Field(default_factory=dict)
    resumen: str = Field(default="", max_length=4_000)
    resultado: dict | None = None


class ProyectoCrear(BaseModel):
    """Creación de proyecto. Los campos opcionales permiten 'promover' una Vista Rápida:
    el espacio efímero se convierte en proyecto llevándose series y estudios acumulados."""

    titulo: str = Field(default="Investigación sin título", max_length=200)
    series: list[str] = Field(default_factory=list, max_length=20)
    serie_dependiente: str | None = Field(default=None, max_length=80)
    frecuencia: Frecuencia | None = None
    estudios: list[EstudioSemilla] = Field(default_factory=list, max_length=100)


class ProyectoPatch(BaseModel):
    """Campos editables del proyecto; solo se aplican los presentes."""

    titulo: str | None = Field(default=None, max_length=200)
    pregunta: str | None = Field(default=None, max_length=2000)
    objetivos: list[str] | None = Field(default=None, max_length=10)
    hipotesis: list[str] | None = Field(default=None, max_length=10)
    contexto: str | None = Field(default=None, max_length=8000)
    series: list[str] | None = Field(default=None, max_length=20)
    serie_dependiente: str | None = Field(default=None, max_length=80)
    frecuencia: Frecuencia | None = None
    bibliografia_usuario: list[str] | None = Field(default=None, max_length=30)


class NotaCrear(BaseModel):
    texto: str = Field(min_length=1, max_length=10_000)


class InformeTexto(BaseModel):
    texto: str = Field(default="", max_length=100_000)


class PreguntaAgente(BaseModel):
    pregunta: str = Field(min_length=1, max_length=4_000)


class HerramientaEjecutar(BaseModel):
    nombre: str = Field(pattern=r"^[a-z_]{2,30}$")
    args: dict = Field(default_factory=dict)
    proyecto_id: str | None = Field(default=None, pattern=PID_PATTERN)
