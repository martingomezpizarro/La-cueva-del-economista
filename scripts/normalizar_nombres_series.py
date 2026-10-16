"""normalizar_nombres_series.py — desambigua las etiquetas del catálogo.

El problema: 82 etiquetas están usadas por más de una serie. Dentro del árbol se
entienden («Vencimientos a 1 año › FMI › Moneda Local»), pero la etiqueta viaja sola:
al buscador, a la leyenda de un gráfico, a la cita de un informe. Ahí «Moneda Local»
—54 series distintas— no dice nada.

Todas las colisiones responden a cuatro patrones, así que se arreglan con reglas y no
a mano una por una:

  A · Vencimientos, hojas por moneda   «Moneda Local» (×54) y «Moneda Extranjera» (×54)
      -> «Vencimientos 1a — FMI — moneda local»
  B · Deuda, mismo acreedor en tres contextos (saldo / venc. 1a / venc. 2a)
      -> «Saldo de deuda — FMI», «Vencimientos 1a — FMI», «Vencimientos 2a — FMI»
  C · Países que son a la vez socio comercial y componente del ITCRM
      -> «ITCRM bilateral — Brasil» y «Saldo comercial — Brasil»
  D · Oferta y demanda a precios constantes vs corrientes, y su choque con el BdP
      -> «Importaciones FOB (constante 2004)», «(corriente)», «Importaciones de bienes (BdP)»

Se toca SOLO `label`. Los `id` no se tocan: son el contrato con los proyectos guardados.

Uso:
    python scripts/normalizar_nombres_series.py            # simula y muestra el antes/después
    python scripts/normalizar_nombres_series.py --aplicar
"""

from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CATALOGO = RAIZ / "cueva" / "datos" / "catalogo.json"

# Contexto del subgrupo -> prefijo corto con el que se cualifica la etiqueta.
PREFIJO_SUBGRUPO = {
    "Vencimientos a 1 año (USD)": "Vencimientos 1a",
    "Vencimientos a 2 años (USD)": "Vencimientos 2a",
    "Saldo de Deuda Bruta (USD)": "Saldo de deuda",
    "ITCRM — América": "ITCRM bilateral",
    "ITCRM — Europa": "ITCRM bilateral",
    "ITCRM — Asia": "ITCRM bilateral",
    "ITCRM — General": "ITCRM",
    "Saldo por País — América": "Saldo comercial",
    "Saldo por País — Europa": "Saldo comercial",
    "Saldo por País — Asia y Pacífico": "Saldo comercial",
    "Saldo por País — África": "Saldo comercial",
    "Saldo por País — Oceanía": "Saldo comercial",
    "Saldo por País — Totales y Regiones": "Saldo comercial",
    "Oferta y Demanda — Constante 2004": "",          # se resuelve con sufijo, no prefijo
    "Oferta y Demanda — Corriente (nominal)": "",
    "Oferta y Demanda — Precios Implícitos": "",
    "PBI por Sector — Constante 2004": "",
    "PBI por Sector — Corriente (nominal)": "",
    "PBI por Sector — Precios Implícitos": "",
    "FBKF Detalle — Constante 2004": "",
    "FBKF Detalle — Corriente (nominal)": "",
}

# Subgrupos que se distinguen por valuación: va como sufijo, que es como se lee.
SUFIJO_VALUACION = {
    "Oferta y Demanda — Constante 2004": "constante 2004",
    "PBI por Sector — Constante 2004": "constante 2004",
    "FBKF Detalle — Constante 2004": "constante 2004",
    "Oferta y Demanda — Corriente (nominal)": "corriente",
    "PBI por Sector — Corriente (nominal)": "corriente",
    "FBKF Detalle — Corriente (nominal)": "corriente",
    "Oferta y Demanda — Precios Implícitos": "precios implícitos",
    "PBI por Sector — Precios Implícitos": "precios implícitos",
}

# Series del balance de pagos cuyo nombre choca con las cuentas nacionales.
SUFIJO_BDP = "BdP"
MONEDA_HOJA = {"Moneda Local": "moneda local", "Moneda Extranjera": "moneda extranjera"}


def _recorrer(items: list, fam: str, sub: str, padres: list[str] | None = None):
    padres = padres or []
    for item in items:
        yield fam, sub, padres, item
        yield from _recorrer(item.get("children") or [], fam, sub,
                             padres + [item.get("label", item["id"])])


def _todas(catalogo: dict):
    for fam in catalogo["familias"]:
        for s in fam.get("subs", []):
            yield from _recorrer(s["items"], fam["grp"], s["sub"])
        yield from _recorrer(fam.get("items", []), fam["grp"], "—")


