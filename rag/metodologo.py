#!/usr/bin/env python3
"""🧭 Agente Metodólogo — el primer agente-profesor de La Cueva del Economista.

A diferencia de ask.py (pregunta suelta → respuesta), el Metodólogo recibe el
CONTEXTO DEL ANÁLISIS (variable, frecuencia, objetivo, datos disponibles) y recomienda
el método correcto ANTES de que empieces, advirtiendo qué supuestos verificar.

Se apoya en:
  - La Cueva-LM (índice de rag/_indice/, mismo que ask.py) → pasajes citados.
  - Las fichas cara-al-agente (knowledge-base/fichas/) → supuestos y errores típicos.

Uso:
    # Descripción libre en un solo comando
    python rag/metodologo.py "Quiero explicar el riesgo país argentino (EMBI, mensual)
        con reservas del BCRA y tipo de cambio real. Objetivo: relación de largo plazo."

    # Campos estructurados (opcional, se combinan con la descripción)
    python rag/metodologo.py --variable "EMBI Argentina" --frecuencia mensual \
        --objetivo "relación de largo plazo con reservas y TCR"

    # Modo conversación (hacer repreguntas al Metodólogo)
    python rag/metodologo.py -i "..."

Redacción de la recomendación (elige el primero disponible):
  - GEMINI_API_KEY (o GOOGLE_API_KEY) → Gemini, capa GRATUITA. `pip install google-genai`.
    Key gratis en https://aistudio.google.com/apikey. Modelo: CUEVA_MODELO_GEMINI
    (default gemini-2.5-flash).
  - ANTHROPIC_API_KEY → Claude (pago). Modelo: CUEVA_MODELO (default claude-sonnet-4-6).
Sin ninguna clave, igual muestra los pasajes y fichas recuperados.
"""
import argparse
import os
import re
import sys
import textwrap
from pathlib import Path

# Reusar la recuperación de La Cueva-LM (ask.py vive en la misma carpeta)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ask import cargar_indice, recuperar  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FICHAS_DIR = ROOT / "knowledge-base" / "fichas"
PROMPT_BASE = (ROOT / "rag" / "prompts" / "metodologo.md").read_text(encoding="utf-8")

INSTRUCCIONES_SALIDA = """
SOS EL AGENTE METODÓLOGO: intervenís ANTES del análisis. Dado el contexto del usuario
(variable, frecuencia, objetivo, datos), tu salida debe tener esta estructura:

1. **Diagnóstico** — qué tipo de problema econométrico es (1-3 líneas).
2. **Método recomendado** — el camino principal y, si aplica, una alternativa. Justificá con la bibliografía.
3. **Supuestos a verificar primero** — tests concretos y en qué orden (ej.: ADF/KPSS antes de decidir VAR vs VECM).
4. **⚠️ Errores típicos a evitar** — los relevantes a ESTE análisis (usá las fichas).
5. **Plan de trabajo** — pasos numerados, del dato crudo al resultado.

Si el contexto del usuario está incompleto (no dice frecuencia, muestra, si las series
son I(0)/I(1), etc.), empezá señalando QUÉ falta y qué cambiaría según la respuesta.
Citá SIEMPRE fuente y referencia entre corchetes, ej.: [Enders p.360] o [ficha: granger_causalidad].
"""

PALABRA = re.compile(r"[a-záéíóúñü]{4,}")


def _palabras(texto):
    return set(PALABRA.findall(texto.lower()))


def fichas_relevantes(contexto, n=3):
    """Top-n fichas por solapamiento de vocabulario con el contexto del análisis."""
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


def armar_contexto_usuario(contexto, pasajes, fichas):
    bloques = []
    if fichas:
        cuerpo = "\n\n---\n\n".join(f"[ficha: {n}]\n{t}" for n, t in fichas)
        bloques.append(f"FICHAS METODOLÓGICAS (supuestos y errores típicos):\n\n{cuerpo}")
    if pasajes:
        cuerpo = "\n\n".join(f"[{p['fuente']} {p['ref']}] {p['texto']}" for p, _ in pasajes)
        bloques.append(f"BIBLIOGRAFÍA RECUPERADA DE LA CUEVA-LM:\n\n{cuerpo}")
    bloques.append(f"CONTEXTO DEL ANÁLISIS DEL USUARIO:\n\n{contexto}")
    return "\n\n{}\n\n".format("=" * 40).join(bloques)


SYSTEM = PROMPT_BASE + INSTRUCCIONES_SALIDA


def elegir_backend():
    """Devuelve (nombre, cliente) del primer LLM disponible: Gemini (gratis) > Claude."""
    if os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"):
        try:
            from google import genai
        except ImportError:
            raise SystemExit("Tenés GEMINI_API_KEY pero falta el paquete: pip install google-genai")
        return "gemini", genai.Client()  # toma la key del entorno
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            import anthropic
        except ImportError:
            raise SystemExit("Tenés ANTHROPIC_API_KEY pero falta el paquete: pip install anthropic")
        return "claude", anthropic.Anthropic()
    return None, None


