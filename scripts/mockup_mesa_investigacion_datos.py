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
from itertools import combinations
from pathlib import Path

import numpy as np
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


def ljung_box_p(resid, lags=12):
    from statsmodels.stats.diagnostic import acorr_ljungbox

    r = np.asarray(resid)
    r = r[np.isfinite(r)]
    return float(acorr_ljungbox(r, lags=[lags], return_df=True)["lb_pvalue"].iloc[0])


def ardl_lr(df, x_vars, p, q):
    """ARDL en niveles; coeficiente de largo plazo θ_x = Σβ_x / (1 − Σφ) con EE por método delta."""
    from statsmodels.tsa.ardl import ARDL

    res = ARDL(df[DEP], lags=p, exog=df[x_vars], order={x: q for x in x_vars}, trend="c").fit()
    nombres = list(res.params.index)
    b = res.params.values
    V = res.cov_params().values
    iy = [i for i, n in enumerate(nombres) if n.startswith(f"{DEP}.L")]
    den = 1 - b[iy].sum()
    salida = {}
    for x in x_vars:
        ix = [i for i, n in enumerate(nombres) if n.startswith(f"{x}.L")]
        num = b[ix].sum()
        th = num / den
        g = np.zeros(len(b))
        g[ix] = 1 / den
        g[iy] = num / den**2
        se = float(np.sqrt(max(g @ V @ g, 1e-300)))
        from scipy import stats

        salida[x] = (float(th), float(2 * stats.norm.sf(abs(th / se))))
    return res, salida


