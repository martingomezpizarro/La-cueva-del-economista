"""gateway — wrapper único de LLM con backoff, presupuesto, transcript y function calling.

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

Function calling (`conversar_con_herramientas`, solo Gemini):
  el modelo puede PEDIR herramientas declaradas con JSON Schema; este módulo ejecuta el
  bucle pedido→ejecución→respuesta con un TOPE de ejecuciones y devuelve además la lista
  de resultados (para dejarlos como evidencia auditable en la pizarra). La decisión de QUÉ
  herramientas se ofrecen (lista blanca) es del llamador, nunca del modelo.
"""

from __future__ import annotations

import logging
import os
import random
import textwrap
import time
from dataclasses import dataclass, field

from cueva import config

from .presupuesto import ContadorTokens
from .transcript import Transcript

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
    llamadas_funcion: list = field(default_factory=list)  # [{"name", "args"}] pedidas por el modelo
    _partes_crudas: list = field(default_factory=list)  # partes SDK del turno del modelo (uso interno)


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
    modelo: str | None = None,
    transcript: Transcript | None = None,
) -> Respuesta:
    """Una llamada de chat (un solo turno de usuario)."""
    return conversar(
        system,
        [{"role": "user", "content": usuario}],
        max_tokens=max_tokens,
        temperatura=temperatura,
        contador=contador,
        reintentos=reintentos,
        modelo=modelo,
        transcript=transcript,
    )


def conversar(
    system: str,
    messages: list[dict],
    *,
    max_tokens: int = 1100,
    temperatura: float = 0.4,
    contador: ContadorTokens | None = None,
    reintentos: int = 3,
    modelo: str | None = None,
    transcript: Transcript | None = None,
) -> Respuesta:
    """Una llamada de chat con historial. messages: [{"role": "user"|"assistant", "content": str}]."""
    back = backend()
    ultimo = messages[-1]["content"] if messages else ""

    corte = _sin_backend(back, system, ultimo, contador)
    if corte is not None:
        _transcribir(transcript, system, ultimo, corte)
        return corte

    r = _con_reintentos(
        lambda: _llamar(back, system, messages, max_tokens, temperatura, modelo=modelo),
        back,
        reintentos,
        contador,
        fallback_usuario=ultimo,
        fallback_system=system,
    )
    _transcribir(transcript, system, ultimo, r)
    return r


def conversar_con_herramientas(
    system: str,
    messages: list[dict],
    *,
    declaraciones: list[dict],
    ejecutar_fn,
    max_herramientas: int = 3,
    max_tokens: int = 1100,
    temperatura: float = 0.4,
    contador: ContadorTokens | None = None,
    reintentos: int = 3,
    modelo: str | None = None,
    transcript: Transcript | None = None,
) -> tuple[Respuesta, list[dict]]:
    """Bucle de function calling (solo Gemini): el modelo pide herramientas, acá se ejecutan.

    - `declaraciones`: [{"name", "description", "parameters_json_schema"}] — la LISTA BLANCA.
    - `ejecutar_fn(nombre, args) -> dict`: ejecuta y devuelve el resultado (contrato de
      cueva.econometria: {"ok", "resumen", ...}).
    - Tope duro de `max_herramientas` ejecuciones; al alcanzarlo se fuerza respuesta en texto.

    Devuelve (respuesta_final, resultados_de_herramientas_ejecutadas).
    """
    back = backend()
    ultimo = messages[-1]["content"] if messages else ""

    corte = _sin_backend(back, system, ultimo, contador)
    if corte is not None:
        _transcribir(transcript, system, ultimo, corte)
        return corte, []
    if back != "gemini" or not declaraciones:
        # Claude sin tool-use implementado: cae a conversación normal (documentado).
        r = conversar(
            system,
            messages,
            max_tokens=max_tokens,
            temperatura=temperatura,
            contador=contador,
            reintentos=reintentos,
            modelo=modelo,
            transcript=transcript,
        )
        return r, []

    from google.genai import types

    contents = [
        types.Content(
            role="user" if m["role"] == "user" else "model",
            parts=[types.Part.from_text(text=m["content"])],
        )
        for m in messages
    ]
    ejecutadas: list[dict] = []
    r: Respuesta | None = None

    for _ronda in range(max_herramientas + 1):
        ofrecer = declaraciones if len(ejecutadas) < max_herramientas else None
        r = _con_reintentos(
            lambda ofrecer=ofrecer: _llamar(
                "gemini",
                system,
                contents,
                max_tokens,
                temperatura,
                modelo=modelo,
                herramientas=ofrecer,
                contents_crudos=True,
            ),
            "gemini",
            reintentos,
            contador,
            fallback_usuario=ultimo,
            fallback_system=system,
        )
        if r.estado != "ok" or not r.llamadas_funcion:
            break

        # el modelo pidió herramientas: ejecutarlas y devolverle los resultados
        contents.append(types.Content(role="model", parts=r._partes_crudas))
        partes_resp = []
        for llamada in r.llamadas_funcion:
            nombre, args = llamada["name"], llamada["args"]
            resultado = ejecutar_fn(nombre, args)
            ejecutadas.append(resultado)
            _transcribir(
                transcript,
                system,
                f"[herramienta] {nombre}({args})",
                r,
                herramienta=resultado.get("resumen", ""),
            )
            partes_resp.append(
                types.Part.from_function_response(name=nombre, response={"resultado": resultado})
            )
            if len(ejecutadas) >= max_herramientas:
                break
        contents.append(types.Content(role="user", parts=partes_resp))

    if r is not None:
        _transcribir(transcript, system, ultimo, r, n_herramientas=len(ejecutadas))
    return r, ejecutadas


