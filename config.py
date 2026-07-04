"""
config.py — Rutas y configuración central de La Cueva del Economista.

Detecta automáticamente las carpetas de datos del Trabajo Final y de ANÁLISIS MATRIZ ARG
si están como carpetas hermanas de este repo. Todo se puede sobreescribir con variables de
entorno o con un archivo `cueva.local.toml` en la raíz (no se versiona).

Variables de entorno reconocidas:
    CUEVA_TRABAJO_FINAL   → carpeta raíz del Trabajo Final (la que contiene data/Variables Finales)
    CUEVA_MATRIZ_ARG      → carpeta ANÁLISIS MATRIZ ARG (la que contiene Series/)
    CUEVA_MODELO_GEMINI   → modelo de Gemini (default: gemini-2.5-flash)
    GEMINI_API_KEY / GOOGLE_API_KEY → clave de Gemini, GRATIS (https://aistudio.google.com/apikey)
    CUEVA_MODELO          → modelo de Claude (default: claude-sonnet-4-6)
    ANTHROPIC_API_KEY     → clave de Claude, de pago (si falta ninguna clave, modo offline)
"""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INDICE_RAG = ROOT / "rag" / "_indice"
KNOWLEDGE_BASE = ROOT / "knowledge-base"

# Cargar .env acá (una sola vez, apenas se importa config) para que las claves lleguen sin
# tener que exportarlas a mano en cada terminal — vale para server/app.py, mesa_cli.py, etc.
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass

MODELO_CLAUDE = os.environ.get("CUEVA_MODELO", "claude-sonnet-4-6")


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
    return _primero_que_existe([
        os.environ.get("CUEVA_TRABAJO_FINAL"),
        _LOCAL.get("trabajo_final"),
        ROOT.parent / "Trabajo Final" / "Trabajo",
        ROOT.parent.parent / "ECONOMICS" / "TRABAJO FINAL" / "Trabajo",
        ROOT.parent / "Trabajo",
    ])


def carpeta_matriz_arg() -> Path | None:
    """Carpeta ANÁLISIS MATRIZ ARG (contiene Series/)."""
    return _primero_que_existe([
        os.environ.get("CUEVA_MATRIZ_ARG"),
        _LOCAL.get("matriz_arg"),
        ROOT.parent / "ANÁLISIS MATRIZ ARG",
        ROOT.parent / "ANALISIS MATRIZ ARG",
    ])


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
    return {
        "root": str(ROOT),
        "trabajo_final": str(tf) if tf else None,
        "matriz_arg": str(ma) if ma else None,
        "indice_rag": str(INDICE_RAG) if INDICE_RAG.exists() else None,
        "backend_llm": back,
        "modelo": (os.environ.get("CUEVA_MODELO_GEMINI", "gemini-2.5-flash") if back == "gemini"
                   else MODELO_CLAUDE),
        "api_key": back is not None,
    }


if __name__ == "__main__":
    import json
    print(json.dumps(diagnostico(), indent=2, ensure_ascii=False))
