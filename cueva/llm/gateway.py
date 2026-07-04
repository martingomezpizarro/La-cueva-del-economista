"""gateway — wrapper único de LLM con backoff, presupuesto y modo offline.

Backends (elige el primero disponible):
  - GEMINI_API_KEY o GOOGLE_API_KEY → Gemini, capa GRATUITA (`google-genai`).
  - ANTHROPIC_API_KEY → Claude (pago, `anthropic`).
  - Ninguna clave → MODO OFFLINE: devuelve una maqueta estructurada construida con el
    contexto recibido. La plataforma corre de punta a punta sin clave (y los tests en CI
    usan exclusivamente este camino: es determinista y cuesta $0).

Robustez (el free tier de Gemini limita las llamadas por minuto):
  - errores transitorios (429/quota/5xx/timeout) → reintento con backoff exponencial;
  - error definitivo → respuesta offline con `estado="error"` (el agente lo dice, no lo esconde);
  - presupuesto agotado → respuesta offline con `estado="presupuesto"`.
"""

from __future__ import annotations

import logging
import os
import random
import textwrap
import time
from dataclasses import dataclass

from cueva import config

from .presupuesto import ContadorTokens

log = logging.getLogger("cueva.llm")

_CLIENTE = None
_BACKEND = None


@dataclass
class Respuesta:
    texto: str
    backend: str  # "gemini" | "claude" | "offline"
    modelo: str = ""
    tokens_entrada: int = 0
    tokens_salida: int = 0
    intentos: int = 1
    estado: str = "ok"  # "ok" | "offline" | "error" | "presupuesto"


def backend() -> str | None:
    """'gemini' > 'claude' > None, según qué clave haya en el entorno."""
    return config.backend_llm()


def disponible() -> bool:
    return backend() is not None


# ──────────────────────────────────────────────────────────────────────────
# API pública
# ──────────────────────────────────────────────────────────────────────────
def completar(
    system: str,
    usuario: str,
    *,
    max_tokens: int = 1100,
    temperatura: float = 0.4,
    contador: ContadorTokens | None = None,
    reintentos: int = 3,
) -> Respuesta:
    """Una llamada de chat (un solo turno de usuario)."""
    return conversar(
        system,
        [{"role": "user", "content": usuario}],
        max_tokens=max_tokens,
        temperatura=temperatura,
        contador=contador,
        reintentos=reintentos,
    )


def conversar(
    system: str,
    messages: list[dict],
    *,
    max_tokens: int = 1100,
    temperatura: float = 0.4,
    contador: ContadorTokens | None = None,
    reintentos: int = 3,
) -> Respuesta:
    """Una llamada de chat con historial. messages: [{"role": "user"|"assistant", "content": str}]."""
    back = backend()
    ultimo = messages[-1]["content"] if messages else ""

    if back is None:
        return Respuesta(texto=_offline(system, ultimo), backend="offline", estado="offline")
    if contador is not None and contador.agotado():
        log.warning("presupuesto de llamadas agotado (%s)", contador.limite_llamadas)
        return Respuesta(
            texto="(PRESUPUESTO AGOTADO — esta sesión llegó a su límite de llamadas al LLM.)\n\n"
            + _offline(system, ultimo),
            backend="offline",
            estado="presupuesto",
        )

    ultimo_error: Exception | None = None
    for intento in range(1, reintentos + 1):
        try:
            t0 = time.time()
            resp = _llamar(back, system, messages, max_tokens, temperatura)
            resp.intentos = intento
            if contador is not None:
                contador.registrar(back, resp.tokens_entrada, resp.tokens_salida)
            log.info(
                "llm ok backend=%s modelo=%s intento=%d dur_ms=%d tokens=%d/%d",
                resp.backend,
                resp.modelo,
                intento,
                int((time.time() - t0) * 1000),
                resp.tokens_entrada,
                resp.tokens_salida,
            )
            return resp
        except Exception as e:  # noqa: BLE001 — el gateway ES la frontera de errores del LLM
            ultimo_error = e
            if _es_transitorio(e) and intento < reintentos:
                espera = 2**intento + random.uniform(0, 1)
                log.warning(
                    "llm transitorio backend=%s intento=%d: %s — reintento en %.1fs", back, intento, e, espera
                )
                time.sleep(espera)
            else:
                break

    log.error("llm falló backend=%s tras %d intento(s): %s", back, reintentos, ultimo_error)
    if contador is not None:
        contador.registrar(back, 0, 0, error=True)
    return Respuesta(
        texto=f"(⚠️ no pude llamar a {back}: {ultimo_error})\n\n" + _offline(system, ultimo),
        backend="offline",
        estado="error",
        intentos=reintentos,
    )


