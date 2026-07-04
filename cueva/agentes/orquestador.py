"""orquestador — Conduce la conversación entre los agentes.

Recorre las fases de una investigación (encuadre → exploratorio → control → modelización →
interpretación → conclusiones). En cada fase:
  1. ejecuta las herramientas econométricas estándar de la fase (modo híbrido),
  2. les da el turno a los agentes según un guion, pero respetando los HANDOFFS
     (si un agente interpela a otro, ese otro responde) — así emerge la conversación,
  3. fija un hallazgo que sintetiza lo discutido.

`correr()` es un GENERADOR: rinde cada Mensaje apenas se produce, para que la UI muestre la
mesa conversando en vivo. Lleva un ContadorTokens por sesión (queda en pizarra.uso_llm).
"""

from __future__ import annotations

from collections.abc import Iterator

from cueva import llm
from cueva.llm import ContadorTokens

from .agentes import AGENTES
from .modelos import FASE_LABEL, FASES, Hallazgo, Mensaje, Proyecto
from .pizarra import Pizarra

try:
    from cueva.econometria import herramientas as H
except Exception:  # pragma: no cover
    H = None

# Techo de llamadas al LLM por sesión de mesa (guion completo ≈ 13; margen para handoffs).
# Al agotarse, los turnos restantes salen en modo offline y lo dicen (degradación visible).
LIMITE_LLAMADAS_MESA = 30


class Orquestador:
    def __init__(self, proyecto: Proyecto, max_handoffs: int = 2, piz: Pizarra | None = None):
        self.piz = piz if piz is not None else Pizarra(proyecto)
        self.max_handoffs = max_handoffs
        self.contador = ContadorTokens(limite_llamadas=LIMITE_LLAMADAS_MESA)

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
        # TODOS los resultados quedan en el mensaje (antes solo el primero → se perdía
        # la prueba de cointegración y la mesa nunca elegía VECM; bug B1).
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
    ) -> Iterator[Mensaje]:
        agente = AGENTES[agente_id]
        msg = agente.intervenir(
            self.piz,
            instruccion,
            evidencia=evidencia,
            consulta_rag=consulta_rag,
            responde_a=responde_a,
            contador=self.contador,
        )
        yield msg
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
        return [r for r in res if r]

    def evidencia_previa(self) -> list[dict]:
        """Todos los resultados de herramientas ya publicados en la mesa."""
        out = []
        for m in self.piz.mensajes:
            if m.autor == "herramientas":
                out.extend(m.herramientas)
        return out

    # ── guion de agentes por fase ─────────────────────────────────────────
    def _guion(self, fase: str) -> Iterator[Mensaje]:
        if fase == "encuadre":
            yield from self._turno(
                "metodologo",
                "Aterrizá la pregunta en un diseño econométrico: ¿qué familia de modelos es candidata "
                "y por qué? Nombrá los 2-3 supuestos críticos a verificar antes de avanzar.",
            )
            yield from self._turno(
                "bibliografo",
                "¿Qué antecedentes o definiciones de la bibliografía respaldan o matizan el enfoque propuesto?",
            )
        elif fase == "exploratorio":
            yield from self._turno(
                "critico",
                "Mirá la evidencia descriptiva: forma, escala, posibles huecos/outliers/estacionalidad. "
                "¿Qué hay que tratar antes de testear o modelar?",
                evidencia=self._ultima_evidencia(),
            )
        elif fase == "control":
            yield from self._turno(
                "critico",
                "Leé los tests de estacionariedad y la prueba de cointegración. ¿Qué órdenes de integración hay? "
                "¿Riesgo de regresión espuria? ¿Hace falta diferenciar o usar marco de cointegración?",
                evidencia=self._ultima_evidencia(),
            )
            yield from self._turno(
                "metodologo",
                "Dado el control de series, fijá el método a estimar (en niveles, diferencias, VECM/ARDL) "
                "y justificá el orden de los pasos.",
            )
        elif fase == "modelizacion":
            yield from self._turno(
                "metodologo",
                "Comentá la estimación obtenida: ¿el modelo quedó bien especificado? ¿qué validar todavía?",
                evidencia=self._ultima_evidencia(),
            )
        elif fase == "interpretacion":
            yield from self._turno(
                "interprete",
                "Traducí los resultados a economía: signo, magnitud y significancia de lo relevante, "
                "conectándolo con la pregunta y las hipótesis. Citá la bibliografía que respalda la lectura.",
                evidencia=self._ultima_evidencia(),
            )
            yield from self._turno(
                "critico",
                "Auditá la interpretación: ¿la evidencia la sostiene o se está sobre-leyendo? "
                "¿algún diagnóstico pendiente (autocorrelación, estabilidad, espuria) que la debilite?",
            )
        elif fase == "conclusiones":
            yield from self._turno(
                "interprete",
                "Redactá una respuesta provisoria a la pregunta de investigación a partir de los hallazgos "
                "fijados, separando lo que la evidencia sostiene de lo conjetural, y nombrando límites.",
            )

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
        r = llm.completar(sys, usuario, max_tokens=200, temperatura=0.2, contador=self.contador)
        self.piz.fijar_hallazgo(Hallazgo(fase=fase, texto=r.texto, autor="orquestador"))
        return self._sistema(f"📌 Hallazgo fijado · {FASE_LABEL.get(fase, fase)}: {r.texto}", fase=fase)

    # ── bucle principal ───────────────────────────────────────────────────
    def correr(self) -> Iterator[Mensaje]:
        p = self.piz.proyecto
        yield self._sistema(
            f"Abrimos la mesa para «{p.titulo}». Pregunta: {p.pregunta or '(sin definir)'}. "
            f"Series: {len(p.series)}. Modo IA: {llm.backend() or 'offline (sin API key)'}."
        )
        for fase, label, desc in FASES:
            self.piz.avanzar_fase(fase)
            yield self._sistema(f"━━━ {label} ━━━ {desc}", fase=fase)
            resultados = self._correr_herramientas(fase)
            ev = self._evidencia(resultados, fase)
            if ev is not None:
                yield ev
            yield from self._guion(fase)
            yield self._fijar_hallazgo(fase)
            self.piz.uso_llm = self.contador.to_dict()
        yield self._sistema(
            "Mesa cerrada. El usuario redacta; la mesa deja el andamiaje, la evidencia y las citas.",
            fase="conclusiones",
        )
        self.piz.uso_llm = self.contador.to_dict()


def investigar(proyecto: Proyecto) -> Pizarra:
    """Corre la mesa entera y devuelve la pizarra (versión no-streaming, para CLI/tests)."""
    orq = Orquestador(proyecto)
    for _ in orq.correr():
        pass
    return orq.piz
