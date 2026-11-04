"""recetas — Series derivadas como RECETAS: un árbol de operaciones sobre series del catálogo.

Una receta es JSON plano y se puede guardar, comparar, mostrar y re-evaluar cuando llegan
datos nuevos:

    "emae_original"                                   ← hoja: id del catálogo (o de Mis series)
    {"op": "log", "de": ["emae_original"]}
    {"op": "dif", "de": [{"op": "log", "de": ["emae_original"]}], "p": {"k": 12}}
    {"op": "cociente", "de": ["deuda_ext", "reservas"]}

Es la ÚNICA definición de las transformaciones de la plataforma: el parámetro `transf` de los
métodos, las herramientas viejas, la pantalla (arrastrar «Δ» sobre una ficha) y el linaje
pasan por acá. Sumar una operación = una función con `@operacion(...)`.

Garantías:
- Gramática cerrada: sólo operaciones registradas, parámetros validados; nada de `eval`.
- `texto(receta)` la escribe para humanos («Δ₁₂ log(emae_original)»); `huella(receta)` da un
  identificador estable (misma receta ⇒ misma huella), que sirve de clave de caché y de id.
- `hojas(receta)` devuelve las series del catálogo de las que depende (para el linaje).

Qué NO hace: no carga archivos por su cuenta (usa `insumos.cargar_base`) ni persiste nada.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from cueva.metodos.contrato import ErrorMetodo

MAX_PROFUNDIDAD = 12
MAX_NODOS = 60


@dataclass
class Operacion:
    id: str
    nombre: str
    clase: str  # transformar | combinar | descomponer
    aridad: int  # cuántas series recibe (2 = A, B)
    fn: Callable[..., pd.Series]
    params: dict[str, tuple] = field(default_factory=dict)  # nombre → (tipo, defecto, min, max)
    formato: str = "{op}({a})"  # cómo se escribe; {a}, {b} y los parámetros
    ayuda: str = ""

    def a_dict(self) -> dict:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "clase": self.clase,
            "aridad": self.aridad,
            "params": {
                k: {"tipo": v[0], "defecto": v[1], "min": v[2], "max": v[3]} for k, v in self.params.items()
            },
            "ayuda": self.ayuda,
        }


OPS: dict[str, Operacion] = {}


def operacion(id, nombre, clase, aridad=1, params=None, formato=None, ayuda=""):
    def deco(fn):
        OPS[id] = Operacion(id, nombre, clase, aridad, fn, params or {}, formato or f"{id}({{a}})", ayuda)
        return fn

    return deco


# ── transformar: 1 serie → 1 serie ──────────────────────────────────────────
@operacion("log", "Logaritmo", "transformar", formato="log {a}")
def _log(s):
    return np.log(s[s > 0])


@operacion("dif", "Diferencia", "transformar", params={"k": ("entero", 1, 1, 60)}, formato="Δ{k} {a}")
def _dif(s, k=1):
    return s.diff(k)


@operacion("dif2", "Diferencia segunda", "transformar", formato="Δ² {a}")
def _dif2(s):
    return s.diff().diff()


@operacion(
    "dif_log",
    "Diferencia del logaritmo (≈ tasa)",
    "transformar",
    params={"k": ("entero", 1, 1, 60)},
    formato="Δ{k} log {a}",
)
def _dif_log(s, k=1):
    return np.log(s[s > 0]).diff(k)


@operacion(
    "pct", "Variación porcentual", "transformar", params={"k": ("entero", 1, 1, 60)}, formato="%Δ{k} {a}"
)
def _pct(s, k=1):
    return s.pct_change(k) * 100


@operacion(
    "base100",
    "Base 100",
    "transformar",
    params={"fecha": ("fecha", "", None, None)},
    formato="{a} (base 100)",
)
def _base100(s, fecha=""):
    ref = s.loc[s.index >= pd.Timestamp(fecha)].iloc[0] if fecha else s.iloc[0]
    if not ref:
        raise ErrorMetodo("La base es cero.")
    return s / ref * 100


@operacion("mm", "Media móvil", "transformar", params={"k": ("entero", 12, 2, 400)}, formato="mm{k} {a}")
def _mm(s, k=12):
    return s.rolling(k).mean()


@operacion("z", "Estandarizar", "transformar", formato="z({a})")
def _z(s):
    return (s - s.mean()) / s.std()


@operacion(
    "winsor",
    "Recortar outliers (colas)",
    "transformar",
    params={"q": ("real", 0.01, 0.0, 0.25)},
    formato="winsor{q}({a})",
)
def _winsor(s, q=0.01):
    return s.clip(s.quantile(q), s.quantile(1 - q))


@operacion("rezago", "Rezagar", "transformar", params={"k": ("entero", 1, -60, 60)}, formato="{a}(t−{k})")
def _rezago(s, k=1):
    return s.shift(k)


@operacion(
    "recorte",
    "Recortar un tramo",
    "transformar",
    params={"desde": ("fecha", "", None, None), "hasta": ("fecha", "", None, None)},
    formato="{a}[{desde}:{hasta}]",
)
def _recorte(s, desde="", hasta=""):
    if desde:
        s = s[s.index >= pd.Timestamp(desde)]
    if hasta:
        s = s[s.index <= pd.Timestamp(hasta) + pd.offsets.MonthEnd(0)]
    return s


@operacion(
    "frecuencia",
    "Cambiar frecuencia",
    "transformar",
    params={
        "a": ("opcion", "mensual", ["mensual", "trimestral", "anual"], None),
        "como": ("opcion", "promedio", ["promedio", "suma", "ultimo"], None),
    },
    formato="{a} → {a_}",
)
def _frecuencia(s, a="mensual", como="promedio"):
    regla = {"mensual": "ME", "trimestral": "QE", "anual": "YE"}[a]
    g = s.resample(regla)
    return {"promedio": g.mean, "suma": g.sum, "ultimo": g.last}[como]()


# ── combinar: 2 series → 1 serie (alineadas por fecha) ───────────────────────
@operacion("suma", "A + B", "combinar", 2, formato="({a} + {b})")
def _suma(a, b):
    return a + b


@operacion("resta", "A − B (spread)", "combinar", 2, formato="({a} − {b})")
def _resta(a, b):
    return a - b


@operacion("producto", "A × B", "combinar", 2, formato="({a} × {b})")
def _producto(a, b):
    return a * b


@operacion("cociente", "A ÷ B (ratio, deflactar)", "combinar", 2, formato="({a} ÷ {b})")
def _cociente(a, b):
    return a / b.replace(0, np.nan)


@operacion("residuo", "Residuo de A sobre B (MCO)", "combinar", 2, formato="resid({a} ~ {b})")
def _residuo(a, b):
    X = np.column_stack([np.ones(len(b)), b.values])
    beta, *_ = np.linalg.lstsq(X, a.values, rcond=None)
    return pd.Series(a.values - X @ beta, index=a.index)


# ── descomponer: 1 serie → un componente elegido ─────────────────────────────
@operacion(
    "hp",
    "Filtro HP",
    "descomponer",
    params={"lamb": ("real", 129600.0, 1.0, 1e9), "parte": ("opcion", "ciclo", ["ciclo", "tendencia"], None)},
    formato="HP-{parte}({a})",
)
def _hp(s, lamb=129600.0, parte="ciclo"):
    from statsmodels.tsa.filters.hp_filter import hpfilter

    ciclo, tend = hpfilter(s.values, lamb=lamb)
    return pd.Series(ciclo if parte == "ciclo" else tend, index=s.index)


@operacion("sin_tendencia", "Quitar tendencia lineal", "descomponer", formato="detrend({a})")
def _sin_tendencia(s):
    t = np.arange(len(s), dtype=float)
    b = np.polyfit(t, s.values, 1)
    return s - np.polyval(b, t)


# ──────────────────────────────────────────────────────────────────────────
# Validación, texto, huella, hojas
# ──────────────────────────────────────────────────────────────────────────
def validar(r, profundidad: int = 0, cuenta: list | None = None) -> None:
    cuenta = cuenta if cuenta is not None else [0]
    cuenta[0] += 1
    if cuenta[0] > MAX_NODOS or profundidad > MAX_PROFUNDIDAD:
        raise ErrorMetodo("Receta demasiado grande.")
    if isinstance(r, str):
        if not r or len(r) > 120 or not all(c.isalnum() or c in "_.-:" for c in r):
            raise ErrorMetodo(f"Id de serie inválido en la receta: {r!r}")
        return
    if not isinstance(r, dict) or set(r) - {"op", "de", "p"}:
        raise ErrorMetodo("Una receta es un id de serie o {op, de, p}.")
    op = OPS.get(r.get("op"))
    if op is None:
        raise ErrorMetodo(f"Operación desconocida: {r.get('op')!r} (hay: {', '.join(sorted(OPS))})")
    de = r.get("de") or []
    if not isinstance(de, list) or len(de) != op.aridad:
        raise ErrorMetodo(f"«{op.nombre}» recibe {op.aridad} serie(s).")
    p = r.get("p") or {}
    if not isinstance(p, dict) or set(p) - set(op.params):
        raise ErrorMetodo(f"Parámetros inválidos para «{op.nombre}»: {sorted(set(p) - set(op.params))}")
    for k, v in p.items():
        tipo, _, lo, hi = op.params[k]
        if tipo in ("entero", "real"):
            if (
                not isinstance(v, (int, float))
                or isinstance(v, bool)
                or (tipo == "entero" and not float(v).is_integer())
            ):
                raise ErrorMetodo(f"«{k}» tiene que ser numérico.")
            if (lo is not None and v < lo) or (hi is not None and v > hi):
                raise ErrorMetodo(f"«{k}» fuera de rango [{lo}, {hi}].")
        elif tipo == "opcion" and v not in lo:
            raise ErrorMetodo(f"«{k}»: opción inválida {v!r}.")
        elif tipo == "fecha" and v and not (isinstance(v, str) and len(v) in (7, 10)):
            raise ErrorMetodo(f"«{k}»: fecha inválida.")
    for h in de:
        validar(h, profundidad + 1, cuenta)


def canonica(r) -> str:
    return json.dumps(r, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def huella(r) -> str:
    return hashlib.sha1(canonica(r).encode()).hexdigest()[:12]


def texto(r) -> str:
    if isinstance(r, str):
        return r
    op = OPS[r["op"]]
    de = [texto(h) for h in r.get("de", [])]
    p = {**{k: v[1] for k, v in op.params.items()}, **(r.get("p") or {})}
    vals = {"a": de[0] if de else "", "b": de[1] if len(de) > 1 else "", "op": op.id, **p}
    vals["a_"] = p.get("a", "")
    if "k" in p and p["k"] == 1:
        vals["k"] = ""
    try:
        return op.formato.format(**vals)
    except (KeyError, IndexError):
        return f"{op.id}({', '.join(de)})"


def hojas(r) -> list[str]:
    if isinstance(r, str):
        return [r]
    out: list[str] = []
    for h in r.get("de", []):
        for x in hojas(h):
            if x not in out:
                out.append(x)
    return out


def de_transf(sid: str, transf: str | None):
    """El viejo parámetro `transf` (nivel/log/dif/dif2/dif_log/pct) como receta."""
    t = (transf or "nivel").lower()
    if t in ("", "nivel", "none"):
        return sid
    if t not in OPS or OPS[t].clase != "transformar":
        raise ErrorMetodo(f"Transformación desconocida: {transf}")
    return {"op": t, "de": [sid]}


# ──────────────────────────────────────────────────────────────────────────
# Evaluación (con caché por huella dentro de una evaluación)
# ──────────────────────────────────────────────────────────────────────────
def evaluar(r, freq: str = "mensual", cargar: Callable[[str, str], pd.Series] | None = None) -> pd.Series:
    """Evalúa una receta y devuelve la serie (índice de fechas, sin NaN ni infinitos)."""
    validar(r)
    if cargar is None:
        from cueva.metodos.insumos import cargar_base

        cargar = cargar_base
    memo: dict[str, pd.Series] = {}

    def ev(n) -> pd.Series:
        h = huella(n)
        if h in memo:
            return memo[h]
        if isinstance(n, str):
            s = cargar(n, freq)
        else:
            op = OPS[n["op"]]
            args = [ev(x) for x in n["de"]]
            if op.aridad == 2:
                a, b = args[0].align(args[1], join="inner")
                if len(a) < 3:
                    raise ErrorMetodo(f"«{op.nombre}»: las series casi no comparten fechas.")
                args = [a, b]
            s = op.fn(*args, **(n.get("p") or {}))
        s = s.replace([np.inf, -np.inf], np.nan).dropna().astype(float)
        memo[h] = s
        return s

    out = ev(r).copy()
    out.name = texto(r)
    return out


def catalogo_operaciones() -> list[dict]:
    return [o.a_dict() for o in OPS.values()]
