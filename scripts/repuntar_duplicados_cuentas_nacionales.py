"""repuntar_duplicados_cuentas_nacionales.py — cierra la duplicación FBKF / Oferta y Demanda /
PBI por sector / EMAE entre el archivo del Trabajo Final (que este catálogo no puede auditar)
y el CSV nuevo generado por `scripts/ingestar_cuentas_nacionales.py` a partir del mismo .xls
del INDEC, ya versionado en este repo.

Repunta el campo `file` (y, para EMAE, `dateCol`) de las series *viejas* al archivo nuevo,
que ya trae todas las columnas del cuadro. Antes de reescribir cada referencia, verifica que
`valCol` exista como columna real en el archivo nuevo — si no coincide, la deja intacta y
avisa, en vez de romperla en silencio.

Simula por defecto; escribe con `--aplicar`.

    python scripts/repuntar_duplicados_cuentas_nacionales.py
    python scripts/repuntar_duplicados_cuentas_nacionales.py --aplicar
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CATALOGO = RAIZ / "cueva" / "datos" / "catalogo.json"
CARPETA_NUEVA = RAIZ / "data" / "series" / "1.Actividad y Cuentas Nacionales"

# archivo viejo (Trabajo Final, inalcanzable) -> (archivo nuevo, override de dateCol o None)
MAPA = {
    "fbkf_constante.csv": ("cn_fbkf_constante.csv", None),
    "fbkf_corriente.csv": ("cn_fbkf_corriente.csv", None),
    "oferta_demanda_constante.csv": ("cn_oferta_demanda_constante.csv", None),
    "oferta_demanda_corriente.csv": ("cn_oferta_demanda_corriente.csv", None),
    "oferta_demanda_ipi.csv": ("cn_oferta_demanda_ipi.csv", None),
    "pbi_sectores_constante.csv": ("cn_pbi_categoria_constante.csv", None),
    "pbi_sectores_corriente.csv": ("cn_pbi_categoria_corriente.csv", None),
    "pbi_sectores_ipi.csv": ("cn_pbi_categoria_ipi.csv", None),
    "emae_mensual.csv": ("emae_nivel_general.csv", "fecha"),
    "emae_trimestral.csv": ("emae_nivel_general_trimestral.csv", "fecha"),
    "emae_anual.csv": ("emae_nivel_general_anual.csv", "fecha"),
}


def _columnas(nombre: str) -> set[str]:
    with (CARPETA_NUEVA / nombre).open(encoding="utf-8") as fh:
        return set(next(csv.reader(fh)))


def _fuentes_del_item(it: dict) -> list[dict]:
    """Los dicts con `file`/`dateCol`/`valCol` propios: el item mismo, o cada entrada de `sources`."""
    if "sources" in it:
        return it["sources"]
    if "file" in it:
        return [it]
    return []


def _descender(items: list, out: list) -> None:
    for it in items:
        if "sub" in it:
            _descender(it.get("items") or it.get("subs") or [], out)
        else:
            out.append(it)
            if it.get("children"):
                _descender(it["children"], out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()

    columnas_nuevas = {viejo: _columnas(nuevo) for viejo, (nuevo, _) in MAPA.items()}

    cat = json.loads(CATALOGO.read_text(encoding="utf-8"))
    items: list[dict] = []
    for f in cat["familias"]:
        _descender(f.get("subs", []), items)

    cambiados, saltados = [], []
    for it in items:
        for fuente in _fuentes_del_item(it):
            viejo = fuente.get("file")
            if viejo not in MAPA:
                continue
            nuevo, date_override = MAPA[viejo]
            val = fuente.get("valCol")
            if val not in columnas_nuevas[viejo]:
                saltados.append((it["id"], viejo, val))
                continue
            antes = (fuente["file"], fuente.get("dateCol"))
            fuente["file"] = nuevo
            if date_override:
                fuente["dateCol"] = date_override
            fuente.setdefault("proc", {})["migrado_desde"] = f"{antes[0]} (Trabajo Final, 2026-08-29)"
            cambiados.append((it["id"], antes, (fuente["file"], fuente.get("dateCol"))))

    print(f"Repunteadas: {len(cambiados)}")
    for sid, antes, despues in cambiados:
        print(f"  {sid:20s} {antes} -> {despues}")
    if saltados:
        print(f"\nSalteadas (valCol no existe en el archivo nuevo): {len(saltados)}")
        for sid, viejo, val in saltados:
            print(f"  {sid:20s} file={viejo} valCol={val!r}")

    if args.aplicar:
        CATALOGO.write_text(json.dumps(cat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"\nEscrito {CATALOGO.relative_to(RAIZ)}")
    else:
        print("\n(simulación — corré con --aplicar para escribir)")


if __name__ == "__main__":
    main()
