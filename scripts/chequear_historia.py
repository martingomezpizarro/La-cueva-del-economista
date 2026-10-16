#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Chequeo de consistencia de data/historia/ — versión de línea de comandos.

Es el borrador de lo que después vive en tests/test_historia.py. Se corre sin
dependencias: sólo stdlib. Devuelve 0 si está todo bien, 1 si hay errores.

    python scripts/chequear_historia.py
"""
from __future__ import annotations
import csv, json, re, sys, datetime, pathlib

RAIZ = pathlib.Path(__file__).resolve().parents[1]
H = RAIZ / "data" / "historia"
BIB = RAIZ / "RAG" / "referencias.bib"

ID_RE = re.compile(r"^[a-z0-9-]+$")
CITA_RE = re.compile(r"\[@([a-zA-Z0-9\-_]+)")
CIFRA_RE = re.compile(r"\{\{c:([a-zA-Z0-9_-]+)\}\}")

errores: list[str] = []
avisos: list[str] = []


def err(m): errores.append(m)
def avi(m): avisos.append(m)


def fecha(s: str):
    try:
        return datetime.date.fromisoformat(s)
    except ValueError:
        return None


def claves_bib(p: pathlib.Path) -> set[str]:
    if not p.exists():
        err(f"no existe {p}")
        return set()
    txt = p.read_text(encoding="utf-8")
    return set(re.findall(r"^@\w+\{([^,]+),", txt, re.M))


def frontmatter(texto: str) -> tuple[dict, str]:
    """Parser mínimo del subconjunto de YAML que usan las fichas.

    No reemplaza a pyyaml: sólo saca lo que los chequeos necesitan
    (id, cifras con sus claves y fuentes, relacionados, verificado).
    """
    if not texto.startswith("---"):
        return {}, texto
    fin = texto.find("\n---", 3)
    head, cuerpo = texto[3:fin], texto[fin + 4:]
    fm: dict = {"cifras": [], "relacionados": [], "series": []}
    cifra = None
    for linea in head.splitlines():
        s = linea.strip()
        if s.startswith("id:") and not linea.startswith("    "):
            fm["id"] = s[3:].strip()
        elif s.startswith("verificado:"):
            fm["verificado"] = s.split(":", 1)[1].strip()
        elif s.startswith("relacionados:"):
            fm["relacionados"] = [x.strip() for x in
                                  s.split(":", 1)[1].strip().strip("[]").split(",") if x.strip()]
        elif s.startswith("series:"):
            fm["series"] = [x.strip() for x in
                            s.split(":", 1)[1].strip().strip("[]").split(",") if x.strip()]
        elif s.startswith("- id:"):
            cifra = {"id": s[5:].strip(), "fuente": None}
            fm["cifras"].append(cifra)
        elif s.startswith("fuente:") and cifra is not None:
            cifra["fuente"] = s.split(":", 1)[1].strip().strip('"')
    return fm, cuerpo


def main() -> int:
    voc = json.loads((H / "vocabulario.json").read_text(encoding="utf-8"))
    cats, subs = set(voc["categorias"]), set(voc["subtipos"])
    nivs, precs = set(voc["niveles"]), set(voc["precision"])
    bib = claves_bib(BIB)

    # ---------------------------------------------------------- eventos.csv
    filas = list(csv.DictReader((H / "eventos.csv").open(encoding="utf-8")))
    ids: set[str] = set()
    for f in filas:
        i = f["id"]
        if i in ids:
            err(f"eventos.csv: id duplicado {i}")
        ids.add(i)
        if not ID_RE.match(i):
            err(f"eventos.csv: id mal formado {i}")
        d = fecha(f["desde"])
        if d is None:
            err(f"{i}: 'desde' inválido ({f['desde']})")
        if f["hasta"]:
            h = fecha(f["hasta"])
            if h is None:
                err(f"{i}: 'hasta' inválido ({f['hasta']})")
            elif d and h < d:
                err(f"{i}: hasta < desde")
        for campo, permitido in (("categoria", cats), ("subtipo", subs),
                                 ("nivel", nivs), ("precision", precs)):
            if f[campo] not in permitido:
                err(f"{i}: {campo}='{f[campo]}' fuera del vocabulario")
        for campo in ("verificado", "ficha"):
            if f[campo] not in ("si", "no"):
                err(f"{i}: {campo}='{f[campo]}' debe ser si/no")
        if not (f["refs"] or f["fuente"]):
            err(f"{i}: sin refs ni fuente")
        for k in filter(None, f["refs"].split(";")):
            if k not in bib:
                err(f"{i}: refs '{k}' no está en referencias.bib")
        if f["ficha"] == "si" and not (H / "fichas" / f"{i}.md").exists():
            err(f"{i}: ficha=si pero falta fichas/{i}.md")
        if not f["resumen"]:
            avi(f"{i}: sin resumen")

    # ------------------------------------------------------------- fichas
    for p in sorted((H / "fichas").glob("*.md")):
        if p.name.startswith("_"):
            continue
        fm, cuerpo = frontmatter(p.read_text(encoding="utf-8"))
        n = p.stem
        if fm.get("id") != n:
            err(f"{p.name}: 'id' del frontmatter ({fm.get('id')}) != nombre de archivo")
        if n not in ids:
            err(f"{p.name}: no tiene fila en eventos.csv")
        nombres = {c["id"] for c in fm["cifras"]}
        for c in fm["cifras"]:
            if not c["fuente"]:
                err(f"{n}: cifra '{c['id']}' sin fuente")
        usadas = set(CIFRA_RE.findall(cuerpo))
        for u in usadas - nombres:
            err(f"{n}: {{{{c:{u}}}}} no existe en 'cifras'")
        for s in nombres - usadas:
            avi(f"{n}: cifra '{s}' declarada y no usada en el relato")
        for k in set(CITA_RE.findall(cuerpo)):
            if k not in bib:
                err(f"{n}: cita [@{k}] no está en referencias.bib")
        for r in fm["relacionados"]:
            if r not in ids:
                err(f"{n}: relacionado '{r}' no existe en eventos.csv")
        if not (H / "series.json").exists() and fm["series"]:
            avi(f"{n}: declara series {fm['series']} pero todavía no hay series.json")

    # ------------------------------------------------------- presidencias
    pres = list(csv.DictReader((H / "presidencias.csv").open(encoding="utf-8")))
    pres.sort(key=lambda r: r["desde"])
    for a, b in zip(pres, pres[1:]):
        if a["hasta"] != b["desde"]:
            err(f"presidencias.csv: hueco o solapamiento entre "
                f"{a['nombre']} ({a['hasta']}) y {b['nombre']} ({b['desde']})")

    # -------------------------------------------------------------- salida
    print(f"eventos: {len(filas)}  ·  fichas: "
          f"{len(list((H / 'fichas').glob('[!_]*.md')))}  ·  "
          f"presidencias: {len(pres)}  ·  referencias.bib: {len(bib)} claves")
    sin_ver = sum(1 for f in filas if f["verificado"] == "no")
    print(f"sin verificar: {sin_ver}/{len(filas)} eventos")
    for a in avisos:
        print(f"  aviso  · {a}")
    for e in errores:
        print(f"  ERROR  · {e}")
    print("OK" if not errores else f"{len(errores)} error(es)")
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())
