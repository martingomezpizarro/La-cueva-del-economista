"""bajar_crisis_rr.py — trae la base de crisis de Reinhart & Rogoff y extrae Argentina.

«Global Crises Data by Country», que mantiene el Behavioral Finance & Financial Stability
de Harvard Business School. Es la pieza más valiosa de la cronología: cubre **1800 en
adelante** y ya trae fechadas las crisis bancarias, cambiarias, inflacionarias, de deuda
externa y de deuda doméstica, más la clasificación de régimen cambiario y el patrón oro.

Qué hace: baja el Excel, encuentra la hoja de Argentina, convierte las banderas anuales
(0/1 por año y tipo de crisis) en **episodios con fecha de inicio y de fin**, y los
escribe en `data/historia/eventos.csv` con el esquema de la cronología.

IMPORTANTE — este script no se pudo probar contra la fuente real: desde el sandbox de
Cowork `hbs.edu` está bloqueado por la allowlist de egress. Por eso trae `--inspeccionar`:
corrélo primero, mirá lo que reporta, y si los nombres de hoja o de columna no son los
que espera, ajustá `COLUMNAS` en vez de pelearte con el resto.

Uso:
    python scripts/bajar_crisis_rr.py --inspeccionar     # qué hojas y columnas trae
    python scripts/bajar_crisis_rr.py                    # extrae Argentina a eventos.csv
"""

from __future__ import annotations

import argparse
import csv
from datetime import date
from pathlib import Path

import pandas as pd
import requests

RAIZ = Path(__file__).resolve().parent.parent
CRUDO = RAIZ / "data" / "historia" / "_crudo"
# OJO: NO escribir en eventos.csv — ese archivo es la cronología curada a mano, con otro
# esquema (fichas, citas, verificación). Los episodios de R&R quedan en un archivo de
# trabajo y se integran a mano o con un script de fusión aparte.
SALIDA = RAIZ / "data" / "historia" / "_crudo" / "rr_argentina_episodios.csv"

URL = ("https://www.hbs.edu/behavioral-finance-and-financial-stability/"
       "Documents/ChartData/MapCharts/20160923_global_crisis_data.xlsx")
FUENTE = "Reinhart & Rogoff — Global Crises Data by Country (HBS)"

CAMPOS = ["id", "fecha_inicio", "fecha_fin", "ambito", "tipo", "titulo",
          "descripcion", "magnitud", "fuente", "verificado", "nota"]

# Fragmento del nombre de columna (en minúsculas) -> (tipo de evento, título legible).
# El Excel de HBS usa nombres largos y algo inconsistentes entre hojas; se busca por
# fragmento para no depender del texto exacto.
COLUMNAS: dict[str, tuple[str, str]] = {
    "banking crisis": ("crisis bancaria", "Crisis bancaria"),
    "systemic crisis": ("crisis bancaria sistémica", "Crisis bancaria sistémica"),
    "currency cris": ("crisis cambiaria", "Crisis cambiaria"),        # "Currency Crises"
    "inflation cris": ("crisis inflacionaria", "Crisis inflacionaria"),  # "Inflation Crises"
    "gold standard": ("patrón oro", "Patrón oro"),
    "sovereign external debt 1": ("default externo", "Default de deuda externa"),
    "domestic_debt_in_default": ("default doméstico", "Default de deuda doméstica"),
    "stock market crash": ("colapso bursátil", "Colapso del mercado accionario"),
    "independence": ("independencia", "Independencia"),
}
DESCARTAR = {"independencia"}  # no es un evento económico para nuestra cronología


def bajar(verificar_tls: bool = True) -> Path:
    CRUDO.mkdir(parents=True, exist_ok=True)
    destino = CRUDO / "rr_global_crisis_data.xlsx"
    if destino.exists():
        print(f"  ya estaba: {destino.relative_to(RAIZ)}")
        return destino
    print(f"  bajando {URL}")
    r = requests.get(URL, timeout=180, verify=verificar_tls)
    r.raise_for_status()
    destino.write_bytes(r.content)
    print(f"  {len(r.content) // 1024} KB -> {destino.relative_to(RAIZ)}")
    return destino


