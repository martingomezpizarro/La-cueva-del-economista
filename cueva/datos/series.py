"""series — Catálogo unificado de series de tiempo.

La fuente de verdad es un **catálogo curado** (`cueva/datos/catalogo.json`): 9 familias
(grupo → subgrupo → series) con etiqueta, unidad y fuentes por frecuencia (M/Q/A). Ese mismo
archivo alimenta el árbol del visualizador (ver `scripts/generar_arbol_visualizador.py`), así
que el usuario, los agentes y el explorador ven UNA sola taxonomía.

Sobre ese catálogo:
- Cada serie curada trae `grupo`, `subgrupo`, `unidad`, `etiqueta` e `id` estable.
- Las columnas que el catálogo cubre NO se vuelven a listar como series "crudas": el escaneo
  de archivos queda solo como *fallback* para CSVs sueltos (datos sintéticos de test, subidas
  futuras, archivos aún sin curar).
- Se leen los archivos in situ desde la carpeta del Trabajo Final (ver `cueva/config.py`); no se
  mueve ni copia nada. ANÁLISIS MATRIZ ARG queda excluido: sus CSVs duplicaban EMAE/ICA que ya
  están, mejor abiertos, en el Trabajo Final.

El catálogo se cachea en memoria y se invalida cuando cambia el contenido de la carpeta fuente o
el propio `catalogo.json` (o llamando a `refrescar()`).
"""

from __future__ import annotations

import json
import re
import unicodedata
import warnings
from dataclasses import asdict, dataclass, field
from pathlib import Path

from cueva import config

_ORD_FREQ = {"D": 0, "W": 1, "M": 2, "Q": 3, "A": 4}
_RUTA_CATALOGO = Path(__file__).with_name("catalogo.json")


@dataclass
class SerieInfo:
    id: str
    nombre: str
    origen: str  # "Trabajo Final"
    archivo: str  # ruta absoluta de la fuente primaria
    col_fecha: str
    col_valor: str
    n: int
    desde: str
    hasta: str
    grupo: str = ""
    subgrupo: str = ""
    unidad: str = ""
    fuentes: list[dict] = field(default_factory=list)  # [{freq,file,dateCol,valCol,path}]

    def to_dict(self) -> dict:
        return asdict(self)


def _slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "_", s).strip("_").lower()
    return s[:60] or "serie"


_PAT_FECHA = re.compile(r"fecha|periodo|date|indice_tiempo|time|mes|trimestre|anio|a_o", re.I)


def _es_columna_fecha(nombre: str) -> bool:
    return bool(_PAT_FECHA.search(str(nombre)))


def _carpeta_vars() -> Path | None:
    """Carpeta con los CSV del Trabajo Final (data/Variables Finales), o None si no está."""
    tf = config.carpeta_trabajo_final()
    if not tf:
        return None
    carpeta = tf / "data" / "Variables Finales"
    return carpeta if carpeta.exists() else None


def _fuentes() -> list[tuple[str, Path]]:
    carpeta = _carpeta_vars()
    return [("Trabajo Final", carpeta)] if carpeta else []


def _firma() -> tuple:
    """Huella del estado: cambia si se toca algún CSV fuente o el propio catalogo.json."""
    partes = []
    for origen, carpeta in _fuentes():
        archivos = sorted(Path(carpeta).glob("*.csv"))
        partes.append(
            (origen, str(carpeta), len(archivos), max((f.stat().st_mtime for f in archivos), default=0))
        )
    cat_mtime = _RUTA_CATALOGO.stat().st_mtime if _RUTA_CATALOGO.exists() else 0
    return (cat_mtime, tuple(partes))


_CACHE: dict[str, SerieInfo] | None = None
_CACHE_FIRMA: tuple | None = None


def refrescar() -> None:
    """Invalida el caché del catálogo (fuerza re-escaneo en la próxima consulta)."""
    global _CACHE, _CACHE_FIRMA
    _CACHE = None
    _CACHE_FIRMA = None


# ── Catálogo curado (catalogo.json) ───────────────────────────────────────────


