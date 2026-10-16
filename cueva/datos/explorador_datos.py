"""explorador_datos — payload de datos columnares para el explorador nativo.

El explorador (`web/explorador.html`, la SPA heredada del visualizador del Trabajo Final)
espera un objeto `EMBEDDED = {archivo: {columna: [valores]}}`. Antes ese objeto se horneaba
dentro del HTML con `generar_visualizador.py` (proyecto TF); ahora lo sirve la API en vivo
(`GET /api/v1/explorador/datos`) leyendo los mismos archivos in situ.

Qué incluye (mismo contrato que el generador original):
  - Todos los CSV referenciados por `catalogo.json` (solo las columnas fecha/valor citadas).
  - Los deflactores: PBI ARS/USD/constante (+ versiones Kalman mensuales), `__cer__`, `__tip__`.
  - Las dummies del explorador (cepo, covid, gobierno, elecciones).
  - Los xlsx del catálogo y los vencimientos (xlsx transpuesto → columnas venc_*).

Este módulo NO toca la red y NO conoce HTTP: devuelve dicts. El caché se invalida por
huella (mtime del catálogo + carpeta de datos).
"""

from __future__ import annotations

import logging
import re
import threading
import unicodedata
from datetime import datetime
from pathlib import Path

from cueva import config
from cueva.datos.series import _cargar_definicion_curada

log = logging.getLogger("cueva.datos")

# Dummies que el explorador dibuja como bandas (definidas en la SPA, no en el catálogo)
_DUMMIES: dict[str, set[str]] = {
    "dummy_cepo.csv": {"fecha", "dummy_cepo"},
    "dummy_covid.csv": {"fecha", "dummy_covid"},
    "dummy_gob.csv": {"fecha", "gobierno_nombre"},
    "dummy_elec.csv": {"fecha", "dummy_electoral"},
}

# Archivos que la SPA pide por código (deflactores PBI) y no siempre están en el catálogo
_EXTRAS_PBI: dict[str, set[str]] = {
    "pbi_corriente.csv": {"fecha", "pbi"},
    "pbi_nominal_kalman.csv": {"fecha", "y_pred"},
    "pbi_constante_2004.csv": {"fecha", "pbi"},
    "pbi_constante_kalman.csv": {"fecha", "y_pred"},
    "pbi_trimestral_usd_mep.csv": {"periodo", "pbi_usd_mm", "pbi_pesos_mm"},
    "pbi_usd_kalman.csv": {"fecha", "y_pred"},
    "brecha_cambiaria.csv": {"fecha", "mep"},
}

# Estos "csv" no existen: los produce el parser de vencimientos (xlsx transpuesto)
_VENCIMIENTOS = {
    "vencimientos_1y_nuevo.csv": "vencimientos_1y_nuevo.xlsx",
    "vencimientos_2y_nuevo.csv": "vencimientos_2y_nuevo.xlsx",
}

_cache_lock = threading.Lock()
_cache: dict | None = None
_cache_firma: tuple | None = None


def _carpeta_vars() -> Path | None:
    tf = config.carpeta_trabajo_final()
    if not tf:
        return None
    carpeta = tf / "data" / "Variables Finales"
    return carpeta if carpeta.exists() else None


def _carpeta_raw() -> Path | None:
    tf = config.carpeta_trabajo_final()
    if not tf:
        return None
    carpeta = tf / "data" / "raw"
    return carpeta if carpeta.exists() else None


def _archivos_requeridos() -> dict[str, set[str]]:
    """{archivo → columnas necesarias} según catálogo + dummies + deflactores."""
    requeridos: dict[str, set[str]] = {}
    for hoja in _cargar_definicion_curada():
        for f in hoja["fuentes"]:
            cols = requeridos.setdefault(f["file"], set())
            if f.get("dateCol"):
                cols.add(f["dateCol"])
            if f.get("valCol"):
                cols.add(f["valCol"])
    for archivo, cols in {**_DUMMIES, **_EXTRAS_PBI}.items():
        requeridos.setdefault(archivo, set()).update(cols)
    return requeridos


def _valor(v):
    """Serializa un valor de celda: float redondeado, None si NaN, string si no es número."""
    import pandas as pd

    if v is None or (isinstance(v, float) and v != v):
        return None
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    if hasattr(v, "strftime"):
        return str(v)[:10]
    if isinstance(v, (int, float)):
        return round(float(v), 4)
    s = str(v).strip()
    if s == "":
        return None
    try:
        return round(float(s), 4)
    except ValueError:
        return s


def _leer_csv(path: Path, cols: set[str]) -> dict | None:
    import pandas as pd

    try:
        df = pd.read_csv(path, encoding="utf-8-sig", dtype=str)
    except Exception as e:
        log.warning("explorador: no pude leer %s: %s", path.name, e)
        return None
    df.columns = [str(c).strip() for c in df.columns]
    presentes = [c for c in cols if c.strip() in df.columns]
    if not presentes:
        return None
    out: dict[str, list] = {}
    for c in presentes:
        out[c] = [_valor(v) for v in df[c.strip()].tolist()]
    return out


