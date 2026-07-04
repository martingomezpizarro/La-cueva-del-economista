"""fichas — acceso a las fichas metodológicas (el ingrediente secreto).

Una ficha = 1 página por método con supuestos, errores típicos y cuándo usar / cuándo no
(knowledge-base/fichas/). Se eligen por solapamiento de vocabulario con el contexto.
"""

from __future__ import annotations

import re

from cueva import config

FICHAS_DIR = config.KNOWLEDGE_BASE / "fichas"

_PALABRA = re.compile(r"[a-záéíóúñü]{4,}")


def _palabras(texto: str) -> set[str]:
    return set(_PALABRA.findall(texto.lower()))


def fichas_relevantes(contexto: str, n: int = 3) -> list[tuple[str, str]]:
    """Top-n fichas (nombre, texto) por solapamiento de vocabulario con el contexto."""
    if not FICHAS_DIR.exists():
        return []
    q = _palabras(contexto)
    puntuadas = []
    for f in sorted(FICHAS_DIR.glob("*.md")):
        if f.name.startswith("_"):
            continue
        texto = f.read_text(encoding="utf-8")
        score = len(q & _palabras(texto))
        if score > 0:
            puntuadas.append((score, f.stem, texto))
    puntuadas.sort(reverse=True)
    return [(nombre, texto) for _, nombre, texto in puntuadas[:n]]
