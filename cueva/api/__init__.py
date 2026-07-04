"""cueva.api — capa HTTP (FastAPI): valida, delega y serializa.

No contiene lógica de negocio: traduce HTTP ↔ dominio. Los contratos de entrada
viven en `esquemas.py` (Pydantic); la app se construye con `crear_app()`.
"""

from .app import crear_app

__all__ = ["crear_app"]
