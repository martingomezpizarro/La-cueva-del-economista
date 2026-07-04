"""
grafo_cueva.py — EQUIPO COMPLETO de La Cueva del Economista (pipeline por fases).

Cablea a los 10 especialistas definidos en knowledge-base/skills/ como nodos de un grafo
de LangGraph, recorriendo las fases de una investigación econométrica:

    🎯 ENCUADRE        → 👔 lider
    🔍 EXPLORATORIO    → 🧰 curador_datos · 🔧 transformaciones
    🧪 CONTROL         → 📊 multivariados · 🔎 critico
    📐 MODELIZACIÓN    → 📈 volatilidad · 🔮 pronostico_ml · 🧪 controles_causal · 🔬 robustez
    📖 INTERPRETACIÓN  → 📖 interprete
    🏁 CONCLUSIONES    → 👔 lider (síntesis)

Multi-modelo (cuida créditos): el tier de cada agente se LEE del frontmatter de su skill
(`modelo: Claude | medio | barato`) para que código y skills nunca queden desfasados.

    barato → Gemini Flash Lite   (CUEVA_MODELO_BARATO)
    medio  → Gemini Pro          (CUEVA_MODELO_MEDIO)
    claude → Claude              (CUEVA_MODELO_CLAUDE)

Si falta la API key de un tier (o el modelo falla), ESE nodo responde en MODO OFFLINE
(maqueta) y el grafo igual corre completo, para verlo moverse en Studio.
"""
from __future__ import annotations

import operator
import os
import re
import sys
from pathlib import Path
from typing import Annotated, TypedDict

from langgraph.graph import StateGraph, START, END

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Utilidades del proyecto (defensivo: si faltan deps, el grafo igual carga)
try:
    from mesa import rag_cliente
except Exception:
    rag_cliente = None
try:
    from econ import herramientas as H
except Exception:
    H = None


# ── Router de modelos ─────────────────────────────────────────────────────
# Tres tiers. Los nombres de modelo son configurables por variable de entorno.
def _modelo(tier: str):
    """'barato'/'medio' → Gemini · 'claude' → Claude. None si falta la API key del tier."""
    if tier in ("barato", "medio") and os.environ.get("GOOGLE_API_KEY"):
        from langchain_google_genai import ChatGoogleGenerativeAI
        nombre = (os.environ.get("CUEVA_MODELO_BARATO", "gemini-3.1-flash-lite")
                  if tier == "barato"
                  else os.environ.get("CUEVA_MODELO_MEDIO", "gemini-3.1-pro"))
        return ChatGoogleGenerativeAI(model=nombre, temperature=0.3)
    if tier == "claude" and os.environ.get("ANTHROPIC_API_KEY"):
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=os.environ.get("CUEVA_MODELO_CLAUDE", "claude-sonnet-4-6"),
            temperature=0.3, max_tokens=1100)
    return None


def _llamar(tier: str, system: str, user: str) -> str:
    """Una llamada al modelo del tier. Cae a modo offline si no hay clave o si el modelo falla."""
    m = _modelo(tier)
    if m is None:
        return (f"⚠️ (MODO OFFLINE — falta API key para el tier '{tier}'.) "
                f"Acá iría la respuesta real del agente, fundamentada en la bibliografía recuperada.")
    try:
        from langchain_core.messages import SystemMessage, HumanMessage
        r = m.invoke([SystemMessage(content=system), HumanMessage(content=user)])
        return r.content if isinstance(r.content, str) else str(r.content)
    except Exception as e:  # un modelo mal configurado no debe tumbar el grafo
        return (f"⚠️ (MODO OFFLINE — no pude llamar al modelo del tier '{tier}': {e}.) "
                f"Revisá el nombre del modelo o la API key; el resto del equipo sigue trabajando.")


# ── Skills: system prompt + tier de modelo, leídos del archivo del especialista ──
_FRONT_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)
_TIER_MAP = {"claude": "claude", "medio": "medio", "barato": "barato"}


def _leer_skill(nombre: str) -> tuple[str, str]:
    """Devuelve (system_prompt, tier) del especialista. Tolera ausencia de archivo/frontmatter."""
    p = ROOT / "knowledge-base" / "skills" / f"{nombre}.md"
    if not p.exists():
        return (f"Sos el agente {nombre} de 'La Cueva del Economista'.", "claude")
    texto = p.read_text(encoding="utf-8")
    tier = "claude"
    m = _FRONT_RE.match(texto)
    cuerpo = texto
    if m:
        front = m.group(1)
        cuerpo = texto[m.end():].strip()
        mm = re.search(r"^modelo:\s*(\w+)", front, re.M | re.I)
        if mm:
            tier = _TIER_MAP.get(mm.group(1).lower(), "claude")
    return (cuerpo or f"Sos el agente {nombre}.", tier)


