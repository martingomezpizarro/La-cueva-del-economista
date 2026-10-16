"""normalizar_ids_actividad.py — el id de cada serie dice de qué archivo y columna sale.

Decisión de Martín (2026-08-29): `data/series/` es la fuente de verdad, así que el catálogo
tiene que poder encontrar cada serie ahí. El id pasa a ser **`<prefijo del archivo><columna>`**,
con un prefijo fijo por archivo. Antes era una abreviatura heredada (`sec_c_eega`, `emae_inmob`)
que no se podía relacionar con ningún archivo.

Solo toca la familia Actividad y Cuentas Nacionales, que es la única con los datos en la carpeta.
Las series sin archivo ahí conservan su id: no hay columna de la que derivarlo.

Se verificó que los cuatro proyectos guardados de `data/proyectos/` no referencian ningún id de
esta familia, así que el renombre no rompe nada. El script lo vuelve a chequear antes de aplicar.

    python scripts/normalizar_ids_actividad.py            # simula
    python scripts/normalizar_ids_actividad.py --aplicar
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CATALOGO = RAIZ / "cueva" / "datos" / "catalogo.json"
DATOS = RAIZ / "data" / "series" / "1.Actividad y Cuentas Nacionales"
PROYECTOS = RAIZ / "data" / "proyectos"
MAPA = RAIZ / "docs" / "ids_actividad.csv"
FAMILIA = "Actividad y Cuentas Nacionales"

# Un prefijo por archivo. Los dos vacíos son a propósito: las columnas de esos archivos ya son
# únicas y descriptivas (`emae_original`), y anteponerles `emae_` daría `emae_emae_original`.
PREFIJO = {
    "cn_vab_rama_constante.csv": "vab_c_", "cn_vab_rama_corriente.csv": "vab_n_",
    "cn_vab_rama_ivf.csv": "vab_q_", "cn_vab_rama_ipi.csv": "vab_p_",
    "cn_vbp_rama_constante.csv": "vbp_c_", "cn_vbp_rama_corriente.csv": "vbp_n_",
    "cn_pbi_categoria_constante.csv": "sec_c_", "cn_pbi_categoria_corriente.csv": "sec_n_",
    "cn_pbi_categoria_ipi.csv": "sec_p_",
    "cn_oferta_demanda_constante.csv": "od_c_", "cn_oferta_demanda_corriente.csv": "od_n_",
    "cn_oferta_demanda_ipi.csv": "od_p_", "cn_oferta_demanda_desest.csv": "od_d_",
    "cn_fbkf_constante.csv": "fbkf_c_", "cn_fbkf_corriente.csv": "fbkf_n_",
    "cn_fbkf_ipi.csv": "fbkf_p_",
    "uci_bloques.csv": "uci_",
    "emae_nivel_general_mensual.csv": "",
    "emae_sectorial_mensual.csv": "emae_",
}


def _columnas() -> dict[str, list[str]]:
    out = {}
    for f in sorted(DATOS.glob("*.csv")):
        with f.open(encoding="utf-8") as fh:
            out[f.name] = next(csv.reader(fh))
    return out


def _items(cat: dict, familia: str | None = None):
    for fam in cat["familias"]:
        if familia and fam["grp"] != familia:
            continue
        for b in fam.get("subs", []):
            def baja(items):
                for it in items:
                    yield it
                    yield from baja(it.get("children") or [])
            for it in baja(b["items"]):
                yield fam["grp"], b, it


def plan() -> tuple[list[dict], list[str]]:
    cat = json.loads(CATALOGO.read_text(encoding="utf-8"))
    cols = _columnas()
    ocupados = {it["id"] for _, _, it in _items(cat)}
    filas, avisos = [], []
    for _, b, it in _items(cat, FAMILIA):
        # La primera fuente que exista en la carpeta manda: es la que la plataforma va a resolver.
        fuente = next((fu for fu in (it.get("sources") or [it])
                       if fu.get("file") in cols and fu.get("valCol") in cols[fu["file"]]), None)
        if fuente is None:
            avisos.append(it["id"])
            continue
        arch, col = fuente["file"], fuente["valCol"]
        if arch not in PREFIJO:
            avisos.append(f"{it['id']} (sin prefijo para {arch})")
            continue
        filas.append({"id_viejo": it["id"], "id_nuevo": PREFIJO[arch] + col,
                      "archivo": arch, "columna": col,
                      "grupo": b["grupo"], "subgrupo": b["subgrupo"], "serie": it.get("label", "")})
    # Ningún id nuevo puede repetirse ni pisar uno de otra familia.
    nuevos = [f["id_nuevo"] for f in filas]
    dup = sorted({i for i in nuevos if nuevos.count(i) > 1})
    viejos = {f["id_viejo"] for f in filas}
    choca = sorted(set(nuevos) & (ocupados - viejos))
    if dup or choca:
        raise SystemExit(f"ids repetidos: {dup[:10]} · chocan con otra familia: {choca[:10]}")
    return filas, avisos


def _proyectos_afectados(cambios: dict[str, str]) -> dict[str, list[str]]:
    afectados = {}
    for p in sorted(PROYECTOS.glob("*.json")) if PROYECTOS.exists() else []:
        txt = p.read_text(encoding="utf-8")
        hits = [v for v in cambios if re.search(r'"' + re.escape(v) + r'"', txt)]
        if hits:
            afectados[p.name] = hits
    return afectados


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()

    filas, avisos = plan()
    cambios = {f["id_viejo"]: f["id_nuevo"] for f in filas if f["id_viejo"] != f["id_nuevo"]}
    print(f"{len(filas)} series de «{FAMILIA}» con archivo y columna en la carpeta")
    print(f"  {len(filas) - len(cambios)} ya tienen el id correcto · {len(cambios)} se renombran")
    if avisos:
        print(f"  {len(avisos)} sin archivo en la carpeta, conservan su id: {avisos[:8]}")

    afectados = _proyectos_afectados(cambios)
    if afectados:
        raise SystemExit(f"hay proyectos guardados que usan estos ids: {afectados} — abortado")
    print("  ningún proyecto guardado referencia los ids que cambian")

    MAPA.parent.mkdir(parents=True, exist_ok=True)
    with MAPA.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)
    print(f"\nMapa completo: {MAPA.relative_to(RAIZ)}")
    for f in [x for x in filas if x["id_viejo"] != x["id_nuevo"]][:8]:
        print(f"    {f['id_viejo']:22s} → {f['id_nuevo']:46s} {f['archivo']} · {f['columna']}")

    if args.aplicar:
        cat = json.loads(CATALOGO.read_text(encoding="utf-8"))
        for _, _, it in _items(cat, FAMILIA):
            if it["id"] in cambios:
                it["id"] = cambios[it["id"]]
        CATALOGO.write_text(json.dumps(cat, ensure_ascii=False, indent=1), encoding="utf-8")
        total = len({it["id"] for _, _, it in _items(cat)})
        print(f"\ncatálogo reescrito · {len(cambios)} ids renombrados · {total} ids únicos")


if __name__ == "__main__":
    main()
