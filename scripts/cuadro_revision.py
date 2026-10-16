"""cuadro_revision.py — la grilla de revisión, agrupada como el visualizador del TF.

Genera `docs/cuadro_revision.html`: el catálogo completo con la MISMA jerarquía que el
árbol del visualizador del Trabajo Final —familia › subgrupo › sub-subgrupo › serie, y
las series con apertura como carpeta con su «Total»—, cada nodo colapsable y con el color
de su familia.

A diferencia de `cuadro_series.py`, que es de lectura, esta página es para **revisar y
corregir**: cada serie se abre, se editan sus campos, se marca como revisada y queda
constancia de qué se cambió. Publicada como artifact con la capacidad `artifact`, guarda
las revisiones y se pueden retomar en otra sesión.

Las correcciones NO vuelven solas al catálogo: la página las exporta y se aplican con
`scripts/aplicar_revision.py`. Es a propósito — el catálogo se toca con un diff a la vista.

Uso:
    python scripts/cuadro_revision.py
    python scripts/cuadro_revision.py --cuerpo /tmp/revision.html
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from auditar_series import RAIZ, _buscar, _carpetas_datos, _radiografia  # type: ignore

from cueva.fuentes import unidades

CATALOGO = RAIZ / "cueva" / "datos" / "catalogo.json"
SALIDA = RAIZ / "docs" / "cuadro_revision.html"
ESTILOS = RAIZ / "web" / "cuadro" / "revision.css"
GUION = RAIZ / "web" / "cuadro" / "revision.js"


def _radiografiar(item: dict, carpetas: list[Path]) -> list[dict]:
    """Una entrada por fuente de datos, con el rango real leído del archivo."""
    fuentes = item.get("sources") or ([item] if item.get("file") else [])
    salida = []
    for fd in fuentes:
        ruta = _buscar(fd.get("file", ""), carpetas)
        radio = _radiografia(ruta, fd.get("dateCol", ""), fd.get("valCol", ""))
        proc = fd.get("proc") or item.get("proc") or {}
        salida.append({
            "freq": fd.get("freq") or item.get("freq", ""),
            "base": fd.get("file", ""),
            "cf": fd.get("dateCol", ""),
            "cv": fd.get("valCol", ""),
            "ini": radio.get("origen", ""),
            "fin": radio.get("final", ""),
            "obs": radio.get("n_obs", 0),
            "existe": bool(radio.get("existe")),
            "fuente": proc.get("fuente", ""),
        })
    return salida


def _serie(item: dict, carpetas: list[Path]) -> dict:
    proc = item.get("proc") or {}
    u = unidades.interpretar(item.get("unit", ""))
    nodo = {
        "id": item["id"],
        "label": item.get("label", ""),
        "unit": item.get("unit", ""),
        "mag": u.magnitud,
        "esc": u.escala,
        "mon": u.moneda or "",
        "desc": proc.get("definicion", ""),
        "fuente": proc.get("fuente", ""),
        "ext": str(proc.get("id_externo", "")),
        "conf": proc.get("confianza", ""),
        "nota": proc.get("nota", "") or proc.get("notas", ""),
        "datos": _radiografiar(item, carpetas),
    }
    hijos = item.get("children") or []
    if hijos:
        nodo["hijos"] = [_serie(h, carpetas) for h in hijos]
    return nodo


def _subgrupo(sub: dict, carpetas: list[Path]) -> dict:
    nodo = {"sub": sub.get("sub", "—"), "items": [_serie(i, carpetas) for i in sub.get("items", [])]}
    if sub.get("subs"):
        nodo["subs"] = [_subgrupo(s, carpetas) for s in sub["subs"]]
    return nodo


def arbol() -> list[dict]:
    catalogo = json.loads(CATALOGO.read_text(encoding="utf-8"))
    carpetas = _carpetas_datos()
    familias = []
    for fam in catalogo["familias"]:
        nodo = {"grp": fam["grp"], "clr": fam.get("clr", "#5BA4E6"), "subs": []}
        for sub in fam.get("subs", []):
            nodo["subs"].append(_subgrupo(sub, carpetas))
        if fam.get("items"):
            nodo["subs"].append({"sub": "—", "items": [_serie(i, carpetas) for i in fam["items"]]})
        familias.append(nodo)
    return familias


def _contar(familias: list[dict]) -> dict:
    def series(nodo):
        for s in nodo.get("items", []):
            yield from _aplanar(s)
        for sub in nodo.get("subs", []):
            yield from series(sub)

    total = campos = 0
    for fam in familias:
        for s in series(fam):
            total += 1
            campos += 1 if s["desc"] else 0
    return {"series": total, "con_desc": campos, "familias": len(familias)}


def _aplanar(serie: dict):
    yield serie
    for h in serie.get("hijos", []):
        yield from _aplanar(h)


def construir(familias: list[dict], resumen: dict, cuerpo_solo: bool = False) -> str:
    payload = json.dumps(familias, ensure_ascii=False, separators=(",", ":"))
    vocab = json.dumps(unidades.vocabulario(), ensure_ascii=False, separators=(",", ":"))
    fuentes = json.dumps(
        sorted(json.loads((RAIZ / "cueva" / "fuentes" / "registro.json")
                          .read_text(encoding="utf-8"))["fuentes"]),
        ensure_ascii=False)
    cabeza = "" if cuerpo_solo else (
        '<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n')
    cierre = "" if cuerpo_solo else "</head>\n<body>\n"
    pie = "" if cuerpo_solo else "\n</body>\n</html>\n"

    return f"""{cabeza}<title>Revisión del Catálogo</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Serif:wght@500;600&display=swap">
<style>
{ESTILOS.read_text(encoding="utf-8")}
</style>
{cierre}<div id="app"></div>
<script type="application/json" id="arbol">{payload}</script>
<script type="application/json" id="vocabulario">{vocab}</script>
<script type="application/json" id="fuentes">{fuentes}</script>
<script type="application/json" id="revision">{{}}</script>
<script>
const RESUMEN = {json.dumps(resumen, ensure_ascii=False)};
{GUION.read_text(encoding="utf-8")}
</script>{pie}"""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cuerpo", default="", help="Escribir además la versión sin skeleton.")
    args = ap.parse_args()

    familias = arbol()
    resumen = _contar(familias)
    SALIDA.write_text(construir(familias, resumen), encoding="utf-8")
    print(f"{resumen['series']} series en {resumen['familias']} familias "
          f"-> {SALIDA.relative_to(RAIZ)}")
    print(f"   con descripción: {resumen['con_desc']} · "
          f"sin descripción: {resumen['series'] - resumen['con_desc']}")
    if args.cuerpo:
        Path(args.cuerpo).write_text(construir(familias, resumen, cuerpo_solo=True),
                                     encoding="utf-8")
        print(f"   versión para publicar -> {args.cuerpo}")


if __name__ == "__main__":
    main()
