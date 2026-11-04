"""insumos — Datos de entrada de los métodos: series del catálogo, transformaciones, matriz de
diseño para aprendizaje automático y eventos de la Línea de Tiempo.

Reglas que esta capa garantiza (para que ningún método tenga que acordarse):
- Toda serie pasa por la MISMA transformación que el resto de la plataforma
  (`cueva.econometria.herramientas.TRANSFORMACIONES`).
- La matriz de diseño para ML se arma SIN mirar el futuro: la fila t sólo usa información
  disponible en t (y_t, y_{t-1}…, x_t, x_{t-1}…) y el objetivo es y_{t+h}.
- Lo que falta se informa con `ErrorMetodo` (mensaje para el usuario), nunca con un traceback.

Qué NO hace: no toca la red; sólo lee de disco vía `cueva.datos.series`.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from cueva.econometria.herramientas import TRANSFORMACIONES
from cueva.metodos.contrato import ErrorMetodo, Param

FRECUENCIAS = ["mensual", "trimestral", "anual"]
PERIODO = {"diaria": 7, "mensual": 12, "trimestral": 4, "anual": 1}
LAMBDA_HP = {"mensual": 129600, "trimestral": 1600, "anual": 6.25, "diaria": 1e8}


# ── parámetros comunes (se reusan en las declaraciones) ──────────────────────
def P_SERIE(nombre="sid", etiqueta="Serie", ayuda="") -> Param:
    return Param(nombre, "serie", etiqueta, requerido=True, ayuda=ayuda)


def P_SERIES(nombre="sids", etiqueta="Series", minimo=2, maximo=8, requerido=True, ayuda="") -> Param:
    return Param(
        nombre, "series", etiqueta, requerido=requerido, min_items=minimo, max_items=maximo, ayuda=ayuda
    )


P_FREQ = Param(
    "freq",
    "opcion",
    "Frecuencia",
    defecto="mensual",
    opciones=FRECUENCIAS,
    ayuda="A qué frecuencia se lleva todo",
)
P_TRANSF = Param(
    "transf",
    "opcion",
    "Transformación",
    defecto="nivel",
    opciones=list(TRANSFORMACIONES),
    ayuda="nivel, log, dif (Δ), dif2, dif_log (≈ tasa de variación) o pct",
)
P_DESDE = Param("desde", "fecha", "Desde", ayuda="Recorta la muestra (opcional)")
P_HASTA = Param("hasta", "fecha", "Hasta", ayuda="Recorta la muestra (opcional)")


def P_HORIZONTE(defecto=12, maximo=48) -> Param:
    return Param("horizonte", "entero", "Horizonte", defecto=defecto, minimo=1, maximo=maximo)


# ── carga ────────────────────────────────────────────────────────────────────
def _recortar(s, desde: str | None, hasta: str | None):
    if desde:
        s = s[s.index >= pd.Timestamp(desde)]
    if hasta:
        s = s[s.index <= pd.Timestamp(hasta) + pd.offsets.MonthEnd(0)]
    return s


# ── carga con caché (una serie se lee del disco UNA vez por versión del archivo) ──
_CACHE: dict[tuple, tuple] = {}
_RECETAS: dict[str, object] = {}  # "r:<huella>" → receta (registradas al validar argumentos)


def registrar_receta(receta) -> str:
    """Convierte una receta en un id de serie («r:<huella>») que cualquier método acepta."""
    from cueva.metodos import recetas as R

    R.validar(receta)
    if isinstance(receta, str):
        return receta
    token = "r:" + R.huella(receta)
    _RECETAS[token] = receta
    return token


def receta_de(sid: str):
    """La receta detrás de un id (un id del catálogo es su propia receta)."""
    return _RECETAS.get(sid, sid)


def cargar_base(sid: str, freq: str = "mensual") -> pd.Series:
    """Serie del catálogo (o de Mis series, o una receta registrada) a la frecuencia pedida."""
    import os

    from cueva.datos import series as S

    if sid in _RECETAS:
        from cueva.metodos import recetas as R

        return R.evaluar(_RECETAS[sid], freq)
    cat = S.catalogo()
    if sid not in cat:
        raise ErrorMetodo(f"No existe la serie «{sid}» en el catálogo.")
    try:
        version = os.stat(cat[sid].archivo).st_mtime_ns
    except OSError:
        version = 0
    clave = (sid, freq)
    hit = _CACHE.get(clave)
    if hit and hit[0] == version:
        return hit[1].copy()
    s = S.cargar(sid, freq=freq).astype(float)
    if len(_CACHE) > 512:
        _CACHE.clear()
    _CACHE[clave] = (version, s)
    return s.copy()


def serie(sid: str, freq: str = "mensual", transf: str | None = "nivel", desde=None, hasta=None, minimo=12):
    """Carga UNA serie (id del catálogo o receta registrada), transformada y recortada.
    Devuelve (pd.Series, etiqueta). La transformación pasa por el motor de recetas."""
    from cueva.metodos import recetas as R

    s = R.evaluar(R.de_transf(sid, transf), freq, cargar_base)
    s = _recortar(s, desde, hasta).dropna()
    base = R.texto(receta_de(sid)) if sid in _RECETAS else sid
    t = (transf or "nivel").lower()
    et = base if t in ("", "nivel", "none") else f"{base} ({TRANSFORMACIONES.get(t, t)})"
    s.name = sid
    if len(s) < minimo:
        raise ErrorMetodo(f"«{et}» tiene {len(s)} observaciones; hacen falta al menos {minimo}.")
    return s, et


def panel(
    sids: list[str],
    freq: str = "mensual",
    transf: str | dict | None = "nivel",
    desde=None,
    hasta=None,
    minimo=12,
    como="interseccion",
):
    """Varias series alineadas por fecha. `transf` puede ser global o {sid: transf}.
    `como='interseccion'` deja sólo fechas con todas las series (lo que pide casi todo método)."""
    cols, etiquetas = {}, {}
    for sid in sids:
        t = transf.get(sid, "nivel") if isinstance(transf, dict) else transf
        s, et = serie(sid, freq, t, desde, hasta, minimo=3)
        cols[sid] = s
        etiquetas[sid] = et
    df = pd.concat(cols, axis=1)
    df = df.dropna() if como == "interseccion" else df.dropna(how="all")
    if len(df) < minimo:
        raise ErrorMetodo(
            f"Las series {', '.join(sids)} comparten sólo {len(df)} fechas; hacen falta al menos {minimo}. "
            "Probá con otra frecuencia o sin recortar la muestra."
        )
    return df, etiquetas


# ── matriz de diseño para aprendizaje automático ─────────────────────────────
class Diseno:
    """Problema supervisado de pronóstico directo a h pasos.

    fila t:   [y_t, y_{t-1}, …, y_{t-p+1},  x_t, …, x_{t-q+1},  estacionales, tendencia]
    objetivo: y_{t+h}

    `X` y `y` sólo tienen filas con objetivo conocido; `X_ult` es la fila del último período
    observado, que se usa para el pronóstico fuera de la muestra (su objetivo es futuro).
    """

    def __init__(
        self,
        dep: str,
        indeps: list[str] | None = None,
        freq: str = "mensual",
        transf: str = "nivel",
        rezagos_y: int = 3,
        rezagos_x: int = 1,
        horizonte: int = 1,
        estacionales: bool = False,
        tendencia: bool = False,
        desde=None,
        hasta=None,
        transf_x: str | None = None,
    ):
        indeps = [s for s in (indeps or []) if s != dep]
        tmap = {dep: transf, **{s: (transf_x or transf) for s in indeps}}
        df, et = panel([dep, *indeps], freq, tmap, desde, hasta, minimo=24)
        self.dep, self.indeps, self.freq, self.h = dep, indeps, freq, horizonte
        self.etiquetas = et
        cols = {}
        for k in range(max(1, rezagos_y)):
            cols[f"{dep}_L{k}" if k else dep] = df[dep].shift(k)
        for s in indeps:
            for k in range(max(1, rezagos_x)):
                cols[f"{s}_L{k}" if k else s] = df[s].shift(k)
        X = pd.DataFrame(cols, index=df.index)
        per = PERIODO.get(freq, 1)
        if estacionales and per > 1:
            mes = X.index.month if freq == "mensual" else X.index.quarter
            for m in range(2, per + 1):
                X[f"est_{m}"] = (mes == m).astype(float)
        if tendencia:
            X["tendencia"] = np.arange(len(X), dtype=float)
        y = df[dep].shift(-horizonte)
        completo = X.notna().all(axis=1)
        self.X_todo = X[completo]
        self.y_todo = y[completo]
        conocido = self.y_todo.notna()
        self.X = self.X_todo[conocido]
        self.y = self.y_todo[conocido]
        self.X_ult = self.X_todo.iloc[[-1]]
        self.nivel_dep = df[dep]  # la serie (transformada) del objetivo, para benchmarks
        # fecha a la que corresponde cada objetivo y_{t+h}
        idx = df.index
        pos = {f: i for i, f in enumerate(idx)}
        self.fechas_objetivo = pd.DatetimeIndex([idx[pos[f] + horizonte] for f in self.X.index], name="fecha")
        self.fecha_pron = _sumar_periodos(idx[-1], horizonte, freq)
        if len(self.X) < 30:
            raise ErrorMetodo(
                f"Quedan {len(self.X)} observaciones útiles después de rezagos y horizonte; "
                "hacen falta al menos 30. Bajá los rezagos o el horizonte, o usá otra frecuencia."
            )

    @property
    def columnas(self) -> list[str]:
        return list(self.X.columns)


def _sumar_periodos(fecha, n: int, freq: str):
    if freq == "mensual":
        return fecha + pd.offsets.MonthEnd(n)
    if freq == "trimestral":
        return fecha + pd.offsets.QuarterEnd(n)
    if freq == "anual":
        return fecha + pd.offsets.YearEnd(n)
    return fecha + pd.Timedelta(days=n)


def fechas_futuras(ultima, n: int, freq: str) -> pd.DatetimeIndex:
    return pd.DatetimeIndex([_sumar_periodos(ultima, k, freq) for k in range(1, n + 1)])


# ── eventos de la Línea de Tiempo ────────────────────────────────────────────
def eventos_en(desde, hasta, categorias: list[str] | None = None) -> list[dict]:
    """Eventos de `data/historia/eventos.csv` que caen en [desde, hasta]."""
    try:
        from cueva.datos import historia
    except Exception:  # pragma: no cover
        return []
    try:
        evs = historia.cargar_eventos()
    except Exception:
        return []
    out = []
    d0, d1 = pd.Timestamp(desde), pd.Timestamp(hasta)
    for e in evs:
        f = getattr(e, "desde", None)
        if f is None:
            continue
        t = pd.Timestamp(f)
        if d0 <= t <= d1 and (not categorias or getattr(e, "categoria", "") in categorias):
            out.append(
                {
                    "id": e.id,
                    "titulo": e.titulo,
                    "fecha": str(t.date()),
                    "categoria": getattr(e, "categoria", ""),
                }
            )
    return out


def evento_cercano(fecha, ventana_meses: int = 6, categorias=None) -> dict | None:
    """El evento de la Línea de Tiempo más cercano a una fecha (± ventana)."""
    t = pd.Timestamp(fecha)
    evs = eventos_en(
        t - pd.DateOffset(months=ventana_meses), t + pd.DateOffset(months=ventana_meses), categorias
    )
    if not evs:
        return None
    return min(evs, key=lambda e: abs(pd.Timestamp(e["fecha"]) - t))


def fmt(x, d=3) -> str:
    """Número para el resumen en castellano (coma decimal)."""
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "—"
    if isinstance(x, (int, np.integer)):
        return f"{int(x):,}".replace(",", ".")
    s = f"{x:.{d}g}" if abs(x) >= 1e4 or (abs(x) < 1e-3 and x != 0) else f"{x:.{d}f}"
    return s.replace(".", ",") if "e" not in s else s


def fila_p(p) -> str:
    """Estrellitas de significatividad."""
    if p is None or not np.isfinite(p):
        return ""
    return "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else ""
