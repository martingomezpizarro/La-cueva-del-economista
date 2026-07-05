"""skills — carga las definiciones de agentes desde knowledge-base/skills/.

Cada archivo .md es la FUENTE DE VERDAD de un agente:
  - frontmatter: `agente` (id), `rol` (etiqueta), `modelo` (tier barato/medio/claude),
    `sesgo_rag` (términos que enriquecen su búsqueda bibliográfica) y `herramientas`
    (lista blanca de herramientas que puede pedir vía function calling).
  - cuerpo del markdown: la identidad/system prompt del agente.

Editar un skill cambia al agente SIN tocar Python. Si falta el directorio o un campo,
se cae a valores razonables (la plataforma no se rompe por un skill a medias).
"""

from __future__ import annotations

import logging
import re

from cueva import config

log = logging.getLogger("cueva.agentes")

SKILLS_DIR = config.KNOWLEDGE_BASE / "skills"

_FRONT_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.S)
_TIERS_VALIDOS = {"barato", "medio", "claude"}


def _parsear_frontmatter(front: str) -> dict:
    """Parser mínimo línea-a-línea (clave: valor); las listas van como [a, b, c]."""
    datos: dict = {}
    for linea in front.splitlines():
        m = re.match(r"^(\w+):\s*(.+)$", linea.strip())
        if not m:
            continue
        clave, valor = m.group(1), m.group(2).strip()
        if valor.startswith("[") and valor.endswith("]"):
            datos[clave] = [x.strip() for x in valor[1:-1].split(",") if x.strip()]
        else:
            datos[clave] = valor
    return datos


def leer_skill(ruta) -> dict | None:
    """Devuelve {id, rol, tier, sesgo_rag, herramientas, cuerpo} o None si no es un skill."""
    texto = ruta.read_text(encoding="utf-8")
    m = _FRONT_RE.match(texto)
    if not m:
        return None
    datos = _parsear_frontmatter(m.group(1))
    if "agente" not in datos:
        return None
    tier = str(datos.get("modelo", "medio")).lower()
    if tier not in _TIERS_VALIDOS:
        tier = "medio"
    return {
        "id": datos["agente"].strip().lower(),
        "rol": datos.get("rol", datos["agente"]),
        "tier": tier,
        "sesgo_rag": datos.get("sesgo_rag", ""),
        "herramientas": datos.get("herramientas", []),
        "prioriza_usuario": str(datos.get("prioriza_usuario", "")).lower() in ("si", "sí", "true", "yes"),
        "cuerpo": texto[m.end() :].strip(),
    }


def cargar_definiciones() -> dict[str, dict]:
    """Todos los skills de knowledge-base/skills/ como {id: definición}."""
    defs: dict[str, dict] = {}
    if not SKILLS_DIR.exists():
        log.warning("no existe %s: los agentes usarán solo los defaults", SKILLS_DIR)
        return defs
    for ruta in sorted(SKILLS_DIR.glob("*.md")):
        if ruta.name.startswith(("_", "README")):
            continue
        try:
            d = leer_skill(ruta)
        except Exception as e:
            log.warning("skill ilegible %s: %s", ruta.name, e)
            continue
        if d:
            defs[d["id"]] = d
    return defs
