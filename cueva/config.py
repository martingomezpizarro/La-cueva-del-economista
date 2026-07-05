"""config — rutas y configuración central de La Cueva del Economista.

Detecta automáticamente las carpetas de datos del Trabajo Final y de ANÁLISIS MATRIZ ARG
si están como carpetas hermanas de este repo. Todo se puede sobreescribir con variables de
entorno o con un archivo `cueva.local.toml` en la raíz (no se versiona).

Variables de entorno reconocidas:
    CUEVA_TRABAJO_FINAL   → carpeta raíz del Trabajo Final (la que contiene data/Variables Finales)
    CUEVA_MATRIZ_ARG      → carpeta ANÁLISIS MATRIZ ARG (la que contiene Series/)
    CUEVA_INDICE          → carpeta del índice RAG (default: <repo>/indice)
    CUEVA_MODELO_GEMINI   → modelo de Gemini (default: gemini-2.5-flash)
    GEMINI_API_KEY / GOOGLE_API_KEY → clave de Gemini, GRATIS (https://aistudio.google.com/apikey)
    CUEVA_MODELO          → modelo de Claude (default: claude-sonnet-4-6)
    ANTHROPIC_API_KEY     → clave de Claude, de pago (si falta toda clave: modo offline)
"""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_BASE = ROOT / "knowledge-base"

# Cargar .env una sola vez, apenas se importa config, para que las claves lleguen sin
# exportarlas a mano en cada terminal (server, CLIs, tests los cargan vía este import).
try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
except ImportError:
    pass


def ruta_indice() -> Path:
    """Carpeta del índice de La Cueva-LM (regenerable; no se versiona)."""
    return Path(os.environ.get("CUEVA_INDICE", ROOT / "indice"))


def ruta_datos() -> Path:
    """Carpeta de datos locales (proyectos guardados, transcripts). Override: CUEVA_DATA."""
    return Path(os.environ.get("CUEVA_DATA", ROOT / "data"))


def modelo_gemini() -> str:
    return os.environ.get("CUEVA_MODELO_GEMINI", "gemini-2.5-flash")


def modelo_claude() -> str:
    return os.environ.get("CUEVA_MODELO", "claude-sonnet-4-6")


def modelo_para_tier(tier: str) -> str:
    """Modelo de Gemini según el tier del skill (cuida la cuota del free tier).

    'barato' → flash-lite (agentes de trámite) · 'medio'/'claude' → flash (agentes de criterio).
    El tier 'claude' solo usa Anthropic si es el backend activo (decisión de costos: Gemini)."""
    if tier == "barato":
        return os.environ.get("CUEVA_MODELO_BARATO", "gemini-2.5-flash-lite")
    return modelo_gemini()


def _primero_que_existe(candidatos) -> Path | None:
    for c in candidatos:
        if c and Path(c).expanduser().exists():
            return Path(c).expanduser().resolve()
    return None


def _cargar_toml_local() -> dict:
    archivo = ROOT / "cueva.local.toml"
    if not archivo.exists():
        return {}
    try:
        import tomllib

        return tomllib.loads(archivo.read_text(encoding="utf-8"))
    except Exception:
        return {}


_LOCAL = _cargar_toml_local()


def carpeta_trabajo_final() -> Path | None:
    """Carpeta raíz del Trabajo Final (contiene data/Variables Finales)."""
    return _primero_que_existe(
        [
            os.environ.get("CUEVA_TRABAJO_FINAL"),
            _LOCAL.get("trabajo_final"),
            ROOT.parent / "Trabajo Final" / "Trabajo",
            ROOT.parent.parent / "ECONOMICS" / "TRABAJO FINAL" / "Trabajo",
            ROOT.parent / "Trabajo",
        ]
    )


def carpeta_matriz_arg() -> Path | None:
    """Carpeta ANÁLISIS MATRIZ ARG (contiene Series/)."""
    return _primero_que_existe(
        [
            os.environ.get("CUEVA_MATRIZ_ARG"),
            _LOCAL.get("matriz_arg"),
            ROOT.parent / "ANÁLISIS MATRIZ ARG",
            ROOT.parent / "ANALISIS MATRIZ ARG",
        ]
    )


def backend_llm() -> str | None:
    """'gemini' > 'claude' > None, según qué clave haya en el entorno."""
    if os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"):
        return "gemini"
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "claude"
    return None


def hay_api_key() -> bool:
    return backend_llm() is not None


def diagnostico() -> dict:
    """Resumen del estado de la configuración (para mostrar en la UI / CLI)."""
    tf = carpeta_trabajo_final()
    ma = carpeta_matriz_arg()
    back = backend_llm()
    indice = ruta_indice()
    return {
        "root": str(ROOT),
        "trabajo_final": str(tf) if tf else None,
        "matriz_arg": str(ma) if ma else None,
        "indice_rag": str(indice) if indice.exists() else None,
        "backend_llm": back,
        "modelo": modelo_gemini() if back == "gemini" else modelo_claude(),
        "api_key": back is not None,
    }


if __name__ == "__main__":
    import json

    print(json.dumps(diagnostico(), indent=2, ensure_ascii=False))
