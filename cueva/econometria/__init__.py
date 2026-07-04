"""cueva.econometria — herramientas econométricas ejecutables (modo híbrido).

Funciones puras sobre series: se testean sin red y sin API key. Los agentes las piden
por nombre a través del REGISTRO; jamás ejecutan código arbitrario.
"""

from .herramientas import REGISTRO, catalogo_herramientas, ejecutar

__all__ = ["REGISTRO", "catalogo_herramientas", "ejecutar"]
