#!/usr/bin/env python3
"""Ingesta de conocimiento para La Cueva-LM.

Acepta PDFs (teoría), código Python (.py), notebooks (.ipynb) y docs (.md/.txt).
Construye dos índices de recuperación:
  - TF-IDF (siempre): por palabra clave, rápido, sin dependencias pesadas.
  - Embeddings multilingües (si está instalado sentence-transformers): permite preguntar
    en español y recuperar bibliografía/código en inglés. Modelo: multilingual-e5-small.

Uso:
    python rag/ingest.py "knowledge-base/corpus/01_fundamentos/Enders.pdf" [otros...]
    python rag/ingest.py --no-embeddings archivo.py     # solo TF-IDF

Genera en rag/_indice/:
    fragmentos.jsonl · tfidf.pkl · (embeddings.npy + meta.json)
"""
import argparse
import json
import pickle
import re
from pathlib import Path

import fitz  # pymupdf
from sklearn.feature_extraction.text import TfidfVectorizer

ROOT = Path(__file__).resolve().parent.parent
INDICE = ROOT / "rag" / "_indice"
MODELO_EMB = "intfloat/multilingual-e5-small"

EXT_CODIGO = {".py", ".r", ".jl", ".sql"}
EXT_TEXTO = {".md", ".txt", ".rst"}


def cargar_unidades(path):
    """Devuelve (texto, ref, tipo) por unidad lógica del archivo."""
    p = Path(path)
    ext = p.suffix.lower()
    if ext == ".pdf":
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
            seg = "\n".join(lineas[ini:ini + bloque])
            if seg.strip():
                yield seg, f"líneas {ini + 1}-{min(ini + bloque, len(lineas))}", tipo


def trocear(texto, ref, fuente, tipo, max_chars=1000, overlap=150):
    if tipo == "prosa":
        texto = re.sub(r"\s+", " ", texto).strip()        # prosa: colapsar espacios
    else:
        texto = texto.strip()                              # código: preservar formato
        max_chars = 1500
    if len(texto) < 40:
        return []
    out, ini = [], 0
    while ini < len(texto):
        frag = texto[ini:ini + max_chars]
        if len(frag) > 40:
            out.append({"fuente": fuente, "ref": ref, "tipo": tipo, "texto": frag})
        ini += max_chars - overlap
    return out


def construir_embeddings(textos):
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("  ℹ️  sentence-transformers no instalado → solo TF-IDF (preguntas en inglés).")
        return None
    print(f"  🌐 Calculando embeddings multilingües ({MODELO_EMB})…")
    modelo = SentenceTransformer(MODELO_EMB)
    # e5 requiere el prefijo 'passage:' en los documentos
    vecs = modelo.encode([f"passage: {t}" for t in textos],
                         normalize_embeddings=True, show_progress_bar=True,
                         batch_size=64)
    return vecs


def main():
    ap = argparse.ArgumentParser(description="Ingesta para La Cueva-LM")
    ap.add_argument("archivos", nargs="+", help="PDF/.py/.ipynb/.md/.txt")
    ap.add_argument("--no-embeddings", action="store_true")
    args = ap.parse_args()

    INDICE.mkdir(parents=True, exist_ok=True)

    # Expandir carpetas: si pasás un directorio, ingiere todos los archivos soportados.
    EXT_OK = {".pdf", ".ipynb"} | EXT_CODIGO | EXT_TEXTO
    archivos = []
    for a in args.archivos:
        p = Path(a)
        if p.is_dir():
            archivos += sorted(str(f) for f in p.rglob("*") if f.suffix.lower() in EXT_OK)
        else:
            archivos.append(a)

    registros = []
    for archivo in archivos:
        nombre = Path(archivo).stem.strip()
        n0 = len(registros)
        for texto, ref, tipo in cargar_unidades(archivo):
            registros.extend(trocear(texto, ref, nombre, tipo))
        print(f"  📄 {nombre}: {len(registros) - n0} fragmentos")

    if not registros:
        raise SystemExit("No se extrajo contenido. ¿PDF escaneado (OCR) o tipo no soportado?")

    for i, r in enumerate(registros):
        r["id"] = i
    (INDICE / "fragmentos.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in registros), encoding="utf-8")

    # TF-IDF (siempre)
    vec = TfidfVectorizer(sublinear_tf=True, ngram_range=(1, 2), min_df=2, max_df=0.6)
    matriz = vec.fit_transform([r["texto"] for r in registros])
    with open(INDICE / "tfidf.pkl", "wb") as f:
        pickle.dump({"vectorizer": vec, "matriz": matriz}, f)

    # Embeddings (si se puede)
    meta = {"n": len(registros), "modelo_emb": None}
    if not args.no_embeddings:
        vecs = construir_embeddings([r["texto"] for r in registros])
        if vecs is not None:
            import numpy as np
            np.save(INDICE / "embeddings.npy", vecs.astype("float32"))
            meta["modelo_emb"] = MODELO_EMB
    (INDICE / "meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")

    print(f"✅ {len(registros)} fragmentos indexados → {INDICE}")
    print(f"   Recuperación: {'embeddings multilingües + TF-IDF' if meta['modelo_emb'] else 'TF-IDF'}")


if __name__ == "__main__":
    main()
