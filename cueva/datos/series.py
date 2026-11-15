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
- Los archivos se buscan primero en `data/series/` (la fuente de verdad, sin las carpetas
  `<Familia>_Fuentes/` de crudos) y solo si no están ahí en la carpeta del Trabajo Final, que
  es una muleta: la serie queda marcada con `origen="Trabajo Final"` para que se vea.
  ANÁLISIS MATRIZ ARG queda excluido: sus CSVs duplicaban EMAE/ICA que ya
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
    origen: str  # "data/series" | "Trabajo Final" (muleta) | carpeta del escaneo
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


def _normalizar_nombre(nombre: str) -> str:
    return unicodedata.normalize("NFC", nombre).lower()


def _indice_data_series() -> dict[str, Path]:
    """{nombre de archivo normalizado → ruta} dentro de data/series, sin `<Familia>_Fuentes/`."""
    raiz = config.carpeta_series()
    if not raiz.exists():
        return {}
    return {
        _normalizar_nombre(r.name): r
        for r in raiz.rglob("*")
        if r.is_file() and not any(p.name.endswith("_Fuentes") for p in r.relative_to(raiz).parents)
    }


def _resolver(nombre: str, indice: dict[str, Path], carpeta_tf: Path | None) -> tuple[Path, str] | None:
    """Ruta y origen de un archivo del catálogo: data/series primero, Trabajo Final de respaldo."""
    p = indice.get(_normalizar_nombre(nombre))
    if p is not None:
        return p, ORIGEN_DATA_SERIES
    if carpeta_tf is not None:
        q = carpeta_tf / nombre
        if q.exists():
            return q, "Trabajo Final"
    return None


ORIGEN_DATA_SERIES = "data/series"


ORIGEN_USUARIO = "Mis series"


def carpeta_usuario() -> Path:
    """Series que sube el usuario (CSV de precios, datos propios). Viven fuera del repo, en
    `<CUEVA_DATA>/series_usuario/`, y entran al catálogo por el escaneo (origen «Mis series»)."""
    return config.ruta_datos() / "series_usuario"


def _fuentes() -> list[tuple[str, Path]]:
    carpeta = _carpeta_vars()
    fuentes = [("Trabajo Final", carpeta)] if carpeta else []
    usuario = carpeta_usuario()
    if usuario.exists():
        fuentes.append((ORIGEN_USUARIO, usuario))
    return fuentes


