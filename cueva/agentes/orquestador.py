"""orquestador — Conduce la conversación entre los agentes.

Recorre las fases de una investigación (encuadre → exploratorio → control → modelización →
interpretación → conclusiones). En cada fase:
  1. ejecuta las herramientas econométricas estándar de la fase (modo híbrido),
  2. da los turnos que indica el PIPELINE elegido (ver `pipelines.py`: el guion es un dato),
     respetando los HANDOFFS (si un agente interpela a otro, ese otro responde),
  3. fija un hallazgo que sintetiza lo discutido.

`correr()` es un GENERADOR: rinde cada Mensaje apenas se produce (incluidos los mensajes de
herramientas que un agente pide vía function calling), para que la UI muestre la mesa en vivo.
Cada sesión lleva un ContadorTokens (queda en pizarra.uso_llm) y un Transcript JSONL
(data/proyectos/{id}.transcript.jsonl) que la hace auditable.
"""

from __future__ import annotations

from collections.abc import Iterator

from cueva import config, llm
from cueva.llm import ContadorTokens, Transcript

from .agentes import AGENTES
from .modelos import FASE_LABEL, FASES, Hallazgo, Mensaje, Proyecto
from .pipelines import PIPELINES, turnos_de
from .pizarra import Pizarra

try:
    from cueva.econometria import herramientas as H
except Exception:  # pragma: no cover
    H = None

# Techo de llamadas al LLM por sesión de mesa (guion completo ≈ 13-18; margen para handoffs
# y rondas de function calling: hasta 6 turnos con tool-use × 3 rondas extra cada uno).
# Al agotarse, los turnos restantes salen en modo offline.
LIMITE_LLAMADAS_MESA = 60


