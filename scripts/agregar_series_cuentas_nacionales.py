"""agregar_series_cuentas_nacionales.py — completa la familia Actividad y Cuentas Nacionales.

Hace dos cosas sobre `cueva/datos/catalogo.json`:

1. **Renombra y fusiona los subgrupos.** Se sacan de la etiqueta los términos «constante»,
   «corriente», «apertura» y «(PBI)»: la columna Unidad ya dice si la serie está a precios
   de un año de referencia (`Mill. ARS 2004`) o a precios corrientes (`Mill. ARS`). Los
   subgrupos que solo se distinguían por eso quedan fusionados en uno.
2. **Agrega las series que estaban en los cuadros del INDEC y no en el catálogo**, apuntando
   a los CSV que produce `scripts/ingestar_cuentas_nacionales.py`.

Simula por defecto; escribe con `--aplicar`.

    python scripts/agregar_series_cuentas_nacionales.py
    python scripts/agregar_series_cuentas_nacionales.py --aplicar
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CATALOGO = RAIZ / "cueva" / "datos" / "catalogo.json"
FAMILIA = "Actividad y Cuentas Nacionales"
HOY = "2026-08-29"
URL_CN = "https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-9-47"
URL_EMAE = "https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-9-48"
URL_UCI = "https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-6-15"
SCRIPT = "scripts/ingestar_cuentas_nacionales.py"

# --------------------------------------------------------------- subgrupos

RENOMBRES = {
    "Nivel de Actividad (PBI)": "Nivel de Actividad",
    "EMAE — Sectores (apertura)": "EMAE por sector",
    "Oferta y Demanda — Constante 2004": "Oferta y Demanda",
    "Oferta y Demanda — Corriente (nominal)": "Oferta y Demanda",
    "PBI por Sector — Constante 2004": "PBI por sector",
    "PBI por Sector — Corriente (nominal)": "PBI por sector",
    "PBI por Sector — Precios Implícitos": "PBI por sector — Precios Implícitos",
    "FBKF Detalle — Constante 2004": "FBKF Detalle",
    "FBKF Detalle — Corriente (nominal)": "FBKF Detalle",
}

ORDEN = [
    "Nivel de Actividad",
    "EMAE — Nivel General",
    "EMAE por sector",
    "Utilización de la Capacidad Instalada",
    "Índice Líder (UTDT)",
    "Oferta y Demanda",
    "Oferta y Demanda — Desestacionalizada",
    "Oferta y Demanda — Precios Implícitos",
    "PBI por sector",
    "PBI por sector — Precios Implícitos",
    "VAB por rama",
    "VAB por rama — Índice de Volumen Físico",
    "VAB por rama — Precios Implícitos",
    "VBP por rama",
    "FBKF Detalle",
    "FBKF Detalle — Precios Implícitos",
]

# --------------------------------------------------------------- vocabulario

# (columna del CSV, etiqueta). El orden es el del cuadro del INDEC.
RAMAS = [
    ("total", "VAB total"),
    ("agro", "A — Agro"),
    ("agro_cultivos", "Cultivos agrícolas"),
    ("agro_animales", "Cría de animales"),
    ("agro_serv", "Servicios agrícolas y pecuarios"),
    ("agro_caza", "Caza y servicios conexos"),
    ("agro_construcciones", "Construcciones agropecuarias"),
    ("agro_silvicultura", "Silvicultura y extracción de madera"),
    ("pesca", "B — Pesca"),
    ("mineria", "C — Minería"),
    ("min_petroleo_gas", "Petróleo, gas y carbón"),
    ("min_metaliferos", "Minerales metalíferos y canteras n.c.p."),
    ("industria", "D — Industria"),
    ("ind_alimentos", "Alimentos y bebidas"),
    ("ind_tabaco", "Tabaco"),
    ("ind_textiles", "Productos textiles"),
    ("ind_prendas", "Prendas de vestir y pieles"),
    ("ind_cueros", "Cueros y calzado"),
    ("ind_madera", "Madera y corcho"),
    ("ind_papel", "Papel y productos de papel"),
    ("ind_edicion", "Edición e impresión"),
    ("ind_refinacion", "Refinación del petróleo y coque"),
    ("ind_quimicos", "Sustancias y productos químicos"),
    ("ind_caucho", "Caucho y plástico"),
    ("ind_minerales", "Minerales no metálicos"),
    ("ind_metales", "Metales comunes"),
    ("ind_prod_metal", "Productos de metal"),
    ("ind_maquinaria", "Maquinaria y equipo n.c.p."),
    ("ind_maq_oficina", "Maquinaria de oficina e informática"),
    ("ind_maq_electrica", "Maquinaria y aparatos eléctricos"),
    ("ind_radio_tv", "Radio, TV y comunicaciones"),
    ("ind_instrumentos", "Instrumentos médicos y de precisión"),
    ("ind_automotriz", "Vehículos automotores y remolques"),
    ("ind_transporte_ncp", "Equipo de transporte n.c.p."),
    ("ind_muebles", "Muebles y colchones"),
    ("ind_reciclamiento", "Reciclamiento"),
    ("ind_reparacion", "Reparación e instalación de maquinaria"),
    ("elect_gas_agua", "E — Elect/Gas/Agua"),
    ("ee_electricidad", "Energía eléctrica"),
    ("ee_gas", "Gas"),
    ("ee_agua", "Agua"),
    ("construccion", "F — Construcción"),
    ("comercio", "G — Comercio"),
    ("hoteles", "H — Hoteles/Restaurantes"),
    ("hot_hoteles", "Hoteles y hospedaje"),
    ("hot_restaurantes", "Restaurantes, bares y cantinas"),
    ("transporte", "I — Transporte y Comun."),
    ("tr_transporte", "Transporte"),
    ("tr_comunicaciones", "Comunicaciones"),
    ("intermediacion_fin", "J — Interm. Financiera"),
    ("fin_intermediacion", "Intermediación financiera"),
    ("fin_seguros", "Seguros"),
    ("fin_auxiliares", "Servicios auxiliares financieros"),
    ("inmobiliarias", "K — Inmobiliarias"),
    ("inmo_inmobiliarios", "Servicios inmobiliarios"),
    ("inmo_resto", "Inmobiliarias y empresariales — resto"),
    ("admin_publica", "L — Admin. Pública"),
    ("ensenanza", "M — Enseñanza"),
    ("ense_publica", "Enseñanza pública"),
    ("ense_privada", "Enseñanza privada"),
    ("salud", "N — Salud"),
    ("salud_publica", "Salud pública"),
    ("salud_privada", "Salud privada"),
    ("otros_servicios", "O — Otros Servicios"),
    ("otr_saneamiento", "Saneamiento y desperdicios"),
    ("otr_asociaciones", "Asociaciones"),
    ("otr_culturales", "Servicios culturales y deportivos"),
    ("hogares_dom", "P — Hogares Dom."),
]

# Ramas que el catálogo ya tiene abiertas (nivel letra) en constante y corriente.
YA_LETRA = {
    "total", "agro", "pesca", "mineria", "industria", "elect_gas_agua", "construccion",
    "comercio", "hoteles", "transporte", "intermediacion_fin", "inmobiliarias",
    "admin_publica", "ensenanza", "salud", "otros_servicios", "hogares_dom",
}
# Ramas que ya tienen índice de precios implícitos (sec_p_*).
YA_IPI = {"total", "agro", "industria", "construccion", "comercio"}

UCI_BLOQUES = [
    ("nivel_general", "uci_ng", "Nivel general"),
    ("alimentos_bebidas", "uci_alimentos", "Alimentos y bebidas"),
    ("tabaco", "uci_tabaco", "Tabaco"),
    ("textiles", "uci_textiles", "Textiles"),
    ("papel_carton", "uci_papel", "Papel y cartón"),
    ("edicion_impresion", "uci_edicion", "Edición e impresión"),
    ("refinacion_petroleo", "uci_refinacion", "Refinación del petróleo"),
    ("quimicos", "uci_quimicos", "Sustancias y productos químicos"),
    ("caucho_plastico", "uci_caucho", "Caucho y plástico"),
    ("minerales_no_metalicos", "uci_minerales", "Minerales no metálicos"),
    ("metalicas_basicas", "uci_metalicas", "Industrias metálicas básicas"),
    ("automotriz", "uci_automotriz", "Industria automotriz"),
    ("metalmecanica", "uci_metalmecanica", "Metalmecánica excl. automotriz"),
]

FBKF_IPI = [
    ("fbkf_total", "fbkf_p_tot", "IPI FBKF Total"),
    ("construcciones", "fbkf_p_cons", "IPI Construcciones"),
    ("otras_construcciones", "fbkf_p_otrcons", "IPI Otras Construcciones"),
    ("maq_equipo", "fbkf_p_mq", "IPI Maquinaria y Equipo"),
    ("maq_nacional", "fbkf_p_mqn", "IPI Maq. Nacional"),
    ("maq_importado", "fbkf_p_mqi", "IPI Maq. Importada"),
    ("eq_transporte", "fbkf_p_tr", "IPI Equipo Transporte"),
    ("transp_nacional", "fbkf_p_trn", "IPI Eq. Transporte Nacional"),
    ("transp_importado", "fbkf_p_tri", "IPI Eq. Transporte Importado"),
    ("otros_activos", "fbkf_p_otr", "IPI Otros Activos"),
]

DESEST = [
    ("pbi", "od_d_pbi", "PBI"),
    ("impo", "od_d_impo", "Importaciones"),
    ("consumo_priv", "od_d_cpriv", "Consumo Privado"),
    ("consumo_pub", "od_d_cpub", "Consumo Público"),
    ("fbkf", "od_d_fbkf", "FBKF"),
    ("expo", "od_d_expo", "Exportaciones"),
]


def _proc(definicion: str, url: str) -> dict:
    return {
        "verificado": HOY,
        "fuente": "indec",
        "definicion": definicion,
        "url_humana": url,
        "script": SCRIPT,
        "confianza": "alta",
    }


def _item(sid, label, archivo, col, unidad, freq, definicion, url=URL_CN) -> dict:
    return {
        "id": sid,
        "label": label,
        "file": archivo,
        "dateCol": "fecha",
        "valCol": col,
        "unit": unidad,
        "freq": freq,
        "proc": _proc(definicion, url),
    }


def nuevas() -> list[tuple[str, dict]]:
    """(subgrupo, item) para cada serie que falta."""
    out: list[tuple[str, dict]] = []
    D_OD = "Cuenta de oferta y demanda globales de las cuentas nacionales."
    D_SEC = "PBI por categoría de tabulación, cuentas nacionales."
    D_VAB = "Valor agregado bruto a precios básicos por rama de actividad económica."
    D_VBP = "Valor bruto de producción a precios básicos por rama de actividad económica."
    D_FBKF = "Formación bruta de capital fijo, cuentas nacionales."

    # EMAE tendencia-ciclo (M/Q/A, como las otras dos del nivel general)
    out.append(("EMAE — Nivel General", {
        "id": "emae_tc",
        "label": "EMAE (tendencia-ciclo)",
        "unit": "Índice base 2004=100",
        "sources": [
            {"freq": f, "file": a, "dateCol": "fecha", "valCol": "emae_tendencia_ciclo",
             "proc": _proc("Estimador Mensual de Actividad Económica, serie tendencia-ciclo, "
                           "índice base 2004 = 100.", URL_EMAE)}
            for f, a in [("M", "emae_nivel_general.csv"),
                         ("Q", "emae_nivel_general_trimestral.csv"),
                         ("A", "emae_nivel_general_anual.csv")]
        ],
    }))

    # Utilización de la capacidad instalada
    for col, sid, lab in UCI_BLOQUES:
        out.append(("Utilización de la Capacidad Instalada", _item(
            sid, lab, "uci_bloques.csv", col, "%", "M",
            "Utilización de la capacidad instalada en la industria, por bloque sectorial.",
            URL_UCI)))

    # Oferta y demanda: conceptos que faltaban
    for pref, arch, uni in [("od_c", "cn_oferta_demanda_constante.csv", "Mill. ARS 2004"),
                            ("od_n", "cn_oferta_demanda_corriente.csv", "Mill. ARS")]:
        out.append(("Oferta y Demanda", _item(
            f"{pref}_valiosos", "Objetos Valiosos", arch, "objetos_valiosos", uni, "Q", D_OD)))
        out.append(("Oferta y Demanda", _item(
            f"{pref}_discrep", "Discrepancia Estadística", arch, "discrepancia", uni, "Q", D_OD)))

    for col, sid, lab in [("oferta_global", "od_p_oferta", "IPI Oferta Global"),
                          ("demanda_global", "od_p_demanda", "IPI Demanda Global"),
                          ("var_existencias", "od_p_varex", "IPI Var. Existencias"),
                          ("objetos_valiosos", "od_p_valiosos", "IPI Objetos Valiosos"),
                          ("discrepancia", "od_p_discrep", "IPI Discrepancia Estadística")]:
        out.append(("Oferta y Demanda — Precios Implícitos", _item(
            sid, lab, "cn_oferta_demanda_ipi.csv", col, "Índice", "Q", D_OD)))

    # Oferta y demanda desestacionalizada
    for col, sid, lab in DESEST:
        out.append(("Oferta y Demanda — Desestacionalizada", _item(
            sid, lab, "cn_oferta_demanda_desest.csv", col, "Mill. ARS 2004", "Q",
            "Oferta y demanda globales, serie desestacionalizada del INDEC.")))

    # PBI por sector: impuestos que faltaban
    out.append(("PBI por sector", _item(
        "sec_c_impnet", "Impuestos netos de subsidios", "cn_pbi_categoria_constante.csv",
        "impuestos_netos", "Mill. ARS 2004", "Q", D_SEC)))
    out.append(("PBI por sector", _item(
        "sec_n_impnet", "Impuestos netos de subsidios", "cn_pbi_categoria_corriente.csv",
        "impuestos_netos", "Mill. ARS", "Q", D_SEC)))
    for col, sid, lab in [("impuestos_netos", "sec_p_impnet", "IPI Impuestos netos de subsidios"),
                          ("iva", "sec_p_iva", "IPI IVA"),
                          ("imp_importaciones", "sec_p_impimp", "IPI Imp. Importaciones")]:
        out.append(("PBI por sector — Precios Implícitos", _item(
            sid, lab, "cn_pbi_categoria_ipi.csv", col, "Índice", "Q", D_SEC)))

    # FBKF: aperturas que faltaban + índices de precios implícitos
    for pref, arch, uni in [("fbkf_c", "cn_fbkf_constante.csv", "Mill. ARS 2004"),
                            ("fbkf_n", "cn_fbkf_corriente.csv", "Mill. ARS")]:
        for col, suf, lab in [("otras_construcciones", "otrcons", "Otras Construcciones"),
                              ("transp_nacional", "trn", "Eq. Transporte Nacional"),
                              ("transp_importado", "tri", "Eq. Transporte Importado")]:
            out.append(("FBKF Detalle", _item(
                f"{pref}_{suf}", lab, arch, col, uni, "Q", D_FBKF)))
    for col, sid, lab in FBKF_IPI:
        out.append(("FBKF Detalle — Precios Implícitos", _item(
            sid, lab, "cn_fbkf_ipi.csv", col, "Índice", "Q", D_FBKF)))

    # VAB por rama
    for col, lab in RAMAS:
        if col not in YA_LETRA:
            out.append(("VAB por rama", _item(
                f"vab_c_{col}", lab, "cn_vab_rama_constante.csv", col,
                "Mill. ARS 2004", "Q", D_VAB)))
            out.append(("VAB por rama", _item(
                f"vab_n_{col}", lab, "cn_vab_rama_corriente.csv", col,
                "Mill. ARS", "Q", D_VAB)))
        out.append(("VAB por rama — Índice de Volumen Físico", _item(
            f"vab_q_{col}", lab, "cn_vab_rama_ivf.csv", col, "Índice base 2004=100", "Q",
            "Índice de volumen físico del VAB a precios básicos, por rama de actividad.")))
        if col not in YA_IPI:
            out.append(("VAB por rama — Precios Implícitos", _item(
                f"vab_p_{col}", f"IPI {lab}", "cn_vab_rama_ipi.csv", col,
                "Índice", "Q", D_VAB)))

    # VBP por rama (anual)
    for col, lab in RAMAS:
        etq = "VBP total" if col == "total" else lab
        out.append(("VBP por rama", _item(
            f"vbp_c_{col}", etq, "cn_vbp_rama_constante.csv", col,
            "Mill. ARS 2004", "A", D_VBP)))
        out.append(("VBP por rama", _item(
            f"vbp_n_{col}", etq, "cn_vbp_rama_corriente.csv", col,
            "Mill. ARS", "A", D_VBP)))

    return out


# --------------------------------------------------------------- aplicación

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()

    cat = json.loads(CATALOGO.read_text(encoding="utf-8"))
    fam = next(f for f in cat["familias"] if f["grp"] == FAMILIA)

    ids = set()
    for f in cat["familias"]:
        pila = list(f.get("subs", []))
        while pila:
            n = pila.pop()
            pila.extend(n.get("subs", []) or [])
            for it in n.get("items", []) or []:
                ids.add(it["id"])
                pila.extend(it.get("children", []) or [])

    # 1. renombrar / fusionar
    grupos: dict[str, list] = {s: [] for s in ORDEN}
    for sub in fam["subs"]:
        destino = RENOMBRES.get(sub["sub"], sub["sub"])
        if destino not in grupos:
            raise SystemExit(f"subgrupo sin lugar en ORDEN: {destino!r}")
        grupos[destino].extend(sub["items"])
        if destino != sub["sub"]:
            print(f"  subgrupo  {sub['sub']!r}\n         -> {destino!r}")

    # 2. agregar las que faltan
    agregadas, repetidas = 0, []
    for destino, item in nuevas():
        if item["id"] in ids:
            repetidas.append(item["id"])
            continue
        grupos[destino].append(item)
        ids.add(item["id"])
        agregadas += 1

    fam["subs"] = [{"sub": s, "items": grupos[s]} for s in ORDEN if grupos[s]]

    print(f"\n  subgrupos: {len(fam['subs'])}")
    for s in fam["subs"]:
        print(f"    {len(s['items']):4d}  {s['sub']}")
    print(f"\n  series nuevas: {agregadas}   familia: {sum(len(s['items']) for s in fam['subs'])}")
    if repetidas:
        print(f"  ids ya existentes, salteados: {repetidas}")

    if args.aplicar:
        CATALOGO.write_text(json.dumps(cat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"\n  escrito {CATALOGO.relative_to(RAIZ)}")
    else:
        print("\n  (simulación — corré con --aplicar para escribir)")


if __name__ == "__main__":
    main()
