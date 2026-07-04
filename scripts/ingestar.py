#!/usr/bin/env python3
"""ingestar — CLI de ingesta de conocimiento para La Cueva-LM.

Uso:
    python scripts/ingestar.py knowledge-base/corpus            # todo el corpus
    python scripts/ingestar.py archivo.pdf otro.md              # archivos sueltos
    python scripts/ingestar.py --no-embeddings knowledge-base/corpus
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cueva.conocimiento import ingesta  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="Ingesta para La Cueva-LM")
    ap.add_argument("archivos", nargs="+", help="PDF/.py/.ipynb/.md/.txt o carpetas")
    ap.add_argument(
        "--no-embeddings",
        action="store_true",
        help="solo TF-IDF (sin sentence-transformers; recuperación por palabra clave)",
    )
    args = ap.parse_args()
    ingesta.ingestar(args.archivos, embeddings=not args.no_embeddings)


if __name__ == "__main__":
    main()
