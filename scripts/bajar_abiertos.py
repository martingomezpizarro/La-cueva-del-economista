"""Baja al corpus los textos de acceso abierto listados en el manifiesto.

Uso (desde la raiz del repo, con tu Python de Windows que SI tiene internet):

    python scripts/bajar_abiertos.py                 # baja lo que falte
    python scripts/bajar_abiertos.py --forzar        # re-baja todo
    python scripts/bajar_abiertos.py --listar        # solo muestra el plan

Solo biblioteca estandar: no necesita requests ni el venv.

Despues de bajar, reindexar segun knowledge-base/GUIA_CARGA.md:
    python rag/ingest.py knowledge-base/corpus
"""

from __future__ import annotations

import argparse
import sys
import urllib.error
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
MANIFIESTO = RAIZ / "knowledge-base" / "fuentes_abiertas.tsv"
CORPUS = RAIZ / "knowledge-base" / "corpus"

# Varios editores rechazan el user-agent por defecto de urllib.
CABECERAS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"
    ),
    "Accept": "application/pdf,*/*",
}

MINIMO_BYTES = 20_000  # por debajo de esto casi seguro es una pagina de error


def leer_manifiesto(ruta: Path) -> list[tuple[str, str, str]]:
    if not ruta.exists():
        sys.exit(f"No encuentro el manifiesto: {ruta}")
    filas = []
    for nro, linea in enumerate(ruta.read_text(encoding="utf-8").splitlines(), 1):
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue
        partes = linea.split("\t")
        if len(partes) != 3:
            print(f"  ! linea {nro} mal formada (esperaba 3 columnas con TAB), la salteo")
            continue
        filas.append((partes[0].strip(), partes[1].strip(), partes[2].strip()))
    return filas


def bajar(url: str, destino: Path) -> tuple[bool, str]:
    pedido = urllib.request.Request(url, headers=CABECERAS)
    try:
        with urllib.request.urlopen(pedido, timeout=120) as resp:
            datos = resp.read()
            tipo = resp.headers.get("Content-Type", "")
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}"
    except urllib.error.URLError as e:
        return False, f"red: {e.reason}"
    except Exception as e:  # noqa: BLE001
        return False, f"{type(e).__name__}: {e}"

    if len(datos) < MINIMO_BYTES:
        return False, f"solo {len(datos)} bytes (probable pagina de error)"
    if destino.suffix.lower() == ".pdf" and not datos.startswith(b"%PDF"):
        return False, f"no es un PDF (Content-Type: {tipo or 'desconocido'})"

    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(datos)
    return True, f"{len(datos) / 1_048_576:.1f} MB"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--forzar", action="store_true", help="re-baja archivos que ya existen")
    ap.add_argument("--listar", action="store_true", help="muestra el plan sin descargar")
    args = ap.parse_args()

    filas = leer_manifiesto(MANIFIESTO)
    print(f"{len(filas)} fuentes en el manifiesto -> {CORPUS}\n")

    bajados, salteados, fallados = 0, 0, []
    for carpeta, nombre, url in filas:
        destino = CORPUS / carpeta / nombre
        etiqueta = f"{carpeta}/{nombre}"

        if args.listar:
            estado = "ya esta" if destino.exists() else "falta"
            print(f"  [{estado:>7}] {etiqueta}\n            {url}")
            continue

        if destino.exists() and not args.forzar:
            print(f"  [ ya esta] {etiqueta}")
            salteados += 1
            continue

        print(f"  [bajando ] {etiqueta} ...", end=" ", flush=True)
        ok, detalle = bajar(url, destino)
        if ok:
            print(f"OK ({detalle})")
            bajados += 1
        else:
            print(f"FALLO ({detalle})")
            fallados.append((etiqueta, url, detalle))

    if args.listar:
        return 0

    print(f"\nResumen: {bajados} bajados, {salteados} ya estaban, {len(fallados)} fallaron")
    if fallados:
        print("\nFallaron (bajalos a mano desde el navegador y ponelos en su carpeta):")
        for etiqueta, url, detalle in fallados:
            print(f"  - {etiqueta}\n      {url}\n      motivo: {detalle}")
    if bajados:
        print("\nAhora reindexa:  python rag/ingest.py knowledge-base/corpus")
    return 1 if fallados else 0


if __name__ == "__main__":
    raise SystemExit(main())