class Orquestador:
    def __init__(
        self,
        proyecto: Proyecto,
        max_handoffs: int = 2,
        piz: Pizarra | None = None,
        pipeline: str = "clasica",
    ):
        if pipeline not in PIPELINES:
            raise ValueError(f"Pipeline desconocido: {pipeline} (hay: {', '.join(PIPELINES)})")
        self.piz = piz if piz is not None else Pizarra(proyecto)
        self.max_handoffs = max_handoffs
        self.pipeline = pipeline
        self.contador = ContadorTokens(limite_llamadas=LIMITE_LLAMADAS_MESA)
        self.transcript = Transcript(config.ruta_datos() / "proyectos" / f"{self.piz.id}.transcript.jsonl")

    # ── utilidades de publicación ─────────────────────────────────────────
    def _sistema(self, texto: str, fase: str = "general") -> Mensaje:
        return self.piz.publicar(
            Mensaje(autor="orquestador", rol="🎛️ Orquestador", contenido=texto, fase=fase)
        )

    def _evidencia(self, resultados: list[dict], fase: str) -> Mensaje | None:
        utiles = [r for r in resultados if r]
        if not utiles:
            return None
        lineas = []
        for r in utiles:
            marca = "✅" if r.get("ok") else "⚠️"
            lineas.append(f"{marca} {r.get('resumen', '(sin resumen)')}")
        # TODOS los resultados quedan en el mensaje (bug B1: antes solo el primero).
        return self.piz.publicar(
            Mensaje(
                autor="herramientas",
                rol="🧪 Herramientas",
                contenido="\n".join(lineas),
                fase=fase,
                herramientas=utiles,
            )
        )

    # ── un turno de agente, resolviendo su handoff ────────────────────────
    def _turno(
        self,
        agente_id: str,
        instruccion: str,
        *,
        evidencia=None,
        consulta_rag=None,
        responde_a=None,
        profundidad=0,
        permitir_herramientas=False,
    ) -> Iterator[Mensaje]:
        agente = AGENTES[agente_id]
        antes = len(self.piz.mensajes)
        msg = agente.intervenir(
            self.piz,
            instruccion,
            evidencia=evidencia,
            consulta_rag=consulta_rag,
            responde_a=responde_a,
            contador=self.contador,
            transcript=self.transcript,
            permitir_herramientas=permitir_herramientas,
        )
        # rinde TODO lo publicado en el turno (incluye la evidencia de tool-use, si hubo)
        yield from self.piz.mensajes[antes:]
        # resolver handoff (conversación encadenada, con límite de profundidad)
        if msg.handoff:
            destino = msg.handoff["destino"]
            pregunta = msg.handoff["pregunta"]
            if destino in AGENTES and destino != agente_id and profundidad < self.max_handoffs:
                yield from self._turno(
                    destino,
                    f"{AGENTES[agente_id].rol} te pregunta: «{pregunta}». "
                    f"Respondé concreto y, si querés, devolvé la pelota.",
                    responde_a=msg,
                    profundidad=profundidad + 1,
                )

    # ── herramientas por fase (lo que se ejecuta de verdad) ───────────────
    def _correr_herramientas(self, fase: str) -> list[dict]:
        if H is None:
            return []
        p = self.piz.proyecto
        series = p.series or []
        freq = p.frecuencia
        res: list[dict] = []
        if fase == "exploratorio":
            for sid in series[:6]:
                res.append(H.ejecutar("describir", sid=sid, freq=freq))
        elif fase == "control":
            for sid in series[:6]:
                res.append(H.ejecutar("estacionariedad", sid=sid, freq=freq))
            if len(series) >= 2:
                res.append(H.ejecutar("vecm", sids=series[:4], freq=freq))
        elif fase == "modelizacion":
            coint = next((r for r in self.evidencia_previa() if r.get("herramienta") == "vecm"), None)
            if coint and coint.get("rango_cointegracion", 0) > 0:
                res.append(H.ejecutar("vecm", sids=series[:4], freq=freq))
            elif p.serie_dependiente and len(series) >= 2:
                indeps = [s for s in series if s != p.serie_dependiente][:4]
                res.append(H.ejecutar("ols", dep=p.serie_dependiente, indeps=indeps, freq=freq))
                res.append(H.ejecutar("var", sids=series[:4], freq=freq))
            elif len(series) >= 2:
                res.append(H.ejecutar("var", sids=series[:4], freq=freq))
            elif len(series) == 1:
                res.append(H.ejecutar("garch", sid=series[0], freq=freq))
            # precedencia predictiva hacia la dependiente: evidencia base para el turno
            # causal (antes se le pedía leer "Granger" y Granger jamás se corría)
            dep = p.serie_dependiente or (series[0] if len(series) >= 2 else None)
            if dep and len(series) >= 2:
                for sx in [s for s in series if s != dep][:2]:
                    res.append(H.ejecutar("granger", sid_x=sx, sid_y=dep, freq=freq))
        return [r for r in res if r]

    def evidencia_previa(self) -> list[dict]:
        """Todos los resultados de herramientas ya publicados en la mesa."""
        out = []
        for m in self.piz.mensajes:
            if m.autor == "herramientas":
                out.extend(m.herramientas)
        return out

    # ── modo 2: líder supervisor, a demanda (no forma parte de correr()) ───
    def revisar(self, disparador: str = "") -> Iterator[Mensaje]:
        """El Líder mira el estado actual del proyecto (a demanda, sin correr toda la mesa)
        y decide si advierte algo, convoca a un especialista (HANDOFF) o da el visto bueno."""
        instruccion = (
            "Revisá cómo viene la investigación hasta ahora. Estado actual:\n\n"
            f"NOTAS DEL USUARIO:\n{self.piz.notas_texto()}\n\n"
            f"INFORME EN BORRADOR:\n{self.piz.informe_texto()}\n\n"
            + (f"LO QUE ACABA DE PASAR: {disparador}\n\n" if disparador else "")
            + "¿Está bien encaminado respecto a la pregunta/hipótesis, falta un paso previo, o "
            "conviene convocar a un especialista? Sé concreto."
        )
        yield from self._turno("lider", instruccion)
        self.piz.uso_llm = self.contador.to_dict()

    def _ultima_evidencia(self) -> list[dict]:
        """Todos los resultados de herramientas de la fase más reciente que tenga alguno."""
        for m in reversed(self.piz.mensajes):
            if m.autor == "herramientas" and m.herramientas:
                return [
                    r
                    for x in self.piz.mensajes
                    if x.autor == "herramientas" and x.fase == m.fase
                    for r in x.herramientas
                ]
        return []

    # ── síntesis de fase → hallazgo ───────────────────────────────────────
    def _fijar_hallazgo(self, fase: str) -> Mensaje:
        sys = (
            "Sos el relator de una mesa de econometría. Resumí en 1-2 oraciones, sin inventar, "
            "la conclusión operativa de esta fase a partir de lo que dijeron los agentes."
        )
        usuario = (
            f"Pregunta de investigación: {self.piz.proyecto.pregunta}\n"
            f"Fase: {FASE_LABEL.get(fase, fase)}\n\n"
            f"Conversación:\n{self.piz.transcripcion(ultimos=6)}"
        )
        r = llm.completar(
            sys, usuario, max_tokens=200, temperatura=0.2, contador=self.contador, transcript=self.transcript
        )
        self.piz.fijar_hallazgo(Hallazgo(fase=fase, texto=r.texto, autor="orquestador"))
        return self._sistema(f"📌 Hallazgo fijado · {FASE_LABEL.get(fase, fase)}: {r.texto}", fase=fase)

    # ── bucle principal ───────────────────────────────────────────────────
    def correr(self) -> Iterator[Mensaje]:
        p = self.piz.proyecto
        yield self._sistema(
            f"Abrimos la mesa para «{p.titulo}». Pregunta: {p.pregunta or '(sin definir)'}. "
            f"Series: {len(p.series)}. Pipeline: {self.pipeline}. "
            f"Modo IA: {llm.backend() or 'offline (sin API key)'}."
        )
        for fase, label, desc in FASES:
            self.piz.avanzar_fase(fase)
            yield self._sistema(f"━━━ {label} ━━━ {desc}", fase=fase)
            resultados = self._correr_herramientas(fase)
            ev = self._evidencia(resultados, fase)
            if ev is not None:
                yield ev
            for turno in turnos_de(self.pipeline, fase):
                yield from self._turno(
                    turno["agente"],
                    turno["tarea"],
                    evidencia=self._ultima_evidencia() if turno.get("evidencia") else None,
                    permitir_herramientas=bool(turno.get("herramientas")),
                )
            yield self._fijar_hallazgo(fase)
            self.piz.uso_llm = self.contador.to_dict()
        yield self._sistema(
            "Mesa cerrada. El usuario redacta; la mesa deja el andamiaje, la evidencia y las citas.",
            fase="conclusiones",
        )
        self.piz.uso_llm = self.contador.to_dict()


def investigar(proyecto: Proyecto, pipeline: str = "clasica") -> Pizarra:
    """Corre la mesa entera y devuelve la pizarra (versión no-streaming, para CLI/tests)."""
    orq = Orquestador(proyecto, pipeline=pipeline)
    for _ in orq.correr():
        pass
    return orq.piz
