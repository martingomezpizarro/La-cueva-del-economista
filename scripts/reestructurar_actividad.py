"""reestructurar_actividad.py — la familia Actividad en cuatro niveles.

Decisión de Martín (2026-08-29). La presentación de las series en La Cueva tiene **cuatro
niveles fijos**:

    Familia › Grupo › Subgrupo › Serie

y la unidad **no es un nivel**: es la columna `Unidad` que ya existe. Una misma serie aparece
dos veces en el catálogo —«Mill. ARS 2004» y «Mill. ARS», una arriba de la otra— y en la
plataforma se resuelve con el botón «Precios: Constantes | Corrientes», igual que la frecuencia.

Ejemplo del caso que motivó esto:

    Familia    Actividad y Cuentas Nacionales
    Grupo      Valor Agregado Bruto por rama
    Subgrupo   Electricidad, gas y agua
    Serie      Captación, depuración y distribución de agua
    Unidad     Mill. ARS 2004  ·  Mill. ARS

El nombre de la serie es **literalmente** el del cuadro del INDEC. Antes decía «Agua».

Qué hace:
  · toma los nombres textuales de `cn_nombres.csv` (los escribe `ingestar_cuentas_nacionales.py`)
  · asigna Grupo y Subgrupo a cada columna con las reglas de abajo
  · cataloga las columnas que hoy quedan afuera, respetando la convención de id de cada grupo

Qué NO hace: tocar los `id` ni los `valCol`. Son el contrato con los proyectos guardados de
`data/proyectos/` y con el visualizador. Cambia cómo se ordenan y cómo se llaman, no qué son.

Uso:
    python scripts/reestructurar_actividad.py
    python scripts/reestructurar_actividad.py --ver "Valor Agregado"
    python scripts/reestructurar_actividad.py --aplicar
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
CATALOGO = RAIZ / "cueva" / "datos" / "catalogo.json"
DATOS = RAIZ / "data" / "series" / "1.Actividad y Cuentas Nacionales"
NOMBRES = DATOS / "cn_nombres.csv"
DETALLE = RAIZ / "docs" / "reestructura_actividad.csv"

FAMILIA = "Actividad y Cuentas Nacionales"
TOTAL = "Total"

LETRAS = ["agro", "pesca", "mineria", "industria", "elect_gas_agua", "construccion", "comercio",
          "hoteles", "transporte", "intermediacion_fin", "inmobiliarias", "admin_publica",
          "ensenanza", "salud", "otros_servicios", "hogares_dom"]

# El prefijo de la columna ya dice de qué letra cuelga la rama: la jerarquía no hay que
# inventarla, estaba codificada ahí desde la ingesta.
PREFIJOS = {"agro_": "agro", "min_": "mineria", "ind_": "industria", "ee_": "elect_gas_agua",
            "hot_": "hoteles", "tr_": "transporte", "fin_": "intermediacion_fin",
            "inmo_": "inmobiliarias", "ense_": "ensenanza", "salud_": "salud",
            "otr_": "otros_servicios"}


def _sin_letra(nombre: str) -> str:
    """Saca el «A - » del cuadro de PBI por categoría. La letra identifica la categoría de
    tabulación en ESE cuadro; como nombre de la categoría sobra, y hace que la misma
    «Agricultura, ganadería, caza y silvicultura» se escriba distinto según el cuadro."""
    return re.sub(r"^[A-Z] - ", "", nombre)


def _ubic_rama(col: str, nombre: dict[str, str]) -> tuple[str, str]:
    """(subgrupo, serie) de una columna de los cuadros por rama.

    El subgrupo es la categoría agregada —«Electricidad, gas y agua»— y la serie es el concepto
    que cuelga de ella. Cuando el concepto ES el agregado de su categoría, la serie se llama
    «Total»: por eso hay subgrupos que solo tienen un Total (Pesca, Construcción, Comercio,
    Administración pública, Hogares no abren en ramas)."""
    if col == "total" or col in LETRAS:
        return nombre[col], TOTAL
    for pre, padre in PREFIJOS.items():
        if col.startswith(pre):
            return nombre[padre], nombre[col]
    return nombre[col], TOTAL


def _ubic_pbi_cat(col: str, nombre: dict[str, str]) -> tuple[str, str]:
    """El cuadro que va del VAB al PBI: el subgrupo «Producto Interno Bruto» tiene como series
    los componentes que hacen ese puente; cada letra es su propia categoría."""
    if col in ("vab", "impuestos_netos", "iva", "imp_importaciones"):
        return nombre["pbi"], nombre[col]
    if col == "pbi":
        return nombre["pbi"], TOTAL
    return _sin_letra(nombre[col]), TOTAL


def _ubic_od(col: str, nombre: dict[str, str]) -> tuple[str, str]:
    lado = "Oferta Global" if col in ("pbi", "impo", "oferta_global") else "Demanda Global"
    if col in ("oferta_global", "demanda_global"):
        return lado, TOTAL
    return lado, nombre[col]


def _ubic_fbkf(col: str, nombre: dict[str, str]) -> tuple[str, str]:
    """Acá el subgrupo no es cosmético: el INDEC escribe «Nacional» e «Importado» dos veces, una
    bajo Maquinaria y equipo y otra bajo Equipo de transporte. Sin la categoría son cuatro series
    con dos nombres."""
    if col.startswith("maq_") and col != "maq_equipo":
        return nombre["maq_equipo"], nombre[col]
    if col.startswith("transp_"):
        return nombre["eq_transporte"], nombre[col]
    if col == "otras_construcciones":
        return nombre["construcciones"], nombre[col]
    return nombre[col], TOTAL


def _ubic_uci(col: str, nombre: dict[str, str]) -> tuple[str, str]:
    return nombre["nivel_general"], (TOTAL if col == "nivel_general" else nombre[col])


def _ubic_emae(col: str, nombre: dict[str, str]) -> tuple[str, str]:
    return "Estimador Mensual de Actividad Económica", nombre[col]


def _ubic_emae_sec(col: str, nombre: dict[str, str]) -> tuple[str, str]:
    return nombre[col], TOTAL


# (Grupo, {archivo: unidad por defecto para las series nuevas}, regla de subgrupo)
GRUPOS = [
    ("Valor Agregado Bruto por rama",
     {"cn_vab_rama_constante.csv": "Mill. ARS 2004", "cn_vab_rama_corriente.csv": "Mill. ARS"},
     _ubic_rama),
    ("Valor Bruto de Producción por rama",
     {"cn_vbp_rama_constante.csv": "Mill. ARS 2004", "cn_vbp_rama_corriente.csv": "Mill. ARS"},
     _ubic_rama),
    ("Índice de Volumen Físico por rama",
     {"cn_vab_rama_ivf.csv": "Índice base 2004=100"}, _ubic_rama),
    ("Índice de Precios Implícitos por rama",
     {"cn_vab_rama_ipi.csv": "Índice"}, _ubic_rama),
    ("PBI por categoría de tabulación",
     {"cn_pbi_categoria_constante.csv": "Mill. ARS 2004",
      "cn_pbi_categoria_corriente.csv": "Mill. ARS"}, _ubic_pbi_cat),
    ("PBI por categoría de tabulación — Precios Implícitos",
     {"cn_pbi_categoria_ipi.csv": "Índice"}, _ubic_pbi_cat),
    ("Oferta y Demanda Globales",
     {"cn_oferta_demanda_constante.csv": "Mill. ARS 2004",
      "cn_oferta_demanda_corriente.csv": "Mill. ARS"}, _ubic_od),
    ("Oferta y Demanda Globales — Desestacionalizada",
     {"cn_oferta_demanda_desest.csv": "Mill. ARS 2004"}, _ubic_od),
    ("Oferta y Demanda Globales — Precios Implícitos",
     {"cn_oferta_demanda_ipi.csv": "Índice"}, _ubic_od),
    ("Formación Bruta de Capital Fijo",
     {"cn_fbkf_constante.csv": "Mill. ARS 2004", "cn_fbkf_corriente.csv": "Mill. ARS"},
     _ubic_fbkf),
    ("Formación Bruta de Capital Fijo — Precios Implícitos",
     {"cn_fbkf_ipi.csv": "Índice"}, _ubic_fbkf),
    ("Utilización de la Capacidad Instalada", {"uci_bloques.csv": "%"}, _ubic_uci),
    ("EMAE — Nivel General", {"emae_nivel_general.csv": "Índice base 2004=100"}, _ubic_emae),
    # Solo el archivo mensual: el trimestral y el anual son otras FRECUENCIAS de la misma serie
    # (viven en `sources`), no otras unidades. Las series ya existen y conservan sus tres fuentes.
    ("EMAE por sector", {"emae_sectorial_mensual.csv": "Índice base 2004=100"}, _ubic_emae_sec),
]

# Columnas que un cuadro trae pero que ya están catalogadas en otro grupo. Sin esto el script
# crearía `od_c_pbi` y `sec_c_pbi` como series nuevas, duplicando el PBI que ya vive en «Nivel de
# Actividad» y que ahora lee de estos mismos archivos.
SALTAR = {
    # El PBI del cuadro de categorías es el mismo número que el de Oferta y Demanda, donde ya vive
    # como `pbi_constante` / `pbi_nominal`. Se cataloga una sola vez, en el cuadro que lo encabeza.
    "cn_pbi_categoria_constante.csv": {"pbi"}, "cn_pbi_categoria_corriente.csv": {"pbi"},
}

# Duplicados a eliminar: los creó la primera corrida de este script, antes de repuntar
# `pbi_constante` / `pbi_nominal` a estos mismos archivos. Son el mismo número con otro id y no
# están en ningún proyecto guardado (no existían hace una hora).
BORRAR = {"od_c_pbi", "od_n_pbi", "sec_c_pbi", "sec_n_pbi"}

# Subgrupos que no salen de los cuadros de `cn_nombres.csv` porque su archivo todavía no está
# en la carpeta (EMAE sectorial, PBI nivel, Índice Líder). No se tocan: se reubican tal cual en
# el esquema de cuatro niveles y se les deja el label que tienen. Si no estuvieran acá,
# `aplicar()` los borraría al reescribir `subs`.
RESTO = {
    "Nivel de Actividad": ("Nivel de Actividad", "Producto Interno Bruto"),
    "Índice Líder (UTDT)": ("Índice Líder (UTDT)", "Índice Líder"),
}

PREFIJO_ID = {
    "cn_vab_rama_constante.csv": "vab_c_", "cn_vab_rama_corriente.csv": "vab_n_",
    "cn_vab_rama_ivf.csv": "vab_q_", "cn_vab_rama_ipi.csv": "vab_p_",
    "cn_vbp_rama_constante.csv": "vbp_c_", "cn_vbp_rama_corriente.csv": "vbp_n_",
    "cn_pbi_categoria_constante.csv": "sec_c_", "cn_pbi_categoria_corriente.csv": "sec_n_",
    "cn_pbi_categoria_ipi.csv": "sec_p_",
    "cn_oferta_demanda_constante.csv": "od_c_", "cn_oferta_demanda_corriente.csv": "od_n_",
    "cn_oferta_demanda_ipi.csv": "od_p_", "cn_oferta_demanda_desest.csv": "od_d_",
    "cn_fbkf_constante.csv": "fbkf_c_", "cn_fbkf_corriente.csv": "fbkf_n_",
    "cn_fbkf_ipi.csv": "fbkf_p_", "uci_bloques.csv": "uci_", "emae_nivel_general.csv": "emae_",
}


def _catalogo() -> dict:
    return json.loads(CATALOGO.read_text(encoding="utf-8"))


def _actual(cat: dict) -> dict[tuple[str, str], dict]:
    """(archivo, valCol) → el item tal como está hoy, más el subgrupo del que cuelga."""
    fam = next(f for f in cat["familias"] if f["grp"] == FAMILIA)
    idx: dict[tuple[str, str], dict] = {}

    def bajar(items, sub):
        for it in items:
            for fu in (it.get("sources") or [it]):
                if fu.get("file"):
                    idx[(fu["file"], fu.get("valCol"))] = {"item": it, "sub_viejo": sub}
            bajar(it.get("children") or [], sub)

    for s in fam["subs"]:
        bajar(s["items"], s["sub"])
    return idx


def _ids_ocupados(cat: dict) -> set[str]:
    vistos: set[str] = set()

    def recorrer(nodo):
        for clave in ("subs", "items", "children"):
            for hijo in nodo.get(clave, []) or []:
                if isinstance(hijo, dict):
                    if "id" in hijo:
                        vistos.add(hijo["id"])
                    recorrer(hijo)

    for fam in cat["familias"]:
        recorrer(fam)
    return vistos


def _sufijos(actual: dict) -> dict[str, dict[str, str]]:
    """columna → sufijo de id, aprendido de lo ya catalogado, por raíz de prefijo.

    Los ids viejos no son uniformes (`sec_c_indus` para `industria`, `sec_c_eega` para
    `elect_gas_agua`). Antes de inventar uno se mira cómo se llamó esa columna en el resto del
    grupo, para no dejar dos convenciones conviviendo en el mismo subgrupo."""
    mapa: dict[str, dict[str, str]] = {}
    for (arch, col), info in actual.items():
        pre = PREFIJO_ID.get(arch)
        sid = info["item"]["id"]
        if not pre or not sid.startswith(pre):
            continue
        raiz = pre[: pre.index("_") + 1] if "_" in pre else pre
        mapa.setdefault(raiz, {})[col] = sid[len(pre):]
    return mapa


def proponer() -> pd.DataFrame:
    nombres = pd.read_csv(NOMBRES).fillna("")
    por_archivo = {a: dict(zip(g.columna, g.nombre_indec)) for a, g in nombres.groupby("archivo")}
    cat = _catalogo()
    actual = _actual(cat)
    sufijos = _sufijos(actual)

    filas = []
    for grupo, archivos, ubic_de in GRUPOS:
        nombre = por_archivo.get(next(iter(archivos)), {})
        for col in nombre:
            if all(col in SALTAR.get(a, ()) for a in archivos):
                continue
            ubic = ubic_de(col, nombre)
            for arch, unidad in archivos.items():
                if col in SALTAR.get(arch, ()):
                    continue
                info = actual.get((arch, col))
                pre = PREFIJO_ID.get(arch, "")
                raiz = pre[: pre.index("_") + 1] if "_" in pre else pre
                sid = info["item"]["id"] if info else pre + sufijos.get(raiz, {}).get(col, col)
                filas.append({
                    "familia": FAMILIA, "grupo": grupo,
                    "subgrupo": ubic[0], "serie": ubic[1], "id": sid,
                    "unidad": info["item"].get("unit", unidad) if info else unidad,
                    "archivo": arch, "columna": col,
                    "estado": "existe" if info else "NUEVA",
                    "serie_vieja": info["item"].get("label", "") if info else "",
                    "subgrupo_viejo": info["sub_viejo"] if info else "",
                })
    return pd.DataFrame(filas)


def aplicar(df: pd.DataFrame) -> None:
    """Reescribe la familia con Grupo › Subgrupo › Serie, conservando el resto del item.

    El catálogo guarda un solo nivel de `subs`, así que cada bloque lleva `grupo` y `subgrupo`
    como campos nuevos y `sub` queda compuesto. Así `auditar_series.py`, `series.py` y el
    visualizador siguen andando sin tocarlos, y la planilla y la plataforma leen los campos
    nuevos. Cuando el visualizador entienda cuatro niveles nativos se cambia acá.

    Las series nuevas heredan la procedencia de una hermana del mismo archivo: son columnas del
    mismo cuadro, con la misma fuente, la misma URL y el mismo script. Inventarles un `proc`
    propio sería declarar algo que no se verificó; dejarlas sin él rompe `test_fuentes.py`."""
    cat = _catalogo()
    fam = next(f for f in cat["familias"] if f["grp"] == FAMILIA)
    fam_original = [dict(b) for b in fam["subs"]]
    viejos = _actual(cat)

    # Todas las series de un mismo archivo salen del mismo cuadro del INDEC y del mismo script,
    # así que comparten frecuencia y procedencia: se heredan de una hermana en vez de inventarlas.
    freq, proc = {}, {}
    for (arch, _), info in viejos.items():
        for fu in (info["item"].get("sources") or [info["item"]]):
            if fu.get("file") == arch:
                freq[arch] = fu.get("freq", "Q")
                if fu.get("proc") and arch not in proc:
                    proc[arch] = fu["proc"]

    bloques = []
    for (grupo, sub), g in df.groupby(["grupo", "subgrupo"], sort=False):
        items = []
        for _, r in g.iterrows():
            info = viejos.get((r.archivo, r.columna))
            if info:
                it = dict(info["item"])
                it["label"] = r.serie      # el nombre pasa a ser el del INDEC
                it["unit"] = r.unidad
                it.pop("children", None)   # la jerarquía ahora vive en Grupo › Subgrupo
            else:
                it = {"id": r.id, "label": r.serie, "unit": r.unidad, "file": r.archivo,
                      "dateCol": "fecha", "valCol": r.columna, "freq": freq.get(r.archivo, "Q")}
                if r.archivo in proc:
                    it["proc"] = dict(proc[r.archivo])
            items.append(it)
        bloques.append({"sub": f"{grupo} › {sub}", "grupo": grupo, "subgrupo": sub, "items": items})

    # Lo que no cubre ningún cuadro se reubica sin tocarlo: su archivo todavía no está en
    # data/series, así que no hay nombre del organismo del que sacar el label. Se respeta el
    # grupo/subgrupo que el bloque ya tenga; `RESTO` solo traduce los nombres previos a la
    # reestructura.
    cubiertos = {r.id for r in df.itertuples()}
    for b in fam_original:
        faltantes = [it for it in b["items"]
                     if it["id"] not in cubiertos and it["id"] not in BORRAR]
        if not faltantes:
            continue
        # RESTO se busca por el nombre viejo del bloque y también por el grupo ya reestructurado,
        # para que una segunda corrida no herede el subgrupo provisorio de la primera.
        grupo, sub = (RESTO.get(b["sub"]) or RESTO.get(b.get("grupo", ""))
                      or (b.get("grupo", b["sub"]), b.get("subgrupo", TOTAL)))
        bloques.append({"sub": f"{grupo} › {sub}", "grupo": grupo, "subgrupo": sub,
                        "items": faltantes})

    # Verificación dura: ningún id del catálogo viejo puede desaparecer sin estar en BORRAR.
    quedaron = {it["id"] for b in bloques for it in b["items"]}
    perdidos = sorted({it["id"] for b in fam_original for it in b["items"]} - quedaron - BORRAR)
    if perdidos:
        raise SystemExit(f"se perderían {len(perdidos)} series: {perdidos[:10]} — abortado")
    if BORRAR & quedaron:
        raise SystemExit(f"BORRAR no se aplicó: {sorted(BORRAR & quedaron)}")
    print(f"duplicados eliminados: {len(BORRAR)} ({', '.join(sorted(BORRAR))})")

    fam["subs"] = bloques
    CATALOGO.write_text(json.dumps(cat, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\ncatálogo reescrito: {len(bloques)} bloques · {len(df)} series en la familia")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--aplicar", action="store_true", help="reescribe el catálogo (por defecto simula)")
    ap.add_argument("--ver", default="", help="imprime el árbol de este grupo")
    args = ap.parse_args()

    df = proponer()
    nuevas = df[df.estado == "NUEVA"]
    choques = sorted(set(nuevas.id) & _ids_ocupados(_catalogo()))

    print(f"{df.grupo.nunique()} grupos · {len(df.groupby(['grupo', 'subgrupo']))} subgrupos"
          f" · {len(df)} filas de catálogo · {len(nuevas)} nuevas")
    print(f"ids nuevos que chocan con alguno existente: {len(choques)}"
          + (f"  → {choques}" if choques else "  (ninguno)") + "\n")
    for grupo, g in df.groupby("grupo", sort=False):
        print(f"  {grupo:54s} {g.subgrupo.nunique():3d} subg · {len(g):4d} filas"
              f" · {len(g[g.estado == 'NUEVA']):3d} nuevas")

    if args.ver:
        g = df[df.grupo.str.lower() == args.ver.lower()] if args.ver.lower() in set(df.grupo.str.lower()) else df[df.grupo.str.lower().str.startswith(args.ver.lower())]
        if g.empty:
            raise SystemExit(f"ningún grupo empieza con «{args.ver}»")
        print(f"\n=== {g.grupo.iloc[0]} ===")
        for sub, s in g.groupby("subgrupo", sort=False):
            print(f"\n  {sub}")
            for serie, v in s.groupby("serie", sort=False):
                us = " · ".join(f"{r.unidad}: {r.id}" + (" (nueva)" if r.estado == "NUEVA" else "")
                                for r in v.itertuples())
                print(f"    {serie}\n        {us}")

    df.to_csv(DETALLE, index=False)
    print(f"\nDetalle: {DETALLE.relative_to(RAIZ)}")

    if args.aplicar:
        aplicar(df)


if __name__ == "__main__":
    main()
