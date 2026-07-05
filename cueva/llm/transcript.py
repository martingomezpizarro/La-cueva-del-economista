"""transcript — registro JSONL de cada llamada al LLM de una sesión.

Hace la sesión AUDITABLE y re-ejecutable: qué prompt recibió cada agente, qué respondió
el modelo, con qué backend/modelo, cuántos tokens y qué herramientas pidió. Una línea JSON
por evento, en data/proyectos/{id}.transcript.jsonl (ignorado por git).
"""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path


class Transcript:
    def __init__(self, ruta: str | Path):
        self.ruta = Path(ruta)
        self._lock = threading.Lock()

    def registrar(self, **evento) -> None:
        """Best-effort: un transcript que falla no debe tumbar la mesa."""
        evento.setdefault("ts", time.time())
        try:
            self.ruta.parent.mkdir(parents=True, exist_ok=True)
            linea = json.dumps(evento, ensure_ascii=False, default=str)
            with self._lock, open(self.ruta, "a", encoding="utf-8") as f:
                f.write(linea + "\n")
        except Exception:
            pass
