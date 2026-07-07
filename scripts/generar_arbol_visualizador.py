#!/usr/bin/env python3
"""generar_arbol_visualizador — vuelca el catálogo curado al árbol del visualizador.

La fuente de verdad es `cueva/datos/catalogo.json` (9 familias). Este script emite el
literal `const CATALOG = [...]` en el estilo JS que ya usa el visualizador (comillas
simples, claves sin comillas — así el generador de datos de TF sigue funcionando sin
cambios) y lo inyecta en `visualizador_template.html` entre marcadores.

Flujo para cambiar la organización de las series:
    1. Editar `cueva/datos/catalogo.json`.
    2. python scripts/generar_arbol_visualizador.py      # actualiza el template
    3. (en la carpeta del Trabajo Final) python notebooks/generar_visualizador.py  # embebe datos

`series.py` (agentes + API + drawer) lee el mismo JSON directamente: una sola taxonomía.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cueva import config  # noqa: E402

RUTA_CATALOGO = Path(__file__).resolve().parent.parent / "cueva" / "datos" / "catalogo.json"
MARCA_INI = "/*__CATALOG_INICIO__*/"
MARCA_FIN = "/*__CATALOG_FIN__*/"
# claves cuyo valor SIEMPRE es string (se emiten con comillas simples)
_CLAVES = ("grp", "clr", "sub", "id", "label", "unit", "freq", "file", "dateCol", "valCol")


def _esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace("'", "\\'")


def _emit(v, nivel: int) -> str:
    """Serializa dict/list/str al estilo JS del visualizador (claves bare, strings ''')."""
    ind = "  " * nivel
    ind2 = "  " * (nivel + 1)
    if isinstance(v, str):
        return f"'{_esc(v)}'"
    if isinstance(v, list):
        if not v:
            return "[]"
        partes = [f"{ind2}{_emit(x, nivel + 1)}" for x in v]
        return "[\n" + ",\n".join(partes) + f"\n{ind}]"
    if isinstance(v, dict):
        partes = []
        for k, val in v.items():
            partes.append(f"{k}:{_emit(val, nivel + 1)}")
        return "{ " + ", ".join(partes) + " }"
    # números o booleanos (no debería haber, pero por las dudas)
    return json.dumps(v, ensure_ascii=False)


def _bloque_catalog(familias: list) -> str:
    cuerpo = ",\n\n".join("  " + _emit(f, 1) for f in familias)
    aviso = (
        f"{MARCA_INI}\n"
        "/* GENERADO desde cueva/datos/catalogo.json — NO editar a mano.\n"
        "   Editá el JSON y corré: python scripts/generar_arbol_visualizador.py */\n"
        "const CATALOG = [\n" + cuerpo + "\n];\n" + MARCA_FIN
    )
    return aviso


def _rango_catalog_actual(html: str) -> tuple[int, int]:
    """Devuelve (inicio, fin) del bloque a reemplazar: región marcada o `const CATALOG=[...]`."""
    if MARCA_INI in html and MARCA_FIN in html:
        i = html.index(MARCA_INI)
        j = html.index(MARCA_FIN) + len(MARCA_FIN)
        return i, j
    # primer run: localizar `const CATALOG = [ ... ];` por conteo de corchetes
    i = html.index("const CATALOG = [")
    k = html.index("[", i)
    prof, en_str, m = 0, False, k
    while m < len(html):
        c = html[m]
        if en_str:
            if c == "\\":
                m += 2
                continue
            if c == "'":
                en_str = False
        else:
            if c == "'":
                en_str = True
            elif c == "[":
                prof += 1
            elif c == "]":
                prof -= 1
                if prof == 0:
                    fin = m + 1
                    if html[fin : fin + 1] == ";":
                        fin += 1
                    return i, fin
        m += 1
    raise ValueError("no se pudo delimitar el CATALOG en el template")


def main() -> int:
    doc = json.loads(RUTA_CATALOGO.read_text(encoding="utf-8"))
    familias = doc.get("familias", doc if isinstance(doc, list) else [])
    if not familias:
        print("[!] catalogo.json vacío o sin 'familias'")
        return 1

    tf = config.carpeta_trabajo_final()
    if not tf:
        print("[!] No encuentro la carpeta del Trabajo Final (config.carpeta_trabajo_final()).")
        print("    Configurá CUEVA_TRABAJO_FINAL o cueva.local.toml.")
        return 1
    template = tf / "notebooks" / "visualizador_template.html"
    if not template.exists():
        print(f"[!] No existe {template}")
        return 1

    html = template.read_text(encoding="utf-8")
    ini, fin = _rango_catalog_actual(html)
    nuevo = html[:ini] + _bloque_catalog(familias) + html[fin:]
    template.write_text(nuevo, encoding="utf-8")

    n_fam = len(familias)
    print(f"[OK] Árbol inyectado en {template.name}: {n_fam} familias.")
    print("    Ahora, en la carpeta del Trabajo Final:  python notebooks/generar_visualizador.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