def tabla_argentina(libro: pd.ExcelFile) -> tuple[str, pd.DataFrame]:
    """Devuelve (descripción, filas de Argentina). Soporta los dos formatos de HBS:
    una hoja por país (versiones viejas) o una sola hoja larga con columna 'Country'
    (versión 2016-09-23, la que se baja hoy)."""
    for nombre in libro.sheet_names:
        if "argentin" in nombre.lower():
            return nombre, libro.parse(nombre)
    for nombre in libro.sheet_names:
        df = libro.parse(nombre)
        col = next((c for c in df.columns if str(c).strip().lower() == "country"), None)
        if col is not None:
            arg = df[df[col].astype(str).str.strip().str.lower() == "argentina"]
            if len(arg):
                return f"{nombre} (filas de Argentina)", arg.reset_index(drop=True)
    raise SystemExit(
        "No encontré una hoja de Argentina. Hojas disponibles:\n  "
        + "\n  ".join(libro.sheet_names)
    )


def _anio(valor) -> int | None:
    try:
        n = int(float(valor))
    except (TypeError, ValueError):
        return None
    return n if 1700 <= n <= 2100 else None


def episodios(anios: list[int], banderas: list) -> list[tuple[int, int]]:
    """Convierte una columna de 0/1 por año en tramos [inicio, fin]."""
    tramos, abierto = [], None
    for anio, v in zip(anios, banderas, strict=False):
        activo = False
        try:
            activo = float(v) >= 0.5
        except (TypeError, ValueError):
            activo = False
        if activo and abierto is None:
            abierto = anio
        elif not activo and abierto is not None:
            tramos.append((abierto, anio - 1))
            abierto = None
    if abierto is not None:
        tramos.append((abierto, anios[-1]))
    return tramos


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--inspeccionar", action="store_true",
                    help="Solo mostrar hojas y columnas, sin extraer nada.")
    ap.add_argument("--sin-verificar-tls", action="store_true")
    args = ap.parse_args()

    ruta = bajar(verificar_tls=not args.sin_verificar_tls)
    libro = pd.ExcelFile(ruta)

    if args.inspeccionar:
        print(f"\n{len(libro.sheet_names)} hojas:")
        for n in libro.sheet_names:
            print(f"  {n}")
        hoja, df = tabla_argentina(libro)
        print(f"\nColumnas de «{hoja}» ({len(df)} filas):")
        for c in df.columns:
            print(f"  {c}")
        return

    hoja, df = tabla_argentina(libro)
    col_anio = next((c for c in df.columns if "year" in str(c).lower()), df.columns[0])
    anios = [_anio(v) for v in df[col_anio]]
    validos = [i for i, a in enumerate(anios) if a is not None]
    if not validos:
        raise SystemExit(f"No pude leer los años de la columna '{col_anio}'. Probá --inspeccionar.")
    anios = [anios[i] for i in validos]
    df = df.iloc[validos].reset_index(drop=True)
    print(f"hoja «{hoja}»: {anios[0]}–{anios[-1]}")

    filas: list[dict] = []
    for columna in df.columns:
        texto = str(columna).lower()
        match = next((v for k, v in COLUMNAS.items() if k in texto), None)
        if match is None or match[0] in DESCARTAR:
            continue
        tipo, titulo = match
        for ini, fin in episodios(anios, list(df[columna])):
            filas.append({
                "id": f"rr_{tipo.replace(' ', '_')}_{ini}",
                "fecha_inicio": f"{ini}-01-01",
                "fecha_fin": f"{fin}-12-31",
                "ambito": "económico",
                "tipo": tipo,
                "titulo": f"{titulo} ({ini}{'–' + str(fin) if fin != ini else ''})",
                "descripcion": f"Episodio marcado por Reinhart & Rogoff en la columna «{columna}».",
                "magnitud": fin - ini + 1,
                "fuente": FUENTE,
                "verificado": "no",
                "nota": "Resolución ANUAL: el año se abre el 1 de enero y se cierra el 31 "
                        "de diciembre. Para fechas exactas hay que ir a la fuente primaria.",
            })

    filas.sort(key=lambda f: (f["fecha_inicio"], f["tipo"]))
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    with SALIDA.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CAMPOS)
        w.writeheader()
        w.writerows(filas)

    print(f"\n{len(filas)} episodios -> {SALIDA.relative_to(RAIZ)}")
    por_tipo: dict[str, int] = {}
    for f in filas:
        por_tipo[f["tipo"]] = por_tipo.get(f["tipo"], 0) + 1
    for tipo, n in sorted(por_tipo.items(), key=lambda x: -x[1]):
        print(f"  {n:>3}  {tipo}")
    print(f"\nconsultado: {date.today().isoformat()}")


if __name__ == "__main__":
    main()
