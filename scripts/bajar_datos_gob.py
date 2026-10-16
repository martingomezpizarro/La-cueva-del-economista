"""bajar_datos_gob.py — trae de datos.gob.ar las series del catálogo que todavía no están en disco.

Cubre lo que el Trabajo Final bajaba con `scripts/download/download_datos_gob.py`: los cuadros del
INDEC y de Economía que el Estado publica en el portal nacional de datos abiertos (saldo comercial
por países, balance de pagos, términos del intercambio, IPC, deuda externa…). Hoy son ~160 entradas
del catálogo que apuntan a archivos que no están en `data/series/`.

Tres trabajos, separables:

1. `--descubrir`  Recorre `catalogo.json` (bajando por `children`), junta los archivos que faltan y
   cuya fuente es un organismo publicado en datos.gob.ar, y busca en el portal (CKAN) qué recurso
   CSV corresponde a cada uno. Escribe los candidatos en `cueva/fuentes/datos_gob_mapa.json`.
   NO baja nada y NO confirma nada: elegir el recurso correcto es una decisión con criterio.

2. `--bajar`      Baja los recursos del mapa que tengan `"confirmado": true`, verifica que el CSV
   traiga la columna de fecha y TODAS las columnas que el catálogo le pide, y recién entonces lo
   guarda en la carpeta de la familia dentro de `data/series/`. Si falta una columna, no guarda y
   lo informa. No pisa un archivo existente salvo con `--pisar`.

3. `--ids`        Baja series sueltas de la API de Series de Tiempo por id
   (ej. `--ids 82.2_ITI_2004_T_27 --archivo ti_trimestral.csv`) a un CSV ancho
   `indice_tiempo` + una columna por id. Sirve para series nuevas que todavía no están en el
   catálogo.

Ejemplos:
    python scripts/bajar_datos_gob.py --descubrir
    python scripts/bajar_datos_gob.py --descubrir --familia "Sector Externo"
    python scripts/bajar_datos_gob.py --bajar
    python scripts/bajar_datos_gob.py --ids 82.2_ITI_2004_T_27 --archivo ti_trimestral.csv

Requiere red. El portal es público y no pide clave. Solo usa la biblioteca estándar.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CATALOGO = RAIZ / "cueva" / "datos" / "catalogo.json"
MAPA = RAIZ / "cueva" / "fuentes" / "datos_gob_mapa.json"
SERIES = RAIZ / "data" / "series"

CKAN = "https://datos.gob.ar/api/3/action"
API_SERIES = "https://apis.datos.gob.ar/series/api/series/"
# Organismos del catálogo cuyos cuadros están en el portal nacional.
FUENTES_PORTAL = {"indec", "mecon"}
PAUSA_S = 1.0  # el portal es público: no lo martillemos
AGENTE = "LaCuevaDelEconomista/1.0 (+datos abiertos; uso académico)"


# --------------------------------------------------------------------- red
def _get(url: str, intentos: int = 3) -> bytes:
    ultimo: Exception | None = None
    for i in range(intentos):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": AGENTE})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001 — se reintenta y se informa
            ultimo = e
            time.sleep(PAUSA_S * (i + 2))
    raise RuntimeError(f"no pude bajar {url}: {ultimo}")


def _ckan(accion: str, **params) -> dict:
    url = f"{CKAN}/{accion}?{urllib.parse.urlencode(params)}"
    datos = json.loads(_get(url).decode("utf-8"))
    time.sleep(PAUSA_S)
    if not datos.get("success"):
        raise RuntimeError(f"CKAN respondió error en {accion}: {datos.get('error')}")
    return datos["result"]


# --------------------------------------------------------------- catálogo
def _sin_tildes(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", _sin_tildes(s).lower()).strip("_")


def archivos_en_disco() -> dict[str, Path]:
    disco: dict[str, Path] = {}
    for raiz, _dirs, archivos in os.walk(SERIES):
        for a in archivos:
            disco.setdefault(a, Path(raiz) / a)
    return disco


def faltantes(familia: str | None = None) -> dict[str, dict]:
    """Archivo faltante → {familia, fuente, dateCol, columnas, ids, url_humana}.

    Recorre TODO el catálogo, incluidos los `children` anidados (hasta 5 niveles).
    """
    cat = json.loads(CATALOGO.read_text(encoding="utf-8"))
    disco = archivos_en_disco()
    out: dict[str, dict] = {}

    def caminar(nodo, fam: str) -> None:
        if isinstance(nodo, dict):
            if "file" in nodo:
                proc = nodo.get("proc") or {}
                fuente = (proc.get("fuente") or "").lower()
                arch = nodo["file"]
                if fuente in FUENTES_PORTAL and arch not in disco and arch.lower().endswith(".csv"):
                    e = out.setdefault(arch, {"familia": fam, "fuente": fuente, "dateCol": nodo.get("dateCol"),
                                              "columnas": [], "ids": [], "url_humana": proc.get("url_humana") or proc.get("endpoint") or ""})
                    if nodo.get("valCol") and nodo["valCol"] not in e["columnas"]:
                        e["columnas"].append(nodo["valCol"])
                    if nodo.get("id"):
                        e["ids"].append(nodo["id"])
            for k, v in nodo.items():
                if k != "proc" and isinstance(v, (dict, list)):
                    caminar(v, fam)
        elif isinstance(nodo, list):
            for x in nodo:
                caminar(x, fam)

    for f in cat["familias"]:
        if familia and f["grp"] != familia:
            continue
        caminar(f, f["grp"])
    return out


def carpeta_de(familia: str) -> Path:
    """La carpeta de la familia en data/series/ (respeta la numeración que ya exista: `1.Actividad…`)."""
    for d in SERIES.iterdir() if SERIES.exists() else []:
        if d.is_dir() and re.sub(r"^\d+\.\s*", "", d.name) == familia:
            return d
    return SERIES / familia


# ------------------------------------------------------------- descubrir
def _consulta_desde(archivo: str) -> str:
    """'saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv'
    → 'saldo comercial paises regiones fob cif valores'. Saca fragmentos cortos y repetidos."""
    palabras = [p for p in Path(archivo).stem.split("_") if len(p) > 2]
    vistas: list[str] = []
    for p in palabras:
        if p not in vistas:
            vistas.append(p)
    return " ".join(vistas[:8])


def _puntaje(archivo: str, recurso: dict, dataset: dict) -> float:
    a = set(Path(archivo).stem.split("_"))
    r = set(_slug(f"{dataset.get('title', '')} {recurso.get('name', '')}").split("_"))
    # los nombres del TF vienen truncados ('mensua', 'trimes'): cuenta como coincidencia un prefijo de 5+ letras
    def coincide(x: str) -> bool:
        return any(x == y or (min(len(x), len(y)) >= 5 and (x.startswith(y) or y.startswith(x))) for y in r)
    comunes = {x for x in a if len(x) > 2 and coincide(x)}
    # la frecuencia pesa doble: es lo que distingue mensual/trimestral/anual del mismo cuadro
    extra = sum(1 for x in comunes if x.startswith(("mensua", "trimes", "anual", "semest")))
    return round((len(comunes) + extra) / max(1, len({x for x in a if len(x) > 2})), 3)


def descubrir(familia: str | None) -> None:
    falta = faltantes(familia)
    mapa = json.loads(MAPA.read_text(encoding="utf-8")) if MAPA.exists() else {}
    print(f"\n{len(falta)} archivos faltantes con fuente en datos.gob.ar")
    for i, (arch, info) in enumerate(sorted(falta.items()), 1):
        previo = mapa.get(arch, {})
        if previo.get("confirmado"):
            print(f"  [{i}] {arch}: ya confirmado, no lo toco")
            continue
        q = _consulta_desde(arch)
        if len(q.split()) < 2:
            # 'ti_mensual.csv', 'ICC.csv': nombres armados a mano en el Trabajo Final, no títulos del portal
            print(f"  [{i}] {arch}: el nombre no alcanza para buscar; probablemente es un archivo armado a mano")
            mapa[arch] = {**previo, "familia": info["familia"], "fuente": info["fuente"], "dateCol": info["dateCol"],
                          "columnas": info["columnas"], "series_catalogo": len(info["ids"]), "candidatos": [],
                          "elegido": previo.get("elegido"), "confirmado": False}
            continue
        print(f"  [{i}] {arch}\n      busco: «{q}»")
        candidatos = []
        try:
            res = _ckan("package_search", q=q, rows=5)
            for ds in res.get("results", []):
                for rec in ds.get("resources", []):
                    if (rec.get("format") or "").upper() != "CSV":
                        continue
                    candidatos.append({
                        "dataset": ds.get("name"), "dataset_titulo": ds.get("title"),
                        "recurso_id": rec.get("id"), "recurso": rec.get("name"),
                        "url": rec.get("url") or rec.get("download_url"),
                        "puntaje": _puntaje(arch, rec, ds),
                    })
        except RuntimeError as e:
            print(f"      ⚠ {e}")
        candidatos.sort(key=lambda c: -c["puntaje"])
        mapa[arch] = {
            **{k: v for k, v in previo.items() if k == "nota"},
            "familia": info["familia"], "fuente": info["fuente"], "dateCol": info["dateCol"],
            "columnas": info["columnas"], "series_catalogo": len(info["ids"]),
            "candidatos": candidatos[:5],
            "elegido": candidatos[0]["url"] if candidatos else None,
            "confirmado": False,
        }
        if candidatos:
            c = candidatos[0]
            print(f"      → {c['dataset_titulo']} · {c['recurso']}  (puntaje {c['puntaje']})")
        else:
            print("      → sin candidatos: hay que buscarlo a mano")
    MAPA.parent.mkdir(parents=True, exist_ok=True)
    MAPA.write_text(json.dumps(mapa, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\n  -> {MAPA.relative_to(RAIZ)}")
    print("  Revisá cada `elegido`, cambialo si hace falta y poné `\"confirmado\": true`. Después: --bajar")


# ------------------------------------------------------------------ bajar
def _encabezado(contenido: bytes) -> list[str]:
    texto = contenido.decode("utf-8-sig", errors="replace")
    return next(csv.reader(io.StringIO(texto)), [])


def bajar(pisar: bool) -> None:
    if not MAPA.exists():
        sys.exit("No hay mapa. Corré primero --descubrir.")
    mapa = json.loads(MAPA.read_text(encoding="utf-8"))
    confirmados = {a: m for a, m in mapa.items() if m.get("confirmado") and m.get("elegido")}
    # Las columnas se leen del catálogo en el momento: si se corrigió un valCol, manda el catálogo, no el mapa.
    vigentes = faltantes()
    for a, m in confirmados.items():
        if a in vigentes:
            m["columnas"] = vigentes[a]["columnas"]
            m["dateCol"] = vigentes[a]["dateCol"]
    print(f"\n{len(confirmados)} archivos confirmados (de {len(mapa)} en el mapa)")
    ok = mal = 0
    for arch, m in sorted(confirmados.items()):
        destino = carpeta_de(m["familia"]) / arch
        if destino.exists() and not pisar:
            print(f"  = {arch}: ya existe (usá --pisar para reemplazarlo)")
            continue
        try:
            contenido = _get(m["elegido"])
            time.sleep(PAUSA_S)
        except RuntimeError as e:
            print(f"  ✗ {arch}: {e}")
            mal += 1
            continue
        cols = _encabezado(contenido)
        pedidas = [c for c in [m.get("dateCol"), *m.get("columnas", [])] if c]
        faltan = [c for c in pedidas if c not in cols]
        if faltan:
            print(f"  ✗ {arch}: el CSV no trae {len(faltan)} columnas que pide el catálogo "
                  f"(ej. {', '.join(faltan[:4])}). NO se guarda: revisar el recurso elegido.")
            m["ultimo_error"] = {"faltan": faltan, "trae": cols[:60]}
            mal += 1
            continue
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(contenido)
        m.pop("ultimo_error", None)
        m["bajado"] = time.strftime("%Y-%m-%d")
        print(f"  ✓ {arch} → {destino.relative_to(RAIZ)}  ({len(pedidas) - 1} columnas verificadas)")
        ok += 1
    MAPA.write_text(json.dumps(mapa, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\n  {ok} guardados · {mal} con problemas")


# -------------------------------------------------------------------- ids
def bajar_ids(ids: list[str], archivo: str, carpeta: str | None) -> None:
    params = {"ids": ",".join(ids), "format": "csv", "limit": 5000, "header": "ids"}
    contenido = _get(f"{API_SERIES}?{urllib.parse.urlencode(params)}")
    cols = _encabezado(contenido)
    faltan = [i for i in ids if i not in cols]
    if faltan:
        sys.exit(f"La API no devolvió: {', '.join(faltan)}")
    destino = (SERIES / carpeta if carpeta else SERIES / "datos_gob") / archivo
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(contenido)
    filas = contenido.decode("utf-8-sig").count("\n") - 1
    print(f"  ✓ {len(ids)} series, {filas} filas → {destino.relative_to(RAIZ)}")


# -------------------------------------------------------------------- CLI
def main() -> None:
    # La consola de Windows (cp1252) no imprime «→» ni «✓»: forzar UTF-8.
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--descubrir", action="store_true", help="Buscar en el portal el recurso de cada archivo faltante y escribir el mapa.")
    ap.add_argument("--familia", help="Limitar --descubrir a una familia del catálogo (ej. \"Sector Externo\").")
    ap.add_argument("--bajar", action="store_true", help="Bajar los recursos confirmados del mapa.")
    ap.add_argument("--pisar", action="store_true", help="Con --bajar: reemplazar archivos existentes.")
    ap.add_argument("--ids", help="Ids de la API de Series de Tiempo, separados por coma.")
    ap.add_argument("--archivo", help="Con --ids: nombre del CSV de salida.")
    ap.add_argument("--carpeta", help="Con --ids: subcarpeta de data/series/ (por defecto datos_gob/).")
    args = ap.parse_args()

    if args.ids:
        if not args.archivo:
            sys.exit("--ids necesita --archivo")
        bajar_ids([i.strip() for i in args.ids.split(",") if i.strip()], args.archivo, args.carpeta)
    elif args.descubrir:
        descubrir(args.familia)
    elif args.bajar:
        bajar(args.pisar)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
