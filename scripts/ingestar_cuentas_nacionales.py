"""ingestar_cuentas_nacionales.py — pasa los cuadros del INDEC a CSV tidy.

Lee los .xls y .csv crudos de `data/series/Actividad y Cuentas Nacionales_Fuentes/` y escribe,
en `data/series/1.Actividad y Cuentas Nacionales/`, un CSV por cuadro con formato ancho:
`fecha` + una columna por concepto. Los trimestres se fechan en el ÚLTIMO mes del trimestre
(03/06/09/12), que es la convención del resto del catálogo.

Además escribe `cn_nombres.csv`: el nombre TEXTUAL que el INDEC le da a cada concepto, por
(archivo, columna). El encabezado del CSV tiene que ser un código corto —los nombres del INDEC
llevan comas y punto y coma, y `valCol` es el contrato con el catálogo—, así que el nombre largo
se guarda al lado en vez de perderse. Es lo que alimenta el `label` y la jerarquía del catálogo.

Uso:
    python scripts/ingestar_cuentas_nacionales.py
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
CRUDO = RAIZ / "data" / "series" / "Actividad y Cuentas Nacionales_Fuentes"
SALIDA = RAIZ / "data" / "series" / "1.Actividad y Cuentas Nacionales"
NOMBRES = SALIDA / "cn_nombres.csv"

OD = CRUDO / "sh_oferta_demanda_03_26.xls"
SEC = CRUDO / "sh_oferta_demanda_por_sector_03_26.xls"
DES = CRUDO / "sh_oferta_demanda_desestimado_03_26.xls"
UCI = CRUDO / "UCCI 04-26.xls"

PIE = ("(1)", "(2)", "(3)", "(4)", "(5)", "Nota", "Fuente", "Las variaciones")

MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
}


def _sin_tildes(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()


# ---------------------------------------------------------------- etiquetas

# Nombres de columna cortos y estables. El orden es el del cuadro.
OD_COLS = [
    "pbi", "impo", "oferta_global", "demanda_global", "consumo_priv", "consumo_pub",
    "expo", "fbkf", "var_existencias", "objetos_valiosos", "discrepancia",
]

PBI_CAT_COLS = [
    "pbi", "impuestos_netos", "iva", "imp_importaciones", "vab",
    "agro", "pesca", "mineria", "industria", "elect_gas_agua", "construccion",
    "comercio", "hoteles", "transporte", "intermediacion_fin", "inmobiliarias",
    "admin_publica", "ensenanza", "salud", "otros_servicios", "hogares_dom",
]

FBKF_COLS = [
    "fbkf_total", "construcciones", "otras_construcciones", "maq_equipo",
    "maq_nacional", "maq_importado", "eq_transporte", "transp_nacional",
    "transp_importado", "otros_activos",
]

RAMA_COLS = [
    "total", "agro", "agro_cultivos", "agro_animales", "agro_serv", "agro_caza",
    "agro_construcciones", "agro_silvicultura", "pesca", "mineria",
    "min_petroleo_gas", "min_metaliferos", "industria", "ind_alimentos",
    "ind_tabaco", "ind_textiles", "ind_prendas", "ind_cueros", "ind_madera",
    "ind_papel", "ind_edicion", "ind_refinacion", "ind_quimicos", "ind_caucho",
    "ind_minerales", "ind_metales", "ind_prod_metal", "ind_maquinaria",
    "ind_maq_oficina", "ind_maq_electrica", "ind_radio_tv", "ind_instrumentos",
    "ind_automotriz", "ind_transporte_ncp", "ind_muebles", "ind_reciclamiento",
    "ind_reparacion", "elect_gas_agua", "ee_electricidad", "ee_gas", "ee_agua",
    "construccion", "comercio", "hoteles", "hot_hoteles", "hot_restaurantes",
    "transporte", "tr_transporte", "tr_comunicaciones", "intermediacion_fin",
    "fin_intermediacion", "fin_seguros", "fin_auxiliares", "inmobiliarias",
    "inmo_inmobiliarios", "inmo_resto", "admin_publica", "ensenanza",
    "ense_publica", "ense_privada", "salud", "salud_publica", "salud_privada",
    "otros_servicios", "otr_saneamiento", "otr_asociaciones", "otr_culturales",
    "hogares_dom",
]

UCI_COLS = [
    "nivel_general", "alimentos_bebidas", "tabaco", "textiles", "papel_carton",
    "edicion_impresion", "refinacion_petroleo", "quimicos", "caucho_plastico",
    "minerales_no_metalicos", "metalicas_basicas", "automotriz", "metalmecanica",
]

DESEST_COLS = ["pbi", "impo", "consumo_priv", "consumo_pub", "fbkf", "expo"]


# ---------------------------------------------------------------- lectores

def _conceptos(d: pd.DataFrame) -> list[tuple[int, str]]:
    """(fila, nombre del INDEC) de cada concepto. Corta en el pie de cuadro.

    Devuelve también el TEXTO: es el nombre real de la serie y antes se descartaba."""
    filas = []
    for i in range(5, len(d)):
        v = d.iat[i, 0]
        if pd.isna(v):
            continue
        s = str(v).strip()
        if not s:
            continue
        if s.startswith(PIE):
            break
        filas.append((i, s))
    return filas


_NOMBRES: dict[str, dict[str, str]] = {}


def _registrar(cols: list[str], textos: list[str]) -> None:
    """Guarda el nombre del INDEC de cada columna del cuadro que se está leyendo."""
    _NOMBRES[_CUADRO[0]] = dict(zip(cols, textos))


_CUADRO = [""]  # cuadro que se está leyendo, para etiquetar los nombres


def _anios(d: pd.DataFrame) -> list[int]:
    crudos = [v for v in d.iloc[3].tolist() if pd.notna(v)]
    return [int(str(a).strip()[:4]) for a in crudos]


def _trimestral(ruta: Path, hoja: str, cols: list[str]) -> pd.DataFrame:
    """Cuadros con 22 años × (4 trimestres + Total + columna en blanco): paso 6."""
    d = pd.read_excel(ruta, sheet_name=hoja, header=None)
    pares = _conceptos(d)
    if len(pares) != len(cols):
        raise SystemExit(f"{ruta.name}/{hoja}: {len(pares)} conceptos, esperaba {len(cols)}")
    filas = [i for i, _ in pares]
    _registrar(cols, [t for _, t in pares])
    anios = _anios(d)
    fechas, datos = [], {c: [] for c in cols}
    for y, anio in enumerate(anios):
        for t in range(4):
            col = 1 + 6 * y + t
            valores = [d.iat[f, col] for f in filas]
            if all(pd.isna(v) for v in valores):
                continue
            fechas.append(f"{anio}-{3 * (t + 1):02d}-01")
            for c, v in zip(cols, valores):
                datos[c].append(v)
    return pd.DataFrame({"fecha": fechas, **datos})


def _anual(ruta: Path, hoja: str, cols: list[str]) -> pd.DataFrame:
    d = pd.read_excel(ruta, sheet_name=hoja, header=None)
    pares = _conceptos(d)
    if len(pares) != len(cols):
        raise SystemExit(f"{ruta.name}/{hoja}: {len(pares)} conceptos, esperaba {len(cols)}")
    filas = [i for i, _ in pares]
    _registrar(cols, [t for _, t in pares])
    anios = _anios(d)
    fechas, datos = [], {c: [] for c in cols}
    for y, anio in enumerate(anios):
        col = 1 + y
        valores = [d.iat[f, col] for f in filas]
        if all(pd.isna(v) for v in valores):
            continue
        fechas.append(f"{anio}-01-01")
        for c, v in zip(cols, valores):
            datos[c].append(v)
    return pd.DataFrame({"fecha": fechas, **datos})


def _desestacionalizado() -> pd.DataFrame:
    d = pd.read_excel(DES, sheet_name="desestacionalizado n", header=None)
    fechas, filas = [], []
    anio = None
    for i in range(6, len(d)):
        a, t = d.iat[i, 0], d.iat[i, 1]
        if pd.notna(a) and str(a).strip().isdigit():
            anio = int(str(a).strip())
        if pd.isna(t) or anio is None:
            continue
        trim = {"I": 1, "II": 2, "III": 3, "IV": 4}.get(str(t).strip())
        if not trim:
            continue
        valores = [d.iat[i, c] for c in range(2, 8)]
        if all(pd.isna(v) for v in valores):
            continue
        fechas.append(f"{anio}-{3 * trim:02d}-01")
        filas.append(valores)
    # Los nombres viven en la fila 3, columnas 2..7 ("PIB", "Importaciones", …).
    _registrar(DESEST_COLS, [str(d.iat[3, c]).strip() for c in range(2, 8)])
    return pd.DataFrame(filas, columns=DESEST_COLS).assign(fecha=fechas)[["fecha", *DESEST_COLS]]


def _uci() -> pd.DataFrame:
    d = pd.read_excel(UCI, sheet_name=0, header=None)
    fechas, filas = [], []
    anio = None
    for i in range(7, len(d)):
        etq = d.iat[i, 0]
        if pd.isna(etq):
            continue
        s = str(etq).strip()
        if s.lower().startswith("año"):
            anio = int(s.split()[-1])
            continue
        mes = MESES.get(_sin_tildes(s).strip("* ").lower())
        if not mes or anio is None:
            continue
        valores = [d.iat[i, c] for c in range(1, 14)]
        if all(pd.isna(v) for v in valores):
            continue
        fechas.append(f"{anio}-{mes:02d}-01")
        filas.append(valores)
    # Acá el cuadro está transpuesto: los conceptos son ENCABEZADOS (fila 2, columnas 1..13).
    _registrar(UCI_COLS, [str(d.iat[2, c]).strip() for c in range(1, 14)])
    return pd.DataFrame(filas, columns=UCI_COLS).assign(fecha=fechas)[["fecha", *UCI_COLS]]


# El EMAE no viene de un cuadro sino de la serie que publica el INDEC en datos.gob.ar: los
# nombres son los de esa publicación, no hay fila de la que leerlos.
EMAE_NOMBRES = {
    "emae_original": "Serie original",
    "emae_desestacionalizada": "Serie desestacionalizada",
    "emae_tendencia_ciclo": "Serie tendencia-ciclo",
}


# El EMAE sectorial son las mismas categorías de tabulación del cuadro de PBI por categoría, así
# que el nombre bueno es el que el INDEC usa ahí (sin la letra, que es del otro cuadro). El CSV de
# datos.gob.ar trae los encabezados en snake_case y no sirven como nombre de serie.
EMAE_SEC_NOMBRES = {
    "agricultura_ganaderia_caza_silvicultura": "Agricultura, ganadería, caza y silvicultura",
    "pesca": "Pesca",
    "explotacion_minas_canteras": "Explotación de minas y canteras",
    "industria_manufacturera": "Industria manufacturera",
    "electricidad_gas_agua": "Electricidad, gas y agua",
    "construccion": "Construcción",
    "comercio_mayorista_minorista_reparaciones": "Comercio mayorista, minorista y reparaciones",
    "hoteles_restaurantes": "Hoteles y restaurantes",
    "transporte_comunicaciones": "Transporte, almacenamiento y comunicaciones",
    "intermediacion_financiera": "Intermediación financiera",
    "actividades_inmobiliarias_empresariales_alquiler":
        "Actividades inmobiliarias, empresariales y de alquiler",
    "admin_publica_planes_seguridad_social_afiliacion_obligatoria":
        "Administración pública y defensa; planes de seguridad social de afiliación obligatoria",
    "ensenianza": "Enseñanza",
    "servicios_sociales_salud": "Servicios sociales y de salud",
    "otras_actividades_servicios_comunitarias_sociales_personales":
        "Otras actividades de servicios comunitarias, sociales y personales",
    "impuestos_netos_subsidios":
        "Impuesto a los productos netos de subsidios",
}


def _emae_sectorial(sufijo: str) -> pd.DataFrame:
    """Apertura del EMAE por sector. El crudo ya viene tidy: solo se renombra la columna de fecha.

    El archivo trimestral del INDEC se llama `...trimestra.csv` (sin la l final): el nombre viene
    truncado desde la descarga, no es un error de tipeo."""
    nombre = f"emae_sectorial_emae_apertura_por_sectores_ndice_base_2004_valores_{sufijo}.csv"
    d = pd.read_csv(CRUDO / nombre)
    _registrar(list(EMAE_SEC_NOMBRES), list(EMAE_SEC_NOMBRES.values()))
    return d.rename(columns={"indice_tiempo": "fecha"})[["fecha", *EMAE_SEC_NOMBRES]]


def _emae_nivel(sufijo: str) -> pd.DataFrame:
    d = pd.read_csv(CRUDO / f"emae_emae_ndice_base_2004_valores_{sufijo}.csv")
    _registrar(list(EMAE_NOMBRES), list(EMAE_NOMBRES.values()))
    return d.rename(columns={"indice_tiempo": "fecha"})[
        ["fecha", "emae_original", "emae_desestacionalizada", "emae_tendencia_ciclo"]
    ]


# ---------------------------------------------------------------- salida

TAREAS = [
    ("cn_oferta_demanda_constante.csv", lambda: _trimestral(OD, "cuadro 1", OD_COLS)),
    ("cn_oferta_demanda_corriente.csv", lambda: _trimestral(OD, "cuadro 8", OD_COLS)),
    ("cn_oferta_demanda_ipi.csv", lambda: _trimestral(OD, "cuadro 9", OD_COLS)),
    ("cn_oferta_demanda_desest.csv", _desestacionalizado),
    ("cn_pbi_categoria_constante.csv", lambda: _trimestral(OD, "cuadro 4", PBI_CAT_COLS)),
    ("cn_pbi_categoria_corriente.csv", lambda: _trimestral(OD, "cuadro 12", PBI_CAT_COLS)),
    ("cn_pbi_categoria_ipi.csv", lambda: _trimestral(OD, "cuadro 13", PBI_CAT_COLS)),
    ("cn_fbkf_constante.csv", lambda: _trimestral(OD, "cuadro 6", FBKF_COLS)),
    ("cn_fbkf_corriente.csv", lambda: _trimestral(OD, "cuadro 14", FBKF_COLS)),
    ("cn_fbkf_ipi.csv", lambda: _trimestral(OD, "cuadro 15", FBKF_COLS)),
    ("cn_vbp_rama_constante.csv", lambda: _anual(SEC, "Cuadro 1", RAMA_COLS)),
    ("cn_vbp_rama_corriente.csv", lambda: _anual(SEC, "Cuadro 2", RAMA_COLS)),
    ("cn_vab_rama_constante.csv", lambda: _trimestral(SEC, "Cuadro 3", RAMA_COLS)),
    ("cn_vab_rama_corriente.csv", lambda: _trimestral(SEC, "Cuadro 4", RAMA_COLS)),
    ("cn_vab_rama_ivf.csv", lambda: _trimestral(SEC, "Cuadro 5", RAMA_COLS)),
    ("cn_vab_rama_ipi.csv", lambda: _trimestral(SEC, "Cuadro 6", RAMA_COLS)),
    ("uci_bloques.csv", _uci),
    ("emae_nivel_general_mensual.csv", lambda: _emae_nivel("mensuales")),
    ("emae_nivel_general_trimestral.csv", lambda: _emae_nivel("trimestrales")),
    ("emae_nivel_general_anual.csv", lambda: _emae_nivel("anuales")),
    ("emae_sectorial_mensual.csv", lambda: _emae_sectorial("mensuales")),
    ("emae_sectorial_trimestral.csv", lambda: _emae_sectorial("trimestra")),
    ("emae_sectorial_anual.csv", lambda: _emae_sectorial("anuales")),
]


def _escribir_nombres() -> None:
    """`cn_nombres.csv`: (archivo, columna) → nombre textual del INDEC.

    La llamada al pie —el `(3)` de «Variación de existencias (3)»— se separa en su propia
    columna: no es parte del nombre, pero aclara el alcance y no hay que perderla."""
    filas = []
    for archivo, mapa in _NOMBRES.items():
        for columna, texto in mapa.items():
            pie = re.search(r"\((\d)\)\s*$", texto)
            filas.append({
                "archivo": archivo,
                "columna": columna,
                "nombre_indec": re.sub(r"\s*\(\d\)\s*$", "", texto),
                "llamada_al_pie": pie.group(1) if pie else "",
            })
    pd.DataFrame(filas).to_csv(NOMBRES, index=False)
    print(f"{NOMBRES.name:38s} {len(filas):4d} nombres de {len(_NOMBRES)} archivos")


def main() -> None:
    SALIDA.mkdir(parents=True, exist_ok=True)
    for nombre, fn in TAREAS:
        _CUADRO[0] = nombre
        df = fn()
        df.to_csv(SALIDA / nombre, index=False)
        print(f"{nombre:38s} {len(df):4d} filas  {df['fecha'].iloc[0]} → {df['fecha'].iloc[-1]}")
    _escribir_nombres()


if __name__ == "__main__":
    main()
