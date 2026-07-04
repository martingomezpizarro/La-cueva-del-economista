"""
rag_cliente.py — Acceso a La Cueva-LM desde los agentes.

Recupera pasajes del índice existente (rag/_indice/) sin lanzar subprocesos: usa embeddings
multilingües si el índice los tiene, si no cae a TF-IDF. Es lo que permite que cada agente
fundamente lo que dice en bibliografía real con cita de fuente y página.
"""
from __future__ import annotations

import json
import pickle
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import config

INDICE = config.INDICE_RAG


@dataclass
class Pasaje:
    fuente: str
    ref: str
    tipo: str
    texto: str
    score: float

    @property
    def cita(self) -> str:
        return f"{self.fuente} {self.ref}"


@lru_cache(maxsize=1)
def _cargar():
    frag = INDICE / "fragmentos.jsonl"
    if not frag.exists():
        return None
    registros = [json.loads(l) for l in frag.read_text(encoding="utf-8").splitlines() if l.strip()]
    meta = {}
    if (INDICE / "meta.json").exists():
        meta = json.loads((INDICE / "meta.json").read_text(encoding="utf-8"))
    return registros, meta


def indice_disponible() -> bool:
    return _cargar() is not None


def buscar(pregunta: str, k: int = 5) -> list[Pasaje]:
    """Devuelve los k pasajes más relevantes (lista vacía si no hay índice)."""
    data = _cargar()
    if not data:
        return []
    registros, meta = data
    import numpy as np

    modelo_emb = meta.get("modelo_emb")
    emb_path = INDICE / "embeddings.npy"
    if modelo_emb and emb_path.exists():
        try:
            from sentence_transformers import SentenceTransformer
            modelo = _modelo_emb(modelo_emb)
            q = modelo.encode([f"query: {pregunta}"], normalize_embeddings=True)[0]
            sims = np.load(emb_path) @ q
        except Exception:
            sims = _tfidf_sims(pregunta, registros)
    else:
        sims = _tfidf_sims(pregunta, registros)

    orden = np.argsort(sims)[::-1][:k]
    out = []
    for i in orden:
        if sims[i] <= 0:
            continue
        r = registros[i]
        out.append(Pasaje(r.get("fuente", "?"), r.get("ref", ""), r.get("tipo", "prosa"),
                          r.get("texto", ""), float(sims[i])))
    return out


def contexto_citado(pregunta: str, k: int = 5, max_chars: int = 600) -> tuple[str, list[str]]:
    """Texto listo para inyectar al prompt + lista de citas. ('', []) si no hay índice."""
    pasajes = buscar(pregunta, k)
    if not pasajes:
        return "", []
    bloques, citas = [], []
    for p in pasajes:
        bloques.append(f"[{p.cita}] {p.texto[:max_chars].strip()}")
        citas.append(p.cita)
    return "\n\n".join(bloques), list(dict.fromkeys(citas))


@lru_cache(maxsize=2)
def _modelo_emb(nombre: str):
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(nombre)


def _tfidf_sims(pregunta: str, registros):
    import numpy as np
    from sklearn.metrics.pairwise import linear_kernel
    with open(INDICE / "tfidf.pkl", "rb") as f:
        idx = pickle.load(f)
    q = idx["vectorizer"].transform([pregunta])
    return linear_kernel(q, idx["matriz"]).ravel()
