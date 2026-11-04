"""Datos REALES para el mockup de la Mesa de investigación (docs/mockup/mesa-investigacion.html).

Reproduce, en versión reducida, la iteración del Trabajo Final de Martín
(«Un popurrí de determinantes: riesgo país idiosincrático argentino 2007-2026»,
repo `riesgo-pais-argentino`, notebooks/02a_analisis_basico.py): sobre el panel mensual
219 × 43 itera combinaciones de explicativas para ARDL, VAR y VECM, filtra por diagnóstico de
residuos, arma la tabla larga modelo × variable (coeficiente de largo plazo, p-valor) y la
matriz de causalidad de Granger. Todo eso queda como datos que el mockup vuelve a graficar.

Uso:
    python scripts/mockup_mesa_investigacion_datos.py <ruta a panel_mensual.csv> <ruta a diccionario_variables.csv>
Salida:
    docs/mockup/mesa_investigacion_datos.js   (const DATOS_TF = {...})
"""

from __future__ import annotations

import json
import sys
import time
import warnings
from pathlib import Path

import pandas as pd

warnings.filterwarnings("ignore")

DEP = "embig_argentina_a_b_embi_global_latinoamerica"
VARS = [
    "brecha_cambiaria_mep_oficial",
    "reservas_brutas_bcra_pbi_usd",
    "prestamos_privados_usd_pbi_usd",
    "depositos_usd_total_pbi_usd",
    "total_cuenta_corriente_pbi_usd",
    "deuda_externa_bruta_total_pbi_usd",
    "itcrm_multilateral",
    "terminos_de_intercambio_nominal",
    "se_resultado_estructural_pbi",
    "resultado_financiero_pbi_ars",
    "vix_cboe_volatility_index",
    "dxy_us_dollar_index",
    "icg_transformado_d_icg2_0",
    "us_treasury_10y",
    "anos_desde_ultimo_default",
    "m2_pbi",
]
CORTOS = {
    DEP: "RPI (EMBI Arg − Latam)",
    "brecha_cambiaria_mep_oficial": "Brecha MEP/oficial",
    "reservas_brutas_bcra_pbi_usd": "Reservas / PBI",
    "prestamos_privados_usd_pbi_usd": "Préstamos USD / PBI",
    "depositos_usd_total_pbi_usd": "Depósitos USD / PBI",
    "total_cuenta_corriente_pbi_usd": "Cuenta corriente / PBI",
    "deuda_externa_bruta_total_pbi_usd": "Deuda externa / PBI",
    "itcrm_multilateral": "ITCRM",
    "terminos_de_intercambio_nominal": "Términos de intercambio",
    "se_resultado_estructural_pbi": "Resultado estructural",
    "resultado_financiero_pbi_ars": "Resultado financiero / PBI",
    "vix_cboe_volatility_index": "VIX",
    "dxy_us_dollar_index": "DXY",
    "icg_transformado_d_icg2_0": "ICG (transf.)",
    "us_treasury_10y": "Treasury 10 años",
    "anos_desde_ultimo_default": "Años desde el default",
    "m2_pbi": "M2 / PBI",
}


def main(panel_csv: str, dicc_csv: str):
    """La iteración y Granger son los MISMOS del catálogo (cueva/metodos/familias/universo.py):
    acá sólo se arman los datos para el mockup."""
    from cueva.metodos.familias.universo import estacionarias, granger_nxn, iterar

    t0 = time.time()
    df = pd.read_csv(panel_csv, parse_dates=["fecha"]).set_index("fecha")
    df.index.freq = "ME"
    dic = pd.read_csv(dicc_csv).set_index("columna")
    orden = {c: dic.loc[c, "orden_integracion"] if c in dic.index else "" for c in [DEP, *VARS]}
    orden[DEP] = "I(1)"  # el RPI entra en diferencias al VAR, como en el TF
    unidades = {c: dic.loc[c, "unidad"] if c in dic.index else "" for c in [DEP, *VARS]}
    modelos, efectos = iterar(df, DEP, VARS, orden=orden)
    print(f"Universo: {len(modelos)} modelos ({time.time() - t0:.0f} s)")
    todas = [DEP, *VARS]
    G, LAG = granger_nxn(estacionarias(df[todas], orden))
    print(f"Granger listo ({time.time() - t0:.0f} s)")
    # el mejor ARDL con residuos limpios (por BIC): sus resultados también son series
    from cueva.metodos.familias.universo import _ardl_largo_plazo

    ardl_ok = [m for m in range(len(modelos)) if modelos[m][0] == "ARDL" and modelos[m][8]]
    ajuste = None
    if ardl_ok:
        mejor = min(ardl_ok, key=lambda m: modelos[m][5])
        _, vx, spec, *_ = modelos[mejor]
        res, _ = _ardl_largo_plazo(df, DEP, [VARS[i] for i in vx], int(spec[1]), int(spec[3]))
        ajuste = {
            "modelo": mejor,
            "fechas": [str(f.date()) for f in res.fittedvalues.index],
            "ajustado": [round(float(v), 3) for v in res.fittedvalues.values],
            "residuo": [round(float(v), 3) for v in res.resid.values],
        }
    salida = {
        "fuente": "riesgo-pais-argentino · data/replicacion/panel_mensual.csv",
        "titulo": "Un popurrí de determinantes: riesgo país idiosincrático argentino (2007–2026)",
        "dep": DEP,
        "vars": VARS,
        "cortos": CORTOS,
        "unidades": unidades,
        "orden": orden,
        "fechas": [str(f.date()) for f in df.index],
        "panel": {c: [round(float(v), 5) for v in df[c].values] for c in todas},
        "modelos_cols": ["tipo", "vars", "spec", "r2", "aic", "bic", "nobs", "lb_p", "pasa"],
        "modelos": modelos,
        "efectos_cols": ["modelo", "var", "coef_lp", "p"],
        "efectos": efectos,
        "granger": {"series": todas, "p": G, "lag": LAG},
        "ajuste_mejor": ajuste,
        "segundos": round(time.time() - t0, 1),
    }
    destino = Path(__file__).resolve().parents[1] / "docs" / "mockup" / "mesa_investigacion_datos.js"
    destino.write_text(
        "// Generado por scripts/mockup_mesa_investigacion_datos.py — no editar a mano\nconst DATOS_TF = "
        + json.dumps(salida, ensure_ascii=False, separators=(",", ":"))
        + ";\n",
        encoding="utf-8",
    )
    n_por = {t: sum(1 for m in modelos if m[0] == t) for t in ("ARDL", "VAR", "VECM")}
    print(f"{destino} · modelos {n_por} · efectos {len(efectos)} · {destino.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