def llamar_llm(backend, cliente, messages):
    """messages: [{'role': 'user'|'assistant', 'content': str}, ...] → texto de respuesta."""
    if backend == "gemini":
        from google.genai import types
        contents = [
            types.Content(role="user" if m["role"] == "user" else "model",
                          parts=[types.Part.from_text(text=m["content"])])
            for m in messages
        ]
        resp = cliente.models.generate_content(
            model=os.environ.get("CUEVA_MODELO_GEMINI", "gemini-2.5-flash"),
            contents=contents,
            config=types.GenerateContentConfig(system_instruction=SYSTEM,
                                               max_output_tokens=2000),
        )
        return resp.text
    msg = cliente.messages.create(
        model=os.environ.get("CUEVA_MODELO", "claude-sonnet-4-6"),
        max_tokens=2000,
        system=SYSTEM,
        messages=messages,
    )
    return msg.content[0].text


def mostrar_recuperado(pasajes, fichas, modo):
    print(f"\n📇 Fichas consultadas: {', '.join(n for n, _ in fichas) or '(ninguna)'}")
    print(f"📚 Pasajes recuperados ({modo}):")
    for p, score in pasajes:
        print(f"  ▸ [{p['fuente']} · {p['ref']}]  (relevancia {score:.2f})")


def main():
    ap = argparse.ArgumentParser(description="Agente Metodólogo de La Cueva del Economista")
    ap.add_argument("descripcion", nargs="?", default="",
                    help="Descripción libre del análisis que querés hacer")
    ap.add_argument("--variable", help="Variable(s) de interés, ej.: 'EMBI Argentina'")
    ap.add_argument("--frecuencia", help="diaria / mensual / trimestral…")
    ap.add_argument("--objetivo", help="qué querés responder / estimar")
    ap.add_argument("--datos", help="qué series tenés y período muestral")
    ap.add_argument("-k", type=int, default=8, help="pasajes a recuperar (default 8)")
    ap.add_argument("--fichas", type=int, default=3, help="fichas a incluir (default 3)")
    ap.add_argument("-i", "--interactivo", action="store_true",
                    help="modo conversación: repreguntar al Metodólogo")
    args = ap.parse_args()

    partes = [args.descripcion]
    for etiqueta, valor in [("Variable", args.variable), ("Frecuencia", args.frecuencia),
                            ("Objetivo", args.objetivo), ("Datos", args.datos)]:
        if valor:
            partes.append(f"{etiqueta}: {valor}")
    contexto = "\n".join(p for p in partes if p).strip()
    if not contexto:
        ap.error("Contá qué análisis querés hacer (descripción libre y/o --variable/--objetivo…)")

    registros, meta = cargar_indice()
    pasajes, modo = recuperar(contexto, registros, meta, args.k)
    fichas = fichas_relevantes(contexto, args.fichas)

    print("=" * 78)
    print("🧭 METODÓLOGO — La Cueva del Economista")
    print("=" * 78)
    print(textwrap.fill(contexto, width=76, initial_indent="  ", subsequent_indent="  "))
    mostrar_recuperado(pasajes, fichas, modo)

    backend, cliente = elegir_backend()
    if backend is None:
        print("\n🔑 Sin clave de LLM: te muestro lo recuperado, pero no puedo redactar la")
        print("    recomendación. Opción GRATIS: sacá una key en https://aistudio.google.com/apikey,")
        print("    hacé `pip install google-genai` y seteá GEMINI_API_KEY.")
        return

    messages = [{"role": "user", "content": armar_contexto_usuario(contexto, pasajes, fichas)}]
    respuesta = llamar_llm(backend, cliente, messages)
    print("\n" + "-" * 78)
    print(f"🧭 Recomendación del Metodólogo ({backend}):\n")
    print(respuesta)

    if not args.interactivo:
        return

    messages.append({"role": "assistant", "content": respuesta})
    print("\n💬 Modo conversación — repreguntá al Metodólogo (Enter vacío o 'salir' para terminar).")
    while True:
        try:
            pregunta = input("\nvos > ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not pregunta or pregunta.lower() in {"salir", "exit", "q"}:
            break
        # recuperar bibliografía fresca para la repregunta
        pasajes_p, _ = recuperar(pregunta, registros, meta, max(4, args.k // 2))
        extra = "\n\n".join(f"[{p['fuente']} {p['ref']}] {p['texto']}" for p, _ in pasajes_p)
        contenido = (f"BIBLIOGRAFÍA ADICIONAL RECUPERADA:\n\n{extra}\n\n---\n\n{pregunta}"
                     if extra else pregunta)
        messages.append({"role": "user", "content": contenido})
        respuesta = llamar_llm(backend, cliente, messages)
        messages.append({"role": "assistant", "content": respuesta})
        print("\n🧭 " + respuesta)


if __name__ == "__main__":
    main()
