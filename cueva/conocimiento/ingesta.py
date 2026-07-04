"""ingesta — carga de conocimiento a La Cueva-LM.

Acepta PDFs (teoría), código Python (.py), notebooks (.ipynb) y docs (.md/.txt).
Construye el índice en <repo>/indice/ (o CUEVA_INDICE):
  - TF-IDF (siempre): por palabra clave, liviano, sin dependencias pesadas.
    Se guarda SIN pickle (tfidf.json + tfidf_matriz.npz): cargarlo nunca ejecuta código.
  - Embeddings multilingües (si está instalado sentence-transformers): permite preguntar
    en español y recuperar bibliografía/código en inglés. Modelo: multilingual-e5-small.

Uso (CLI en scripts/ingestar.py):
    python scripts/ingestar.py knowledge-base/corpus
    python scripts/ingestar.py --no-embeddings archivo.md
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from cueva import config

MODELO_EMB = "intfloat/multilingual-e5-small"

EXT_CODIGO = {".py", ".r", ".jl", ".sql"}
EXT_TEXTO = {".md", ".txt", ".rst"}
EXT_OK = {".pdf", ".ipynb"} | EXT_CODIGO | EXT_TEXTO


def cargar_unidades(path):
    """Devuelve (texto, ref, tipo) por unidad lógica del archivo."""
    p = Path(path)
    ext = p.suffix.lower()
    if ext == ".pdf":
        import fitz  # pymupdf (import perezoso: los tests de texto no lo necesitan)

        doc = fitz.open(path)
        for i in range(doc.page_count):
            yield doc[i].get_text(), f"p.{i + 1}", "prosa"
    elif ext == ".ipynb":
        nb = json.loads(p.read_text(encoding="utf-8", errors="ignore"))
        for j, cell in enumerate(nb.get("cells", []), 1):
            src = "".join(cell.get("source", []))
            if src.strip():
                tipo = "codigo" if cell.get("cell_type") == "code" else "prosa"
                yield src, f"celda {j}", tipo
    elif ext in EXT_CODIGO or ext in EXT_TEXTO:
        tipo = "codigo" if ext in EXT_CODIGO else "prosa"
        lineas = p.read_text(encoding="utf-8", errors="ignore").splitlines()
        bloque = 55
        for ini in range(0, len(lineas), bloque):
            seg = "\n".join(lineas[ini : ini + bloque])
            if seg.strip():
                yield seg, f"líneas {ini + 1}-{min(ini + bloque, len(lineas))}", tipo


def trocear(texto, ref, fuente, tipo, max_chars=1000, overlap=150):
    if tipo == "prosa":
        texto = re.sub(r"\s+", " ", texto).strip()  # prosa: colapsar espacios
    else:
        texto = texto.strip()  # código: preservar formato
        max_chars = 1500
    if len(texto) < 40:
        return []
    out, ini = [], 0
    while ini < len(texto):
        frag = texto[ini : ini + max_chars]
        if len(frag) > 40:
            out.append({"fuente": fuente, "ref": ref, "tipo": tipo, "texto": frag})
        ini += max_chars - overlap
    return out


def expandir_archivos(entradas: list[str | Path]) -> list[Path]:
    """Si una entrada es carpeta, incluye todos sus archivos soportados (recursivo)."""
    archivos: list[Path] = []
    for a in entradas:
        p = Path(a)
        if p.is_dir():
            archivos += sorted(f for f in p.rglob("*") if f.suffix.lower() in EXT_OK)
        else:
            archivos.append(p)
    return archivos


def construir_tfidf(textos: list[str], indice: Path) -> None:
    """TF-IDF sin pickle: vocabulario+idf en JSON, matriz dispersa en .npz."""
    import numpy as np
    from scipy import sparse
    from sklearn.feature_extraction.text import TfidfVectorizer

    vec = TfidfVectorizer(sublinear_tf=True, ngram_range=(1, 2), min_df=2, max_df=0.6)
    matriz = vec.fit_transform(textos)
    vocabulario = {t: int(i) for t, i in vec.vocabulary_.items()}
    (indice / "tfidf.json").write_text(
        json.dumps(
            {"vocabulario": vocabulario, "idf": np.asarray(vec.idf_).tolist(), "ngram_max": 2},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    sparse.save_npz(indice / "tfidf_matriz.npz", matriz.tocsr())


def construir_embeddings(textos: list[str]):
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("  ℹ️  sentence-transformers no instalado → solo TF-IDF (preguntas en inglés).")
        return None
    print(f"  🌐 Calculando embeddings multilingües ({MODELO_EMB})…")
    modelo = SentenceTransformer(MODELO_EMB)
    # e5 requiere el prefijo 'passage:' en los documentos
    return modelo.encode(
        [f"passage: {t}" for t in textos],
        normalize_embeddings=True,
        show_progress_bar=True,
        batch_size=64,
    )


def ingestar(entradas: list[str | Path], *, embeddings: bool = True, verboso: bool = True) -> dict:
    """Ingesta completa: archivos/carpetas → índice en config.ruta_indice(). Devuelve el meta."""
    indice = config.ruta_indice()
    indice.mkdir(parents=True, exist_ok=True)

    registros = []
    for archivo in expandir_archivos(entradas):
        nombre = Path(archivo).stem.strip()
        n0 = len(registros)
        for texto, ref, tipo in cargar_unidades(archivo):
            registros.extend(trocear(texto, ref, nombre, tipo))
        if verboso:
            print(f"  📄 {nombre}: {len(registros) - n0} fragmentos")

    if not registros:
        raise SystemExit("No se extrajo contenido. ¿PDF escaneado (OCR) o tipo no soportado?")

    for i, r in enumerate(registros):
        r["id"] = i
    (indice / "fragmentos.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in registros), encoding="utf-8"
    )

    construir_tfidf([r["texto"] for r in registros], indice)

    meta = {"n": len(registros), "modelo_emb": None}
    if embeddings:
        vecs = construir_embeddings([r["texto"] for r in registros])
        if vecs is not None:
            import numpy as np

            np.save(indice / "embeddings.npy", vecs.astype("float32"))
            meta["modelo_emb"] = MODELO_EMB
    (indice / "meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")

    if verboso:
        print(f"✅ {len(registros)} fragmentos indexados → {indice}")
        print(f"   Recuperación: {'embeddings multilingües + TF-IDF' if meta['modelo_emb'] else 'TF-IDF'}")
    return meta