# ── RAG: sesgo de búsqueda de bibliografía por especialista ────────────────
_SESGO = {
    "lider": "visión transversal pregunta de investigación método candidato objetivos",
    "curador_datos": "datos medición fuente procedencia calidad de la serie frecuencia huecos",
    "transformaciones": "transformaciones logaritmo diferencias desestacionalizar deflactar frecuencia",
    "multivariados": "VAR VECM cointegración Johansen orden de integración estacionariedad",
    "critico": "regresión espuria raíz unitaria quiebre estructural autocorrelación diagnóstico residuos",
    "volatilidad": "volatilidad GARCH heterocedasticidad condicional ARCH riesgo",
    "pronostico_ml": "pronóstico forecasting ARIMA machine learning evaluación fuera de muestra",
    "controles_causal": "inferencia causal controles variables instrumentales DiD control sintético",
    "robustez": "robustez selección de modelos especificación model averaging ajuste múltiple",
    "interprete": "interpretación coeficientes largo plazo velocidad de ajuste significancia económica",
}


def _rag(nombre: str, pregunta: str, k: int = 4) -> tuple[str, list[str]]:
    if rag_cliente is None:
        return ("", [])
    try:
        return rag_cliente.contexto_citado(f"{_SESGO.get(nombre, '')} {pregunta}", k=k)
    except Exception:
        return ("", [])


# ── Evidencia econométrica real por especialista (modo híbrido, sale $0) ───
def _evidencia(nombre: str, estado: "Estado") -> str:
    if H is None:
        return ""
    series, freq, dep = estado["series"], estado["freq"], estado["dependiente"]
    res: list[dict] = []
    try:
        if nombre == "curador_datos":
            for sid in series[:6]:
                res.append(H.ejecutar("describir", sid=sid, freq=freq))
        elif nombre == "transformaciones":
            for sid in series[:4]:
                res.append(H.ejecutar("estacionariedad", sid=sid, freq=freq))
        elif nombre == "multivariados":
            for sid in series[:4]:
                res.append(H.ejecutar("estacionariedad", sid=sid, freq=freq))
            if len(series) >= 2:
                res.append(H.ejecutar("vecm", sids=series[:4], freq=freq))
                res.append(H.ejecutar("var", sids=series[:4], freq=freq))
        elif nombre == "volatilidad":
            res.append(H.ejecutar("garch", sid=dep, freq=freq))
        elif nombre == "controles_causal":
            otras = [s for s in series if s != dep]
            if otras:
                res.append(H.ejecutar("granger", sid_x=otras[0], sid_y=dep, freq=freq))
        elif nombre == "robustez":
            indeps = [s for s in series if s != dep]
            if indeps:
                res.append(H.ejecutar("ols", dep=dep, indeps=indeps[:4], freq=freq))
    except Exception as e:
        return f"(no pude ejecutar herramientas: {e})"
    utiles = [r for r in res if r]
    if not utiles:
        return ""
    return "\n".join(f"- {('✅' if r.get('ok') else '⚠️')} {r.get('resumen', '(sin resumen)')}" for r in utiles)


# ── Estado que viaja por el grafo ─────────────────────────────────────────
class Estado(TypedDict, total=False):
    pregunta: str
    series: list[str]
    dependiente: str
    freq: str
    mensajes: Annotated[list[dict], operator.add]   # se acumula (Studio lo muestra)


def _defaults(estado: Estado) -> Estado:
    """Valores por defecto para que el equipo corra sin configurar nada."""
    estado.setdefault("pregunta", "¿Los depósitos totales ayudan a explicar las reservas brutas?")
    estado.setdefault("series", ["001_reservas_brutas", "021_dep_total"])
    estado.setdefault("dependiente", "001_reservas_brutas")
    estado.setdefault("freq", "mensual")
    return estado


def _transcripcion(estado: Estado, ultimos: int = 6) -> str:
    msgs = estado.get("mensajes", []) or []
    if not msgs:
        return "(la mesa recién arranca)"
    recientes = msgs[-ultimos:]
    return "\n".join(f"[{m.get('agente', '?')}] {str(m.get('texto', ''))[:400]}" for m in recientes)


