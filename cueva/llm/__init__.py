"""cueva.llm — ÚNICO punto de salida hacia los modelos de lenguaje.

Ningún otro módulo debe llamar a los SDKs de Gemini/Anthropic directamente:
todo pasa por `gateway.completar()` / `gateway.conversar()`, que agregan
reintentos con backoff, modo offline y contabilidad de tokens.
"""

from .gateway import Respuesta, backend, completar, conversar, disponible
from .presupuesto import ContadorTokens

__all__ = ["Respuesta", "ContadorTokens", "backend", "completar", "conversar", "disponible"]
