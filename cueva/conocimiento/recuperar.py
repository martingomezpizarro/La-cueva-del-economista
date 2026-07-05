"""recuperar — consulta al índice de La Cueva-LM: pregunta → pasajes citados.

Usa embeddings multilingües si el índice los tiene (preguntás en español, recupera
bibliografía en inglés); si no, cae a TF-IDF. El índice se carga una sola vez por proceso
(`limpiar_cache()` lo invalida, útil en tests y tras re-ingestar).

Colecciones (provenance): cada pasaje sabe si viene del corpus curado o de la biblioteca
subida por el usuario, y su cita lo marca. `buscar(..., coleccion=...)` filtra;
`contexto_citado(..., prioridad_usuario=True)` antepone la biblioteca del usuario
(la usa el Bibliógrafo).

Formato del índice (generado por `ingesta.py`, SIN pickle):
    fragmentos.jsonl   una línea JSON por fragmento {fuente, ref, tipo, texto, archivo, coleccion, id}
    meta.json          {"n": ..., "modelo_emb": ... | null, "colecciones": {...}}
    manifest.json      hash + nº de fragmentos por archivo (para la ingesta incremental)
    embeddings.npy     matriz float32 normalizada (si hay sentence-transformers)
    tfidf.json         {"vocabulario": {término: índice}, "idf": [...], "ngram_max": 2}
    tfidf_matriz.npz   matriz dispersa TF-IDF de los fragmentos (scipy)
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache

from cueva import config


@dataclass
class Pasaje:
    fuente: str
    ref: str
    tipo: str
    texto: str
    score: float
    coleccion: str = "corpus"

    @property
    def cita(self) -> str:
        base = f"{self.fuente} {self.ref}"
        return f"{base} · biblioteca del usuario" if self.coleccion == "usuario" else base


@lru_cache(maxsize=1)
def _cargar():
    indice = config.ruta_indice()
    frag = indice / "fragmentos.jsonl"
    if not frag.exists():
        return None
    registros = [json.loads(line) for line in frag.read_text(encoding="utf-8").splitlines() if line.strip()]
    meta = {}
    if (indice / "meta.json").exists():
        meta = json.loads((indice / "meta.json").read_text(encoding="utf-8"))
    return registros, meta


def limpiar_cache() -> None:
    """Invalida el índice cargado (llamar tras re-ingestar o al cambiar CUEVA_INDICE)."""
    _cargar.cache_clear()
    _modelo_emb.cache_clear()
    _tfidf_cargar.cache_clear()


def indice_disponible() -> bool:
    return _cargar() is not None


def buscar(
    pregunta: str, k: int = 5, *, coleccion: str | None = None, modo: str | None = None
) -> list[Pasaje]:
    """Devuelve los k pasajes más relevantes (lista vacía si no hay índice).

    - `coleccion`: filtrar por procedencia ("corpus" | "usuario"). None = todas.
    - `modo`: forzar "tfidf" o "embeddings" (para la evaluación); None = el mejor disponible.
    """
    data = _cargar()
    if not data:
        return []
    registros, meta = data
    import numpy as np

    indice = config.ruta_indice()
    modelo_emb = meta.get("modelo_emb")
    emb_path = indice / "embeddings.npy"
    usar_emb = modo != "tfidf" and modelo_emb and emb_path.exists()
    if modo == "embeddings" and not usar_emb:
        return []
    if usar_emb:
        try:
            modelo = _modelo_emb(modelo_emb)
            q = modelo.encode([f"query: {pregunta}"], normalize_embeddings=True)[0]
            sims = np.load(emb_path) @ q
        except Exception:
            sims = _tfidf_sims(pregunta)
    else:
        sims = _tfidf_sims(pregunta)

    if sims is None:
        return []
    orden = np.argsort(sims)[::-1]
    out: list[Pasaje] = []
    for i in orden:
        if sims[i] <= 0 or len(out) >= k:
            break
        r = registros[i]
        if coleccion and r.get("coleccion", "corpus") != coleccion:
            continue
        out.append(
            Pasaje(
                r.get("fuente", "?"),
                r.get("ref", ""),
                r.get("tipo", "prosa"),
                r.get("texto", ""),
                float(sims[i]),
                r.get("coleccion", "corpus"),
            )
        )
    return out


def contexto_citado(
    pregunta: str, k: int = 5, max_chars: int = 600, *, prioridad_usuario: bool = False
) -> tuple[str, list[str]]:
    """Texto listo para inyectar al prompt + lista de citas. ('', []) si no hay índice.

    Con `prioridad_usuario=True` (el Bibliógrafo), la biblioteca subida por el usuario va
    primero (hasta la mitad de los k lugares) y el corpus curado completa el resto.
    """
    if prioridad_usuario:
        del_usuario = buscar(pregunta, max(1, k // 2), coleccion="usuario")
        resto = [p for p in buscar(pregunta, k) if p.coleccion != "usuario"]
        pasajes = (del_usuario + resto)[:k]
    else:
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


# ──────────────────────────────────────────────────────────────────────────
# TF-IDF sin pickle: se reconstruye el vector de la consulta a mano con el
# vocabulario + idf guardados (mismo esquema que TfidfVectorizer(sublinear_tf=True)).
# ──────────────────────────────────────────────────────────────────────────
@lru_cache(maxsize=1)
def _tfidf_cargar():
    indice = config.ruta_indice()
    voc_path = indice / "tfidf.json"
    mat_path = indice / "tfidf_matriz.npz"
    if not voc_path.exists() or not mat_path.exists():
        return None
    import numpy as np
    from scipy import sparse

    d = json.loads(voc_path.read_text(encoding="utf-8"))
    vocabulario = d["vocabulario"]
    idf = np.asarray(d["idf"], dtype="float64")
    ngram_max = int(d.get("ngram_max", 2))
    matriz = sparse.load_npz(mat_path)
    return vocabulario, idf, ngram_max, matriz


def _tfidf_sims(pregunta: str):
    data = _tfidf_cargar()
    if data is None:
        return None
    import numpy as np
    from sklearn.feature_extraction.text import CountVectorizer
    from sklearn.preprocessing import normalize

    vocabulario, idf, ngram_max, matriz = data
    cv = CountVectorizer(vocabulary=vocabulario, ngram_range=(1, ngram_max))
    q = cv.transform([pregunta]).astype("float64")
    if q.nnz:
        q.data = 1.0 + np.log(q.data)  # sublinear_tf, igual que el índice
    q = normalize(q.multiply(idf).tocsr())
    return (matriz @ q.T).toarray().ravel()
