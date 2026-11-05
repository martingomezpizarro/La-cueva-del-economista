"""codigo — Python RESTRINGIDO para construir series: el usuario pega código, la plataforma lo
interpreta sin `eval`.

    ratio = deuda / reservas
    brecha_mm = brecha.rolling(6).mean()
    ciclo = hp(np.log(emae_original), lamb=129600)
    alta_infl = (ipc_nivel.pct_change(12) > 0.5) * 1          # dummy 0/1
    resid = residuo(rpi, reservas, vix)                         # residuo de una regresión
    tramo = rpi["2018-01":"2020-12"]

Cómo: el texto se parsea con `ast` y se recorre con una LISTA BLANCA de nodos. Lo que no
está en la lista (imports, bucles, funciones propias, lambdas, atributos con «_», acceso a
archivos) se rechaza ANTES de ejecutar nada. No hay `eval`/`exec` en ningún punto.

Disponible:
- Variables: cualquier id del catálogo (o de Mis series, o una receta registrada «r:…» vía
  `serie("id")`) y lo que el propio código asigna.
- `np.`: log, log1p, exp, sqrt, abs, sign, where, maximum, minimum, clip, nan.
- Métodos de una serie: rolling(k).mean/std/sum/min/max/median, ewm(span=…).mean,
  shift, diff, pct_change, cumsum, cumprod, abs, clip, mean, std, min, max, median, quantile,
  sum, count, rank, round.
- Funciones: todas las operaciones de recetas (dif, log, mm, z, hp, base100, winsor, rezago,
  recorte, cociente…) con sus parámetros por nombre, más residuo(y, *x), ajustado(y, *x),
  corr_movil(a, b, k), dummy(x, desde, hasta), serie("id").

Cada variable asignada que resulta en una serie se devuelve; como receta queda
`{"op": "codigo", "de": [ids usados], "p": {"codigo": …, "salida": nombre}}` (ver `recetas`).
"""

from __future__ import annotations

import ast
from collections.abc import Callable

import numpy as np
import pandas as pd

from cueva.metodos.contrato import ErrorMetodo

MAX_CARACTERES = 6000
MAX_NODOS = 3000
MAX_SENTENCIAS = 80

_BIN = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
    ast.FloorDiv: lambda a, b: a // b,
    ast.Mod: lambda a, b: a % b,
    ast.Pow: lambda a, b: a**b,
}
_CMP = {
    ast.Lt: lambda a, b: a < b,
    ast.Gt: lambda a, b: a > b,
    ast.LtE: lambda a, b: a <= b,
    ast.GtE: lambda a, b: a >= b,
    ast.Eq: lambda a, b: a == b,
    ast.NotEq: lambda a, b: a != b,
}
_NODOS = (
    ast.Module, ast.Assign, ast.Expr, ast.Name, ast.Load, ast.Store, ast.Constant, ast.BinOp,
    ast.UnaryOp, ast.USub, ast.UAdd, ast.Not, ast.Compare, ast.BoolOp, ast.And, ast.Or, ast.Call,
    ast.keyword, ast.Attribute, ast.Subscript, ast.Slice, *_BIN, *_CMP,
)  # fmt: skip

NP = {
    "log": lambda x: np.log(x.where(x > 0)) if isinstance(x, pd.Series) else np.log(x),
    "log1p": np.log1p,
    "exp": np.exp,
    "sqrt": np.sqrt,
    "abs": np.abs,
    "sign": np.sign,
    "where": lambda c, a, b: _alinear_where(c, a, b),
    "maximum": np.maximum,
    "minimum": np.minimum,
    "clip": lambda x, lo=None, hi=None: x.clip(lo, hi),
    "nan": np.nan,
}
METODOS_SERIE = {
    "shift", "diff", "pct_change", "cumsum", "cumprod", "abs", "clip", "mean", "std", "min",
    "max", "median", "quantile", "sum", "count", "rank", "round",
}  # fmt: skip
AGREGADOS = {"mean", "std", "sum", "min", "max", "median"}


