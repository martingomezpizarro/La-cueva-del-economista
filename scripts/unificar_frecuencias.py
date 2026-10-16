"""unificar_frecuencias.py — deja una sola frecuencia cuando las demás son agregación.

El problema: 100 series del catálogo declaran la misma serie en varias frecuencias
(A+M+Q, M+Q, A+M…). Pero no todas son el mismo caso, y confundirlos destruye datos:

  · Mensual OBSERVADA (50 series, EMAE e ICA del INDEC). El trimestral y el anual son
    agregaciones del mismo dato mensual. Se pueden reconstruir; guardarlos es
    redundante y multiplica las entradas del catálogo.

  · Mensual ESTIMADA (44 series, PBI y cuentas nacionales). Acá el dato nativo es el
    TRIMESTRAL del INDEC y la mensual es una estimación propia por filtro de Kalman.
    Quedarse solo con la mensual sería tirar el dato oficial y conservar la estimación.
    **Estas no se tocan.**

  · Sin mensual (6 series). No hay nada que unificar.

Antes de quitar una frecuencia, el script la VERIFICA: prueba las tres formas de agregar
(suma, promedio, último valor del período) y se queda con la que reproduce el archivo
existente dentro de la tolerancia. Si ninguna lo reproduce, el trimestral trae algo que
el mensual no tiene y la serie se deja como está.

La regla que sí funcionó se guarda en la serie como `agregacion`, así el explorador puede
recalcular el trimestral y el anual al vuelo.

Uso:
    python scripts/unificar_frecuencias.py             # simula: verifica y reporta
    python scripts/unificar_frecuencias.py --aplicar
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from cueva import config

RAIZ = Path(__file__).resolve().parent.parent
CATALOGO = RAIZ / "cueva" / "datos" / "catalogo.json"
TOLERANCIA = 0.005  # 0,5 %: absorbe el redondeo con que publica el INDEC

REGLAS = {
    "suma": lambda s, r: s.resample(r).sum(),
    "promedio": lambda s, r: s.resample(r).mean(),
    "ultimo": lambda s, r: s.resample(r).last(),
}
PERIODO = {"Q": "QS", "A": "YS"}


def _carpetas() -> list[Path]:
    carpetas = [RAIZ / "data" / "series"]
    tf = config.carpeta_trabajo_final()
    if tf:
        carpetas.append(tf / "data" / "Variables Finales")
    return [c for c in carpetas if c.exists()]


_CACHE: dict[str, Path | None] = {}


def _buscar(archivo: str, carpetas: list[Path]) -> Path | None:
    if archivo not in _CACHE:
        hallada = None
        for carpeta in carpetas:
            directo = carpeta / archivo
            if directo.exists():
                hallada = directo
                break
            hallada = next(iter(carpeta.rglob(archivo)), None)
            if hallada:
                break
        _CACHE[archivo] = hallada
    return _CACHE[archivo]


def _serie(fuente: dict, carpetas: list[Path]) -> pd.Series | None:
    ruta = _buscar(fuente.get("file", ""), carpetas)
    if ruta is None:
        return None
    try:
        df = pd.read_excel(ruta) if ruta.suffix.lower() in {".xlsx", ".xls", ".xlsm"} \
            else pd.read_csv(ruta)
    except Exception:
        return None
    dc, vc = fuente.get("dateCol"), fuente.get("valCol")
    if dc not in df.columns or vc not in df.columns:
        return None
    d = pd.DataFrame({
        "f": pd.to_datetime(df[dc], errors="coerce", format="mixed"),
        "v": pd.to_numeric(df[vc], errors="coerce"),
    }).dropna()
    return None if d.empty else d.set_index("f")["v"].sort_index()


def regla_que_reproduce(mensual: pd.Series, objetivo: pd.Series, freq: str) -> tuple[str | None, float]:
    """Cuál de las tres formas de agregar reproduce el archivo `objetivo`."""
    mejor, mejor_err = None, float("inf")
    for nombre, fn in REGLAS.items():
        try:
            rec = fn(mensual, PERIODO[freq])
        except Exception:
            continue
        per = "Q" if freq == "Q" else "Y"
        a = rec.copy()
        a.index = a.index.to_period(per)
        b = objetivo.copy()
        b.index = b.index.to_period(per)
        comun = a.index.intersection(b.index)
        if len(comun) < 8:
            continue
        rel = ((a[comun] - b[comun]).abs() /
               b[comun].abs().replace(0, np.nan)).dropna()
        if rel.empty:
            continue
        err = float(rel.max())
        if err < mejor_err:
            mejor, mejor_err = nombre, err
    return (mejor, mejor_err) if mejor_err <= TOLERANCIA else (None, mejor_err)


def _recorrer(items: list):
    for item in items:
        yield item
        yield from _recorrer(item.get("children") or [])


def _todas(catalogo: dict):
    for fam in catalogo["familias"]:
        for s in fam.get("subs", []):
            yield from _recorrer(s["items"])
        yield from _recorrer(fam.get("items", []))


def clasificar(item: dict) -> str:
    fuentes = item.get("sources") or []
    if len(fuentes) < 2:
        return "una sola frecuencia"
    mensual = next((f for f in fuentes if f.get("freq") == "M"), None)
    if mensual is None:
        return "sin mensual"
    if (mensual.get("proc") or {}).get("fuente") == "propia":
        return "mensual estimada (Kalman)"
    return "mensual observada"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aplicar", action="store_true", help="Escribir los cambios en el catálogo.")
    ap.add_argument("--ver", type=int, default=15, help="Cuántas series detallar (0 = todas).")
    args = ap.parse_args()

    catalogo = json.loads(CATALOGO.read_text(encoding="utf-8"))
    carpetas = _carpetas()

    resumen: dict[str, int] = {}
    unificables: list[dict] = []
    problematicas: list[dict] = []

    for item in _todas(catalogo):
        tipo = clasificar(item)
        resumen[tipo] = resumen.get(tipo, 0) + 1
        if tipo != "mensual observada":
            continue

        fuentes = item["sources"]
        mensual = next(f for f in fuentes if f.get("freq") == "M")
        m = _serie(mensual, carpetas)
        if m is None:
            problematicas.append({"id": item["id"], "motivo": "no se pudo leer el mensual"})
            continue

        veredicto, reglas = {}, set()
        for f in fuentes:
            if f.get("freq") not in PERIODO:
                continue
            objetivo = _serie(f, carpetas)
            regla, err = regla_que_reproduce(m, objetivo, f["freq"]) \
                if objetivo is not None else (None, float("inf"))
            veredicto[f["freq"]] = (regla, err)
            if regla:
                reglas.add(regla)

        if not veredicto or any(r is None for r, _ in veredicto.values()):
            problematicas.append({
                "id": item["id"], "label": item.get("label", ""),
                "motivo": "alguna frecuencia no se reconstruye desde el mensual",
                "detalle": {k: (r or "—", round(e, 5)) for k, (r, e) in veredicto.items()},
            })
            continue
        if len(reglas) > 1:
            problematicas.append({"id": item["id"], "motivo": f"reglas distintas por frecuencia: {reglas}"})
            continue

        unificables.append({
            "item": item, "id": item["id"], "label": item.get("label", ""),
            "regla": reglas.pop(), "quita": sorted(veredicto),
            "error": max(e for _, e in veredicto.values()),
        })

    print("Series por tipo:")
    for k, n in sorted(resumen.items(), key=lambda x: -x[1]):
        print(f"  {n:>4}  {k}")

    print(f"\nUnificables a mensual (verificado contra el archivo): {len(unificables)}")
    muestra = unificables if args.ver == 0 else unificables[:args.ver]
    for u in muestra:
        print(f"  {u['id']:<18} {u['label'][:42]:<42} agregación={u['regla']:<9} "
              f"quita {'+'.join(u['quita'])}  err máx {u['error']:.4%}")
    if len(unificables) > len(muestra):
        print(f"  … y {len(unificables) - len(muestra)} más")

    if problematicas:
        print(f"\nNO se tocan ({len(problematicas)}): el trimestral o el anual trae algo propio")
        for p in problematicas[:10]:
            print(f"  {p['id']:<18} {p['motivo']}"
                  + (f"  {p.get('detalle')}" if p.get("detalle") else ""))

    quitadas = sum(len(u["quita"]) for u in unificables)
    print(f"\nEfecto: {len(unificables)} series pasan a una sola fuente · "
          f"-{quitadas} entradas del catálogo")

    if not args.aplicar:
        print("\n(simulación: no se escribió nada. Agregá --aplicar cuando estés de acuerdo)")
        return

    for u in unificables:
        item = u["item"]
        item["sources"] = [f for f in item["sources"] if f.get("freq") == "M"]
        item["agregacion"] = u["regla"]
        proc = item.setdefault("proc", {})
        proc["notas"] = (
            f"Trimestral y anual se derivan del mensual por {u['regla']}; verificado contra "
            f"los archivos del INDEC con un error máximo de {u['error']:.3%}. "
            + proc.get("notas", "")
        ).strip()
    CATALOGO.write_text(json.dumps(catalogo, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\n-> {CATALOGO.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