def _leer_xlsx(path: Path, cols: set[str]) -> dict | None:
    import pandas as pd

    try:
        if "fiscal" in path.name.lower():
            df = pd.read_excel(path, sheet_name="Unificado")
        else:
            df = pd.read_excel(path, sheet_name=0)
    except Exception as e:
        log.warning("explorador: no pude leer %s: %s", path.name, e)
        return None
    presentes = [c for c in cols if c in df.columns]
    if not presentes:
        return None
    return {c: [_valor(v) for v in df[c].tolist()] for c in presentes}


def _columna_venc(principal: str, sub: str | None = None) -> str:
    t = str.maketrans("ÁÉÍÓÚáéíóúÑñ", "AEIOUaeiouNn")
    s = re.sub(r"[^A-Z0-9\s]", " ", principal.strip().translate(t).upper())
    s = re.sub(r"_+", "_", re.sub(r"\s+", "_", s.strip())).lower()
    p = f"venc_{s}"
    if sub:
        if "local" in sub.lower():
            return f"{p}_local"
        if "extranjera" in sub.lower():
            return f"{p}_ext"
    return p


def _leer_vencimientos(path: Path) -> dict | None:
    """Parsea el xlsx transpuesto de vencimientos (filas=categorías, columnas=fechas MM/YY)."""
    import pandas as pd

    try:
        df = pd.read_excel(path, sheet_name="Por Tipo y Moneda", header=None)
    except Exception as e:
        log.warning("explorador: no pude leer %s: %s", path.name, e)
        return None
    crudas = [df.iloc[5, j] for j in range(1, df.shape[1]) if pd.notna(df.iloc[5, j])]
    n = len(crudas)
    if not n:
        return None

    def _fecha(d) -> datetime:
        mm, yy = str(d).strip().split("/")
        return datetime(int(yy), int(mm), 1)

    orden = sorted(range(n), key=lambda i: _fecha(crudas[i]))
    fechas = [_fecha(crudas[i]).strftime("%Y-%m-%d") for i in orden]
    out: dict[str, list] = {"fecha": fechas}
    principal = None
    for ri in range(6, df.shape[0]):
        celda = df.iloc[ri, 0]
        if pd.isna(celda):
            continue
        etiqueta = str(celda)
        limpia = etiqueta.strip()
        if not etiqueta.startswith("  "):
            principal = limpia
            col = _columna_venc(principal)
        else:
            col = _columna_venc(principal or "", limpia)
        fila = [df.iloc[ri, j + 1] for j in range(n)]
        out[col] = [_valor(fila[i]) for i in orden]
    return out


def _normalizar(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def _firma() -> tuple:
    carpeta = _carpeta_vars()
    partes = []
    if carpeta:
        archivos = sorted(carpeta.iterdir())
        partes.append((str(carpeta), len(archivos), max((f.stat().st_mtime for f in archivos), default=0)))
    cat = Path(__file__).with_name("catalogo.json")
    return (cat.stat().st_mtime if cat.exists() else 0, tuple(partes))


def payload() -> dict:
    """Arma (cacheado) el payload {archivo: {col: [valores]}} para la SPA del explorador.

    Devuelve {} si no se encuentra la carpeta de datos del Trabajo Final."""
    global _cache, _cache_firma
    carpeta = _carpeta_vars()
    if not carpeta:
        return {}
    firma = _firma()
    with _cache_lock:
        if _cache is not None and firma == _cache_firma:
            return _cache

    datos: dict[str, dict] = {}
    # los nombres del catálogo pueden diferir en normalización unicode del filesystem
    en_disco = {_normalizar(f.name): f for f in carpeta.iterdir() if f.is_file()}

    for archivo, cols in sorted(_archivos_requeridos().items()):
        if archivo in _VENCIMIENTOS:
            continue  # se procesan aparte, desde el xlsx transpuesto
        path = en_disco.get(_normalizar(archivo))
        if path is None:
            log.debug("explorador: no encontrado %s", archivo)
            continue
        if archivo.lower().endswith((".xlsx", ".xls")):
            leido = _leer_xlsx(path, cols)
        else:
            leido = _leer_csv(path, cols)
        if leido:
            datos[archivo] = leido

    for csv_virtual, xlsx in _VENCIMIENTOS.items():
        path = en_disco.get(_normalizar(xlsx))
        if path is None:
            continue
        leido = _leer_vencimientos(path)
        if leido:
            datos[csv_virtual] = leido

    raw = _carpeta_raw()
    if raw:
        cer = raw / "bcra" / "cer.csv"
        if cer.exists():
            leido = _leer_csv(cer, {"fecha", "cer"})
            if leido:
                datos["__cer__"] = leido
        tip = raw / "global" / "tip_etf.csv"
        if tip.exists():
            leido = _leer_csv(tip, {"fecha", "tip_close"})
            if leido:
                datos["__tip__"] = leido

    with _cache_lock:
        _cache, _cache_firma = datos, firma
    return datos


def refrescar() -> None:
    """Invalida el caché (fuerza relectura en la próxima consulta)."""
    global _cache, _cache_firma
    with _cache_lock:
        _cache = None
        _cache_firma = None
