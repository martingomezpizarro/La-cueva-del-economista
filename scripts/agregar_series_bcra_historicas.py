"""agregar_series_bcra_historicas.py — suma al catálogo el bloque histórico del BCRA.

El 2026-08-21 el BCRA incorporó a la API v4.0 dos categorías nuevas:
«Agregados monetarios y sus componentes» (28 series mensuales, la mayoría desde
junio de 1940) y «Activos y Pasivos del BCRA», que trae reservas internacionales a
fin de mes desde febrero de 1940.

Este script las agrega a `cueva/datos/catalogo.json` con su procedencia completa.
Es idempotente: si la serie ya está, no la duplica.

Los archivos todavía no existen en disco; se bajan con:
    python scripts/actualizar_bcra.py --indice
    python scripts/actualizar_bcra.py --series --categoria "Agregados monetarios y sus componentes"
    python scripts/actualizar_bcra.py --series --ids 1605

Uso:
    python scripts/agregar_series_bcra_historicas.py --simular
    python scripts/agregar_series_bcra_historicas.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CATALOGO = RAIZ / "cueva" / "datos" / "catalogo.json"
SNAPSHOT = RAIZ / "cueva" / "fuentes" / "bcra_variables.json"

FAMILIA = "Monetario y Cambiario"
CAT_AGREGADOS = "Agregados monetarios y sus componentes"

SUB_AGREGADOS = "Agregados Monetarios — serie histórica (BCRA)"
SUB_COMPONENTES = "Componentes de los Agregados — serie histórica (BCRA)"
SUB_RESERVAS = "Reservas y Liquidez"

# id de catálogo, idVariable del BCRA, etiqueta legible, subgrupo
PLAN: list[tuple[str, int, str, str]] = [
    ("bm_hist",        1606, "Base Monetaria (mensual, histórica)",                        SUB_AGREGADOS),
    ("circ_hist",      1607, "Circulación Monetaria (mensual, histórica)",                 SUB_AGREGADOS),
    ("bym_publico",    1608, "Billetes y Monedas en Poder del Público (histórica)",        SUB_AGREGADOS),
    ("efectivo_eeff",  1609, "Efectivo en Entidades Financieras (histórica)",              SUB_AGREGADOS),
    ("dep_eeff_bcra",  1610, "Depósitos de EEFF en Cta. Cte. en el BCRA (histórica)",      SUB_AGREGADOS),
    ("m1_total",       1611, "M1 — moneda local y extranjera",                             SUB_AGREGADOS),
    ("m1_ml",          1612, "M1 — moneda local",                                          SUB_AGREGADOS),
    ("m2_total",       1617, "M2 — moneda local y extranjera",                             SUB_AGREGADOS),
    ("m2_ml",          1618, "M2 — moneda local",                                          SUB_AGREGADOS),
    ("m3_total",       1623, "M3 — moneda local y extranjera",                             SUB_AGREGADOS),
    ("m3_ml",          1624, "M3 — moneda local",                                          SUB_AGREGADOS),
    ("cc_priv_ml",     1613, "Cuentas Corrientes — sector privado (ARS)",                  SUB_COMPONENTES),
    ("cc_pub_ml",      1614, "Cuentas Corrientes — sector público (ARS)",                  SUB_COMPONENTES),
    ("cc_priv_me",     1615, "Cuentas Corrientes — sector privado (m. extranjera, valuada en ARS)",                  SUB_COMPONENTES),
    ("cc_pub_me",      1616, "Cuentas Corrientes — sector público (m. extranjera, valuada en ARS)",                  SUB_COMPONENTES),
    ("ca_priv_ml",     1619, "Cajas de Ahorro — sector privado (ARS)",                     SUB_COMPONENTES),
    ("ca_pub_ml",      1620, "Cajas de Ahorro — sector público (ARS)",                     SUB_COMPONENTES),
    ("ca_priv_me",     1621, "Cajas de Ahorro — sector privado (m. extranjera, valuada en ARS)",                     SUB_COMPONENTES),
    ("ca_pub_me",      1622, "Cajas de Ahorro — sector público (m. extranjera, valuada en ARS)",                     SUB_COMPONENTES),
    ("pf_priv_ml",     1625, "Depósitos a Plazo Fijo — sector privado (ARS)",              SUB_COMPONENTES),
    ("pf_pub_ml",      1626, "Depósitos a Plazo Fijo — sector público (ARS)",              SUB_COMPONENTES),
    ("pf_priv_me",     1630, "Depósitos a Plazo Fijo — sector privado (m. extranjera, valuada en ARS)",              SUB_COMPONENTES),
    ("pf_pub_me",      1631, "Depósitos a Plazo Fijo — sector público (m. extranjera, valuada en ARS)",              SUB_COMPONENTES),
    ("otrosdep_priv_ml", 1627, "Otros Depósitos — sector privado (ARS)",                   SUB_COMPONENTES),
    ("otrosdep_pub_ml",  1628, "Otros Depósitos — sector público (ARS)",                   SUB_COMPONENTES),
    ("otrosdep_priv_me", 1632, "Otros Depósitos — sector privado (m. extranjera, valuada en ARS)",                   SUB_COMPONENTES),
    ("otrosdep_pub_me",  1633, "Otros Depósitos — sector público (m. extranjera, valuada en ARS)",                   SUB_COMPONENTES),
    ("aceptaciones",   1629, "Aceptaciones",                                               SUB_COMPONENTES),
    ("res_mensual",    1605, "Reservas Internacionales (saldo a fin de mes, histórica)",   SUB_RESERVAS),
]

DEFINICIONES = {
    1611: "M1: billetes y monedas en poder del público más depósitos en cuenta corriente, sumando las partidas en moneda local y en moneda extranjera.",
    1612: "M1 en moneda local: billetes y monedas en poder del público más depósitos en cuenta corriente en pesos.",
    1617: "M2: M1 más cajas de ahorro, sumando moneda local y extranjera.",
    1618: "M2 en moneda local: M1 en pesos más cajas de ahorro en pesos.",
    1623: "M3: M2 más depósitos a plazo fijo y otros depósitos, sumando moneda local y extranjera. Es el agregado más amplio que publica el BCRA.",
    1624: "M3 en moneda local: M2 en pesos más plazos fijos y otros depósitos en pesos.",
    1605: "Saldo de reservas internacionales del BCRA a fin de mes. Es la versión mensual y larga de la serie diaria (idVariable 1), y llega hasta febrero de 1940.",
    1629: "Aceptaciones bancarias: obligaciones que la entidad asume por cuenta de un cliente y que integran el agregado amplio.",
}


def _por_id_bcra() -> dict[int, dict]:
    if not SNAPSHOT.exists():
        raise SystemExit(
            "Falta cueva/fuentes/bcra_variables.json.\n"
            "Corré primero: python scripts/actualizar_bcra.py --indice"
        )
    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    return {v["id"]: v for v in snap["variables"]}


def _proc(meta: dict) -> dict:
    categoria = meta["categoria"]
    return {
        "verificado": "2026-08-27",
        "fuente": "bcra",
        "id_externo": str(meta["id"]),
        "endpoint": f"/estadisticas/v4.0/Monetarias/{meta['id']}",
        "categoria_fuente": categoria,
        "definicion": DEFINICIONES.get(meta["id"], meta["descripcion"]),
        "cobertura": {"desde": meta["desde"], "hasta": meta["hasta"]},
        "script": "scripts/actualizar_bcra.py",
        "confianza": "alta",
        "notas": (
            "Serie incorporada por el BCRA a la API el 2026-08-21. La metodología oficial "
            "se completa corriendo `python scripts/actualizar_bcra.py --indice`."
        ),
    }


def _subgrupo(familia: dict, nombre: str) -> dict:
    for sub in familia["subs"]:
        if sub["sub"] == nombre:
            return sub
    nuevo = {"sub": nombre, "items": []}
    familia["subs"].append(nuevo)
    return nuevo


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--simular", action="store_true", help="No escribir; solo informar.")
    args = ap.parse_args()

    catalogo = json.loads(CATALOGO.read_text(encoding="utf-8"))
    familia = next(f for f in catalogo["familias"] if f["grp"] == FAMILIA)
    metas = _por_id_bcra()

    existentes = set()
    for fam in catalogo["familias"]:
        for sub in fam.get("subs", []):
            existentes.update(i["id"] for i in sub["items"])
        existentes.update(i["id"] for i in fam.get("items", []))

    agregadas = omitidas = 0
    for sid, id_bcra, etiqueta, nombre_sub in PLAN:
        if sid in existentes:
            omitidas += 1
            continue
        meta = metas.get(id_bcra)
        if meta is None:
            print(f"  ! idVariable {id_bcra} no está en el índice; salteada")
            continue
        _subgrupo(familia, nombre_sub)["items"].append({
            "id": sid,
            "label": etiqueta,
            "file": f"{meta['slug']}.csv",
            "dateCol": "fecha",
            "valCol": "valor",
            "unit": "Mill. USD" if "USD" in meta["unidad"] else "Miles de ARS",
            "freq": meta["periodicidad"],
            "proc": _proc(meta),
        })
        agregadas += 1

    print(f"{agregadas} series agregadas · {omitidas} ya estaban")
    if args.simular:
        print("(simulación: no se escribió nada)")
        return
    CATALOGO.write_text(json.dumps(catalogo, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"-> {CATALOGO.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