def _alinear_where(c, a, b):
    idx = c.index
    a = a.reindex(idx) if isinstance(a, pd.Series) else a
    b = b.reindex(idx) if isinstance(b, pd.Series) else b
    return pd.Series(np.where(c.astype(bool), a, b), index=idx)


class _Ventana:
    """Lo que devuelve `.rolling(k)` / `.ewm(...)`: sólo admite agregados."""

    def __init__(self, obj, tipo):
        self.obj, self.tipo = obj, tipo

    def agregar(self, nombre):
        if nombre not in AGREGADOS or (self.tipo == "ewm" and nombre not in ("mean", "std")):
            raise ErrorMetodo(f"«.{self.tipo}(…).{nombre}()» no está permitido.")
        return getattr(self.obj, nombre)


class _Modulo:
    def __init__(self, nombre, funciones):
        self.nombre, self.funciones = nombre, funciones


def _funciones(cargar: Callable[[str], pd.Series]) -> dict:
    from cueva.metodos import recetas as R

    fs = {}
    for op_id, op in R.OPS.items():

        def envolver(*args, _op=op, **kw):
            if len(args) != _op.aridad:
                raise ErrorMetodo(f"{_op.id}() recibe {_op.aridad} serie(s).")
            series = [_serie(a, _op.id) for a in args]
            if _op.aridad == 2:
                series = list(series[0].align(series[1], join="inner"))
            return _op.fn(*series, **kw)

        fs[op_id] = envolver

    def regresion(y, *xs, parte="residuo"):
        if not xs:
            raise ErrorMetodo("residuo/ajustado necesitan al menos una explicativa.")
        d = pd.concat([_serie(y, "y"), *[_serie(x, "x") for x in xs]], axis=1).dropna()
        X = np.column_stack([np.ones(len(d)), d.iloc[:, 1:].values])
        b, *_ = np.linalg.lstsq(X, d.iloc[:, 0].values, rcond=None)
        ajuste = X @ b
        return pd.Series(d.iloc[:, 0].values - ajuste if parte == "residuo" else ajuste, index=d.index)

    fs["residuo"] = lambda y, *xs: regresion(y, *xs, parte="residuo")
    fs["ajustado"] = lambda y, *xs: regresion(y, *xs, parte="ajustado")
    fs["corr_movil"] = lambda a, b, k=12: _serie(a, "a").rolling(int(k)).corr(_serie(b, "b"))

    def dummy(x, desde, hasta=""):
        idx = _serie(x, "x").index
        dentro = idx >= pd.Timestamp(desde)
        if hasta:
            h = str(hasta)  # «2009-06» incluye todo junio; «2009», todo el año
            fin = pd.Period(h, "M" if len(h) == 7 else "Y").end_time if len(h) in (4, 7) else pd.Timestamp(h)
            dentro &= idx <= fin
        return pd.Series(dentro.astype(float), index=idx)

    fs["dummy"] = dummy
    fs["serie"] = lambda sid: cargar(str(sid))
    return fs


def _serie(v, donde):
    if not isinstance(v, pd.Series):
        raise ErrorMetodo(f"{donde}: se esperaba una serie.")
    return v