def _iter_hojas(nodo, grupo="", subgrupo=""):
    """Recorre familias → subs → items → children y produce (grupo, subgrupo, item)."""
    if isinstance(nodo, list):
        for x in nodo:
            yield from _iter_hojas(x, grupo, subgrupo)
        return
    if not isinstance(nodo, dict):
        return
    g = nodo.get("grp", grupo)
    s = nodo.get("sub", subgrupo)
    if "id" in nodo:
        yield g, s, nodo
    for hijo in nodo.get("children", []):
        yield from _iter_hojas(hijo, g, s)
    for sub in nodo.get("subs", []):
        yield from _iter_hojas(sub, g, subgrupo)
    for it in nodo.get("items", []):
        yield from _iter_hojas(it, g, s)


def _fuentes_de_item(item: dict) -> list[dict]:
    """Normaliza un item del catálogo a lista de fuentes {freq,file,dateCol,valCol}."""
    if item.get("sources"):
        return [dict(s) for s in item["sources"]]
    if item.get("file"):
        return [
            {
                "freq": item.get("freq", ""),
                "file": item["file"],
                "dateCol": item.get("dateCol", ""),
                "valCol": item.get("valCol", ""),
            }
        ]
    return []


def _cargar_definicion_curada() -> list[dict]:
    """Lee catalogo.json y devuelve una lista de hojas normalizadas (sin tocar disco)."""
    if not _RUTA_CATALOGO.exists():
        return []
    try:
        doc = json.loads(_RUTA_CATALOGO.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    familias = doc.get("familias", doc if isinstance(doc, list) else [])
    hojas = []
    for grupo, subgrupo, item in _iter_hojas(familias):
        fuentes = _fuentes_de_item(item)
        if not fuentes:
            continue
        hojas.append(
            {
                "id": item["id"],
                "etiqueta": item.get("label", item["id"]),
                "unidad": item.get("unit", ""),
                "grupo": grupo,
                "subgrupo": subgrupo,
                "fuentes": fuentes,
            }
        )
    return hojas


def catalogo() -> dict[str, SerieInfo]:
    """Arma el catálogo {id: SerieInfo} combinando el curado con el escaneo (cacheado)."""
    global _CACHE, _CACHE_FIRMA
    firma = _firma()
    if _CACHE is not None and firma == _CACHE_FIRMA:
        return _CACHE

    import pandas as pd

    carpeta = _carpeta_vars()
    _cache_df: dict = {}  # ruta -> DataFrame de encabezado (nrows=400) o None

    def _encabezado(path: Path):
        clave = str(path)
        if clave not in _cache_df:
            try:
                df = pd.read_csv(path, nrows=400, encoding="utf-8-sig")
                df.columns = [str(c).strip() for c in df.columns]
                _cache_df[clave] = df
            except Exception:
                _cache_df[clave] = None
        return _cache_df[clave]

    cat: dict[str, SerieInfo] = {}
    archivos_curados: set[str] = set()

    # 1) Series curadas (catalogo.json)
    for hoja in _cargar_definicion_curada():
        # un archivo referenciado por el catálogo es "territorio curado": el escaneo no vuelve a
        # explotar sus otras columnas (así no reaparecen los slugs crípticos de los INDEC anuales).
        for f in hoja["fuentes"]:
            archivos_curados.add(f["file"].lower())
        if not carpeta:
            continue
        # resolver fuentes CSV existentes; primaria = la de frecuencia más fina disponible
        resueltas = []
        for f in hoja["fuentes"]:
            if not f["file"].lower().endswith(".csv"):
                continue
            p = carpeta / f["file"]
            if p.exists():
                g = dict(f)
                g["path"] = str(p)
                resueltas.append(g)
        if not resueltas:
            continue
        resueltas.sort(key=lambda f: _ORD_FREQ.get(f.get("freq", ""), 9))
        prim = resueltas[0]
        df = _encabezado(Path(prim["path"]))
        if df is None or prim["valCol"] not in df.columns:
            continue
        col_fecha = (
            prim["dateCol"]
            if prim["dateCol"] in df.columns
            else next((c for c in df.columns if _es_columna_fecha(c)), df.columns[0])
        )
        valores = pd.to_numeric(df[prim["valCol"]], errors="coerce")
        n_val = int(valores.notna().sum())
        if n_val < 8:
            continue
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            fechas = pd.to_datetime(df[col_fecha], errors="coerce").dropna()
        cat[hoja["id"]] = SerieInfo(
            id=hoja["id"],
            nombre=hoja["etiqueta"],
            origen="Trabajo Final",
            archivo=prim["path"],
            col_fecha=col_fecha,
            col_valor=prim["valCol"],
            n=n_val,
            desde=str(fechas.min().date()) if len(fechas) else "",
            hasta=str(fechas.max().date()) if len(fechas) else "",
            grupo=hoja["grupo"],
            subgrupo=hoja["subgrupo"],
            unidad=hoja["unidad"],
            fuentes=resueltas,
        )

    # 2) Escaneo de archivos (fallback): solo archivos que el catálogo NO curó
    for origen, carp in _fuentes():
        for f in sorted(Path(carp).glob("*.csv")):
            if f.name.lower() in archivos_curados:
                continue
            df = _encabezado(f)
            if df is None:
                continue
            cols = list(df.columns)
            col_fecha = next((c for c in cols if _es_columna_fecha(c)), cols[0])
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
                    fechas = pd.to_datetime(df[col_fecha], errors="coerce").dropna()
                cat[sid] = SerieInfo(
                    id=sid,
                    nombre=f"{f.stem} · {c}" if c.lower() not in ("valor", "value") else f.stem,
                    origen=origen,
                    archivo=str(f),
                    col_fecha=col_fecha,
                    col_valor=c,
                    n=int(serie.notna().sum()),
                    desde=str(fechas.min().date()) if len(fechas) else "",
                    hasta=str(fechas.max().date()) if len(fechas) else "",
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
        if f and not any(f in campo.lower() for campo in (s.id, s.nombre, s.grupo, s.subgrupo)):
            continue
        out.append(s.to_dict())
    out.sort(key=lambda d: (d["grupo"], d["subgrupo"], d["nombre"].lower()))
    return out[:limite] if limite else out


def _regla_resample(freq: str | None) -> str | None:
    return {
        "diaria": "D",
        "mensual": "ME",
        "trimestral": "QE",
        "anual": "YE",
        "D": "D",
        "M": "ME",
        "Q": "QE",
        "A": "YE",
    }.get(freq or "", None)


def _fuente_para_freq(info: SerieInfo, freq: str | None) -> dict:
    """Elige, entre las fuentes de la serie, la de frecuencia más cercana a la pedida."""
    if not info.fuentes:
        return {"path": info.archivo, "dateCol": info.col_fecha, "valCol": info.col_valor}
    objetivo = {"diaria": "D", "mensual": "M", "trimestral": "Q", "anual": "A"}.get(freq or "", freq)
    obj = _ORD_FREQ.get(objetivo or "", None)
    if obj is None:
        return info.fuentes[0]
    return min(
        info.fuentes,
        key=lambda f: (abs(_ORD_FREQ.get(f.get("freq", ""), 9) - obj), _ORD_FREQ.get(f.get("freq", ""), 9)),
    )


def cargar(sid: str, freq: str | None = None):
    """Devuelve un pandas.Series indexado por fecha. freq: 'D','M','Q','A' para remuestrear."""
    import pandas as pd

    cat = catalogo()
    if sid not in cat:
        raise KeyError(f"Serie desconocida: {sid}")
    info = cat[sid]
    fuente = _fuente_para_freq(info, freq)
    df = pd.read_csv(fuente["path"], encoding="utf-8-sig")
    df.columns = [str(c).strip() for c in df.columns]
    col_fecha = fuente["dateCol"] if fuente["dateCol"] in df.columns else info.col_fecha
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fechas = pd.to_datetime(df[col_fecha], errors="coerce")
    valores = pd.to_numeric(df[fuente["valCol"]], errors="coerce")
    s = pd.Series(valores.values, index=fechas, name=sid).dropna()
    s = s[~s.index.isna()].sort_index()
    regla = _regla_resample(freq)
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
