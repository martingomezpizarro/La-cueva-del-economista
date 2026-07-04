"""cueva.conocimiento — La Cueva-LM: ingesta, índice y recuperación de bibliografía.

- `ingesta`   : PDFs/código/markdown → índice en <repo>/indice/ (fragmentos + TF-IDF + embeddings)
- `recuperar` : pregunta → pasajes citados (embeddings multilingües si están, si no TF-IDF)
- `fichas`    : las fichas metodológicas de knowledge-base/fichas/ (supuestos y errores típicos)

El índice NO usa pickle (formato: JSONL + .npy + .npz + JSON): cargarlo nunca ejecuta código.
"""

from .fichas import fichas_relevantes
from .recuperar import Pasaje, buscar, contexto_citado, indice_disponible

__all__ = ["Pasaje", "buscar", "contexto_citado", "indice_disponible", "fichas_relevantes"]