def validar_codigo(codigo: str) -> ast.Module:
    if not isinstance(codigo, str) or not codigo.strip():
        raise ErrorMetodo("El código está vacío.")
    if len(codigo) > MAX_CARACTERES:
        raise ErrorMetodo(f"El código supera {MAX_CARACTERES} caracteres.")
    try:
        arbol = ast.parse(codigo, mode="exec")
    except SyntaxError as e:
        raise ErrorMetodo(f"Error de sintaxis en la línea {e.lineno}: {e.msg}") from e
    nodos = list(ast.walk(arbol))
    if len(nodos) > MAX_NODOS or len(arbol.body) > MAX_SENTENCIAS:
        raise ErrorMetodo("El código es demasiado largo.")
    for n in nodos:
        if not isinstance(n, _NODOS):
            raise ErrorMetodo(
                f"Línea {getattr(n, 'lineno', '?')}: «{type(n).__name__}» no está permitido (sin imports, bucles, funciones ni lambdas)."
            )
        if isinstance(n, ast.Attribute) and n.attr.startswith("_"):
            raise ErrorMetodo(f"Línea {n.lineno}: los atributos con «_» no están permitidos.")
        if isinstance(n, ast.Name) and n.id.startswith("_"):
            raise ErrorMetodo(f"Línea {n.lineno}: los nombres con «_» al principio no están permitidos.")
        if isinstance(n, ast.Assign) and (len(n.targets) != 1 or not isinstance(n.targets[0], ast.Name)):
            raise ErrorMetodo(f"Línea {n.lineno}: sólo se asigna a un nombre por línea (x = …).")
        if isinstance(n, ast.Constant) and isinstance(n.value, (bytes, complex)):
            raise ErrorMetodo(f"Línea {n.lineno}: constante no permitida.")
    return arbol


