#!/usr/bin/env python3
"""preguntar — Consulta suelta a La Cueva-LM: pregunta → pasajes citados → respuesta fundamentada.

Usa embeddings multilingües si el índice los tiene (preguntás en español, recupera en
inglés); si no, cae a TF-IDF. Con clave de LLM (Gemini gratis > Claude), redacta la
respuesta citada; sin clave, muestra solo los pasajes.

Uso:
    python scripts/preguntar.py "¿Para qué sirve el test de Dickey-Fuller aumentado?"
    python scripts/preguntar.py "¿Cómo estimo un VECM en Python con statsmodels?" -k 6
"""

from __future__ import annotations

import argparse
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cueva import config, llm  # noqa: E402
from cueva.conocimiento import buscar, indice_disponible  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="Consultar La Cueva-LM")
    ap.add_argument("pregunta")
    ap.add_argument("-k", type=int, default=5)
    args = ap.parse_args()

    if not indice_disponible():
        raise SystemExit("No hay índice. Corré primero: python scripts/ingestar.py knowledge-base/corpus")

    pasajes = buscar(args.pregunta, args.k)

    print("=" * 78)
    print(f"❓ {args.pregunta}")
    print("=" * 78)

    if not pasajes:
        print("Sin pasajes relevantes. Reformulá o cargá bibliografía que lo cubra.")
        return

    print(f"\n📚 Pasajes recuperados (top {len(pasajes)}):\n")
    for p in pasajes:
        etiqueta = "🐍 código" if p.tipo == "codigo" else "📖 teoría"
        print(f"  ▸ {etiqueta}  [{p.cita}]  (relevancia {p.score:.2f})")
        print(
            textwrap.fill(
                p.texto[:280].replace("\n", " "), width=76, initial_indent="    ", subsequent_indent="    "
            )
        )
        print()

    if not llm.disponible():
        print("-" * 78)
        print("🔑 Sin clave de LLM: opción GRATIS en https://aistudio.google.com/apikey (GEMINI_API_KEY).")
        return

    system = (config.KNOWLEDGE_BASE / "prompts" / "metodologo.md").read_text(encoding="utf-8")
    contexto = "\n\n".join(f"[{p.cita}] {p.texto}" for p in pasajes)
    r = llm.completar(
        system,
        f"Bibliografía y código recuperados:\n\n{contexto}\n\n---\nPregunta: {args.pregunta}",
        max_tokens=1200,
    )
    print("-" * 78)
    print(f"🧭 Respuesta fundamentada ({r.backend}):\n")
    print(textwrap.fill(r.texto, width=78))


if __name__ == "__main__":
    main()
