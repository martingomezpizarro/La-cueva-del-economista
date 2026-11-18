"""bandeja — la bandeja de series, guardada en el servidor.

La bandeja lleva cosas entre pantallas: una serie de la Terminal, un ratio, una serie macro,
una capa transformada, la salida de un método o una figura. Hasta ahora vivía en el navegador;
acá se guarda en el servidor para que la vean TODAS las pestañas y también el asistente que
trabaja por MCP (lo que agrega uno lo ve el otro).

Cada ítem guarda:
- `tipo`: serie · figura · resultado · dataset
- `ref`: a qué apunta (id de serie, ticker, id de resultado…)
- `receta` y `procedencia`: el linaje, para que no se pierda al trasladarlo
- `autor`: "usuario" o "claude", para marcar lo que agregó cada uno

Qué NO hace: no calcula ni descarga nada; solo guarda y lista. Un único archivo JSON en
`<CUEVA_DATA>/bandeja.json`, protegido con un lock (un proceso, igual que el repositorio de
proyectos).
"""

from __future__ import annotations

import json
import threading
import time
import uuid
from pathlib import Path

from cueva import config

TIPOS = ("serie", "figura", "resultado", "dataset")
AUTORES = ("usuario", "claude")
TOPE = 200  # la bandeja es un lugar de paso, no un archivo


class ItemDesconocido(KeyError):
    pass


class Bandeja:
    def __init__(self, ruta: str | Path | None = None):
        self._ruta_fija = Path(ruta) if ruta else None
        self._lock = threading.RLock()

    @property
    def ruta(self) -> Path:
        # se resuelve en cada uso: los tests cambian CUEVA_DATA entre casos
        return self._ruta_fija or config.ruta_datos() / "bandeja.json"

    # ── internos ──────────────────────────────────────────────────────────
    def _leer(self) -> list[dict]:
        if not self.ruta.exists():
            return []
        try:
            return json.loads(self.ruta.read_text(encoding="utf-8")).get("items", [])
        except (json.JSONDecodeError, OSError):
            return []

    def _escribir(self, items: list[dict]) -> None:
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.ruta.with_suffix(".tmp")
        tmp.write_text(json.dumps({"items": items}, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(self.ruta)

    # ── API pública ───────────────────────────────────────────────────────
    def listar(self) -> list[dict]:
        with self._lock:
            return self._leer()

    def agregar(
        self,
        tipo: str,
        ref: str,
        etiqueta: str = "",
        receta: dict | None = None,
        procedencia: dict | None = None,
        datos: dict | None = None,
        autor: str = "usuario",
    ) -> dict:
        if tipo not in TIPOS:
            raise ValueError(f"Tipo desconocido: {tipo}. Opciones: {', '.join(TIPOS)}")
        if autor not in AUTORES:
            raise ValueError(f"Autor desconocido: {autor}")
        item = {
            "id": uuid.uuid4().hex[:10],
            "tipo": tipo,
            "ref": ref,
            "etiqueta": etiqueta or ref,
            "receta": receta,
            "procedencia": procedencia,
            "datos": datos,
            "autor": autor,
            "ts": time.time(),
        }
        with self._lock:
            items = self._leer()
            items.append(item)
            self._escribir(items[-TOPE:])
        return item

    def quitar(self, item_id: str) -> None:
        with self._lock:
            items = self._leer()
            quedan = [i for i in items if i.get("id") != item_id]
            if len(quedan) == len(items):
                raise ItemDesconocido(item_id)
            self._escribir(quedan)

    def vaciar(self) -> int:
        with self._lock:
            n = len(self._leer())
            self._escribir([])
        return n


_bandeja: Bandeja | None = None


def get_bandeja() -> Bandeja:
    global _bandeja
    if _bandeja is None:
        _bandeja = Bandeja()
    return _bandeja
