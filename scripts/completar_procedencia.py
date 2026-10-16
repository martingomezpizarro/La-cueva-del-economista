"""completar_procedencia.py — carga la procedencia de cada serie en el catálogo.

Escribe el bloque `proc` de `cueva/datos/catalogo.json`: de qué organismo sale la
serie, con qué identificador externo, bajo qué licencia, con qué script se repone y
—si es elaboración propia— sobre qué insumos y con qué transformación.

La atribución sale de evidencia, no de memoria: las carpetas `data/raw/<organismo>/`
del repositorio de replicación del Trabajo Final, sus scripts de descarga y
`DATOS_LICENCIAS.md`. Cada entrada lleva `confianza`:

    alta   — el archivo vive en la carpeta del organismo o lo produce su script
    media  — se deduce del nombre y del contenido, falta confirmarlo contra la fuente

Es idempotente: se puede correr las veces que haga falta. No pisa un `proc` que ya
tenga `confianza: "verificada"` (esa marca la pone una persona, a mano, cuando
comprobó la serie contra la fuente original).

Uso:
    python scripts/completar_procedencia.py --simular   # muestra qué haría
    python scripts/completar_procedencia.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CATALOGO = RAIZ / "cueva" / "datos" / "catalogo.json"

KALMAN = {
    "fuente": "propia",
    "transformacion": "Mensualización por filtro de Kalman de una serie trimestral (modelo local lineal con observación trimestral agregada).",
    "script": "kalman_filter.py (repo del Trabajo Final)",
    "confianza": "alta",
    "notas": "La columna de valor es `y_pred`: es una ESTIMACIÓN, no un dato observado. No usar para reportar niveles oficiales.",
}

# archivo -> procedencia. Un archivo puede alimentar varias series del catálogo.
POR_ARCHIVO: dict[str, dict] = {
    # ---------------------------------------------------------------- BCRA API
    "001_reservas_brutas.csv": {
        "fuente": "bcra", "id_externo": "1",
        "endpoint": "/estadisticas/v4.0/monetarias/1",
        "definicion": "Saldo diario de reservas internacionales publicado por Comunicación «C». Excluye las asignaciones de DEG de 2009. El dato del último día hábil del año incorpora los ajustes del Balance General.",
        "script": "scripts/actualizar_bcra.py", "confianza": "alta",
    },
    "021_dep_total.csv": {
        "fuente": "bcra", "id_externo": "21",
        "endpoint": "/estadisticas/v4.0/monetarias/21",
        "definicion": "Depósitos en efectivo del total de sectores en las entidades financieras, en moneda nacional y extranjera.",
        "script": "scripts/actualizar_bcra.py", "confianza": "alta",
    },
    "rem_expectativas.csv": {
        "fuente": "bcra", "id_externo": "29",
        "definicion": "Relevamiento de Expectativas de Mercado (REM): pronósticos macroeconómicos de analistas relevados por el BCRA.",
        "url_humana": "https://www.bcra.gob.ar/PublicacionesEstadisticas/Relevamiento_Expectativas_de_Mercado.asp",
        "script": "scripts/download/download_rem.py (repo del Trabajo Final)", "confianza": "alta",
    },
    # ------------------------------------------- BCRA planillas estadísticas
    "itcrm_diario.csv": {
        "fuente": "bcra",
        "definicion": "Índice de Tipo de Cambio Real Multilateral: tipo de cambio real de Argentina contra una canasta de socios comerciales, ponderado por comercio.",
        "url_humana": "https://www.bcra.gob.ar/PublicacionesEstadisticas/Principales_variables.asp",
        "insumo_original": "ITCRMSerie.xlsx", "confianza": "alta",
        "script": "scripts/convert_bcra_excels.py (repo del Trabajo Final)",
    },
    "depositos_usd_totales.csv": {
        "fuente": "bcra",
        "definicion": "Depósitos en dólares en el sistema financiero — total de sectores.",
        "url_humana": "https://www.bcra.gob.ar/PublicacionesEstadisticas/", "confianza": "alta",
        "script": "scripts/convert_bcra_excels.py (repo del Trabajo Final)",
    },
    "depositos_usd_residentes.csv": {
        "fuente": "bcra",
        "definicion": "Depósitos en dólares de residentes en el sistema financiero.",
        "url_humana": "https://www.bcra.gob.ar/PublicacionesEstadisticas/", "confianza": "alta",
        "script": "scripts/convert_bcra_excels.py (repo del Trabajo Final)",
    },
    "depositos_usd_secprivnofin.csv": {
        "fuente": "bcra",
        "definicion": "Depósitos en dólares del sector privado no financiero.",
        "url_humana": "https://www.bcra.gob.ar/PublicacionesEstadisticas/", "confianza": "alta",
        "script": "scripts/convert_bcra_excels.py (repo del Trabajo Final)",
    },
    "prestamos_privados_usd_q.csv": {
        "fuente": "bcra",
        "definicion": "Préstamos en dólares otorgados al sector privado no financiero.",
        "url_humana": "https://www.bcra.gob.ar/PublicacionesEstadisticas/", "confianza": "alta",
        "script": "scripts/convert_bcra_excels.py (repo del Trabajo Final)",
    },
    # ------------------------------------------------------------------ INDEC
    "ipc_nacional.csv": {
        "fuente": "indec",
        "definicion": "Índice de Precios al Consumidor Nacional, nivel general, base diciembre 2016 = 100.",
        "url_humana": "https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-5-31",
        "script": "scripts/download/download_datos_gob.py (repo del Trabajo Final)", "confianza": "alta",
    },
    "pbi_corriente.csv": {
        "fuente": "indec",
        "definicion": "PBI a precios corrientes, cuentas nacionales trimestrales, base 2004.",
        "url_humana": "https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-9-47", "confianza": "alta",
    },
    "pbi_constante_2004.csv": {
        "fuente": "indec",
        "definicion": "PBI a precios constantes de 2004, cuentas nacionales trimestrales (serie desestacionalizada y original según columna).",
        "url_humana": "https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-9-47", "confianza": "alta",
    },
    "deuda_externa_sectores.csv": {
        "fuente": "indec",
        "definicion": "Deuda externa bruta total por sector residente (cuadro 23 de Cuentas Internacionales, MBP6).",
        "url_humana": "https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-35-45",
        "insumo_original": "cin_{ROMANO}_{ANIO}.xls",
        "script": "scripts/build_deuda_externa_indec.py (repo del Trabajo Final)", "confianza": "alta",
    },
    "deuda_externa_plazo.csv": {
        "fuente": "indec",
        "definicion": "Deuda externa bruta por plazo contractual original (corto y largo plazo), Cuentas Internacionales MBP6.",
        "url_humana": "https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-35-45",
        "script": "scripts/build_deuda_externa_indec.py (repo del Trabajo Final)", "confianza": "alta",
    },
    # --------------------------------------------------------- MECON/Finanzas
    "Resultado fiscal-unificado.xlsx": {
        "fuente": "mecon",
        "definicion": "Esquema Ahorro-Inversión-Financiamiento del Sector Público Nacional, empalmado entre los cortes 1993-2006, 2007-2014 y 2017-actual.",
        "url_humana": "https://www.economia.gob.ar/onp/ejecucion/",
        "transformacion": "Empalme de los tres cortes del AIF publicados por separado.",
        "confianza": "media",
        "notas": "El empalme es elaboración propia sobre datos del MECON; conviene documentar el criterio de unión en docs/metodologia.",
    },
    "saldo_deuda.csv": {
        "fuente": "finanzas",
        "definicion": "Saldo de la deuda bruta de la Administración Central, por instrumento y moneda.",
        "url_humana": "https://www.argentina.gob.ar/economia/finanzas/graficos-deuda",
        "script": "scripts/build_saldo_unificado.py (repo del Trabajo Final)", "confianza": "alta",
    },
    "deuda_externa_calendario_serie.csv": {
        "fuente": "finanzas",
        "definicion": "Calendario de vencimientos de deuda externa, construido desde las planillas SIGADE.",
        "url_humana": "https://www.argentina.gob.ar/economia/finanzas/graficos-deuda",
        "script": "scripts/build_calendario_deuda_externa_serie.py (repo del Trabajo Final)", "confianza": "alta",
    },
    "vencimientos_1y_nuevo.csv": {
        "fuente": "finanzas",
        "definicion": "Vencimientos de deuda a 1 año vista, por moneda.",
        "script": "scripts/build_vencimientos_1y.py (repo del Trabajo Final)", "confianza": "alta",
    },
    "vencimientos_2y_nuevo.csv": {
        "fuente": "finanzas",
        "definicion": "Vencimientos de deuda a 2 años vista, por moneda.",
        "script": "scripts/build_vencimientos_2y.py (repo del Trabajo Final)", "confianza": "alta",
    },
    # ----------------------------------------------------- mercado / globales
    "vix.csv": {"fuente": "yahoo", "id_externo": "^VIX",
                "definicion": "Índice de volatilidad implícita del S&P 500 (CBOE VIX).",
                "script": "scripts/download/download_yfinance.py (repo del Trabajo Final)", "confianza": "alta"},
    "dxy.csv": {"fuente": "yahoo", "id_externo": "DX-Y.NYB",
                "definicion": "Índice del dólar estadounidense contra una canasta de seis monedas (ICE DXY).",
                "script": "scripts/download/download_yfinance.py (repo del Trabajo Final)", "confianza": "alta"},
    "ust2y.csv": {"fuente": "yahoo", "id_externo": "^FVX/2Y",
                  "definicion": "Rendimiento del bono del Tesoro de EE.UU. a 2 años.",
                  "script": "scripts/download/download_yfinance.py (repo del Trabajo Final)", "confianza": "media"},
    "ust5y.csv": {"fuente": "yahoo", "id_externo": "^FVX",
                  "definicion": "Rendimiento del bono del Tesoro de EE.UU. a 5 años.",
                  "script": "scripts/download/download_yfinance.py (repo del Trabajo Final)", "confianza": "media"},
    "ust10y.csv": {"fuente": "yahoo", "id_externo": "^TNX",
                   "definicion": "Rendimiento del bono del Tesoro de EE.UU. a 10 años.",
                   "script": "scripts/download/download_yfinance.py (repo del Trabajo Final)", "confianza": "media"},
    "ust30y.csv": {"fuente": "yahoo", "id_externo": "^TYX",
                   "definicion": "Rendimiento del bono del Tesoro de EE.UU. a 30 años.",
                   "script": "scripts/download/download_yfinance.py (repo del Trabajo Final)", "confianza": "media"},
    "ofr_fsi.csv": {"fuente": "ofr",
                    "definicion": "OFR Financial Stress Index: índice diario de estrés financiero global construido con 33 variables de mercado.",
                    "url_humana": "https://www.financialresearch.gov/financial-stress-index/",
                    "script": "scripts/download/download_ofr.py (repo del Trabajo Final)", "confianza": "alta"},
    "riesgo_pais_arg.csv": {"fuente": "argentinadatos",
                            "definicion": "Riesgo país de Argentina (EMBI+ Argentina), en puntos básicos.",
                            "endpoint": "https://api.argentinadatos.com/v1/finanzas/indices/riesgo-pais",
                            "confianza": "alta",
                            "notas": "El índice subyacente es de J.P. Morgan: no se republica el archivo, se repone con el script."},
    "embi_latam.csv": {"fuente": "bcrp",
                       "definicion": "EMBI Global América Latina (spread soberano de la región), en puntos básicos.",
                       "id_externo": "PD04708XD",
                       "script": "scripts/build_embig_bcrp.py (repo del Trabajo Final)", "confianza": "alta"},
    "embig_bcrp.csv": {"fuente": "bcrp",
                       "definicion": "EMBI Global por país, difundido por el BCRP.",
                       "script": "scripts/build_embig_bcrp.py + sync_embi_bcrp.py (repo del Trabajo Final)", "confianza": "alta"},
    "heritage_mensual_arg.csv": {"fuente": "heritage",
                                 "definicion": "Índice de Libertad Económica de Argentina (Heritage Foundation), anual interpolado a frecuencia mensual.",
                                 "transformacion": "Interpolación del dato anual a mensual.",
                                 "script": "scripts/download/download_heritage.py (repo del Trabajo Final)", "confianza": "alta"},
    "wgi_political_stability_arg.csv": {"fuente": "banco_mundial", "id_externo": "PV.EST",
                                        "definicion": "Worldwide Governance Indicators — Estabilidad política y ausencia de violencia, puntaje de Argentina.",
                                        "script": "scripts/download/download_worldbank.py (repo del Trabajo Final)", "confianza": "alta"},
    "ICC.csv": {"fuente": "utdt",
                "definicion": "Índice de Confianza del Consumidor (UTDT/CIF), relevamiento mensual de hogares.",
                "url_humana": "https://www.utdt.edu/ver_contenido.php?id_contenido=1351",
                "script": "scripts/build_utdt.py (repo del Trabajo Final)", "confianza": "alta"},
    "ICG_utdt.csv": {"fuente": "utdt",
                     "definicion": "Índice de Confianza en el Gobierno (UTDT/CIF), relevamiento mensual.",
                     "url_humana": "https://www.utdt.edu/ver_contenido.php?id_contenido=1351",
                     "script": "scripts/build_utdt.py (repo del Trabajo Final)", "confianza": "alta"},
    "utdt_ei.csv": {"fuente": "utdt",
                    "definicion": "Expectativas de Inflación a 12 meses (UTDT/CIF).",
                    "script": "scripts/build_utdt.py (repo del Trabajo Final)", "confianza": "alta"},
    "utdt_il.csv": {"fuente": "utdt",
                    "definicion": "Índice Líder de la actividad económica (UTDT/CIF).",
                    "script": "scripts/build_utdt.py (repo del Trabajo Final)", "confianza": "alta"},
    # ------------------------------------------------------- elaboración propia
    "m2_pbi.csv": {"fuente": "propia",
                   "definicion": "M2 como porcentaje del PBI nominal: profundidad del sistema de pagos.",
                   "insumos": ["M2 (BCRA, idVariable 109)", "PBI nominal (INDEC, cuentas nacionales)"],
                   "transformacion": "M2 promedio mensual / PBI nominal mensualizado, en porcentaje.",
                   "script": "scripts/build_m2_pbi.py (repo del Trabajo Final)", "confianza": "alta"},
    "MTI.csv": {"fuente": "propia",
                "definicion": "Market Turbulence Index: índice sintético de turbulencia de mercado.",
                "insumos": ["VIX", "MOVE", "DXY", "OFR Financial Stress Index"],
                "transformacion": "Estandarización de cada componente y promedio; la planilla original documenta las ponderaciones.",
                "script": "MTI_Market_Turbulence_Index.xlsx (repo del Trabajo Final)", "confianza": "media",
                "notas": "Pendiente: pasar el cálculo de la planilla a un script versionado para que sea replicable de punta a punta."},
    "sentimiento_ciclo_politico.csv": {"fuente": "propia",
                                       "definicion": "Índices de confianza ajustados por el ciclo político: recogen cuánto de la variación de la confianza se explica por el calendario electoral y el signo del gobierno.",
                                       "insumos": ["ICC (UTDT)", "ICG (UTDT)", "calendario electoral argentino"],
                                       "transformacion": "Estandarización de los índices de confianza y ajuste por la fase del ciclo político (pre/post electoral y orientación del gobierno).",
                                       "script": "build_sentimiento_politico.py (repo del Trabajo Final)", "confianza": "media",
                                       "notas": "Serie propia: el criterio de clasificación política de cada período conviene dejarlo escrito en docs/metodologia."},
    "resultado_fiscal_estructural.csv": {"fuente": "propia",
                                         "definicion": "Resultado fiscal estructural: resultado primario corregido por el ciclo económico.",
                                         "insumos": ["Esquema AIF (MECON)", "PBI potencial estimado"],
                                         "script": "scripts/build_resultado_fiscal.py (repo del Trabajo Final)",
                                         "documentacion": "docs/metodologia/guia_resultado_fiscal_estructural.md (repo del Trabajo Final)",
                                         "confianza": "alta"},
    "pbi_trimestral_usd_mep.csv": {"fuente": "propia",
                                   "definicion": "PBI trimestral convertido a dólares al tipo de cambio MEP.",
                                   "insumos": ["PBI corriente (INDEC)", "TC MEP (ArgentinaDatos)"],
                                   "transformacion": "PBI nominal trimestral / TC MEP promedio del trimestre.",
                                   "confianza": "alta"},
    "pbi_per_capita_usd.csv": {"fuente": "propia",
                               "definicion": "PBI per cápita en dólares.",
                               "insumos": ["PBI en USD (elaboración propia)", "Población (Banco Mundial)"],
                               "script": "scripts/build_pbi_per_capita.py (repo del Trabajo Final)", "confianza": "alta"},
    "pbi_per_capita_usd_anual.csv": {"fuente": "propia",
                                     "definicion": "PBI per cápita en dólares, frecuencia anual.",
                                     "insumos": ["PBI en USD (elaboración propia)", "Población (Banco Mundial)"],
                                     "script": "scripts/build_pbi_per_capita.py (repo del Trabajo Final)", "confianza": "alta"},
    "defaults_history.csv": {"fuente": "propia",
                             "definicion": "Cronología de episodios de default soberano argentino.",
                             "transformacion": "Codificación manual a partir de fuentes históricas.",
                             "confianza": "media",
                             "notas": "Falta declarar la bibliografía exacta con la que se fecharon los episodios."},
    "years_since_default.csv": {"fuente": "propia",
                                "definicion": "Años transcurridos desde el último default soberano.",
                                "insumos": ["defaults_history.csv"],
                                "transformacion": "Diferencia en años entre la fecha corriente y el último episodio.",
                                "confianza": "alta"},
}

# Reglas por patrón, para familias enteras de archivos (se aplican si no hubo match exacto).
POR_PATRON: list[tuple[str, dict]] = [
    ("_kalman.csv", KALMAN),
    ("dummy_", {"fuente": "propia",
                "definicion": "Variable binaria que marca un régimen o un evento estructural.",
                "transformacion": "Codificación 0/1 sobre el calendario del evento.",
                "script": "src/build_dummies.py (repo del Trabajo Final)", "confianza": "alta"}),
    ("emae", {"fuente": "indec",
              "definicion": "Estimador Mensual de Actividad Económica, índice base 2004 = 100.",
              "url_humana": "https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-9-48",
              "script": "scripts/download/download_datos_gob.py (repo del Trabajo Final)", "confianza": "alta"}),
    ("ica_", {"fuente": "indec",
              "definicion": "Intercambio Comercial Argentino: exportaciones, importaciones y saldo comercial.",
              "url_humana": "https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-2-40",
              "script": "scripts/download/download_datos_gob.py (repo del Trabajo Final)", "confianza": "alta"}),
    ("saldo_comercial_paises", {"fuente": "indec",
                                "definicion": "Saldo comercial por países y regiones, valores FOB/CIF.",
                                "url_humana": "https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-2-40",
                                "script": "scripts/download/download_datos_gob.py (repo del Trabajo Final)", "confianza": "alta"}),
    ("balance_pagos_", {"fuente": "indec",
                        "definicion": "Balance de pagos según el MBP6 (sexta edición del manual del FMI).",
                        "url_humana": "https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-35-45",
                        "script": "scripts/download/download_datos_gob.py (repo del Trabajo Final)", "confianza": "alta"}),
    ("pbi_sectores", {"fuente": "indec",
                      "definicion": "PBI por sector de actividad económica, cuentas nacionales.",
                      "url_humana": "https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-9-47", "confianza": "alta"}),
    ("oferta_demanda", {"fuente": "indec",
                        "definicion": "Cuenta de oferta y demanda globales de las cuentas nacionales.",
                        "url_humana": "https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-9-47", "confianza": "alta"}),
    ("fbkf_", {"fuente": "indec",
               "definicion": "Formación Bruta de Capital Fijo, cuentas nacionales.",
               "url_humana": "https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-9-47", "confianza": "alta"}),
    ("ti_mensual", {"fuente": "indec",
                    "definicion": "Términos del intercambio: relación entre índices de precios de exportación e importación.",
                    "url_humana": "https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-2-40", "confianza": "media"}),
]

# Overrides por id de serie, para archivos que mezclan columnas de distinto origen.
POR_ID: dict[str, dict] = {
    "tc_a3500": {"fuente": "bcra", "id_externo": "5",
                 "endpoint": "/estadisticas/v4.0/monetarias/5",
                 "definicion": "Tipo de cambio mayorista de referencia peso/dólar calculado por el BCRA según Comunicación A 3500.",
                 "script": "scripts/actualizar_bcra.py", "confianza": "alta"},
    "tc_mep": {"fuente": "argentinadatos",
               "definicion": "Tipo de cambio implícito en la compraventa de bonos con liquidación local (dólar MEP).",
               "endpoint": "https://api.argentinadatos.com/v1/cotizaciones/dolares",
               "confianza": "alta"},
    "brecha": {"fuente": "propia",
               "definicion": "Brecha cambiaria: cuánto se aparta el dólar financiero del oficial.",
               "insumos": ["TC MEP (ArgentinaDatos)", "TC A3500 (BCRA, idVariable 5)"],
               "transformacion": "(MEP / A3500) − 1, expresado como ratio (0,25 = 25 %).",
               "script": "scripts/calcular_brecha.py (repo del Trabajo Final)", "confianza": "alta"},
}

BASE = {"verificado": "2026-08-27"}


def _proc_para(item: dict, archivo: str) -> dict | None:
    if item["id"] in POR_ID:
        return POR_ID[item["id"]]
    if archivo in POR_ARCHIVO:
        return POR_ARCHIVO[archivo]
    for patron, proc in POR_PATRON:
        if patron in archivo:
            return proc
    return None


def _descender(items: list):
    """Items y sus `children` (el catálogo anida hasta 5 niveles)."""
    for item in items:
        yield item
        yield from _descender(item.get("children") or [])


def _items(catalogo: dict):
    for fam in catalogo["familias"]:
        for sub in fam.get("subs", []):
            yield from _descender(sub["items"])
        yield from _descender(fam.get("items", []))


def aplicar(catalogo: dict) -> tuple[int, int, list[str]]:
    """Carga `proc` en cada serie y, si la serie tiene varias fuentes de datos
    (una por frecuencia), también en cada una: no es lo mismo el PBI trimestral
    del INDEC que su mensualización por Kalman, y el catálogo tiene que decirlo.

    El `proc` de la serie describe el DATO OBSERVADO: entre varias fuentes se
    elige la que no es una estimación propia.
    """
    puestos = respetados = 0
    sin_mapa: list[str] = []
    for item in _items(catalogo):
        if (item.get("proc") or {}).get("confianza") == "verificada":
            respetados += 1
            continue
        fuentes_datos = item.get("sources") or [item]
        candidatos: list[tuple[dict, dict | None]] = []
        for fd in fuentes_datos:
            candidatos.append((fd, _proc_para(item, fd.get("file", ""))))

        # proc por fuente de datos (solo si la serie tiene más de una)
        if item.get("sources"):
            for fd, proc in candidatos:
                if proc:
                    fd["proc"] = {**BASE, **proc}

        observadas = [p for _, p in candidatos if p and p.get("fuente") != "propia"]
        elegido = observadas[0] if observadas else next((p for _, p in candidatos if p), None)
        if elegido is None:
            # Una serie cargada a mano (o por otro script) ya trae su proc: no es un hueco.
            if item.get("proc"):
                respetados += 1
                continue
            archivos = [fd.get("file", "") for fd, _ in candidatos]
            if any(archivos):
                sin_mapa.append(f"{item['id']} ({archivos[0]})")
            continue
        item["proc"] = {**BASE, **elegido}
        puestos += 1
    return puestos, respetados, sorted(set(sin_mapa))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--simular", action="store_true", help="No escribir; solo informar.")
    args = ap.parse_args()

    catalogo = json.loads(CATALOGO.read_text(encoding="utf-8"))
    puestos, respetados, sin_mapa = aplicar(catalogo)

    print(f"procedencia cargada en {puestos} series")
    if respetados:
        print(f"{respetados} series con procedencia propia quedaron intactas "
              "(marcadas 'verificada' o cargadas por otro script)")
    if sin_mapa:
        print(f"\n{len(sin_mapa)} series con archivo pero sin regla de procedencia:")
        for s in sin_mapa:
            print(f"  - {s}")

    if args.simular:
        print("\n(simulación: no se escribió nada)")
        return
    CATALOGO.write_text(json.dumps(catalogo, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\n-> {CATALOGO.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