def ejecutar(
    codigo: str, freq: str = "mensual", cargar: Callable[[str, str], pd.Series] | None = None
) -> dict:
    """Interpreta el código. Devuelve {"series": {nombre: pd.Series}, "usadas": [ids],
    "ultimo": valor de la última expresión}."""
    arbol = validar_codigo(codigo)
    if cargar is None:
        from cueva.metodos.insumos import cargar_base

        cargar = cargar_base
    usadas: list[str] = []

    def cargar_id(sid):
        s = cargar(sid, freq)
        if sid not in usadas:
            usadas.append(sid)
        return s

    funcs = _funciones(cargar_id)
    entorno: dict = {}
    salida: dict[str, pd.Series] = {}

    def ev(n):
        if isinstance(n, ast.Constant):
            return n.value
        if isinstance(n, ast.Name):
            if n.id in entorno:
                return entorno[n.id]
            if n.id == "np":
                return _Modulo("np", NP)
            if n.id in funcs:
                return funcs[n.id]
            try:
                return cargar_id(n.id)
            except ErrorMetodo as e:
                raise ErrorMetodo(
                    f"Línea {n.lineno}: «{n.id}» no es una serie del catálogo ni una variable definida antes."
                ) from e
        if isinstance(n, ast.BinOp):
            a, b = ev(n.left), ev(n.right)
            if isinstance(a, str) or isinstance(b, str):
                raise ErrorMetodo(f"Línea {n.lineno}: no se opera con textos.")
            if isinstance(n.op, ast.Pow) and not isinstance(b, pd.Series) and abs(b) > 100:
                raise ErrorMetodo(f"Línea {n.lineno}: exponente demasiado grande.")
            return _BIN[type(n.op)](a, b)
        if isinstance(n, ast.UnaryOp):
            v = ev(n.operand)
            return (
                -v
                if isinstance(n.op, ast.USub)
                else (
                    v
                    if isinstance(n.op, ast.UAdd)
                    else ~v.astype(bool)
                    if isinstance(v, pd.Series)
                    else not v
                )
            )
        if isinstance(n, ast.Compare):
            izq = ev(n.left)
            res = None
            for op, der in zip(n.ops, n.comparators, strict=True):
                d = ev(der)
                r = _CMP[type(op)](izq, d)
                res = r if res is None else (res & r)
                izq = d
            return res.astype(float) if isinstance(res, pd.Series) else res
        if isinstance(n, ast.BoolOp):
            vals = [ev(v) for v in n.values]
            out = vals[0]
            for v in vals[1:]:
                out = (
                    (out.astype(bool) & v.astype(bool))
                    if isinstance(n.op, ast.And)
                    else (out.astype(bool) | v.astype(bool))
                )
            return out.astype(float) if isinstance(out, pd.Series) else out
        if isinstance(n, ast.Subscript):
            base = ev(n.value)
            if (
                not isinstance(base, pd.Series)
                or not isinstance(n.slice, ast.Slice)
                or n.slice.step is not None
            ):
                raise ErrorMetodo(
                    f'Línea {n.lineno}: sólo se recorta una serie por fechas: x["2010-01":"2020-12"].'
                )
            lo = ev(n.slice.lower) if n.slice.lower else None
            hi = ev(n.slice.upper) if n.slice.upper else None
            return base.loc[lo:hi]
        if isinstance(n, ast.Attribute):
            obj = ev(n.value)
            if isinstance(obj, _Modulo):
                if n.attr not in obj.funciones:
                    raise ErrorMetodo(f"Línea {n.lineno}: «{obj.nombre}.{n.attr}» no está disponible.")
                return obj.funciones[n.attr]
            raise ErrorMetodo(f"Línea {n.lineno}: «.{n.attr}» sólo se usa como llamada: x.{n.attr}(…).")
        if isinstance(n, ast.Call):
            args = [ev(a) for a in n.args]
            kw = {k.arg: ev(k.value) for k in n.keywords if k.arg}
            if len(kw) != len(n.keywords):
                raise ErrorMetodo(f"Línea {n.lineno}: «**kwargs» no está permitido.")
            if isinstance(n.func, ast.Attribute):
                obj = ev(n.func.value)
                nombre = n.func.attr
                if isinstance(obj, _Modulo):
                    if nombre not in obj.funciones:
                        raise ErrorMetodo(f"Línea {n.lineno}: «{obj.nombre}.{nombre}» no está disponible.")
                    return obj.funciones[nombre](*args, **kw)
                if isinstance(obj, _Ventana):
                    return obj.agregar(nombre)(*args, **kw)
                if isinstance(obj, pd.Series):
                    if nombre == "rolling":
                        return _Ventana(
                            obj.rolling(int(args[0]) if args else int(kw.get("window", 12))), "rolling"
                        )
                    if nombre == "ewm":
                        return _Ventana(
                            obj.ewm(**{k: v for k, v in kw.items() if k in ("span", "alpha", "halflife")}),
                            "ewm",
                        )
                    if nombre == "log":
                        return np.log(obj.where(obj > 0))
                    if nombre not in METODOS_SERIE:
                        raise ErrorMetodo(f"Línea {n.lineno}: el método «.{nombre}()» no está permitido.")
                    return getattr(obj, nombre)(*args, **kw)
                raise ErrorMetodo(f"Línea {n.lineno}: «.{nombre}()» sobre algo que no es una serie.")
            f = ev(n.func)
            if not callable(f) or isinstance(f, pd.Series):
                raise ErrorMetodo(f"Línea {n.lineno}: eso no es una función.")
            try:
                return f(*args, **kw)
            except TypeError as e:
                raise ErrorMetodo(f"Línea {n.lineno}: argumentos inválidos ({e}).") from e
        raise ErrorMetodo(f"Línea {getattr(n, 'lineno', '?')}: expresión no soportada.")

    ultimo = None
    for st in arbol.body:
        try:
            if isinstance(st, ast.Assign):
                v = ev(st.value)
                nombre = st.targets[0].id
                if nombre in ("np",):
                    raise ErrorMetodo(f"Línea {st.lineno}: «{nombre}» es un nombre reservado.")
                entorno[nombre] = v
                if isinstance(v, pd.Series):
                    salida[nombre] = v.replace([np.inf, -np.inf], np.nan).dropna().astype(float)
            else:
                ultimo = ev(st.value)
        except ErrorMetodo:
            raise
        except Exception as e:  # un error de pandas/numpy en el código del usuario
            raise ErrorMetodo(f"Línea {st.lineno}: {type(e).__name__}: {e}") from e
    if isinstance(ultimo, pd.Series) and not salida:
        salida["resultado"] = ultimo.replace([np.inf, -np.inf], np.nan).dropna().astype(float)
    return {"series": salida, "usadas": usadas, "ultimo": ultimo}


def receta(codigo: str, salida: str, usadas: list[str]) -> dict:
    return {"op": "codigo", "de": list(usadas), "p": {"codigo": codigo, "salida": salida}}
