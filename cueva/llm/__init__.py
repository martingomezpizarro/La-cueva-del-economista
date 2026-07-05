"""cueva.llm — ÚNICO punto de salida hacia los modelos de lenguaje.

Ningún otro módulo debe llamar a los SDKs de Gemini/Anthropic directamente:
todo pasa por el gateway, que agrega reintentos con backoff, modo offline,
contabilidad de tokens, transcript por sesión y el bucle de function calling.
"""

from .gateway import (
    Respuesta,
    backend,
    completar,
    conversar,
    conversar_con_herramientas,
    disponible,
)
from .presupuesto import ContadorTokens
from .transcript import Transcript

__all__ = [
    "Respuesta",
    "ContadorTokens",
    "Transcript",
    "backend",
    "completar",
    "conversar",
    "conversar_con_herramientas",
    "disponible",
]