def _firma() -> tuple:
    """Huella del estado: cambia si se toca algún CSV fuente o el propio catalogo.json."""
    partes = []
    for origen, carpeta in _fuentes():
        archivos = sorted(Path(carpeta).glob("*.csv"))
        partes.append(
            (origen, str(carpeta), len(archivos), max((f.stat().st_mtime for f in archivos), default=0))
        )
    raiz = config.carpeta_series()
    if raiz.exists():
        archivos = [f for f in raiz.rglob("*.csv")]
        partes.append(
            (
                ORIGEN_DATA_SERIES,
                str(raiz),
                len(archivos),
                max((f.stat().st_mtime for f in archivos), default=0),
            )
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
    indice = _indice_data_series()
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
        # resolver fuentes CSV existentes; primaria = la de frecuencia más fina disponible
        resueltas = []
        for f in hoja["fuentes"]:
            if not f["file"].lower().endswith(".csv"):
                continue
            r = _resolver(f["file"], indice, carpeta)
            if r is not None:
                g = dict(f)
                g["path"], g["origen"] = str(r[0]), r[1]
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
            origen=prim["origen"],
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


# ── Explorar: ficha, datos listos para graficar y estado por familia ─────────
_NATIVA = {"D": "diaria", "W": "semanal", "M": "mensual", "Q": "trimestral", "A": "anual"}


def tipo_agregacion(etiqueta: str, unidad: str) -> str:
    """Cómo se agrega la serie al bajar de frecuencia: 'ult' (stock, fin de período),
    'comp' (tasa mensual que se compone) o 'prom' (promedio).

    El catálogo todavía no lo declara, así que es una REGLA sobre etiqueta y unidad; la UI la
    muestra como supuesto. Cuando `proc` traiga `agregacion`, esa manda."""
    e, u = etiqueta.lower(), unidad.lower()
    if "%" in u and ("mensual" in u or "mensual" in e) and ("inflaci" in e or "var" in e or "ipc" in e):
        return "comp"
    if "%" in u or "tna" in u or "pb" == u.strip() or "tasa" in e:
        return "prom"
    if any(
        k in e for k in ("saldo", "reservas", "stock", "base monetaria", "deuda", "depósitos", "préstamos")
    ):
        return "ult"
    return "prom"


def _item_crudo(sid: str) -> tuple[str, str, dict] | None:
    """(familia, subgrupo, item) tal como está en catalogo.json, o None."""
    if not _RUTA_CATALOGO.exists():
        return None
    doc = json.loads(_RUTA_CATALOGO.read_text(encoding="utf-8"))
    for g, s, item in _iter_hojas(doc.get("familias", [])):
        if item.get("id") == sid:
            return g, s, item
    return None


def ficha(sid: str) -> dict:
    """Metadatos de una serie para la ficha de Explorar: catálogo + procedencia + archivo."""
    cat = catalogo()
    if sid not in cat:
        raise KeyError(f"Serie desconocida: {sid}")
    info = cat[sid]
    crudo = _item_crudo(sid)
    item = crudo[2] if crudo else {}
    prim = info.fuentes[0] if info.fuentes else {}
    proc = dict(item.get("proc") or {})
    # una serie con varias frecuencias puede tener `proc` por fuente: vale el de la primaria
    for f in item.get("sources") or []:
        if f.get("file") == prim.get("file") and f.get("proc"):
            proc = dict(f["proc"])
    raiz = config.carpeta_series()
    try:
        archivo = Path(info.archivo).resolve().relative_to(raiz.resolve()).as_posix()
    except ValueError:
        archivo = Path(info.archivo).name
    freq = prim.get("freq", "")
    return {
        "id": info.id,
        "nombre": info.nombre,
        "unidad": info.unidad,
        "familia": info.grupo,
        "subgrupo": info.subgrupo,
        "origen": info.origen,
        "archivo": archivo,
        "frecuencia_nativa": _NATIVA.get(freq, freq or "—"),
        "frecuencias": sorted({f.get("freq", "") for f in info.fuentes}, key=lambda f: _ORD_FREQ.get(f, 9)),
        "desde": info.desde,
        "hasta": info.hasta,
        "agregacion": proc.get("agregacion") or tipo_agregacion(info.nombre, info.unidad),
        "agregacion_supuesta": not proc.get("agregacion"),
        "proc": proc,
    }


def datos_explorar(sid: str) -> dict:
    """Ficha + valores para Explorar. Lo diario/semanal se baja a MENSUAL acá (con la regla
    de agregación de la ficha) para no mandar miles de puntos; lo mensual o más grueso viaja
    en su frecuencia nativa y el navegador lo agrega a trimestral/anual."""
    import pandas as pd

    f = ficha(sid)
    s = cargar(sid)
    nativa = f["frecuencias"][0] if f["frecuencias"] else "M"
    entrega = nativa
    if nativa in ("D", "W"):
        regla = {"ult": "last", "comp": "mean", "prom": "mean"}[f["agregacion"]]
        s = s.resample("ME").agg(regla).dropna()
        entrega = "M"
    s = s[pd.notna(s.values)]
    if len(s):  # el catálogo calcula el rango sobre un encabezado; acá va el real
        f["desde"], f["hasta"] = str(s.index.min().date()), str(s.index.max().date())
    return {
        **f,
        "frecuencia_entrega": entrega,
        "fechas": [d.strftime("%Y-%m-%d") for d in s.index],
        "valores": [float(v) for v in s.values],
    }


def resumen_familias() -> list[dict]:
    """Por familia del catálogo: entradas totales, cuántas resuelven en data/series y cuántas
    siguen colgadas del Trabajo Final. Es el «datos conectados» de Explorar."""
    cat = catalogo()
    orden: list[str] = []
    cuentas: dict[str, dict] = {}
    for hoja in _cargar_definicion_curada():
        g = hoja["grupo"]
        if g not in cuentas:
            orden.append(g)
            cuentas[g] = {"familia": g, "total": 0, "conectadas": 0, "trabajo_final": 0}
        c = cuentas[g]
        c["total"] += 1
        info = cat.get(hoja["id"])
        if info is not None and info.origen == ORIGEN_DATA_SERIES:
            c["conectadas"] += 1
        elif info is not None:
            c["trabajo_final"] += 1
    return [cuentas[g] for g in orden]
