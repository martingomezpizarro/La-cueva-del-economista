#!/usr/bin/env python3
"""evaluar_rag — mide la calidad de la recuperación con las preguntas doradas.

"El RAG mejoró/empeoró" se mide, no se siente: cada pregunta de tests/eval_rag.jsonl
declara qué fuentes DEBERÍAN aparecer en el top-k. El script reporta aciertos@1/@3/@5
y el detalle por pregunta. Corre contra el índice real (no en CI: allí no hay corpus).

Uso:
    python scripts/evaluar_rag.py                 # el mejor modo disponible
    python scripts/evaluar_rag.py --modo tfidf    # forzar TF-IDF (comparar modos)
    python scripts/evaluar_rag.py --modo embeddings
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cueva import config  # noqa: E402
from cueva.conocimiento import buscar, indice_disponible  # noqa: E402

EVAL = config.ROOT / "tests" / "eval_rag.jsonl"


def evaluar(modo: str | None = None, k: int = 5, verboso: bool = True) -> dict:
    casos = [json.loads(line) for line in EVAL.read_text(encoding="utf-8").splitlines() if line.strip()]
    aciertos = {1: 0, 3: 0, 5: 0}
    detalle = []

    def _hit(fuentes: list[str], esperadas: list[str], top: int) -> bool:
        return any(any(e in f.lower() for e in esperadas) for f in fuentes[:top])

    for caso in casos:
        pasajes = buscar(caso["pregunta"], k=k, modo=modo)
        fuentes = [p.fuente for p in pasajes]
        esperadas = [e.lower() for e in caso["fuentes_esperadas"]]
        for top in aciertos:
            aciertos[top] += _hit(fuentes, esperadas, top)
        hit3 = _hit(fuentes, esperadas, 3)
        detalle.append({"tema": caso["tema"], "hit@3": hit3, "top": fuentes[:3]})
        if verboso:
            marca = "✅" if hit3 else "❌"
            print(f"  {marca} {caso['tema']:32s} → {', '.join(f[:36] for f in fuentes[:3]) or '(nada)'}")

    n = len(casos)
    resumen = {f"aciertos@{t}": f"{a}/{n}" for t, a in aciertos.items()}
    resumen["tasa@3"] = round(aciertos[3] / n, 2) if n else 0.0
    if verboso:
        print(
            f"\n  Resultado ({modo or 'mejor disponible'}): "
            + " · ".join(f"{k_}={v}" for k_, v in resumen.items())
        )
    return {"modo": modo, "n": n, **resumen, "detalle": detalle}


def main():
    ap = argparse.ArgumentParser(description="Evaluación de retrieval de La Cueva-LM")
    ap.add_argument(
        "--modo",
        choices=["tfidf", "embeddings"],
        default=None,
        help="forzar un modo de recuperación (default: el mejor disponible)",
    )
    ap.add_argument("-k", type=int, default=5)
    args = ap.parse_args()

    if not indice_disponible():
        raise SystemExit("No hay índice. Corré primero: python scripts/ingestar.py knowledge-base/corpus")

    print("=" * 78)
    print(f"📏 EVALUACIÓN DE RETRIEVAL — {EVAL.name} (modo: {args.modo or 'mejor disponible'})")
    print("=" * 78)
    evaluar(args.modo, args.k)


if __name__ == "__main__":
    main()
