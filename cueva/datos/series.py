"""series — Catálogo unificado de series de tiempo.

Reúne las series del Trabajo Final (data/Variables Finales) y de ANÁLISIS MATRIZ ARG
(Series/). No mueve ni copia archivos: las lee in situ desde sus carpetas originales
(ver cueva/config.py).

Cada serie se identifica con un ID estable (slug del nombre de archivo + columna). La carga
devuelve un pandas.Series con índice de fechas, lista para los tests y modelos.

El catálogo se cachea en memoria y se invalida solo cuando cambia el contenido de las
carpetas fuente (o llamando a `refrescar()`): agregar un CSV nuevo ya no exige reiniciar.
"""

from __future__ import annotations

import re
import unicodedata
import warnings
from dataclasses import asdict, dataclass
from pathlib import Path

from cueva import config


@dataclass
class SerieInfo:
    id: str
    nombre: str
    origen: str  # "Trabajo Final" | "MATRIZ ARG"
    archivo: str  # ruta absoluta
    col_fecha: str
    col_valor: str
    n: int
    desde: str
    hasta: str

    def to_dict(self) -> dict:
        return asdict(self)


def _slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "_", s).strip("_").lower()
    return s[:60] or "serie"


_PAT_FECHA = re.compile(r"fecha|periodo|date|indice_tiempo|time|mes|trimestre|anio|a_o", re.I)


def _es_columna_fecha(nombre: str) -> bool:
    return bool(_PAT_FECHA.search(str(nombre)))


def _fuentes() -> list[tuple[str, Path]]:
    fuentes = []
    tf = config.carpeta_trabajo_final()
    if tf:
        fuentes.append(("Trabajo Final", tf / "data" / "Variables Finales"))
    ma = config.carpeta_matriz_arg()
    if ma:
        fuentes.append(("MATRIZ ARG", ma / "Series"))
    return fuentes


def _firma() -> tuple:
    """Huella del estado de las carpetas fuente: cambia si se agregan/quitan/tocan CSVs."""
    partes = []
    for origen, carpeta in _fuentes():
        c = Path(carpeta)
        if not c.exists():
            continue
        archivos = sorted(c.glob("*.csv"))
        partes.append((origen, str(c), len(archivos), max((f.stat().st_mtime for f in archivos), default=0)))
    return tuple(partes)


_CACHE: dict[str, SerieInfo] | None = None
_CACHE_FIRMA: tuple | None = None


def refrescar() -> None:
    """Invalida el caché del catálogo (fuerza re-escaneo en la próxima consulta)."""
    global _CACHE, _CACHE_FIRMA
    _CACHE = None
    _CACHE_FIRMA = None


def catalogo() -> dict[str, SerieInfo]:
    """Escanea las carpetas de datos y arma el catálogo {id: SerieInfo} (cacheado)."""
    global _CACHE, _CACHE_FIRMA
    firma = _firma()
    if _CACHE is not None and firma == _CACHE_FIRMA:
        return _CACHE

    import pandas as pd

    cat: dict[str, SerieInfo] = {}
    for origen, carpeta in _fuentes():
        if not carpeta or not Path(carpeta).exists():
            continue
        for f in sorted(Path(carpeta).glob("*.csv")):
            try:
                df = pd.read_csv(f, nrows=400, encoding="utf-8-sig")
            except Exception:
                continue
            cols = [str(c).strip() for c in df.columns]
            df.columns = cols
            col_fecha = next((c for c in cols if _es_columna_fecha(c)), None)
            if col_fecha is None:
                col_fecha = cols[0]
            # columnas numéricas candidatas a valor
            for c in cols:
                if c == col_fecha:
                    continue
                serie = pd.to_numeric(df[c], errors="coerce")
                if serie.notna().sum() < 8:
                    continue
                base = _slug(f.stem)
                sid = base if len([x for x in cols if x != col_fecha]) == 1 else f"{base}__{_slug(c)}"
                if sid in cat:
                    continue
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    fechas = pd.to_datetime(df[col_fecha], errors="coerce", dayfirst=False)
                fechas_ok = fechas.dropna()
                cat[sid] = SerieInfo(
                    id=sid,
                    nombre=f"{f.stem} · {c}" if c.lower() not in ("valor", "value") else f.stem,
                    origen=origen,
                    archivo=str(f),
                    col_fecha=col_fecha,
                    col_valor=c,
                    n=int(serie.notna().sum()),
                    desde=str(fechas_ok.min().date()) if len(fechas_ok) else "",
                    hasta=str(fechas_ok.max().date()) if len(fechas_ok) else "",
                )
    _CACHE, _CACHE_FIRMA = cat, firma
    return cat


def listar(filtro: str = "", origen: str = "", limite: int = 0) -> list[dict]:
    cat = catalogo()
    out = []
    f = filtro.lower()
    for s in cat.values():
        if origen and s.origen != origen:
            continue
        if f and f not in s.id.lower() and f not in s.nombre.lower():
            continue
        out.append(s.to_dict())
    out.sort(key=lambda d: d["nombre"].lower())
    return out[:limite] if limite else out


def cargar(sid: str, freq: str | None = None):
    """Devuelve un pandas.Series indexado por fecha. freq: 'D','M','Q','A' para remuestrear."""
    import pandas as pd

    cat = catalogo()
    if sid not in cat:
        raise KeyError(f"Serie desconocida: {sid}")
    info = cat[sid]
    df = pd.read_csv(info.archivo, encoding="utf-8-sig")
    df.columns = [str(c).strip() for c in df.columns]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fechas = pd.to_datetime(df[info.col_fecha], errors="coerce")
    valores = pd.to_numeric(df[info.col_valor], errors="coerce")
    s = pd.Series(valores.values, index=fechas, name=sid).dropna()
    s = s[~s.index.isna()].sort_index()
    if freq:
        regla = {
            "diaria": "D",
            "mensual": "ME",
            "trimestral": "QE",
            "anual": "YE",
            "D": "D",
            "M": "ME",
            "Q": "QE",
            "A": "YE",
        }.get(freq, None)
        if regla:
            s = s.resample(regla).mean().dropna()
    return s


def panel(sids: list[str], freq: str = "mensual"):
    """Arma un DataFrame alineando varias series a la misma frecuencia."""
    import pandas as pd

    cols = {}
    for sid in sids:
        try:
            cols[sid] = cargar(sid, freq=freq)
        except Exception:
            continue
    if not cols:
        return pd.DataFrame()
    return pd.concat(cols, axis=1).dropna(how="all")
