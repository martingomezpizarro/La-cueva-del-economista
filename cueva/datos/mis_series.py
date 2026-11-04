"""mis_series — Series propias del usuario: subir, listar y borrar CSV.

Es la puerta para usar la plataforma con datos que no están en el catálogo curado (precios de
activos, bases propias, exportaciones de otras herramientas). Cada CSV se valida, se guarda en
`<CUEVA_DATA>/series_usuario/` con nombre saneado y entra al catálogo por el escaneo: cada
columna numérica es una serie (`<archivo>__<columna>`, o `<archivo>` si hay una sola).

Checklist de seguridad: extensión .csv, tamaño máximo, decodificación UTF-8, columna de fecha
reconocible, al menos una columna numérica con 8 valores, nombre regenerado (sin rutas).

Qué NO hace: no sale a la red, no modifica `catalogo.json` (lo curado sigue siendo curado).
"""

from __future__ import annotations

import io
import re
import unicodedata
import warnings

from cueva.datos import series as S

MAX_BYTES = 25 * 1024 * 1024


class ArchivoInvalido(ValueError):
    """El archivo no pasa la validación (el mensaje es para el usuario)."""


def _nombre_seguro(nombre: str) -> str:
    base = nombre.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    base = re.sub(r"\.csv$", "", base, flags=re.I)
    base = unicodedata.normalize("NFKD", base).encode("ascii", "ignore").decode()
    base = re.sub(r"[^A-Za-z0-9]+", "_", base).strip("_").lower()[:60]
    if not base:
        raise ArchivoInvalido("Nombre de archivo vacío.")
    return f"mis_{base}"


def guardar(nombre: str, contenido: bytes) -> dict:
    """Valida y guarda un CSV. Devuelve {archivo, series: [{id, nombre, n, desde, hasta}]}."""
    import pandas as pd

    if not nombre.lower().endswith(".csv"):
        raise ArchivoInvalido("Sólo se aceptan archivos .csv.")
    if len(contenido) > MAX_BYTES:
        raise ArchivoInvalido(f"El archivo supera {MAX_BYTES // 1024 // 1024} MB.")
    try:
        texto = contenido.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            texto = contenido.decode("latin-1")
        except UnicodeDecodeError as e:
            raise ArchivoInvalido("No pude leer el archivo como texto.") from e
    sep = ";" if texto.count(";") > texto.count(",") else ","
    decimal = "," if sep == ";" else "."
    try:
        df = pd.read_csv(io.StringIO(texto), sep=sep, decimal=decimal)
    except Exception as e:
        raise ArchivoInvalido(f"No es un CSV válido: {e}") from e
    df.columns = [str(c).strip() for c in df.columns]
    col_fecha = next((c for c in df.columns if S._es_columna_fecha(c)), df.columns[0])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fechas = pd.to_datetime(df[col_fecha], errors="coerce", dayfirst=False)
    if fechas.notna().mean() < 0.8:
        raise ArchivoInvalido(f"La columna «{col_fecha}» no parece de fechas (menos del 80 % se pudo leer).")
    numericas = [
        c for c in df.columns if c != col_fecha and pd.to_numeric(df[c], errors="coerce").notna().sum() >= 8
    ]
    if not numericas:
        raise ArchivoInvalido("No hay ninguna columna numérica con al menos 8 valores.")
    salida = df[[col_fecha, *numericas]].copy()
    salida[col_fecha] = fechas.dt.strftime("%Y-%m-%d %H:%M:%S").str.replace(" 00:00:00", "", regex=False)
    salida = salida[fechas.notna()].sort_values(col_fecha)
    salida = salida.rename(columns={col_fecha: "fecha"})
    carpeta = S.carpeta_usuario()
    carpeta.mkdir(parents=True, exist_ok=True)
    base = _nombre_seguro(nombre)
    ruta = carpeta / f"{base}.csv"
    salida.to_csv(ruta, index=False, encoding="utf-8-sig")
    S.refrescar()
    return {"archivo": ruta.name, "series": [s for s in listar() if s["archivo"] == ruta.name]}


def listar() -> list[dict]:
    out = []
    for sid, info in S.catalogo().items():
        if info.origen == S.ORIGEN_USUARIO:
            out.append(
                {
                    "id": sid,
                    "nombre": info.nombre,
                    "archivo": info.archivo.rsplit("/", 1)[-1],
                    "n": info.n,
                    "desde": info.desde,
                    "hasta": info.hasta,
                }
            )
    return sorted(out, key=lambda x: x["id"])


def borrar(archivo: str) -> bool:
    if not re.match(r"^mis_[a-z0-9_]{1,60}\.csv$", archivo):
        raise ArchivoInvalido("Nombre de archivo inválido.")
    ruta = S.carpeta_usuario() / archivo
    if not ruta.exists():
        return False
    ruta.unlink()
    S.refrescar()
    return True


def guardar_derivada(nombre: str, fechas: list[str], valores: list, descripcion: str = "") -> dict:
    """Guarda como serie propia una SALIDA de un método (ciclo HP, probabilidad de régimen,
    factor, pronóstico…). Así se encadenan métodos: la salida de uno es insumo del siguiente."""
    import pandas as pd

    if len(fechas) != len(valores) or len(fechas) < 8:
        raise ArchivoInvalido("Hacen falta al menos 8 pares fecha-valor del mismo largo.")
    if len(fechas) > 200_000:
        raise ArchivoInvalido("Serie demasiado larga.")
    df = pd.DataFrame({"fecha": fechas, "valor": pd.to_numeric(pd.Series(valores), errors="coerce")}).dropna()
    if len(df) < 8:
        raise ArchivoInvalido("Quedan menos de 8 valores numéricos.")
    carpeta = S.carpeta_usuario()
    carpeta.mkdir(parents=True, exist_ok=True)
    base = _nombre_seguro(nombre)
    df.to_csv(carpeta / f"{base}.csv", index=False, encoding="utf-8-sig")
    if descripcion:
        (carpeta / f"{base}.txt").write_text(descripcion[:500], encoding="utf-8")
    S.refrescar()
    return {"archivo": f"{base}.csv", "id": base}
