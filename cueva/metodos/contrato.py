"""contrato — Cómo se DECLARA un método y cómo se ARMA su resultado.

Esta capa existe para que sumar un método nuevo sea escribir UNA función de Python, sin tocar
el frontend ni los agentes:

- `Param` y `Metodo` describen el método: qué pregunta responde, qué entradas pide (tipadas),
  qué supuestos tiene, qué trampas son típicas, qué paquetes necesita y cuánto tarda.
  De esa declaración salen el formulario de la pantalla y el JSON Schema del function calling.
- `Resultado` arma la salida con BLOQUES TIPADOS (métricas, tablas, gráficos, veredicto,
  advertencias, series derivadas, código reproducible). El frontend sabe dibujar cada tipo de
  bloque, así que no necesita conocer el método.

Qué NO hace: no carga datos (eso es `insumos`), no ejecuta (eso es `registro`).
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

# Tipos de parámetro que el formulario sabe dibujar y el validador sabe chequear
TIPOS_PARAM = {
    "serie",  # un id del catálogo
    "series",  # lista de ids del catálogo
    "entero",
    "real",
    "opcion",  # una de `opciones`
    "opciones",  # varias de `opciones`
    "bool",
    "texto",
    "fecha",  # YYYY-MM o YYYY-MM-DD
}

COSTOS = ("instantaneo", "segundos", "minutos")

# Familias del catálogo, en el orden en que se muestran (el orden de un trabajo)
FAMILIAS: dict[str, dict[str, str]] = {
    "exploratorio": {"nombre": "Exploración y descriptivos", "icono": "🔎"},
    "pruebas": {"nombre": "Pruebas sobre las series", "icono": "🧪"},
    "filtros": {"nombre": "Filtros y descomposición", "icono": "🪚"},
    "univariados": {"nombre": "Modelos univariados y pronóstico", "icono": "📈"},
    "volatilidad": {"nombre": "Volatilidad y riesgo", "icono": "🌪"},
    "regresion": {"nombre": "Regresión y estimación", "icono": "📐"},
    "multivariados": {"nombre": "Sistemas multivariados", "icono": "🕸"},
    "cointegracion": {"nombre": "Cointegración y largo plazo", "icono": "🔗"},
    "regimenes": {"nombre": "No linealidad y regímenes", "icono": "🔀"},
    "estado": {"nombre": "Espacio de estados y factores", "icono": "🛰"},
    "causal": {"nombre": "Inferencia causal y eventos", "icono": "🎯"},
    "ml": {"nombre": "Aprendizaje automático", "icono": "🌲"},
    "redes": {"nombre": "Redes neuronales", "icono": "🧠"},
    "no_supervisado": {"nombre": "No supervisado y anomalías", "icono": "🧩"},
    "finanzas": {"nombre": "Finanzas cuantitativas y activos", "icono": "💹"},
    "evaluacion": {"nombre": "Evaluación y combinación de modelos", "icono": "🏆"},
}


@dataclass
class Param:
    """Un parámetro de un método. `tipo` es uno de TIPOS_PARAM."""

    nombre: str
    tipo: str
    etiqueta: str = ""
    defecto: Any = None
    requerido: bool = False
    minimo: float | None = None
    maximo: float | None = None
    opciones: list[str] | None = None
    ayuda: str = ""
    min_items: int | None = None
    max_items: int | None = None

    def __post_init__(self):
        if self.tipo not in TIPOS_PARAM:
            raise ValueError(f"Tipo de parámetro desconocido: {self.tipo}")
        if not self.etiqueta:
            self.etiqueta = self.nombre

    def a_dict(self) -> dict:
        d = {
            "nombre": self.nombre,
            "tipo": self.tipo,
            "etiqueta": self.etiqueta,
            "defecto": self.defecto,
            "requerido": self.requerido,
            "ayuda": self.ayuda,
        }
        for k in ("minimo", "maximo", "opciones", "min_items", "max_items"):
            v = getattr(self, k)
            if v is not None:
                d[k] = v
        return d

    def esquema(self) -> dict:
        """JSON Schema del parámetro (para function calling)."""
        desc = self.etiqueta + (f". {self.ayuda}" if self.ayuda else "")
        if self.tipo == "serie":
            return {"type": "string", "description": desc + " (id del catálogo de series)"}
        if self.tipo == "series":
            e: dict = {"type": "array", "items": {"type": "string"}, "description": desc}
            if self.min_items:
                e["minItems"] = self.min_items
            if self.max_items:
                e["maxItems"] = self.max_items
            return e
        if self.tipo in ("entero", "real"):
            e = {"type": "integer" if self.tipo == "entero" else "number", "description": desc}
            if self.minimo is not None:
                e["minimum"] = self.minimo
            if self.maximo is not None:
                e["maximum"] = self.maximo
            return e
        if self.tipo == "opcion":
            return {"type": "string", "enum": list(self.opciones or []), "description": desc}
        if self.tipo == "opciones":
            return {
                "type": "array",
                "items": {"type": "string", "enum": list(self.opciones or [])},
                "description": desc,
            }
        if self.tipo == "bool":
            return {"type": "boolean", "description": desc}
        if self.tipo == "fecha":
            return {"type": "string", "description": desc + " (AAAA-MM o AAAA-MM-DD)"}
        return {"type": "string", "description": desc}


@dataclass
class Metodo:
    """Declaración completa de un método del catálogo."""

    id: str
    nombre: str
    familia: str
    fn: Callable[..., Resultado]
    pregunta: str  # qué pregunta del economista responde, en una línea
    params: list[Param] = field(default_factory=list)
    cuando: str = ""  # cuándo conviene usarlo
    supuestos: list[str] = field(default_factory=list)
    trampas: list[str] = field(default_factory=list)  # errores típicos (lo que el Crítico vigila)
    deps: list[str] = field(default_factory=list)  # módulos de Python opcionales
    costo: str = "instantaneo"
    referencias: list[str] = field(default_factory=list)
    etiquetas: list[str] = field(default_factory=list)  # para el buscador
    nivel: str = "intermedio"  # basico | intermedio | avanzado

    def __post_init__(self):
        if self.familia not in FAMILIAS:
            raise ValueError(f"{self.id}: familia desconocida {self.familia}")
        if self.costo not in COSTOS:
            raise ValueError(f"{self.id}: costo desconocido {self.costo}")

    def a_dict(self, disponible: bool = True, falta: list[str] | None = None) -> dict:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "familia": self.familia,
            "familia_nombre": FAMILIAS[self.familia]["nombre"],
            "pregunta": self.pregunta,
            "cuando": self.cuando,
            "supuestos": self.supuestos,
            "trampas": self.trampas,
            "params": [p.a_dict() for p in self.params],
            "deps": self.deps,
            "costo": self.costo,
            "referencias": self.referencias,
            "etiquetas": self.etiquetas,
            "nivel": self.nivel,
            "disponible": disponible,
            "falta": falta or [],
        }

    def esquema(self) -> dict:
        return {
            "type": "object",
            "properties": {p.nombre: p.esquema() for p in self.params},
            "required": [p.nombre for p in self.params if p.requerido],
        }


# ──────────────────────────────────────────────────────────────────────────
# Resultado con bloques tipados
# ──────────────────────────────────────────────────────────────────────────
def _num(v):
    """Número JSON-seguro: NaN/inf → None, numpy → float/int nativos."""
    if v is None:
        return None
    if isinstance(v, bool):
        return v
    try:
        import numpy as np

        if isinstance(v, np.integer):
            return int(v)
        if isinstance(v, np.bool_):
            return bool(v)
        if isinstance(v, np.generic):
            v = v.item()
        elif hasattr(v, "size") and hasattr(v, "item") and getattr(v, "size", 0) == 1:
            v = v.item()  # pd.Series / np.ndarray de un solo elemento
    except Exception:  # pragma: no cover
        pass
    if isinstance(v, int):
        return v
    try:
        f = float(v)
    except (TypeError, ValueError):
        return v
    if math.isnan(f) or math.isinf(f):
        return None
    return f


def _lista(vs) -> list:
    return [_num(v) for v in list(vs)]


def _fechas(indice) -> list[str]:
    out = []
    for f in indice:
        try:
            out.append(str(f.date()))
        except AttributeError:
            out.append(str(f))
    return out


SEMAFOROS = ("verde", "amarillo", "rojo")
MAX_PUNTOS = 1500


class Resultado:
    """Acumula los bloques de la salida de un método.

    Uso típico dentro de un método:
        r = Resultado()
        r.metrica("AIC", 123.4)
        r.tabla("Coeficientes", ["variable", "coef", "p"], filas)
        r.lineas("Ajuste", s.index, {"observado": s, "ajustado": aj})
        r.veredicto("La serie es I(1).", "amarillo")
        r.resumen = "…"   # lo que el agente lee
        return r
    """

    def __init__(self):
        self.resumen: str = ""
        self.bloques: list[dict] = []
        self.metricas: dict[str, Any] = {}
        self.advertencias: list[str] = []
        self.semaforo: str | None = None
        self.series_salida: list[dict] = []
        self.codigo: str = ""
        self.datos: dict[str, Any] = {}  # evidencia estructurada extra (para agentes y tests)

    # ── bloques ──
    def metrica(self, nombre: str, valor, ayuda: str = "", formato: str = "") -> Resultado:
        self.metricas[nombre] = _num(valor)
        self._metricas_bloque().append(
            {"nombre": nombre, "valor": _num(valor), "ayuda": ayuda, "formato": formato}
        )
        return self

    def _metricas_bloque(self) -> list:
        for b in self.bloques:
            if b["tipo"] == "metricas":
                return b["items"]
        b = {"tipo": "metricas", "items": []}
        self.bloques.insert(0, b)
        return b["items"]

    def tabla(
        self,
        titulo: str,
        columnas: list[str],
        filas: list[list],
        nota: str = "",
        resaltar_p: str | None = None,
    ) -> Resultado:
        """`resaltar_p`: nombre de la columna de p-valores a colorear (< 0,05)."""
        self.bloques.append(
            {
                "tipo": "tabla",
                "titulo": titulo,
                "columnas": columnas,
                "filas": [[_num(c) if not isinstance(c, str) else c for c in f] for f in filas],
                "nota": nota,
                "resaltar_p": resaltar_p,
            }
        )
        return self

    def lineas(
        self,
        titulo: str,
        fechas,
        series: dict[str, Any],
        estilos: dict[str, dict] | None = None,
        eje_y: str = "",
        marcas: list[dict] | None = None,
        y2: list[str] | None = None,
    ) -> Resultado:
        """Gráfico de líneas sobre un eje de fechas (o de enteros). `estilos[nombre]` acepta
        {"guion": "dash|dot", "ancho": n, "relleno": "banda_hasta:<otra>"}; `marcas` son
        líneas verticales [{"x": fecha, "texto": "..."}]; `y2` las series al eje derecho."""
        x = _fechas(fechas)
        sal = {k: _lista(v) for k, v in series.items()}
        x, sal = _submuestrear(x, sal)
        self.bloques.append(
            {
                "tipo": "lineas",
                "titulo": titulo,
                "x": x,
                "series": sal,
                "estilos": estilos or {},
                "eje_y": eje_y,
                "marcas": marcas or [],
                "y2": y2 or [],
            }
        )
        return self

    def bandas(
        self,
        titulo: str,
        fechas_hist,
        historia,
        fechas_pron,
        media,
        inferior=None,
        superior=None,
        extra: dict[str, tuple] | None = None,
        nombre_banda: str = "IC 95%",
    ) -> Resultado:
        """Pronóstico (o contrafactual) con banda. `extra`: {nombre: (fechas, valores)}."""
        xh, sh = _submuestrear(_fechas(fechas_hist), {"h": _lista(historia)})
        self.bloques.append(
            {
                "tipo": "bandas",
                "titulo": titulo,
                "x_hist": xh,
                "historia": sh["h"],
                "x_pron": _fechas(fechas_pron),
                "media": _lista(media),
                "inferior": _lista(inferior) if inferior is not None else None,
                "superior": _lista(superior) if superior is not None else None,
                "nombre_banda": nombre_banda,
                "extra": {k: {"x": _fechas(f), "y": _lista(v)} for k, (f, v) in (extra or {}).items()},
            }
        )
        return self

    def barras(
        self,
        titulo: str,
        categorias: list,
        valores: dict[str, Any] | list,
        banda: float | None = None,
        horizontal: bool = False,
        eje_y: str = "",
    ) -> Resultado:
        """Barras (ACF, importancias, coeficientes). `banda`: ± umbral dibujado (ej. 1,96/√n)."""
        if not isinstance(valores, dict):
            valores = {"valor": valores}
        self.bloques.append(
            {
                "tipo": "barras",
                "titulo": titulo,
                "categorias": [str(c) for c in categorias],
                "series": {k: _lista(v) for k, v in valores.items()},
                "banda": _num(banda),
                "horizontal": horizontal,
                "eje_y": eje_y,
            }
        )
        return self

    def mapa_calor(self, titulo: str, filas: list, columnas: list, valores, rango=(-1, 1)) -> Resultado:
        self.bloques.append(
            {
                "tipo": "mapa_calor",
                "titulo": titulo,
                "filas": [str(f) for f in filas],
                "columnas": [str(c) for c in columnas],
                "valores": [_lista(f) for f in valores],
                "rango": list(rango) if rango else None,
            }
        )
        return self

    def dispersion(
        self, titulo: str, x, y, etiqueta_x: str, etiqueta_y: str, recta=None, textos=None
    ) -> Resultado:
        """Nube de puntos; `recta` = (pendiente, ordenada) para dibujar el ajuste."""
        self.bloques.append(
            {
                "tipo": "dispersion",
                "titulo": titulo,
                "x": _lista(x)[:MAX_PUNTOS],
                "y": _lista(y)[:MAX_PUNTOS],
                "etiqueta_x": etiqueta_x,
                "etiqueta_y": etiqueta_y,
                "recta": [_num(recta[0]), _num(recta[1])] if recta is not None else None,
                "textos": [str(t) for t in textos][:MAX_PUNTOS] if textos is not None else None,
            }
        )
        return self

    def texto(self, titulo: str, cuerpo: str) -> Resultado:
        self.bloques.append({"tipo": "texto", "titulo": titulo, "cuerpo": cuerpo})
        return self

    def veredicto(self, texto: str, semaforo: str | None = None) -> Resultado:
        if semaforo and semaforo not in SEMAFOROS:
            raise ValueError(f"semáforo inválido: {semaforo}")
        self.semaforo = semaforo
        self.bloques.append({"tipo": "veredicto", "texto": texto, "semaforo": semaforo})
        return self

    def advertir(self, texto: str) -> Resultado:
        if texto not in self.advertencias:
            self.advertencias.append(texto)
        return self

    def serie(self, nombre: str, fechas, valores, descripcion: str = "") -> Resultado:
        """Serie DERIVADA que el método produce (tendencia, ciclo, factor, residuo, prob. de
        régimen…). Queda disponible para usarla como insumo de otro paso."""
        self.series_salida.append(
            {
                "nombre": nombre,
                "descripcion": descripcion,
                "fechas": _fechas(fechas),
                "valores": _lista(valores),
            }
        )
        return self

    # ── salida ──
    def a_dict(self) -> dict:
        return {
            "resumen": self.resumen,
            "bloques": self.bloques,
            "metricas": self.metricas,
            "advertencias": self.advertencias,
            "semaforo": self.semaforo,
            "series_salida": self.series_salida,
            "codigo": self.codigo,
            **({"datos": _limpiar(self.datos)} if self.datos else {}),
        }


def _submuestrear(x: list, series: dict[str, list], max_n: int = MAX_PUNTOS):
    n = len(x)
    if n <= max_n:
        return x, series
    paso = max(1, n // max_n)
    idx = list(range(0, n, paso))
    if idx[-1] != n - 1:
        idx.append(n - 1)
    return [x[i] for i in idx], {k: [v[i] for i in idx] if len(v) == n else v for k, v in series.items()}


def _limpiar(obj):
    """Vuelve JSON-seguro cualquier estructura (claves numpy, NaN, arrays)."""
    if isinstance(obj, dict):
        return {str(_num(k)) if not isinstance(k, str) else k: _limpiar(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_limpiar(v) for v in obj]
    try:
        import numpy as np

        if isinstance(obj, np.ndarray):
            return [_limpiar(v) for v in obj.tolist()]
    except Exception:  # pragma: no cover
        pass
    if isinstance(obj, str):
        return obj
    try:
        import pandas as pd

        if isinstance(obj, (pd.Series, pd.Index)):
            return [_limpiar(v) for v in obj.tolist()]
        if isinstance(obj, pd.Timestamp):
            return str(obj.date())
    except Exception:  # pragma: no cover
        pass
    v = _num(obj)
    if v is not None and not isinstance(v, (int, float, bool, str)):
        return str(v)
    return v


def limpiar(obj):
    """API pública de `_limpiar`: deja cualquier salida lista para JSON."""
    return _limpiar(obj)


class ErrorMetodo(Exception):
    """Error esperable de un método (datos insuficientes, parámetros incoherentes). Se muestra
    al usuario tal cual; no es un bug."""