# ──────────────────────────────────────────────────────────────────────────
# Backends concretos (lo único que conoce los SDKs)
# ──────────────────────────────────────────────────────────────────────────
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


def _llamar(back: str, system: str, messages: list[dict], max_tokens: int, temperatura: float) -> Respuesta:
    """Una llamada cruda al backend. Lanza excepción si falla (el retry vive arriba)."""
    cliente = _cliente(back)
    if back == "gemini":
        from google.genai import types

        contents = [
            types.Content(
                role="user" if m["role"] == "user" else "model",
                parts=[types.Part.from_text(text=m["content"])],
            )
            for m in messages
        ]
        modelo = config.modelo_gemini()
        r = cliente.models.generate_content(
            model=modelo,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system, max_output_tokens=max_tokens, temperature=temperatura
            ),
        )
        uso = getattr(r, "usage_metadata", None)
        return Respuesta(
            texto=(r.text or "").strip(),
            backend="gemini",
            modelo=modelo,
            tokens_entrada=getattr(uso, "prompt_token_count", 0) or 0,
            tokens_salida=getattr(uso, "candidates_token_count", 0) or 0,
        )

    modelo = config.modelo_claude()
    msg = cliente.messages.create(
        model=modelo,
        max_tokens=max_tokens,
        temperature=temperatura,
        system=system,
        messages=messages,
    )
    texto = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()
    uso = getattr(msg, "usage", None)
    return Respuesta(
        texto=texto,
        backend="claude",
        modelo=modelo,
        tokens_entrada=getattr(uso, "input_tokens", 0) or 0,
        tokens_salida=getattr(uso, "output_tokens", 0) or 0,
    )


def _es_transitorio(e: Exception) -> bool:
    s = f"{type(e).__name__} {e}".lower()
    return any(
        m in s
        for m in (
            "429",
            "rate",
            "resource_exhausted",
            "quota",
            "503",
            "500",
            "overloaded",
            "timeout",
            "temporarily",
        )
    )


# ──────────────────────────────────────────────────────────────────────────
# Modo offline: una "maqueta" útil, no una alucinación.
# ──────────────────────────────────────────────────────────────────────────
def _offline(system: str, usuario: str) -> str:
    rol = "el agente"
    primera = system.strip().splitlines()[0] if system.strip() else ""
    for clave in ("Metodólogo", "Intérprete", "Crítico", "Bibliógrafo", "Líder", "Orquestador"):
        if clave.lower() in (system + primera).lower():
            rol = "el " + clave
            break

    # rescatar pasajes de bibliografía que el agente recibió (vienen marcados con [fuente ref])
    citas = []
    for linea in usuario.splitlines():
        s = linea.strip()
        if s.startswith("[") and "]" in s[:60]:
            citas.append(s[1 : s.index("]")])
    citas = list(dict.fromkeys(citas))[:3]

    pie = ""
    if citas:
        pie = "\n\nApoyado en: " + "; ".join(f"[{c}]" for c in citas)

    cuerpo = textwrap.dedent(
        f"""\
        (MODO OFFLINE — sin GEMINI_API_KEY ni ANTHROPIC_API_KEY. Esto es una maqueta de lo
        que diría {rol}; cargá una clave (Gemini es gratis) para respuestas reales fundamentadas.)

        Leí el estado de la mesa y la bibliografía recuperada. Mi aporte en esta fase:
        resumiría los pasajes citados, marcaría el supuesto clave a verificar y propondría
        el siguiente paso concreto del análisis."""
    )
    return cuerpo + pie
