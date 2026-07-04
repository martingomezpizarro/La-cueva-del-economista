"""cueva.agentes — la Mesa de Trabajo: agentes-profesores, pizarra y orquestador.

Tres modos de uso (mismos agentes, misma pizarra):
  1. Consulta 1:1 a un especialista  → Agente.responder_directo()
  2. Líder supervisor a demanda      → Orquestador.revisar()
  3. Pipeline por fases              → Orquestador.correr()
"""

from .agentes import AGENTES, Agente
from .modelos import FASES, Hallazgo, Mensaje, Proyecto
from .orquestador import Orquestador, investigar
from .pizarra import Pizarra

__all__ = [
    "AGENTES",
    "Agente",
    "FASES",
    "Hallazgo",
    "Mensaje",
    "Proyecto",
    "Orquestador",
    "investigar",
    "Pizarra",
]
