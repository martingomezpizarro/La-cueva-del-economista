"""actualizar_bcra.py — trae del BCRA el índice de variables y las series históricas.

Dos trabajos, separables:

1. `--indice`  Baja el índice completo de la API v4.0 (1610 variables al 2026-08-27) y
   su metodología oficial, y los guarda en `cueva/fuentes/bcra_variables.json`. Ese
   archivo es el diccionario que usamos para documentar cada serie: qué es, en qué
   unidad y moneda, con qué periodicidad y desde cuándo la publica el BCRA, con el texto
   del propio Banco.

2. `--series`  Baja las series históricas a `data/series/bcra/` (un CSV por variable,
   columnas `fecha,valor`) y escribe `data/series/bcra/_index.csv` con el resumen.
   Por defecto baja las variables que el catálogo declara con `proc.fuente == "bcra"`;
   con `--todas` baja las 1610 (son muchas: conviene filtrar con `--categoria`).

Sin argumentos hace las dos cosas.

Ejemplos:
    python scripts/actualizar_bcra.py --categorias
    python scripts/actualizar_bcra.py --indice
    python scripts/actualizar_bcra.py --series --categoria "Agregados monetarios y sus componentes"
    python scripts/actualizar_bcra.py --series --ids 1605,1606,1617 --sin-verificar-tls

Requiere red. La API es pública y no pide clave.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date
from pathlib import Path

from cueva.fuentes.bcra import PRIMERA_FECHA, ClienteBCRA, ErrorBCRA

RAIZ = Path(__file__).resolve().parent.parent
SNAPSHOT = RAIZ / "cueva" / "fuentes" / "bcra_variables.json"
CATALOGO = RAIZ / "cueva" / "datos" / "catalogo.json"
DESTINO = RAIZ / "data" / "series" / "bcra"


# --------------------------------------------------------------------- índice

def bajar_indice(cli: ClienteBCRA, con_metodologia: bool = True) -> dict:
    variables = cli.variables()
    print(f"  índice: {len(variables)} variables")
    textos: dict[int, str] = {}
    if con_metodologia:
        textos = cli.metodologia()
        print(f"  metodología: {len(textos)} definiciones")
    snapshot = {
        "fuente": "bcra",
        "servicio": "Estadísticas Monetarias v4.0",
        "endpoint": "https://api.bcra.gob.ar/estadisticas/v4.0/Monetarias",
        "consultado": date.today().isoformat(),
        "total": len(variables),
        "variables": [
            {
                "id": v.id,
                "descripcion": v.descripcion,
                "categoria": v.categoria,
                "tipo_serie": v.tipo_serie,
                "periodicidad": v.periodicidad,
                "unidad": v.unidad,
                "moneda": v.moneda,
                "desde": v.desde,
                "hasta": v.hasta,
                "slug": v.slug,
                "metodologia": textos.get(v.id, ""),
            }
            for v in sorted(variables, key=lambda x: x.id)
        ],
    }
    SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    print(f"  -> {SNAPSHOT.relative_to(RAIZ)}")
    return snapshot


def leer_snapshot() -> dict:
    if not SNAPSHOT.exists():
        raise SystemExit(
            "Falta cueva/fuentes/bcra_variables.json. Corré primero:\n"
            "    python scripts/actualizar_bcra.py --indice"
        )
    return json.loads(SNAPSHOT.read_text(encoding="utf-8"))


# --------------------------------------------------------------------- series

def ids_del_catalogo() -> list[int]:
    """idVariable que el catálogo declara como propios del BCRA (proc.fuente == 'bcra')."""
    catalogo = json.loads(CATALOGO.read_text(encoding="utf-8"))
    ids: list[int] = []
    for fam in catalogo["familias"]:
        bloques = [s["items"] for s in fam.get("subs", [])] + [fam.get("items", [])]
        for items in bloques:
            for item in items:
                proc = item.get("proc") or {}
                if proc.get("fuente") == "bcra" and str(proc.get("id_externo", "")).isdigit():
                    ids.append(int(proc["id_externo"]))
    return sorted(set(ids))


def bajar_series(cli: ClienteBCRA, ids: list[int], catalogo_bcra: dict) -> None:
    por_id = {v["id"]: v for v in catalogo_bcra["variables"]}
    DESTINO.mkdir(parents=True, exist_ok=True)
    resumen: list[dict] = []
    for i, id_var in enumerate(ids, 1):
        meta = por_id.get(id_var, {})
        etiqueta = meta.get("descripcion", f"variable {id_var}")
        print(f"  [{i}/{len(ids)}] {id_var:>4} · {etiqueta[:64]}")
        try:
            filas = cli.serie(id_var, desde=PRIMERA_FECHA)
        except ErrorBCRA as exc:
            print(f"        ! {exc}")
            continue
        if not filas:
            print("        (vacía)")
            continue
        slug = meta.get("slug") or f"{id_var:03d}_variable"
        ruta = DESTINO / f"{slug}.csv"
        with ruta.open("w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["fecha", "valor"])
            w.writerows(filas)
        resumen.append({
            "id": id_var,
            "archivo": ruta.name,
            "descripcion": etiqueta,
            "unidad": meta.get("unidad", ""),
            "moneda": meta.get("moneda", ""),
            "periodicidad": meta.get("periodicidad", ""),
            "categoria": meta.get("categoria", ""),
            "n_obs": len(filas),
            "desde": filas[0][0],
            "hasta": filas[-1][0],
            "consultado": date.today().isoformat(),
        })
        print(f"        {len(filas)} obs · {filas[0][0]} → {filas[-1][0]}")

    if resumen:
        indice = DESTINO / "_index.csv"
        with indice.open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(resumen[0]))
            w.writeheader()
            w.writerows(resumen)
        print(f"\n  {len(resumen)} series -> {DESTINO.relative_to(RAIZ)}")


# ----------------------------------------------------------------------- CLI

def main() -> None:
    # La consola de Windows (cp1252) no imprime «→» ni «·»: forzar UTF-8.
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--categorias", action="store_true", help="Mostrar cuántas variables hay por categoría (para detectar bloques nuevos del BCRA).")
    ap.add_argument("--indice", action="store_true", help="Actualizar el índice de variables y su metodología.")
    ap.add_argument("--series", action="store_true", help="Bajar las series históricas a data/series/bcra/.")
    ap.add_argument("--todas", action="store_true", help="Con --series: bajar TODAS las variables del índice (1610), no solo las del catálogo.")
    ap.add_argument("--ids", default="", help="Con --series: lista de idVariable separados por coma.")
    ap.add_argument("--categoria", default="", help="Con --series: bajar todas las variables de una categoría del BCRA.")
    ap.add_argument("--sin-metodologia", action="store_true", help="Con --indice: saltear el corpus metodológico (más rápido).")
    ap.add_argument("--sin-verificar-tls", action="store_true", help="Desactivar la validación del certificado del BCRA.")
    args = ap.parse_args()

    if not args.indice and not args.series and not args.categorias:
        args.indice = args.series = True

    cli = ClienteBCRA(verificar_tls=not args.sin_verificar_tls)

    if args.categorias:
        print("Variables por categoría")
        for nombre, n in cli.categorias().items():
            print(f"  {n:>5}  {nombre}")
        if not args.indice and not args.series:
            return

    snapshot: dict | None = None
    if args.indice:
        print("Índice de variables del BCRA")
        snapshot = bajar_indice(cli, con_metodologia=not args.sin_metodologia)

    if args.series:
        snapshot = snapshot or leer_snapshot()
        if args.ids:
            ids = [int(x) for x in args.ids.split(",") if x.strip()]
        elif args.categoria:
            ids = [v["id"] for v in snapshot["variables"] if v.get("categoria") == args.categoria]
            if not ids:
                raise SystemExit(
                    f"Ninguna variable del índice está en la categoría '{args.categoria}'.\n"
                    "Mirá las disponibles con: python scripts/actualizar_bcra.py --categorias"
                )
        elif args.todas:
            ids = [v["id"] for v in snapshot["variables"]]
        else:
            ids = ids_del_catalogo()
            if not ids:
                raise SystemExit(
                    "Ninguna serie del catálogo declara proc.fuente == 'bcra' con id_externo.\n"
                    "Usá --todas o --ids para bajar de todos modos."
                )
        print(f"\nSeries históricas ({len(ids)} variables)")
        bajar_series(cli, ids, snapshot)


if __name__ == "__main__":
    main()
