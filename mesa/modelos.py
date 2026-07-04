"""
modelos.py — Estructuras de datos de una sesión de investigación.

Todo es serializable a dict/JSON para poder mandarlo a la UI y persistirlo.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any, Optional


def _id() -> str:
    return uuid.uuid4().hex[:8]


def _ahora() -> float:
    return time.time()


# ──────────────────────────────────────────────────────────────────────────
# Definición de la investigación (lo que carga el usuario)
# ──────────────────────────────────────────────────────────────────────────
@dataclass
class Proyecto:
    """Lo que el economista define al inicio: idea, objetivos, preguntas, hipótesis."""
    id: str = field(default_factory=_id)
    titulo: str = "Investigación sin título"
    pregunta: str = ""                       # pregunta de investigación principal
    objetivos: list[str] = field(default_factory=list)
    hipotesis: list[str] = field(default_factory=list)
    contexto: str = ""                       # marco teórico / contexto que aporta el usuario
    series: list[str] = field(default_factory=list)   # IDs de series a usar
    serie_dependiente: Optional[str] = None  # ID de la serie Y (si aplica)
    frecuencia: str = "mensual"              # diaria | mensual | trimestral | anual
    bibliografia_usuario: list[str] = field(default_factory=list)  # rutas/títulos subidos

    def to_dict(self) -> dict:
        return asdict(self)

    def resumen_para_agente(self) -> str:
        """Texto compacto del proyecto, para inyectar en el prompt de cada agente."""
        L = [f"TÍTULO: {self.titulo}", f"PREGUNTA DE INVESTIGACIÓN: {self.pregunta}"]
        if self.objetivos:
            L.append("OBJETIVOS:\n" + "\n".join(f"  - {o}" for o in self.objetivos))
        if self.hipotesis:
            L.append("HIPÓTESIS:\n" + "\n".join(f"  - {h}" for h in self.hipotesis))
        if self.serie_dependiente:
            L.append(f"VARIABLE DEPENDIENTE (Y): {self.serie_dependiente}")
        if self.series:
            L.append(f"SERIES SELECCIONADAS: {', '.join(self.series)}")
        L.append(f"FRECUENCIA DE TRABAJO: {self.frecuencia}")
        if self.contexto:
            L.append(f"CONTEXTO/MARCO TEÓRICO DEL USUARIO:\n{self.contexto}")
        return "\n".join(L)


# ──────────────────────────────────────────────────────────────────────────
# Mensajes de la conversación entre agentes
# ──────────────────────────────────────────────────────────────────────────
@dataclass
class Mensaje:
    """Un turno en la mesa: lo dice un agente (o el usuario, o el sistema)."""
    autor: str                               # id del agente / "usuario" / "orquestador"
    rol: str                                 # nombre legible: "🧭 Metodólogo", etc.
    contenido: str
    fase: str = "general"                    # exploratorio | control | modelizacion | ...
    dirigido_a: Optional[str] = None         # id del agente al que se le habla (handoff)
    citas: list[str] = field(default_factory=list)   # fuentes de bibliografía citadas
    herramienta: Optional[dict] = None       # si el turno ejecutó una herramienta econométrica
    id: str = field(default_factory=_id)
    ts: float = field(default_factory=_ahora)

    def to_dict(self) -> dict:
        return asdict(self)


# ──────────────────────────────────────────────────────────────────────────
# Hallazgos consolidados (lo que la mesa va "fijando" como conclusión parcial)
# ──────────────────────────────────────────────────────────────────────────
@dataclass
class Hallazgo:
    fase: str
    texto: str
    autor: str
    citas: list[str] = field(default_factory=list)
    evidencia: Optional[dict] = None         # output de herramienta que lo respalda
    id: str = field(default_factory=_id)
    ts: float = field(default_factory=_ahora)

    def to_dict(self) -> dict:
        return asdict(self)


# Fases canónicas del pipeline de investigación
FASES = [
    ("encuadre", "🎯 Encuadre", "Aterrizar pregunta, hipótesis y método candidato."),
    ("exploratorio", "🔍 Análisis exploratorio", "Conocer las series: forma, huecos, outliers, estacionalidad."),
    ("control", "🧪 Control de series", "Estacionariedad, raíces unitarias, quiebres, cointegración."),
    ("modelizacion", "📐 Modelización", "Estimar el/los modelos econométricos pertinentes."),
    ("interpretacion", "📖 Interpretación", "Traducir resultados a economía, con citas."),
    ("conclusiones", "🏁 Conclusiones", "Sintetizar respuesta a la pregunta y límites."),
]

FASE_LABEL = {k: lbl for k, lbl, _ in FASES}
FASE_DESC = {k: d for k, _, d in FASES}