def main(panel_csv: str, dicc_csv: str):
    from statsmodels.tsa.api import VAR
    from statsmodels.tsa.stattools import grangercausalitytests
    from statsmodels.tsa.vector_ar.vecm import VECM, coint_johansen

    t0 = time.time()
    df = pd.read_csv(panel_csv, parse_dates=["fecha"]).set_index("fecha")
    dic = pd.read_csv(dicc_csv).set_index("columna")
    orden = {c: dic.loc[c, "orden_integracion"] if c in dic.index else "" for c in [DEP, *VARS]}
    unidades = {c: dic.loc[c, "unidad"] if c in dic.index else "" for c in [DEP, *VARS]}
    # transformación estacionaria (para VAR y Granger): Δ para I(1) y para la dependiente
    est = pd.DataFrame({c: (df[c].diff() if orden[c] != "I(0)" else df[c]) for c in [DEP, *VARS]}).dropna()

    modelos, efectos = [], []  # modelo: [tipo, vars(idx), spec, r2, aic, bic, nobs, lb_p, pasa]
    idx = {v: i for i, v in enumerate(VARS)}

    def registrar(tipo, xs, spec, r2, aic, bic, nobs, lbp, efs):
        mid = len(modelos)
        modelos.append([tipo, [idx[x] for x in xs], spec, r2, aic, bic, nobs, round(lbp, 4), int(lbp > 0.05)])
        for x, (c, p) in efs.items():
            if np.isfinite(c) and np.isfinite(p):
                efectos.append([mid, idx[x], round(c, 6), round(p, 5)])

    combos = [list(c) for r in (1, 2, 3) for c in combinations(VARS, r)]
    # ── ARDL: todas las combinaciones de 1 a 3 explicativas × (p, q) ∈ {1,2}² ──
    for xs in combos:
        for p in (1, 2):
            for q in (1, 2):
                try:
                    res, lr = ardl_lr(df, xs, p, q)
                    r2 = 1 - np.var(res.resid) / np.var(df[DEP].iloc[-len(res.resid) :])
                    registrar(
                        "ARDL",
                        xs,
                        f"p{p}q{q}",
                        round(float(r2), 4),
                        round(res.aic, 2),
                        round(res.bic, 2),
                        int(res.nobs),
                        ljung_box_p(res.resid),
                        lr,
                    )
                except Exception:
                    continue
    print(f"ARDL listos: {len(modelos)} modelos ({time.time() - t0:.0f} s)")
    # ── VAR en diferencias: efecto acumulado de x sobre ΔRPI y Wald (Granger en el sistema) ──
    for xs in combos:
        try:
            sub = est[[DEP, *xs]]
            sel = VAR(sub.values).select_order(maxlags=4)
            k = max(1, int(sel.selected_orders["aic"]))
            res = VAR(sub.values).fit(k)
            efs = {}
            for j, x in enumerate(xs, start=1):
                coef = float(sum(res.coefs[L][0, j] for L in range(k)))
                p = float(res.test_causality(0, [j], kind="f").pvalue)
                efs[x] = (coef, p)
            e0 = res.resid[:, 0]
            r2 = 1 - np.var(e0) / np.var(sub.values[k:, 0])
            registrar(
                "VAR",
                xs,
                f"k{k}",
                round(float(r2), 4),
                round(float(res.aic), 3),
                round(float(res.bic), 3),
                int(res.nobs),
                ljung_box_p(e0),
                efs,
            )
        except Exception:
            continue
    print(f"VAR listos: {len(modelos)} modelos ({time.time() - t0:.0f} s)")
    # ── VECM en niveles (combinaciones de 1 y 2 explicativas): β normalizado en el RPI ──
    for xs in [c for c in combos if len(c) <= 2]:
        sub = df[[DEP, *xs]]
        try:
            jo = coint_johansen(sub.values, det_order=0, k_ar_diff=1)
            rango = int(sum(jo.lr1 > jo.cvt[:, 1]))
            if rango < 1:
                continue
            res = VECM(sub.values, k_ar_diff=1, coint_rank=1, deterministic="ci").fit()
            beta = res.beta[:, 0] / res.beta[0, 0]
            pv = getattr(res, "pvalues_beta", None)
            efs = {}
            for j, x in enumerate(xs, start=1):
                p = float(np.ravel(pv)[j - 1]) if pv is not None and np.size(pv) >= j else float("nan")
                efs[x] = (float(-beta[j]), p)
            e0 = res.resid[:, 0]
            r2 = 1 - np.var(e0) / np.var(np.diff(sub.values[:, 0]))
            registrar(
                "VECM", xs, f"r{rango}", round(float(r2), 4), None, None, int(res.nobs), ljung_box_p(e0), efs
            )
        except Exception:
            continue
    print(f"VECM listos: {len(modelos)} modelos ({time.time() - t0:.0f} s)")
    # ── Granger N × N sobre las series estacionarias, rezago por AIC (≤ 6) ──
    import inspect

    kw_g = {"verbose": False} if "verbose" in inspect.signature(grangercausalitytests).parameters else {}
    todas = [DEP, *VARS]
    G = [[None] * len(todas) for _ in todas]
    LAG = [[None] * len(todas) for _ in todas]
    for i, causa in enumerate(todas):
        for j, efecto in enumerate(todas):
            if i == j:
                continue
            sub = est[[efecto, causa]].values
            try:
                k = max(1, int(VAR(sub).select_order(maxlags=6).selected_orders["aic"]))
                r = grangercausalitytests(sub, maxlag=[k], **kw_g)
                G[i][j] = round(float(r[k][0]["ssr_ftest"][1]), 5)
                LAG[i][j] = k
            except Exception as e:  # que no falle en silencio
                print(f"  Granger {causa} → {efecto}: {type(e).__name__}: {e}")
                continue
    print(f"Granger listo ({time.time() - t0:.0f} s)")
    # ── el mejor ARDL que pasa el filtro (por BIC): sus resultados también son series ──
    ardl_ok = [m for m in range(len(modelos)) if modelos[m][0] == "ARDL" and modelos[m][8]]
    mejor = min(ardl_ok, key=lambda m: modelos[m][5]) if ardl_ok else None
    ajuste = None
    if mejor is not None:
        tipo, vx, spec, *_ = modelos[mejor]
        xs = [VARS[i] for i in vx]
        p, q = int(spec[1]), int(spec[3])
        res, _ = ardl_lr(df, xs, p, q)
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
        "panel": {c: [round(float(v), 5) for v in df[c].values] for c in [DEP, *VARS]},
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
