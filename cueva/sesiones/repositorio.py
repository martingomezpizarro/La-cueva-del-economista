"""repositorio — carga/guardado de pizarras con lock por proyecto.

- Valida los IDs de proyecto ANTES de tocar el filesystem (cierra el path traversal, bug B2).
- Cachea la pizarra en memoria por proceso: todas las requests ven LA MISMA instancia
  y las mutaciones se serializan con un lock por proyecto (cierra el last-write-wins, bug B3).
- Borrado suave: eliminar mueve el JSON a `_papelera/` en vez de destruirlo.

Vale para un proceso (uvicorn simple). Cuando haya múltiples workers (fase web),
este archivo se reemplaza por una implementación sobre base de datos sin tocar al resto.
"""

from __future__ import annotations

import json
import re
import threading
from contextlib import contextmanager
from pathlib import Path

from cueva import config
from cueva.agentes.modelos import Proyecto
from cueva.agentes.pizarra import Pizarra

PID_RE = re.compile(r"^[0-9a-f]{8,32}$")


class PidInvalido(ValueError):
    pass


class ProyectoNoEncontrado(KeyError):
    pass


class RepositorioProyectos:
    def __init__(self, ruta: str | Path | None = None):
        self.ruta = Path(ruta) if ruta else config.ROOT / "data" / "proyectos"
        self._cache: dict[str, Pizarra] = {}
        self._locks: dict[str, threading.RLock] = {}
        self._global = threading.Lock()

    # ── internos ──────────────────────────────────────────────────────────
    def _validar(self, pid: str) -> str:
        if not isinstance(pid, str) or not PID_RE.match(pid):
            raise PidInvalido(f"ID de proyecto inválido: {pid!r}")
        return pid

    def _archivo(self, pid: str) -> Path:
        return self.ruta / f"{self._validar(pid)}.json"

    def _lock(self, pid: str) -> threading.RLock:
        with self._global:
            if pid not in self._locks:
                self._locks[pid] = threading.RLock()
            return self._locks[pid]

    # ── API pública ───────────────────────────────────────────────────────
    def crear(self, titulo: str = "Investigación sin título") -> Pizarra:
        piz = Pizarra(Proyecto(titulo=titulo))
        with self._global:
            self._cache[piz.id] = piz
        self.guardar(piz)
        return piz

    def obtener(self, pid: str) -> Pizarra:
        """Devuelve la instancia viva de la pizarra (cargándola del disco la primera vez)."""
        pid = self._validar(pid)
        with self._global:
            if pid in self._cache:
                return self._cache[pid]
        archivo = self._archivo(pid)
        if not archivo.exists():
            raise ProyectoNoEncontrado(pid)
        piz = Pizarra.desde_dict(json.loads(archivo.read_text(encoding="utf-8")))
        with self._global:
            self._cache.setdefault(pid, piz)
            return self._cache[pid]

    @contextmanager
    def abrir(self, pid: str):
        """Uso: `with repo.abrir(pid) as piz: ...` — mutación con lock + guardado al salir."""
        piz = self.obtener(pid)
        lock = self._lock(piz.id)
        with lock:
            yield piz
            self.guardar(piz)

    def guardar(self, piz: Pizarra) -> None:
        self.ruta.mkdir(parents=True, exist_ok=True)
        with self._lock(piz.id):
            piz.guardar(self._archivo(piz.id))

    def listar(self) -> list[dict]:
        if not self.ruta.exists():
            return []
        out = []
        for f in self.ruta.glob("*.json"):
            try:
                d = json.loads(f.read_text(encoding="utf-8"))
                out.append(
                    {
                        "id": d.get("id", f.stem),
                        "titulo": d.get("proyecto", {}).get("titulo", "Investigación sin título"),
                        "pregunta": d.get("proyecto", {}).get("pregunta", ""),
                        "actualizado": d.get("actualizado", 0),
                        "n_series": len(d.get("proyecto", {}).get("series", [])),
                    }
                )
            except Exception:
                continue
        out.sort(key=lambda x: x["actualizado"], reverse=True)
        return out

    def eliminar(self, pid: str) -> None:
        """Borrado suave: mueve el archivo a _papelera/ (recuperable a mano)."""
        archivo = self._archivo(pid)
        with self._global:
            self._cache.pop(pid, None)
        if archivo.exists():
            papelera = self.ruta / "_papelera"
            papelera.mkdir(parents=True, exist_ok=True)
            archivo.replace(papelera / archivo.name)