def nuevo_nombre(fam: str, sub: str, padres: list[str], item: dict) -> str | None:
    """La etiqueta desambiguada, o None si la actual ya sirve sola."""
    label = item.get("label", "")

    # A · hoja de vencimientos: el acreedor está en el padre, la moneda en la hoja
    if label in MONEDA_HOJA and padres:
        acreedor = padres[-1]
        prefijo = PREFIJO_SUBGRUPO.get(sub, "")
        base = f"{prefijo} — {acreedor}" if prefijo else acreedor
        return f"{base} — {MONEDA_HOJA[label]}"

    # D · cuentas nacionales: la valuación va como sufijo
    if sub in SUFIJO_VALUACION:
        suf = SUFIJO_VALUACION[sub]
        return label if f"({suf})" in label else f"{label} ({suf})"

    # D bis · balance de pagos: se marca para no confundir con cuentas nacionales
    if fam == "Sector Externo" and sub.startswith("BdP"):
        return label if f"({SUFIJO_BDP})" in label else f"{label} ({SUFIJO_BDP})"

    # B y C · el subgrupo define el contexto y va como prefijo
    prefijo = PREFIJO_SUBGRUPO.get(sub)
    if prefijo:
        return label if label.startswith(prefijo) else f"{prefijo} — {label}"

    return None


def _limpio(texto: str) -> str:
    """El contexto sin las marcas que la etiqueta ya trae, para no repetirlas."""
    for marca in (" (BdP)", "BdP — ", " (USD)"):
        texto = texto.replace(marca, "")
    return texto.strip(" —")


def colisiones(catalogo: dict, campo=lambda i: i.get("label", "")) -> dict[str, int]:
    c = collections.Counter(campo(i) for *_, i in _todas(catalogo))
    return {k: n for k, n in c.items() if n > 1 and k}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aplicar", action="store_true", help="Escribir los cambios en el catálogo.")
    ap.add_argument("--ver", type=int, default=25, help="Cuántos cambios mostrar (0 = todos).")
    args = ap.parse_args()

    catalogo = json.loads(CATALOGO.read_text(encoding="utf-8"))
    antes = colisiones(catalogo)

    cambios: dict[str, tuple[str, str]] = {}

    def registrar(item, propuesto):
        viejo_original = cambios.get(item["id"], (item.get("label", ""), ""))[0]
        cambios[item["id"]] = (viejo_original, propuesto)
        item["label"] = propuesto

    # Primera pasada: las cuatro reglas de patrón.
    for fam, sub, padres, item in _todas(catalogo):
        propuesto = nuevo_nombre(fam, sub, padres, item)
        if propuesto and propuesto != item.get("label"):
            registrar(item, propuesto)

    # Segunda pasada: lo que sigue chocando se cualifica con su contexto inmediato.
    # Pasa cuando dos conceptos distintos comparten nombre dentro de la misma rama:
    # «Otra Inversión» es una renta en la cuenta corriente y un flujo en la financiera.
    for _ in range(2):
        pendientes = colisiones(catalogo)
        if not pendientes:
            break
        for _fam, sub, padres, item in _todas(catalogo):
            label = item.get("label", "")
            if label not in pendientes:
                continue
            contexto = padres[-1] if padres else sub
            propuesto = f"{_limpio(contexto)} — {label}"
            if propuesto != label:
                registrar(item, propuesto)

    despues = colisiones(catalogo)
    cambios = [(sid, v, n) for sid, (v, n) in cambios.items() if v != n]

    print(f"etiquetas ambiguas antes: {len(antes)}  (afectan a {sum(antes.values())} series)")
    print(f"etiquetas ambiguas después: {len(despues)}  (afectan a {sum(despues.values())} series)")
    print(f"renombradas: {len(cambios)}\n")

    muestra = cambios if args.ver == 0 else cambios[:args.ver]
    for sid, viejo, nuevo in muestra:
        print(f"  {sid:<20} {viejo!r}\n  {'':<20}   -> {nuevo!r}")
    if len(cambios) > len(muestra):
        print(f"  … y {len(cambios) - len(muestra)} más (--ver 0 para verlas todas)")

    if despues:
        print("\nsiguen ambiguas:")
        for k, n in sorted(despues.items(), key=lambda x: -x[1])[:15]:
            print(f"  {n}x  {k}")

    if not args.aplicar:
        print("\n(simulación: no se escribió nada. Agregá --aplicar cuando estés de acuerdo)")
        return
    CATALOGO.write_text(json.dumps(catalogo, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\n-> {CATALOGO.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
