"""aplicar_revision.py — lleva al catálogo las correcciones hechas en la grilla de revisión.

La grilla (`docs/cuadro_revision.html`, publicada como artifact) guarda lo que se corrige
en un bloque JSON dentro de la propia página. Este script toma ese bloque y lo escribe en
`cueva/datos/catalogo.json`.

Las correcciones NO vuelven solas: el catálogo se toca con un diff a la vista. Por eso el
script simula por defecto y muestra, campo por campo, qué cambiaría.

Qué hace con cada estado de revisión:

    ok         · marca `proc.confianza = "verificada"` con la fecha. Es la marca que
                 `completar_procedencia.py` respeta y nunca pisa.
    corregida  · aplica los campos editados y también marca `verificada`.
    problema   · NO toca los datos; escribe la nota del revisor en `proc.revision` para
                 que quede a la vista en el inventario.
    pendiente  · se ignora.

Los campos `mag`, `esc` y `mon` no se escriben sueltos: se traducen de vuelta a un `unit`
del vocabulario cerrado. Si la combinación corregida no existe en `unidades.json`, el
script lo dice y no inventa una unidad nueva.

Uso:
    python scripts/aplicar_revision.py --desde docs/cuadro_revision.html
    python scripts/aplicar_revision.py --desde revision.json --aplicar
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path

from cueva.fuentes import unidades

RAIZ = Path(__file__).resolve().parent.parent
CATALOGO = RAIZ / "cueva" / "datos" / "catalogo.json"
POR_DEFECTO = RAIZ / "docs" / "cuadro_revision.html"

# campo de la grilla -> dónde vive en el catálogo
EN_ITEM = {"label": "label"}
EN_PROC = {"desc": "definicion", "fuente": "fuente", "nota": "revision"}


def leer_revision(origen: Path) -> dict:
    """Acepta el HTML de la grilla o un JSON suelto pegado desde «Copiar correcciones»."""
    texto = origen.read_text(encoding="utf-8")
    if origen.suffix.lower() == ".json":
        return json.loads(texto)
    m = re.search(r'<script type="application/json" id="revision">(.*?)</script>', texto, re.S)
    if not m:
        raise SystemExit(f"No encontré el bloque de revisión en {origen}")
    return json.loads(m.group(1) or "{}")


def _recorrer(items: list):
    for item in items:
        yield item
        yield from _recorrer(item.get("children") or [])


def _todos(catalogo: dict):
    for fam in catalogo["familias"]:
        for sub in fam.get("subs", []):
            yield from _recorrer(sub["items"])
        yield from _recorrer(fam.get("items", []))


def unidad_para(mag: str, esc: str, mon: str) -> str | None:
    """Busca en el vocabulario el texto de unidad que corresponde a la combinación."""
    for texto in unidades.vocabulario()["textos"]:
        u = unidades.interpretar(texto)
        if u.magnitud == mag and u.escala == (esc or "unidad") and (u.moneda or "") == (mon or ""):
            return texto
    return None


def aplicar(catalogo: dict, revision: dict) -> tuple[list[str], list[str]]:
    """Devuelve (líneas del diff, avisos). Modifica `catalogo` en el lugar."""
    por_id = {i["id"]: i for i in _todos(catalogo)}
    hoy = date.today().isoformat()
    diff: list[str] = []
    avisos: list[str] = []

    for sid, r in sorted(revision.items()):
        item = por_id.get(sid)
        if item is None:
            avisos.append(f"{sid}: no está en el catálogo (¿se renombró el id?)")
            continue
        estado = r.get("estado", "pendiente")
        if estado == "pendiente":
            continue
        campos = dict(r.get("campos") or {})
        proc = item.setdefault("proc", {})

        if estado == "problema":
            nota = campos.get("nota", "")
            proc["revision"] = f"[{hoy}] PROBLEMA: {nota}" if nota else f"[{hoy}] marcada con problema"
            diff.append(f"  {sid}  ⚑ problema → proc.revision")
            continue

        # unidad: se rearma desde magnitud + escala + moneda
        if {"mag", "esc", "mon"} & set(campos):
            u = unidades.interpretar(item.get("unit", ""))
            mag = campos.pop("mag", u.magnitud)
            esc = campos.pop("esc", u.escala)
            mon = campos.pop("mon", u.moneda or "")
            texto = unidad_para(mag, esc, mon)
            if texto is None:
                avisos.append(
                    f"{sid}: la combinación {mag}/{esc}/{mon or 'sin moneda'} no existe en "
                    "cueva/fuentes/unidades.json. Agregala ahí y volvé a correr; no invento unidades."
                )
            elif texto != item.get("unit"):
                diff.append(f"  {sid}  unit: {item.get('unit')!r} → {texto!r}")
                item["unit"] = texto

        for campo, valor in campos.items():
            if campo in EN_ITEM:
                if item.get(EN_ITEM[campo]) != valor:
                    diff.append(f"  {sid}  {campo}: {item.get(EN_ITEM[campo])!r} → {valor!r}")
                    item[EN_ITEM[campo]] = valor
            elif campo in EN_PROC:
                clave = EN_PROC[campo]
                if proc.get(clave) != valor:
                    viejo = (proc.get(clave) or "")[:40]
                    diff.append(f"  {sid}  proc.{clave}: {viejo!r} → {valor[:40]!r}")
                    proc[clave] = valor
            else:
                avisos.append(f"{sid}: campo '{campo}' desconocido, se ignora")

        proc["confianza"] = "verificada"
        proc["verificado"] = hoy
        diff.append(f"  {sid}  ✓ confianza → verificada ({hoy})")

    return diff, avisos


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--desde", default=str(POR_DEFECTO),
                    help="HTML de la grilla o .json con las correcciones.")
    ap.add_argument("--aplicar", action="store_true", help="Escribir el catálogo.")
    args = ap.parse_args()

    origen = Path(args.desde)
    if not origen.exists():
        raise SystemExit(f"No existe {origen}")
    revision = leer_revision(origen)
    if not revision:
        print("La grilla no tiene ninguna revisión guardada todavía.")
        return

    estados: dict[str, int] = {}
    for r in revision.values():
        e = r.get("estado", "pendiente")
        estados[e] = estados.get(e, 0) + 1
    print(f"{len(revision)} series con revisión en {origen}")
    for e, n in sorted(estados.items(), key=lambda x: -x[1]):
        print(f"  {n:>4}  {e}")

    catalogo = json.loads(CATALOGO.read_text(encoding="utf-8"))
    diff, avisos = aplicar(catalogo, revision)

    print(f"\n{len(diff)} cambios en el catálogo:")
    for linea in diff[:60]:
        print(linea)
    if len(diff) > 60:
        print(f"  … y {len(diff) - 60} más")

    if avisos:
        print(f"\n{len(avisos)} avisos:")
        for a in avisos:
            print(f"  ! {a}")

    if not args.aplicar:
        print("\n(simulación: no se escribió nada. Agregá --aplicar cuando estés de acuerdo)")
        return
    CATALOGO.write_text(json.dumps(catalogo, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\n-> {CATALOGO.relative_to(RAIZ)}")
    print("Ahora conviene correr: python scripts/auditar_series.py && "
          "python scripts/generar_arbol_visualizador.py")


if __name__ == "__main__":
    main()
