"""
llm.py — Wrapper de LLM para los agentes, con modo offline.

Backends (elige el primero disponible):
  - GEMINI_API_KEY o GOOGLE_API_KEY → Gemini, capa GRATUITA. `pip install google-genai`.
    Modelo: CUEVA_MODELO_GEMINI (default gemini-2.5-flash).
  - ANTHROPIC_API_KEY → Claude (pago). Modelo: CUEVA_MODELO (default claude-sonnet-4-6).
  - Ninguna clave → MODO OFFLINE: devuelve una respuesta plausible y estructurada construida
    con los pasajes recuperados del RAG y el contexto. Sirve para que la plataforma funcione
    de punta a punta (UI, orquestación, ejecución de herramientas) sin clave, y para testear.

Así la "red de agentes que conversa" se puede ver moverse aunque todavía no haya API key.
"""
from __future__ import annotations

import os
import textwrap

import config

_CLIENTE = None
_BACKEND = None


def backend() -> str | None:
    """'gemini' > 'claude' > None, según qué clave haya en el entorno."""
    if os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"):
        return "gemini"
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "claude"
    return None


def disponible() -> bool:
    return backend() is not None


def _cliente(back: str):
    global _CLIENTE, _BACKEND
    if _CLIENTE is None or _BACKEND != back:
        if back == "gemini":
            from google import genai
            _CLIENTE = genai.Client()
        else:
            import anthropic
            _CLIENTE = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        _BACKEND = back
    return _CLIENTE


def completar(system: str, usuario: str, max_tokens: int = 1100,
              temperatura: float = 0.4) -> str:
    """Una llamada de chat. Cae a modo offline si no hay clave o falla el SDK."""
    back = backend()
    if back is None:
        return _offline(system, usuario)
    try:
        cliente = _cliente(back)
        if back == "gemini":
            from google.genai import types
            resp = cliente.models.generate_content(
                model=os.environ.get("CUEVA_MODELO_GEMINI", "gemini-2.5-flash"),
                contents=[types.Content(role="user", parts=[types.Part.from_text(text=usuario)])],
                config=types.GenerateContentConfig(system_instruction=system,
                                                   max_output_tokens=max_tokens,
                                                   temperature=temperatura),
            )
            return (resp.text or "").strip()
        msg = cliente.messages.create(
            model=config.MODELO_CLAUDE,
            max_tokens=max_tokens,
            temperature=temperatura,
            system=system,
            messages=[{"role": "user", "content": usuario}],
        )
        return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()
    except Exception as e:  # pragma: no cover
        return f"[⚠️ no pude llamar a {back}: {e}]\n\n" + _offline(system, usuario)


# ──────────────────────────────────────────────────────────────────────────
# Modo offline: una "maqueta" útil, no una alucinación.
# Extrae el rol del agente y los pasajes recuperados para devolver algo coherente.
# ──────────────────────────────────────────────────────────────────────────
def _offline(system: str, usuario: str) -> str:
    rol = "el agente"
    primera = system.strip().splitlines()[0] if system.strip() else ""
    for clave in ("Metodólogo", "Intérprete", "Crítico", "Bibliógrafo", "Orquestador"):
        if clave.lower() in (system + primera).lower():
            rol = "el " + clave
            break

    # rescatar pasajes de bibliografía que el agente recibió (vienen marcados con [fuente ref])
    citas = []
    for linea in usuario.splitlines():
        s = linea.strip()
        if s.startswith("[") and "]" in s[:60]:
            citas.append(s[1:s.index("]")])
    citas = list(dict.fromkeys(citas))[:3]

    pie = ""
    if citas:
        pie = "\n\nApoyado en: " + "; ".join(f"[{c}]" for c in citas)

    cuerpo = textwrap.dedent(f"""\
        (MODO OFFLINE — sin GEMINI_API_KEY ni ANTHROPIC_API_KEY. Esto es una maqueta de lo
        que diría {rol}; cargá una clave (Gemini es gratis) para respuestas reales fundamentadas.)

        Leí el estado de la mesa y la bibliografía recuperada. Mi aporte en esta fase:
        resumiría los pasajes citados, marcaría el supuesto clave a verificar y propondría
        el siguiente paso concreto del análisis.""")
    return cuerpo + pie