# ──────────────────────────────────────────────────────────────────────────
# Núcleo: cortes previos, reintentos y transcript
# ──────────────────────────────────────────────────────────────────────────
def _sin_backend(back, system, ultimo, contador) -> Respuesta | None:
    """Cortes previos a llamar: sin clave → offline; presupuesto agotado → presupuesto."""
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
    return None


def _con_reintentos(
    hacer_llamada, back, reintentos, contador, *, fallback_usuario, fallback_system
) -> Respuesta:
    """Ejecuta una llamada con backoff exponencial; ante fallo definitivo degrada a offline."""
    ultimo_error: Exception | None = None
    for intento in range(1, reintentos + 1):
        try:
            t0 = time.time()
            resp = hacer_llamada()
            resp.intentos = intento
            if contador is not None:
                contador.registrar(back, resp.tokens_entrada, resp.tokens_salida)
            log.info(
                "llm ok backend=%s modelo=%s intento=%d dur_ms=%d tokens=%d/%d fn=%d",
                resp.backend,
                resp.modelo,
                intento,
                int((time.time() - t0) * 1000),
                resp.tokens_entrada,
                resp.tokens_salida,
                len(resp.llamadas_funcion),
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
        texto=f"(⚠️ no pude llamar a {back}: {ultimo_error})\n\n"
        + _offline(fallback_system, fallback_usuario),
        backend="offline",
        estado="error",
        intentos=reintentos,
    )


def _transcribir(transcript, system, ultimo_usuario, r: Respuesta, **extra) -> None:
    if transcript is None:
        return
    transcript.registrar(
        system=system,
        usuario=ultimo_usuario,
        respuesta=r.texto,
        backend=r.backend,
        modelo=r.modelo,
        estado=r.estado,
        tokens_entrada=r.tokens_entrada,
        tokens_salida=r.tokens_salida,
        **extra,
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


def _llamar(
    back: str,
    system: str,
    messages,
    max_tokens: int,
    temperatura: float,
    *,
    modelo: str | None = None,
    herramientas: list[dict] | None = None,
    contents_crudos: bool = False,
) -> Respuesta:
    """Una llamada cruda al backend. Lanza excepción si falla (el retry vive arriba).

    `messages` es la lista estándar de dicts, salvo `contents_crudos=True` (bucle de
    herramientas): ahí ya vienen como objetos Content del SDK de Gemini.
    """
    cliente = _cliente(back)
    if back == "gemini":
        from google.genai import types

        if contents_crudos:
            contents = messages
        else:
            contents = [
                types.Content(
                    role="user" if m["role"] == "user" else "model",
                    parts=[types.Part.from_text(text=m["content"])],
                )
                for m in messages
            ]
        nombre_modelo = modelo or config.modelo_gemini()
        cfg = dict(system_instruction=system, max_output_tokens=max_tokens, temperature=temperatura)
        if herramientas:
            cfg["tools"] = [
                types.Tool(
                    function_declarations=[
                        types.FunctionDeclaration(
                            name=h["name"],
                            description=h.get("description", ""),
                            parameters_json_schema=h.get("parameters_json_schema", {"type": "object"}),
                        )
                        for h in herramientas
                    ]
                )
            ]
        r = cliente.models.generate_content(
            model=nombre_modelo, contents=contents, config=types.GenerateContentConfig(**cfg)
        )
        uso = getattr(r, "usage_metadata", None)
        partes = []
        llamadas = []
        try:
            partes = list(r.candidates[0].content.parts or [])
        except Exception:
            partes = []
        for p in partes:
            fc = getattr(p, "function_call", None)
            if fc is not None:
                llamadas.append({"name": fc.name, "args": dict(fc.args or {})})
        texto = ""
        try:
            texto = (r.text or "").strip()
        except Exception:
            texto = ""
        return Respuesta(
            texto=texto,
            backend="gemini",
            modelo=nombre_modelo,
            tokens_entrada=getattr(uso, "prompt_token_count", 0) or 0,
            tokens_salida=getattr(uso, "candidates_token_count", 0) or 0,
            llamadas_funcion=llamadas,
            _partes_crudas=partes,
        )

    nombre_modelo = modelo or config.modelo_claude()
    msg = cliente.messages.create(
        model=nombre_modelo,
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
        modelo=nombre_modelo,
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