# ── Fábrica de nodos: un nodo por especialista ─────────────────────────────
def _hacer_nodo(nombre: str, etiqueta: str, fase: str, tarea: str):
    """Crea la función-nodo de un especialista para una fase, con su tarea concreta."""

    def _nodo(estado: Estado) -> dict:
        estado = _defaults(dict(estado))
        system, tier = _leer_skill(nombre)
        evid = _evidencia(nombre, estado)
        biblio, citas = _rag(nombre, estado["pregunta"])

        partes = [
            f"=== PROYECTO ===\nPregunta: {estado['pregunta']}\n"
            f"Series: {', '.join(estado['series'])} (dependiente: {estado['dependiente']}) · "
            f"frecuencia {estado['freq']}.",
            f"=== FASE ACTUAL ===\n{fase}",
            f"=== LO QUE YA DIJO LA MESA ===\n{_transcripcion(estado)}",
        ]
        if evid:
            partes.append(f"=== EVIDENCIA ECONOMÉTRICA (ya ejecutada sobre tus series) ===\n{evid}")
        partes.append(f"=== BIBLIOGRAFÍA RECUPERADA (La Cueva-LM) ===\n{biblio or '(sin pasajes)'}")
        partes.append(f"=== TU TAREA AHORA ===\n{tarea}\n"
                      f"Sé breve (4-8 oraciones), citá la fuente entre corchetes cuando uses la bibliografía.")
        user = "\n\n".join(partes)

        texto = _llamar(tier, system, user)
        msg = {"agente": etiqueta, "tier": tier, "texto": texto, "fase": fase}
        if citas:
            msg["citas"] = citas
        if evid:
            msg["evidencia"] = evid
        return {"mensajes": [msg]}

    _nodo.__name__ = f"nodo_{nombre}"
    return _nodo


# ── Definición del pipeline: (id_nodo, agente, etiqueta, fase, tarea) ──────
# El líder aparece dos veces (encuadre y conclusiones) → dos nodos, mismo skill.
_PIPELINE = [
    ("lider_encuadre", "lider", "👔 Líder (encuadre)", "🎯 ENCUADRE",
     "Confirmá la pregunta, ordená objetivos e hipótesis y proponé el método candidato y el orden de trabajo."),
    ("curador_datos", "curador_datos", "🧰 Curador de datos", "🔍 EXPLORATORIO",
     "Revisá la calidad y forma de las series (rango, escala, huecos, outliers) y advertí qué cuidar antes de modelar."),
    ("transformaciones", "transformaciones", "🔧 Transformaciones", "🔍 EXPLORATORIO",
     "Recomendá las transformaciones necesarias (log, diferencias, desestacionalizar, deflactar, frecuencia) según la evidencia."),
    ("multivariados", "multivariados", "📊 Multivariados", "🧪 CONTROL",
     "Con los tests de estacionariedad y Johansen, decidí el modelo (niveles/diferencias/VECM) y justificá."),
    ("critico", "critico", "🔎 Crítico", "🧪 CONTROL",
     "Auditá lo dicho hasta acá: buscá raíz unitaria ignorada, espuria, quiebres o autocorrelación, y proponé cómo mitigar."),
    ("volatilidad", "volatilidad", "📈 Volatilidad", "📐 MODELIZACIÓN",
     "Evaluá si hay heterocedasticidad/volatilidad condicional relevante (GARCH) en la dependiente y qué implica."),
    ("pronostico_ml", "pronostico_ml", "🔮 Pronóstico / ML", "📐 MODELIZACIÓN",
     "Proponé un esquema de pronóstico y su evaluación fuera de muestra (benchmark naive, ARIMA/ETS, ML) si la pregunta lo amerita."),
    ("controles_causal", "controles_causal", "🧪 Controles / causal", "📐 MODELIZACIÓN",
     "Con Granger y el marco causal, distinguí precedencia predictiva de causalidad y advertí qué controles harían falta."),
    ("robustez", "robustez", "🔬 Robustez", "📐 MODELIZACIÓN",
     "Revisá la robustez de los resultados (especificaciones alternativas, sensibilidad, ajuste múltiple) y señalá fragilidades."),
    ("interprete", "interprete", "📖 Intérprete", "📖 INTERPRETACIÓN",
     "Traducí la evidencia y los modelos a economía clara: signos, magnitudes, largo plazo y conexión con la hipótesis."),
    ("lider_conclusiones", "lider", "👔 Líder (conclusiones)", "🏁 CONCLUSIONES",
     "Sintetizá la respuesta a la pregunta de investigación, los límites del análisis y el próximo paso concreto."),
]


# ── Armado del grafo ──────────────────────────────────────────────────────
_g = StateGraph(Estado)
_anterior = START
for _id, _agente, _etq, _fase, _tarea in _PIPELINE:
    _g.add_node(_id, _hacer_nodo(_agente, _etq, _fase, _tarea))
    _g.add_edge(_anterior, _id)
    _anterior = _id
_g.add_edge(_anterior, END)

grafo = _g.compile()


if __name__ == "__main__":
    print("Ejecutando el EQUIPO COMPLETO de La Cueva (pipeline por fases)…\n")
    salida = grafo.invoke({})
    fase_actual = None
    for m in salida["mensajes"]:
        if m.get("fase") != fase_actual:
            fase_actual = m.get("fase")
            print(f"\n{'═' * 70}\n{fase_actual}\n{'═' * 70}")
        print(f"\n[{m['agente']}  ·  modelo: {m.get('tier', '?')}]\n{m['texto']}")
        if m.get("citas"):
            print("   📚", "; ".join(m["citas"]))
