"""modelos — Estructuras de datos de una sesión de investigación.

Todo es serializable a dict/JSON para poder mandarlo a la UI y persistirlo.
Cambios v2 respecto del esquema original:
  - Mensaje.herramientas es una LISTA (antes `herramienta` guardaba solo el primer
    resultado y se perdía la evidencia del VECM, ver bug B1).
  - El handoff es un campo de primera clase (antes viajaba en un atributo fantasma).
  - Mensaje.estado distingue ok / offline / error / presupuesto (degradación visible).
"""

from __future__ import annotations

import time
import uuid
from dataclasses import asdict, dataclass, field


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
    pregunta: str = ""  # pregunta de investigación principal
    objetivos: list[str] = field(default_factory=list)
    hipotesis: list[str] = field(default_factory=list)
    contexto: str = ""  # marco teórico / contexto que aporta el usuario
    series: list[str] = field(default_factory=list)  # IDs de series a usar
    serie_dependiente: str | None = None  # ID de la serie Y (si aplica)
    frecuencia: str = "mensual"  # diaria | mensual | trimestral | anual
    bibliografia_usuario: list[str] = field(default_factory=list)  # rutas/títulos subidos

    def to_dict(self) -> dict:
        return asdict(self)

    def resumen_para_agente(self) -> str:
        """Texto compacto del proyecto, para inyectar en el prompt de cada agente."""
        lineas = [f"TÍTULO: {self.titulo}", f"PREGUNTA DE INVESTIGACIÓN: {self.pregunta}"]
        if self.objetivos:
            lineas.append("OBJETIVOS:\n" + "\n".join(f"  - {o}" for o in self.objetivos))
        if self.hipotesis:
            lineas.append("HIPÓTESIS:\n" + "\n".join(f"  - {h}" for h in self.hipotesis))
        if self.serie_dependiente:
            lineas.append(f"VARIABLE DEPENDIENTE (Y): {self.serie_dependiente}")
        if self.series:
            lineas.append(f"SERIES SELECCIONADAS: {', '.join(self.series)}")
        lineas.append(f"FRECUENCIA DE TRABAJO: {self.frecuencia}")
        if self.contexto:
            lineas.append(f"CONTEXTO/MARCO TEÓRICO DEL USUARIO:\n{self.contexto}")
        return "\n".join(lineas)


# ──────────────────────────────────────────────────────────────────────────
# Mensajes de la conversación entre agentes
# ──────────────────────────────────────────────────────────────────────────
@dataclass
class Mensaje:
    """Un turno en la mesa: lo dice un agente (o el usuario, o el sistema)."""

    autor: str  # id del agente / "usuario" / "orquestador" / "herramientas"
    rol: str  # nombre legible: "🧭 Metodólogo", etc.
    contenido: str
    fase: str = "general"  # exploratorio | control | modelizacion | ...
    dirigido_a: str | None = None  # id del agente al que se le habla (handoff)
    handoff: dict | None = None  # {"destino": id, "pregunta": str} si este turno interpela a otro
    citas: list[str] = field(default_factory=list)  # fuentes de bibliografía citadas
    herramientas: list[dict] = field(default_factory=list)  # resultados econométricos del turno
    estado: str = "ok"  # ok | offline | error | presupuesto | sin_herramientas
    id: str = field(default_factory=_id)
    ts: float = field(default_factory=_ahora)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def desde_dict(cls, d: dict) -> Mensaje:
        """Tolera el esquema v1 (campo `herramienta` singular, sin handoff/estado)."""
        d = dict(d)
        vieja = d.pop("herramienta", None)
        if vieja and not d.get("herramientas"):
            d["herramientas"] = [vieja]
        d.setdefault("herramientas", [])
        campos = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in d.items() if k in campos})


# ──────────────────────────────────────────────────────────────────────────
# Hallazgos consolidados (lo que la mesa va "fijando" como conclusión parcial)
# ──────────────────────────────────────────────────────────────────────────
@dataclass
class Hallazgo:
    fase: str
    texto: str
    autor: str
    citas: list[str] = field(default_factory=list)
    evidencia: dict | None = None  # output de herramienta que lo respalda
    id: str = field(default_factory=_id)
    ts: float = field(default_factory=_ahora)

    def to_dict(self) -> dict:
        return asdict(self)


# IDs canónicos de los agentes de la mesa (los chats 1:1 se indexan por esto):
# los 4 profesores clásicos + líder, y los 7 especialistas de knowledge-base/skills/
AGENTES_IDS = [
    "metodologo",
    "critico",
    "interprete",
    "bibliografo",
    "lider",
    "curador_datos",
    "transformaciones",
    "multivariados",
    "volatilidad",
    "pronostico_ml",
    "controles_causal",
    "robustez",
]

# Fases canónicas del pipeline de investigación
FASES = [
    ("encuadre", "🎯 Encuadre", "Aterrizar pregunta, hipótesis y método candidato."),
    (
        "exploratorio",
        "🔍 Análisis exploratorio",
        "Conocer las series: forma, huecos, outliers, estacionalidad.",
    ),
    ("control", "🧪 Control de series", "Estacionariedad, raíces unitarias, quiebres, cointegración."),
    ("modelizacion", "📐 Modelización", "Estimar el/los modelos econométricos pertinentes."),
    ("interpretacion", "📖 Interpretación", "Traducir resultados a economía, con citas."),
    ("conclusiones", "🏁 Conclusiones", "Sintetizar respuesta a la pregunta y límites."),
]

FASE_LABEL = {k: lbl for k, lbl, _ in FASES}
FASE_DESC = {k: d for k, _, d in FASES}
