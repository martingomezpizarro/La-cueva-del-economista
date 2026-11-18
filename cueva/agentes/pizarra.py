"""pizarra — El "blackboard" compartido de una sesión de investigación.

Es la memoria común que TODOS los agentes leen y escriben. El orquestador la usa para
decidir handoffs; la UI la lee para mostrar la conversación. Es la pieza que hace que los
agentes "conversen entre sí": cada uno ve lo que dijeron los demás y a quién se le habló.

Además de la conversación orquestada, la Pizarra es el "cuaderno" persistido de toda la
investigación: notas sueltas, el informe por secciones y los chats 1:1 con cada agente.

La persistencia (dónde y cómo se guarda, locks entre requests) NO vive acá:
ver cueva/sesiones/repositorio.py. La Pizarra solo sabe serializarse.
"""

from __future__ import annotations

import json
import threading
import time
import uuid
from pathlib import Path

from .modelos import AGENTES_IDS, FASE_LABEL, Hallazgo, Mensaje, Proyecto

SCHEMA_VERSION = 2

SECCIONES_INFORME = [
    "introduccion",
    "resumen_bibliografia",
    "desarrollo",
    "resultados",
    "conclusiones",
    "anexo",
]


def _ahora() -> float:
    return time.time()


class Pizarra:
    def __init__(self, proyecto: Proyecto):
        self.proyecto = proyecto
        self.mensajes: list[Mensaje] = []
        self.hallazgos: list[Hallazgo] = []
        self.fase_actual: str = "encuadre"
        self._lock = threading.Lock()
        self.id = proyecto.id

        self.notas: list[dict] = []
        self.informe: dict = {s: "" for s in SECCIONES_INFORME}
        self.secciones_ocultas: list[str] = []
        self.estudios: list[dict] = []
        # Tablero del proyecto (figuras fijadas) y bloques del Documento: los llenan la
        # Terminal, la Mesa y el asistente por MCP (ver cueva/api/mesa_compartida.py).
        self.figuras: list[dict] = []
        self.documento: list[dict] = []
        self.chats_agentes: dict[str, list[dict]] = {a: [] for a in AGENTES_IDS}
        self.uso_llm: dict = {}
        self.actualizado: float = _ahora()

    # ── escritura (conversación orquestada) ───────────────────────────────
    def publicar(self, msg: Mensaje) -> Mensaje:
        with self._lock:
            self.mensajes.append(msg)
            self.actualizado = _ahora()
        return msg

    def fijar_hallazgo(self, h: Hallazgo) -> Hallazgo:
        with self._lock:
            self.hallazgos.append(h)
            self.actualizado = _ahora()
        return h

    def avanzar_fase(self, fase: str):
        self.fase_actual = fase

    # ── escritura (cuaderno de trabajo) ───────────────────────────────────
    def agregar_nota(self, texto: str) -> dict:
        nota = {"texto": texto, "ts": _ahora()}
        with self._lock:
            self.notas.append(nota)
            self.actualizado = _ahora()
        return nota

    def actualizar_informe(self, seccion: str, texto: str) -> None:
        if seccion not in SECCIONES_INFORME:
            raise KeyError(f"Sección de informe desconocida: {seccion}")
        with self._lock:
            self.informe[seccion] = texto
            self.actualizado = _ahora()

    def toggle_seccion(self, nombre: str) -> bool:
        """Oculta/muestra una sección del Informe. Devuelve True si quedó oculta."""
        with self._lock:
            if nombre in self.secciones_ocultas:
                self.secciones_ocultas.remove(nombre)
                oculta = False
            else:
                self.secciones_ocultas.append(nombre)
                oculta = True
            self.actualizado = _ahora()
        return oculta

    def registrar_estudio(
        self, herramienta: str, args: dict, resumen: str, resultado: dict | None = None
    ) -> dict:
        """Registra una corrida de herramienta en el cuaderno. `resultado` guarda la evidencia
        completa (tablas, gráfico) para poder re-renderizarla en el banco de trabajo."""
        estudio = {
            "id": uuid.uuid4().hex[:8],
            "herramienta": herramienta,
            "args": args,
            "resumen": resumen,
            "resultado": resultado,
            "ts": _ahora(),
        }
        with self._lock:
            self.estudios.append(estudio)
            self.actualizado = _ahora()
        return estudio

    def quitar_estudio(self, estudio_id: str) -> bool:
        """Elimina un estudio del cuaderno por id. Devuelve True si existía."""
        with self._lock:
            antes = len(self.estudios)
            self.estudios = [e for e in self.estudios if e.get("id") != estudio_id]
            hubo = len(self.estudios) < antes
            if hubo:
                self.actualizado = _ahora()
        return hubo

    # ── tablero y documento (compartidos con la Terminal y el asistente) ───
    def fijar_figura(
        self,
        titulo: str,
        tipo: str,
        datos: dict | None = None,
        receta: dict | None = None,
        procedencia: dict | None = None,
        origen: str = "mesa",
        autor: str = "usuario",
    ) -> dict:
        """Fija una figura al tablero del proyecto. `datos` es el bloque a dibujar (el mismo
        formato de bloques tipados de los métodos: lineas, barras, tabla, sankey…) y `receta`
        + `procedencia` son la leyenda que el Documento muestra debajo."""
        fig = {
            "id": uuid.uuid4().hex[:8],
            "titulo": titulo,
            "tipo": tipo,
            "datos": datos,
            "receta": receta,
            "procedencia": procedencia,
            "origen": origen,
            "autor": autor,
            "ts": _ahora(),
        }
        with self._lock:
            self.figuras.append(fig)
            self.actualizado = _ahora()
        return fig

    def quitar_figura(self, figura_id: str) -> bool:
        with self._lock:
            antes = len(self.figuras)
            self.figuras = [f for f in self.figuras if f.get("id") != figura_id]
            hubo = len(self.figuras) < antes
            if hubo:
                # una figura que se va del tablero se va también del documento
                self.documento = [b for b in self.documento if b.get("figura_id") != figura_id]
                self.actualizado = _ahora()
        return hubo

    def insertar_bloque(
        self,
        seccion: str,
        tipo: str,
        texto: str = "",
        figura_id: str | None = None,
        posicion: int | None = None,
        autor: str = "usuario",
    ) -> dict:
        """Inserta un bloque (texto o figura del tablero) en una sección del Documento.
        `posicion` es el lugar dentro de la sección (None = al final)."""
        if seccion not in SECCIONES_INFORME:
            raise KeyError(f"Sección de informe desconocida: {seccion}")
        if tipo not in ("texto", "figura"):
            raise ValueError(f"Tipo de bloque desconocido: {tipo}")
        if tipo == "figura" and not any(f["id"] == figura_id for f in self.figuras):
            raise KeyError(f"La figura {figura_id} no está en el tablero")
        bloque = {
            "id": uuid.uuid4().hex[:8],
            "seccion": seccion,
            "tipo": tipo,
            "texto": texto,
            "figura_id": figura_id,
            "autor": autor,
            "ts": _ahora(),
        }
        with self._lock:
            de_la_seccion = [i for i, b in enumerate(self.documento) if b["seccion"] == seccion]
            if posicion is None or posicion >= len(de_la_seccion):
                donde = (de_la_seccion[-1] + 1) if de_la_seccion else len(self.documento)
            else:
                donde = de_la_seccion[max(posicion, 0)]
            self.documento.insert(donde, bloque)
            self.actualizado = _ahora()
        return bloque

    def editar_bloque(self, bloque_id: str, texto: str) -> dict:
        with self._lock:
            for b in self.documento:
                if b["id"] == bloque_id:
                    if b["tipo"] != "texto":
                        raise ValueError("Solo se edita el texto de un bloque de texto")
                    b["texto"] = texto
                    self.actualizado = _ahora()
                    return b
        raise KeyError(bloque_id)

    def mover_bloque(self, bloque_id: str, seccion: str, posicion: int | None = None) -> dict:
        with self._lock:
            b = next((x for x in self.documento if x["id"] == bloque_id), None)
            if b is None:
                raise KeyError(bloque_id)
            self.documento.remove(b)
        nuevo = self.insertar_bloque(seccion, b["tipo"], b["texto"], b["figura_id"], posicion, b["autor"])
        with self._lock:
            nuevo["id"], nuevo["ts"] = b["id"], b["ts"]  # es el mismo bloque, solo cambió de lugar
        return nuevo

    def quitar_bloque(self, bloque_id: str) -> bool:
        with self._lock:
            antes = len(self.documento)
            self.documento = [b for b in self.documento if b.get("id") != bloque_id]
            hubo = len(self.documento) < antes
            if hubo:
                self.actualizado = _ahora()
        return hubo

    def agregar_chat(self, agente_id: str, quien: str, texto: str) -> dict:
        # la validación de que el agente exista es de la capa API (contra AGENTES);
        # la pizarra acepta cualquier id para soportar agentes nuevos definidos por skills
        if agente_id not in self.chats_agentes:
            self.chats_agentes[agente_id] = []
        turno = {"quien": quien, "texto": texto, "ts": _ahora()}
        with self._lock:
            self.chats_agentes[agente_id].append(turno)
            self.actualizado = _ahora()
        return turno

    # ── lectura / contexto para los agentes ──────────────────────────────
    def transcripcion(self, ultimos: int | None = None) -> str:
        """Conversación reciente en texto plano, para inyectar en el prompt de un agente."""
        msgs = self.mensajes if ultimos is None else self.mensajes[-ultimos:]
        out = []
        for m in msgs:
            destino = f" → @{m.dirigido_a}" if m.dirigido_a else ""
            cita = f"  [cita: {'; '.join(m.citas)}]" if m.citas else ""
            out.append(f"[{m.rol}{destino}] {m.contenido}{cita}")
        return "\n\n".join(out) if out else "(la mesa todavía no dijo nada)"

    def hallazgos_texto(self) -> str:
        if not self.hallazgos:
            return "(sin hallazgos fijados aún)"
        return "\n".join(
            f"- ({FASE_LABEL.get(h.fase, h.fase)}) {h.texto}"
            + (f"  [cita: {'; '.join(h.citas)}]" if h.citas else "")
            for h in self.hallazgos
        )

    def notas_texto(self, ultimos: int = 6) -> str:
        notas = self.notas[-ultimos:]
        if not notas:
            return "(sin notas del usuario)"
        return "\n".join(f"- {n['texto']}" for n in notas)

    def informe_texto(self) -> str:
        escritas = {s: t for s, t in self.informe.items() if t.strip()}
        if not escritas:
            return "(informe todavía vacío)"
        return "\n\n".join(f"[{s}]\n{t}" for s, t in escritas.items())

    def chat_texto(self, agente_id: str, ultimos: int = 12) -> str:
        turnos = self.chats_agentes.get(agente_id, [])[-ultimos:]
        if not turnos:
            return "(sin conversación previa con este agente)"
        return "\n\n".join(f"[{t['quien']}] {t['texto']}" for t in turnos)

    def menciones_a(self, agente_id: str) -> list[Mensaje]:
        """Mensajes dirigidos explícitamente a un agente (para que responda los handoffs)."""
        return [m for m in self.mensajes if m.dirigido_a == agente_id]

    def ultimo_mensaje(self) -> Mensaje | None:
        return self.mensajes[-1] if self.mensajes else None

    # ── serialización (para la UI / persistencia) ────────────────────────
    def to_dict(self) -> dict:
        return {
            "schema_version": SCHEMA_VERSION,
            "id": self.id,
            "fase_actual": self.fase_actual,
            "proyecto": self.proyecto.to_dict(),
            "mensajes": [m.to_dict() for m in self.mensajes],
            "hallazgos": [h.to_dict() for h in self.hallazgos],
            "notas": self.notas,
            "informe": self.informe,
            "secciones_ocultas": self.secciones_ocultas,
            "estudios": self.estudios,
            "figuras": self.figuras,
            "documento": self.documento,
            "chats_agentes": self.chats_agentes,
            "uso_llm": self.uso_llm,
            "actualizado": self.actualizado,
        }

    def resumen(self) -> dict:
        """Versión liviana para listados (selector de investigaciones)."""
        return {
            "id": self.id,
            "titulo": self.proyecto.titulo,
            "pregunta": self.proyecto.pregunta,
            "actualizado": self.actualizado,
            "n_series": len(self.proyecto.series),
        }

    @classmethod
    def desde_dict(cls, d: dict) -> Pizarra:
        proyecto = Proyecto(**d["proyecto"])
        piz = cls(proyecto)
        piz.fase_actual = d.get("fase_actual", "encuadre")
        piz.mensajes = [Mensaje.desde_dict(m) for m in d.get("mensajes", [])]
        piz.hallazgos = [Hallazgo(**h) for h in d.get("hallazgos", [])]
        piz.notas = d.get("notas", [])
        piz.informe = {**{s: "" for s in SECCIONES_INFORME}, **d.get("informe", {})}
        piz.secciones_ocultas = d.get("secciones_ocultas", [])
        piz.estudios = d.get("estudios", [])
        piz.figuras = d.get("figuras", [])
        piz.documento = d.get("documento", [])
        piz.chats_agentes = {**{a: [] for a in AGENTES_IDS}, **d.get("chats_agentes", {})}
        piz.uso_llm = d.get("uso_llm", {})
        piz.actualizado = d.get("actualizado", _ahora())
        return piz

    def guardar(self, ruta: str | Path):
        Path(ruta).write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
