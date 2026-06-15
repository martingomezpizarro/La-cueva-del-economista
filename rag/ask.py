#!/usr/bin/env python3
"""Consulta a La Cueva-LM: pregunta -> pasajes citados -> respuesta fundamentada.

Usa embeddings multilingües si el índice los tiene (preguntás en español, recupera en
inglés); si no, cae a TF-IDF. Con ANTHROPIC_API_KEY, Claude redacta la respuesta citada.

Uso:
    python rag/ask.py "¿Para qué sirve el test de Dickey-Fuller aumentado?"
    python rag/ask.py "¿Cómo estimo un VECM en Python con statsmodels?" -k 6
"""
import argparse
import json
import os
import pickle
import textwrap
from pathlib import Path

import numpy as np
from sklearn.metrics.pairwise import linear_kernel

ROOT = Path(__file__).resolve().parent.parent
INDICE = ROOT / "rag" / "_indice"
PROMPT_METODOLOGO = (ROOT / "rag" / "prompts" / "metodologo.md").read_text(encoding="utf-8")


def cargar_indice():
    frag_path = INDICE / "fragmentos.jsonl"
    if not frag_path.exists():
        raise SystemExit("No hay índice. Corré primero: python rag/ingest.py <archivo>")
    registros = [json.loads(l) for l in frag_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    meta = json.loads((INDICE / "meta.json").read_text(encoding="utf-8")) if (INDICE / "meta.json").exists() else {}
    return registros, meta


def recuperar(pregunta, registros, meta, k=5):
    modelo_emb = meta.get("modelo_emb")
    emb_path = INDICE / "embeddings.npy"
    if modelo_emb and emb_path.exists():
        from sentence_transformers import SentenceTransformer
        modelo = SentenceTransformer(modelo_emb)
        q = modelo.encode([f"query: {pregunta}"], normalize_embeddings=True)[0]
        M = np.load(emb_path)
        sims = M @ q
        modo = "embeddings multilingües"
    else:
        with open(INDICE / "tfidf.pkl", "rb") as f:
            idx = pickle.load(f)
        q = idx["vectorizer"].transform([pregunta])
        sims = linear_kernel(q, idx["matriz"]).ravel()
        modo = "TF-IDF (palabra clave)"
    orden = np.argsort(sims)[::-1][:k]
    return [(registros[i], float(sims[i])) for i in orden if sims[i] > 0], modo


def responder_con_claude(pregunta, pasajes):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    try:
        import anthropic
    except ImportError:
        return None
    contexto = "\n\n".join(f"[{p['fuente']} {p['ref']}] {p['texto']}" for p, _ in pasajes)
    cliente = anthropic.Anthropic(api_key=api_key)
    msg = cliente.messages.create(
        model=os.environ.get("CUEVA_MODELO", "claude-sonnet-4-6"),
        max_tokens=1200,
        system=PROMPT_METODOLOGO,
        messages=[{"role": "user",
                   "content": f"Bibliografía y código recuperados:\n\n{contexto}\n\n---\nPregunta: {pregunta}"}],
    )
    return msg.content[0].text


def main():
    ap = argparse.ArgumentParser(description="Consultar La Cueva-LM")
    ap.add_argument("pregunta")
    ap.add_argument("-k", type=int, default=5)
    args = ap.parse_args()

    registros, meta = cargar_indice()
    pasajes, modo = recuperar(args.pregunta, registros, meta, args.k)

    print("=" * 78)
    print(f"❓ {args.pregunta}")
    print(f"   (recuperación: {modo})")
    print("=" * 78)

    if not pasajes:
        print("Sin pasajes relevantes. Reformulá o cargá bibliografía que lo cubra.")
        return

    print(f"\n📚 Pasajes recuperados (top {len(pasajes)}):\n")
    for p, score in pasajes:
        etiqueta = "🐍 código" if p.get("tipo") == "codigo" else "📖 teoría"
        print(f"  ▸ {etiqueta}  [{p['fuente']} · {p['ref']}]  (relevancia {score:.2f})")
        print(textwrap.fill(p["texto"][:280].replace("\n", " "), width=76,
                            initial_indent="    ", subsequent_indent="    "))
        print()

    respuesta = responder_con_claude(args.pregunta, pasajes)
    print("-" * 78)
    if respuesta:
        print("🧭 Respuesta fundamentada del Metodólogo:\n")
        print(textwrap.fill(respuesta, width=78))
    else:
        print("🔑 Configurá ANTHROPIC_API_KEY (y `pip install anthropic`) para que Claude")
        print("    redacte la respuesta citada a partir de estos pasajes.")


if __name__ == "__main__":
    main()
