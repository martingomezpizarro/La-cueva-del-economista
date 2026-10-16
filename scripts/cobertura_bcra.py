"""cobertura_bcra.py — qué del catálogo puede completar la API del BCRA.

Cruza cada serie del catálogo contra el índice de variables del BCRA
(`cueva/fuentes/bcra_variables.json`) y responde tres preguntas:

  1. ¿Qué series YA declaradas del BCRA se pueden ESTIRAR? Compara el rango real que
     tiene el archivo en disco contra el rango que publica la API, y dice cuántos años
     se ganan hacia atrás y cuántos días hacia adelante.
  2. ¿Qué series del catálogo vienen del BCRA pero NO declaran `id_externo`? Sin él no
     se pueden actualizar solas; hay que emparejarlas a mano.
  3. ¿Qué variables de la API NO están en el catálogo y convendría sumar?

No baja nada: solo compara metadatos. La descarga es `scripts/actualizar_bcra.py`.

Uso:
    python scripts/cobertura_bcra.py
    python scripts/cobertura_bcra.py --csv docs/cobertura_bcra.csv
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import date
from pathlib import Path

from auditar_series import RAIZ, auditar  # type: ignore

SNAPSHOT = RAIZ / "cueva" / "fuentes" / "bcra_variables.json"


def _f(texto: str) -> date | None:
    try:
        return date.fromisoformat((texto or "")[:10])
    except ValueError:
        return None


def _anios(dias: int) -> str:
    return f"{dias / 365.25:.1f} años"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", default="", help="Escribir el detalle a un CSV.")
    args = ap.parse_args()

    if not SNAPSHOT.exists():
        raise SystemExit("Falta cueva/fuentes/bcra_variables.json "
                         "(correr scripts/actualizar_bcra.py --indice)")
    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    api = {v["id"]: v for v in snap["variables"]}
    print(f"Índice del BCRA: {snap['total']} variables conocidas de "
          f"{snap.get('total_en_api', '?')} publicadas"
          + ("  [PARCIAL]" if snap.get("parcial") else ""))

    filas = auditar()
    usados: set[int] = set()
    estirables, sin_id, ok = [], [], []

    for f in filas:
        if f["fuente"] != "bcra":
            continue
        ext = str(f["id_externo"] or "")
        if not ext.isdigit():
            sin_id.append(f)
            continue
        v = api.get(int(ext))
        usados.add(int(ext))
        if v is None:
            continue
        cat_ini, cat_fin = _f(f["origen"]), _f(f["final"])
        api_ini, api_fin = _f(v["desde"]), _f(v["hasta"])
        if not api_ini or not api_fin:
            continue
        atras = (cat_ini - api_ini).days if cat_ini else None
        adelante = (api_fin - cat_fin).days if cat_fin else None
        registro = {
            "id": f["id"], "serie": f["serie"], "idVariable": ext,
            "cat_desde": f["origen"], "cat_hasta": f["final"],
            "api_desde": v["desde"], "api_hasta": v["hasta"],
            "gana_atras_dias": atras if atras and atras > 0 else 0,
            "gana_adelante_dias": adelante if adelante and adelante > 0 else 0,
            "descripcion_api": v["descripcion"],
        }
        if cat_ini is None:
            registro["nota"] = "sin datos en disco: se baja entera"
            estirables.append(registro)
        elif (atras and atras > 30) or (adelante and adelante > 30):
            estirables.append(registro)
        else:
            ok.append(registro)

    print(f"\n{'='*78}\n1 · SERIES QUE SE PUEDEN COMPLETAR ({len(estirables)})\n{'='*78}")
    for r in sorted(estirables, key=lambda x: -(x["gana_atras_dias"] + x["gana_adelante_dias"])):
        if r.get("nota"):
            print(f"  {r['id']:<18} id {r['idVariable']:<5} {r['nota']}")
            print(f"  {'':<18} API: {r['api_desde']} → {r['api_hasta']}")
            continue
        print(f"  {r['id']:<18} id {r['idVariable']:<5} {r['serie'][:40]}")
        print(f"  {'':<18} hoy: {r['cat_desde']} → {r['cat_hasta']}")
        print(f"  {'':<18} API: {r['api_desde']} → {r['api_hasta']}"
              + (f"   ↞ {_anios(r['gana_atras_dias'])} más de historia" if r["gana_atras_dias"] else "")
              + (f"   ↠ {r['gana_adelante_dias']} días más al día" if r["gana_adelante_dias"] else ""))

    if ok:
        print(f"\n{len(ok)} ya están al día y completas: "
              + ", ".join(r["id"] for r in ok))

    print(f"\n{'='*78}\n2 · DEL BCRA PERO SIN idVariable ({len(sin_id)})\n{'='*78}")
    print("  No se pueden actualizar solas hasta emparejarlas con una variable de la API.")
    agrupadas: dict[str, list[str]] = {}
    for f in sin_id:
        agrupadas.setdefault(f["base"] or "(sin archivo)", []).append(f["id"])
    for base, ids in sorted(agrupadas.items()):
        print(f"  {base:<34} {len(ids):>3} series   {', '.join(ids[:4])}"
              + (" …" if len(ids) > 4 else ""))

    print(f"\n{'='*78}\n3 · EN LA API Y NO EN EL CATÁLOGO\n{'='*78}")
    faltan = [v for i, v in api.items() if i not in usados]
    por_cat: dict[str, list] = {}
    for v in faltan:
        por_cat.setdefault(v["categoria"], []).append(v)
    for cat, lista in sorted(por_cat.items(), key=lambda x: -len(x[1])):
        print(f"\n  {cat} ({len(lista)})")
        for v in sorted(lista, key=lambda x: x["desde"]):
            print(f"    id {v['id']:<5} {v['periodicidad']}  {v['desde']} → {v['hasta']}  "
                  f"{v['descripcion'][:56]}")

    if args.csv:
        destino = Path(args.csv)
        campos = ["id", "serie", "idVariable", "cat_desde", "cat_hasta", "api_desde",
                  "api_hasta", "gana_atras_dias", "gana_adelante_dias", "descripcion_api"]
        with destino.open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=campos, extrasaction="ignore")
            w.writeheader()
            w.writerows(estirables + ok)
        print(f"\n-> {destino}")


if __name__ == "__main__":
    main()
