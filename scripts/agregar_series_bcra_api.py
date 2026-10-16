"""agregar_series_bcra_api.py — suma al catálogo lo que la API del BCRA tiene y faltaba.

`scripts/cobertura_bcra.py` encontró que el catálogo no tenía **ninguna tasa de interés
argentina**, ni CER, ni UVA, ni los agregados monetarios diarios, ni el balance del BCRA.
Todo eso está en la API v4.0, sin clave, y parte con mucha historia: la tasa de plazo fijo
a 30 días arranca en 1985 y la inflación mensual en 1943.

Este script las agrega con su procedencia completa. Es idempotente: si la serie ya está,
no la duplica. Los archivos todavía no existen en disco; se bajan con:

    python scripts/actualizar_bcra.py --series --ids <los que liste este script>

Uso:
    python scripts/agregar_series_bcra_api.py --simular
    python scripts/agregar_series_bcra_api.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CATALOGO = RAIZ / "cueva" / "datos" / "catalogo.json"
SNAPSHOT = RAIZ / "cueva" / "fuentes" / "bcra_variables.json"

# (id de catálogo, idVariable, etiqueta, familia, subgrupo, unidad, definición)
PLAN: list[tuple] = [
    # ── Tasas pasivas ────────────────────────────────────────────────────────
    ("tasa_pf30", 12, "Tasa de Plazo Fijo a 30 días", "Monetario y Cambiario",
     "Tasas de Interés — Pasivas", "%",
     "Tasa promedio ponderada por monto de los plazos fijos a 30 días en moneda nacional, "
     "total de entidades (SISCEN-0002). Es la serie de tasa más larga que publica el BCRA."),
    ("tasa_badlar", 7, "BADLAR — bancos privados (TNA)", "Monetario y Cambiario",
     "Tasas de Interés — Pasivas", "%",
     "Tasa promedio ponderada de los plazos fijos de un millón de pesos o más, de 30 a 35 "
     "días, en bancos privados. Es la tasa de referencia del mercado mayorista."),
    ("tasa_badlar_tea", 35, "BADLAR — bancos privados (TEA)", "Monetario y Cambiario",
     "Tasas de Interés — Pasivas", "%",
     "La misma BADLAR expresada en tasa efectiva anual."),
    ("tasa_tm20", 8, "TM20 — bancos privados", "Monetario y Cambiario",
     "Tasas de Interés — Pasivas", "%",
     "Tasa de los plazos fijos de veinte millones de pesos o más, de 30 a 35 días, "
     "en bancos privados."),
    ("tasa_tamar", 44, "TAMAR — bancos privados", "Monetario y Cambiario",
     "Tasas de Interés — Pasivas", "%",
     "Tasa mayorista de plazo fijo de 30 a 35 días. Reemplaza a la BADLAR como referencia "
     "a partir de octubre de 2024; el estrato de monto se actualiza por IPC."),
    # ── Tasas activas ────────────────────────────────────────────────────────
    ("tasa_adelantos", 13, "Adelantos en cuenta corriente", "Monetario y Cambiario",
     "Tasas de Interés — Activas", "%",
     "Tasa de los adelantos en cuenta corriente con acuerdo, de 1 a 7 días y de diez "
     "millones de pesos o más, a empresas del sector privado."),
    ("tasa_personales", 14, "Préstamos personales", "Monetario y Cambiario",
     "Tasas de Interés — Activas", "%",
     "Tasa promedio ponderada de los préstamos personales en pesos a tasa fija o repactable."),
    ("tasa_baibar", 11, "BAIBAR — préstamos entre bancos privados", "Monetario y Cambiario",
     "Tasas de Interés — Activas", "%",
     "Tasa del mercado interbancario: préstamos de efectivo entre entidades privadas hasta "
     "15 días de plazo."),
    ("tasa_justicia", 43, "Tasa Comunicado P 14.290 (uso de justicia)", "Monetario y Cambiario",
     "Tasas de Interés — Activas", "%",
     "Serie de capitalización diaria basada en las tasas de caja de ahorro y plazo fijo. "
     "Es la que usan los tribunales para actualizar créditos."),
    # ── Índices de ajuste ────────────────────────────────────────────────────
    ("cer", 30, "CER — Coeficiente de Estabilización de Referencia", "Precios e Inflación",
     "Índices de Ajuste", "Índice base 2.2.02=1",
     "Índice base 2/2/2002 = 1 construido sobre la variación del IPC. Es el coeficiente con "
     "que se ajusta la deuda indexada en pesos."),
    ("uva", 31, "UVA — Unidad de Valor Adquisitivo", "Precios e Inflación",
     "Índices de Ajuste", "ARS",
     "Vale la milésima parte del costo de construcción de un metro cuadrado de vivienda al "
     "31/3/2016; se actualiza por CER."),
    ("uvi", 32, "UVI — Unidad de Vivienda", "Precios e Inflación",
     "Índices de Ajuste", "ARS",
     "Como la UVA pero ajustada por el Índice del Costo de la Construcción (CAICC)."),
    ("icl", 40, "ICL — Índice para Contratos de Locación", "Precios e Inflación",
     "Índices de Ajuste", "Índice base 30.6.20=1",
     "Índice diario que combina la variación del IPC y la del RIPTE. Es el que ajusta los "
     "alquileres."),
    # ── Inflación con serie larga ────────────────────────────────────────────
    ("infl_mensual", 27, "Inflación mensual (serie larga BCRA)", "Precios e Inflación",
     "IPC — Nivel General", "%",
     "Variación mensual del IPC informado por INDEC. Entre noviembre de 2015 y abril de "
     "2016 se empalma con el IPC de CABA y el de San Luis. Arranca en marzo de 1943."),
    ("infl_ia", 28, "Inflación interanual (serie larga BCRA)", "Precios e Inflación",
     "IPC — Nivel General", "%",
     "Variación interanual del IPC informado por INDEC, con el mismo empalme 2015-2016. "
     "Arranca en enero de 1944."),
    # ── Agregados diarios ────────────────────────────────────────────────────
    ("bm_diaria", 15, "Base Monetaria (diaria)", "Monetario y Cambiario",
     "Agregados Monetarios — diarios", "Mill. ARS",
     "Circulación monetaria total más los depósitos en cuenta corriente en pesos de las "
     "entidades financieras en el BCRA. Se difunde por Comunicación «C»."),
    ("circ_diaria", 16, "Circulación Monetaria (diaria)", "Monetario y Cambiario",
     "Agregados Monetarios — diarios", "Mill. ARS",
     "Billetes y monedas emitidos por el BCRA y puestos en circulación, más cheques "
     "cancelatorios en pesos."),
    ("bym_pub_diaria", 17, "Billetes y Monedas en Poder del Público (diaria)",
     "Monetario y Cambiario", "Agregados Monetarios — diarios", "Mill. ARS",
     "Circulación monetaria que no está en poder de las entidades financieras."),
    ("efectivo_eeff_d", 18, "Efectivo en Entidades Financieras (diaria)",
     "Monetario y Cambiario", "Agregados Monetarios — diarios", "Mill. ARS",
     "Billetes y monedas en cajas y cajeros de las entidades. Se publica con dos días "
     "hábiles de rezago."),
    ("dep_cc_bcra_d", 19, "Depósitos de EEFF en Cta. Cte. en el BCRA (diaria)",
     "Monetario y Cambiario", "Agregados Monetarios — diarios", "Mill. ARS",
     "Depósitos en cuenta corriente en pesos de las entidades financieras en el BCRA; "
     "integran la base monetaria."),
    ("m2_var_ia", 25, "M2 privado — variación interanual", "Monetario y Cambiario",
     "Agregados Monetarios — diarios", "%",
     "Variación interanual del promedio móvil de 30 días del M2 privado (circulante en "
     "poder del público más depósitos a la vista del sector privado)."),
    ("dep_cc", 22, "Depósitos en Cuenta Corriente", "Monetario y Cambiario",
     "Depósitos", "Mill. ARS",
     "Depósitos en efectivo en cuenta corriente del total de sectores, neto de la "
     "utilización de Fondos Unificados de Cuentas Oficiales."),
    ("dep_ca", 23, "Depósitos en Caja de Ahorro", "Monetario y Cambiario",
     "Depósitos", "Mill. ARS",
     "Depósitos en efectivo bajo el sistema de caja de ahorros, del total de sectores."),
    ("dep_pf", 24, "Depósitos a Plazo Fijo", "Monetario y Cambiario",
     "Depósitos", "Mill. ARS",
     "Depósitos a plazo del total de sectores; incluye inversiones a plazo y excluye CEDROs."),
    ("prest_priv_total", 26, "Préstamos al Sector Privado", "Monetario y Cambiario",
     "Préstamos", "Mill. ARS",
     "Préstamos de efectivo de las entidades financieras al sector privado no financiero, "
     "en moneda nacional y extranjera."),
    ("tc_minorista", 4, "TC Minorista (promedio vendedor)", "Monetario y Cambiario",
     "Tipo de Cambio Nominal y Brecha", "ARS/USD",
     "Tipo de cambio peso/dólar minorista informado según Comunicación B 9791."),
    # ── Balance del BCRA ─────────────────────────────────────────────────────
    ("bcra_pasivos_mon", 1247, "Pasivos Monetarios del BCRA", "Monetario y Cambiario",
     "Balance del BCRA", "Mill. ARS",
     "Base monetaria más depósitos y otros pasivos monetarios en moneda extranjera en el BCRA."),
    ("bcra_leliq", 1260, "LELIQ y NOTALIQ", "Monetario y Cambiario",
     "Balance del BCRA", "Mill. ARS",
     "Saldo de Letras y Notas de Liquidez del BCRA en cartera de entidades financieras."),
    ("bcra_lebac", 1258, "LEBAC, NOBAC y otras letras en pesos", "Monetario y Cambiario",
     "Balance del BCRA", "Mill. ARS",
     "Saldo de letras y notas del BCRA en pesos; no incluye LELIQ ni NOTALIQ."),
    ("bcra_pases_neto", 1261, "Posición Neta de Pases", "Monetario y Cambiario",
     "Balance del BCRA", "Mill. ARS",
     "Pases pasivos menos pases activos del BCRA. Positivo = el BCRA absorbe liquidez."),
    ("bcra_dep_gob", 1264, "Depósitos del Gobierno en el BCRA", "Monetario y Cambiario",
     "Balance del BCRA", "Mill. ARS",
     "Saldo de las cuentas del Gobierno Nacional en el Banco Central."),
    ("bcra_redescuentos", 1267, "Redescuentos y Adelantos por Iliquidez",
     "Monetario y Cambiario", "Balance del BCRA", "Mill. ARS",
     "Asistencia del BCRA a entidades financieras con problemas de liquidez."),
    ("bcra_adel_tesoro", 1268, "Adelantos Transitorios al Tesoro", "Monetario y Cambiario",
     "Balance del BCRA", "Mill. ARS",
     "Stock de adelantos transitorios al Gobierno Nacional (artículo 20 de la Carta "
     "Orgánica). Es la medida directa del financiamiento monetario del déficit."),
]


def _por_id_bcra() -> dict[int, dict]:
    if not SNAPSHOT.exists():
        raise SystemExit("Falta cueva/fuentes/bcra_variables.json "
                         "(correr scripts/actualizar_bcra.py --indice)")
    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    return {v["id"]: v for v in snap["variables"]}


def _ids_existentes(catalogo: dict) -> set[str]:
    def rec(items):
        for i in items:
            yield i["id"]
            yield from rec(i.get("children") or [])
    vistos: set[str] = set()
    for fam in catalogo["familias"]:
        for sub in fam.get("subs", []):
            vistos.update(rec(sub["items"]))
        vistos.update(rec(fam.get("items", [])))
    return vistos


def _familia(catalogo: dict, nombre: str) -> dict:
    for fam in catalogo["familias"]:
        if fam["grp"] == nombre:
            return fam
    raise SystemExit(f"La familia «{nombre}» no existe en el catálogo")


def _subgrupo(familia: dict, nombre: str) -> dict:
    familia.setdefault("subs", [])
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
    metas = _por_id_bcra()
    existentes = _ids_existentes(catalogo)

    agregadas, omitidas, sin_meta = [], [], []
    nuevos_subgrupos: set[str] = set()

    for sid, id_bcra, etiqueta, familia, subgrupo, unidad, definicion in PLAN:
        if sid in existentes:
            omitidas.append(sid)
            continue
        meta = metas.get(id_bcra)
        if meta is None:
            sin_meta.append(f"{sid} (idVariable {id_bcra})")
            continue
        fam = _familia(catalogo, familia)
        if not any(s["sub"] == subgrupo for s in fam.get("subs", [])):
            nuevos_subgrupos.add(f"{familia} › {subgrupo}")
        _subgrupo(fam, subgrupo)["items"].append({
            "id": sid,
            "label": etiqueta,
            "file": f"{meta['slug']}.csv",
            "dateCol": "fecha",
            "valCol": "valor",
            "unit": unidad,
            "freq": meta["periodicidad"],
            "proc": {
                "verificado": "2026-08-28",
                "fuente": "bcra",
                "id_externo": str(id_bcra),
                "endpoint": f"/estadisticas/v4.0/Monetarias/{id_bcra}",
                "categoria_fuente": meta["categoria"],
                "definicion": definicion,
                "cobertura": {"desde": meta["desde"], "hasta": meta["hasta"]},
                "script": "scripts/actualizar_bcra.py",
                "confianza": "alta",
                "notas": "Alta desde la API v4.0 el 2026-08-28. La metodología oficial se "
                         "completa con `python scripts/actualizar_bcra.py --indice`.",
            },
        })
        agregadas.append((sid, id_bcra, meta["desde"], etiqueta))

    print(f"{len(agregadas)} series agregadas · {len(omitidas)} ya estaban")
    if nuevos_subgrupos:
        print(f"\n{len(nuevos_subgrupos)} subgrupos nuevos:")
        for s in sorted(nuevos_subgrupos):
            print(f"  {s}")
    if sin_meta:
        print(f"\n{len(sin_meta)} sin metadatos en el índice local (correr --indice):")
        for s in sin_meta:
            print(f"  {s}")
    print("\nSeries (ordenadas por antigüedad):")
    for sid, idb, desde, etiqueta in sorted(agregadas, key=lambda x: x[2]):
        print(f"  {desde}  id {idb:<5} {sid:<18} {etiqueta[:44]}")

    ids = ",".join(str(i) for _, i, _, _ in agregadas)
    print(f"\nPara bajarlas:\n  python scripts/actualizar_bcra.py --series --ids {ids}")

    if args.simular:
        print("\n(simulación: no se escribió nada)")
        return
    CATALOGO.write_text(json.dumps(catalogo, ensure_ascii=False, indent=1) + "\n",
                        encoding="utf-8")
    print(f"\n-> {CATALOGO.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
