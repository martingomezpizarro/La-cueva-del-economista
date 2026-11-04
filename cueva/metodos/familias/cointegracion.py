"""Cointegración y largo plazo: Engle-Granger, ARDL con prueba de límites (Pesaran), Johansen
+ VECM y MCO dinámicos (Stock-Watson)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from cueva.metodos.contrato import ErrorMetodo, Param, Resultado
from cueva.metodos.insumos import P_DESDE, P_FREQ, P_HASTA, P_SERIE, P_SERIES, fila_p, fmt, panel
from cueva.metodos.registro import metodo

F = "cointegracion"
P_NIV = Param(
    "transf",
    "opcion",
    "Transformación",
    defecto="log",
    opciones=["nivel", "log"],
    ayuda="La cointegración se estudia en niveles (o logs)",
)


@metodo(
    "engle_granger",
    "Cointegración de Engle-Granger y modelo de corrección de errores",
    F,
    "¿Y y X comparten una relación de largo plazo? ¿A qué velocidad se corrigen los desvíos?",
    params=[
        P_SERIE("dep", "Dependiente (Y)"),
        P_SERIES("indeps", "Explicativas (X)", minimo=1, maximo=4),
        P_FREQ,
        P_NIV,
        Param("tendencia", "opcion", "Determinísticos", defecto="c", opciones=["c", "ct"]),
        P_DESDE,
        P_HASTA,
    ],
    cuando="Dos (o pocas) series I(1) con una sola relación de equilibrio candidata.",
    supuestos=["Las series son I(1) (correr raiz_unitaria antes).", "A lo sumo un vector de cointegración."],
    trampas=[
        "El resultado depende de cuál variable se normaliza como dependiente.",
        "Los p-valores de la primera etapa NO son estándar: no leas los t de la regresión de largo plazo.",
    ],
    referencias=["Engle y Granger (1987)", "MacKinnon (2010)"],
    etiquetas=["engle-granger", "cointegración", "mce", "corrección de errores", "largo plazo"],
    nivel="basico",
)
def engle_granger(dep, indeps, freq, transf, tendencia, desde, hasta):
    import statsmodels.api as sm
    from statsmodels.tsa.stattools import coint

    df, et = panel([dep, *indeps], freq, transf, desde, hasta, minimo=40)
    stat, p, crit = coint(df[dep], df[indeps], trend=tendencia, autolag="aic")
    X = sm.add_constant(df[indeps])
    if tendencia == "ct":
        X["tendencia"] = np.arange(len(df))
    lp = sm.OLS(df[dep], X).fit()
    ect = lp.resid
    # MCE: Δy = α ect_{t-1} + Σ β Δx + γ Δy_{t-1}
    d = df.diff()
    Z = pd.concat(
        [
            ect.shift(1).rename("ECT(t−1)"),
            d[indeps].rename(columns=et),
            d[dep].shift(1).rename(f"Δ{et[dep]}(t−1)"),
        ],
        axis=1,
    )
    m = pd.concat([d[dep].rename("dy"), Z], axis=1).dropna()
    mce = sm.OLS(m["dy"], sm.add_constant(m.drop(columns="dy"))).fit(cov_type="HAC", cov_kwds={"maxlags": 4})
    alfa = mce.params["ECT(t−1)"]
    r = Resultado()
    r.metrica("Estadístico EG", stat)
    r.metrica("p (MacKinnon)", p)
    r.metrica("α (velocidad de ajuste)", alfa)
    if -2 < alfa < 0:
        r.metrica("Vida media del desvío (períodos)", np.log(0.5) / np.log(1 + alfa))
    r.tabla(
        "Relación de largo plazo (los EE no son válidos para inferencia)",
        ["variable", "coef"],
        [[et.get(c, c), v] for c, v in lp.params.items()],
    )
    r.tabla(
        "Modelo de corrección de errores (corto plazo)",
        ["variable", "coef", "EE", "p", ""],
        [[c, v, mce.bse[c], mce.pvalues[c], fila_p(mce.pvalues[c])] for c, v in mce.params.items()],
        resaltar_p="p",
    )
    r.lineas("Desvío del equilibrio (residuo de largo plazo)", df.index, {"desvío": ect.values})
    r.serie(
        f"desvio_eq_{dep}"[:40],
        df.index,
        ect.values,
        f"Desvío de {et[dep]} respecto del equilibrio de largo plazo",
    )
    coint_ = p < 0.05
    ok_alfa = alfa < 0 and mce.pvalues["ECT(t−1)"] < 0.05
    if coint_ and ok_alfa:
        r.veredicto(
            f"Cointegran (p={fmt(p)}) y el desvío se corrige: α={fmt(alfa)} (≈{fmt(-alfa * 100, 2)} % por período).",
            "verde",
        )
    elif coint_:
        r.veredicto(
            f"El test sugiere cointegración (p={fmt(p)}) pero α no es negativo y significativo: revisá la normalización.",
            "amarillo",
        )
    else:
        r.veredicto(
            f"No hay evidencia de cointegración (p={fmt(p)}): la regresión en niveles sería espuria.", "rojo"
        )
    r.resumen = f"Engle-Granger {et[dep]} ~ {', '.join(et[i] for i in indeps)}: p={fmt(p)}; α={fmt(alfa)}{fila_p(mce.pvalues['ECT(t−1)'])}."
    r.datos = {"p": p, "alfa": alfa}
    return r


@metodo(
    "ardl_limites",
    "ARDL con prueba de límites de Pesaran-Shin-Smith",
    F,
    "¿Hay relación de largo plazo aunque las series sean una mezcla de I(0) e I(1)?",
    params=[
        P_SERIE("dep", "Dependiente (Y)"),
        P_SERIES("indeps", "Explicativas (X)", minimo=1, maximo=5),
        P_FREQ,
        P_NIV,
        Param("max_rezagos", "entero", "Rezagos máximos", defecto=4, minimo=1, maximo=12),
        Param(
            "caso",
            "opcion",
            "Caso de Pesaran",
            defecto="3",
            opciones=["2", "3", "4", "5"],
            ayuda="3 = constante sin restringir (lo habitual)",
        ),
        P_DESDE,
        P_HASTA,
    ],
    cuando="Muestras cortas y órdenes de integración ambiguos (típico en macro argentina).",
    supuestos=["Ninguna serie es I(2).", "Una sola relación de largo plazo, con Y como variable de ajuste."],
    trampas=[
        "Entre los límites inferior y superior, el test es inconcluso.",
        "Elegir rezagos por AIC con muchas X sobreajusta.",
    ],
    referencias=["Pesaran, Shin y Smith (2001)", "Narayan (2005)"],
    etiquetas=["ardl", "bounds test", "pesaran", "límites", "uecm", "largo plazo"],
)
def ardl_limites(dep, indeps, freq, transf, max_rezagos, caso, desde, hasta):
    from statsmodels.tsa.ardl import UECM, ardl_select_order

    df, et = panel([dep, *indeps], freq, transf, desde, hasta, minimo=40)
    df = df.rename(columns=et)
    y, X = df[et[dep]], df[[et[i] for i in indeps]]
    tend = {"2": "c", "3": "c", "4": "ct", "5": "ct"}[caso]
    sel = ardl_select_order(y, max_rezagos, X, max_rezagos, ic="aic", trend=tend)
    ardl = sel.model.fit()
    # el UECM exige al menos un rezago por variable: se sube a 1 lo que el AIC dejó en 0
    p_y = max(1, sel.model.ardl_order[0])
    dl = sel.model.dl_lags or {}
    orden_x = {c: max(1, max(dl.get(c) or [0])) for c in X.columns}
    uecm = UECM(y, p_y, X, orden_x, trend=tend).fit()
    b = uecm.bounds_test(case=int(caso))
    crit = b.critical_values
    r = Resultado()
    orden_txt = f"({p_y}, " + ", ".join(str(v) for v in orden_x.values()) + ")"
    r.metrica("Orden ARDL (UECM)", orden_txt)
    r.metrica("F de límites", b.statistic)
    r.metrica("p (aprox.)", b.pvalue)
    try:
        lo5, hi5 = float(crit.loc[95.0, "lower"]), float(crit.loc[95.0, "upper"])
    except Exception:
        lo5, hi5 = float(crit.iloc[1, 0]), float(crit.iloc[1, 1])
    r.metrica("Límite inferior 5 %", lo5)
    r.metrica("Límite superior 5 %", hi5)
    r.tabla(
        "Valores críticos (Pesaran et al. 2001)",
        ["nivel", "I(0)", "I(1)"],
        [[str(i), row.iloc[0], row.iloc[1]] for i, row in crit.iterrows()],
    )
    lr = uecm.params
    ylag = [c for c in lr.index if c.startswith(f"{et[dep]}.L1")]
    if ylag:
        phi = lr[ylag[0]]
        filas = []
        for x in X.columns:
            c = [k for k in lr.index if k.startswith(f"{x}.L1")]
            if c:
                filas.append([x, -lr[c[0]] / phi])
        r.tabla("Coeficientes de largo plazo (−θ/φ)", ["variable", "efecto de largo plazo"], filas)
        r.metrica("Velocidad de ajuste φ", phi)
    r.tabla(
        "ARDL estimado",
        ["término", "coef", "p"],
        [[k, v, ardl.pvalues[k]] for k, v in ardl.params.items()],
        resaltar_p="p",
    )
    if b.statistic > hi5:
        r.veredicto(
            f"F={fmt(b.statistic)} > límite superior ({fmt(hi5)}): HAY relación de largo plazo, sea cual sea el orden de integración.",
            "verde",
        )
    elif b.statistic < lo5:
        r.veredicto(
            f"F={fmt(b.statistic)} < límite inferior ({fmt(lo5)}): no hay relación de largo plazo.", "rojo"
        )
    else:
        r.veredicto(
            f"F={fmt(b.statistic)} entre los límites: inconcluso; hace falta saber el orden de integración.",
            "amarillo",
        )
    r.resumen = f"ARDL{orden_txt} de {et[dep]}: F de límites {fmt(b.statistic)} (5 %: {fmt(lo5)}–{fmt(hi5)})."
    r.codigo = "from statsmodels.tsa.ardl import ardl_select_order, UECM\nsel = ardl_select_order(y, 4, X, 4, ic='aic', trend='c')\nUECM.from_ardl(sel.model).fit().bounds_test(case=3)"
    return r


@metodo(
    "johansen_vecm",
    "Johansen y VECM completo",
    F,
    "¿Cuántas relaciones de equilibrio hay entre varias series y qué variables se ajustan?",
    params=[
        P_SERIES("sids", "Series (2 a 6)", minimo=2, maximo=6),
        P_FREQ,
        P_NIV,
        Param("rezagos", "entero", "Rezagos en diferencias", defecto=2, minimo=0, maximo=12),
        Param(
            "deterministicos",
            "opcion",
            "Determinísticos",
            defecto="ci",
            opciones=["n", "co", "ci", "lo", "li"],
            ayuda="ci = constante en la relación de cointegración (lo habitual)",
        ),
        Param("horizonte", "entero", "Horizonte IRF", defecto=24, minimo=4, maximo=60),
        P_DESDE,
        P_HASTA,
    ],
    cuando="Sistemas con más de una relación de largo plazo posible (dinero-precios-tipo de cambio).",
    supuestos=["Todas las series I(1).", "Errores gaussianos sin autocorrelación con los rezagos elegidos."],
    trampas=[
        "Muy sensible a los rezagos y determinísticos: reportá la robustez.",
        "En muestras cortas la traza sobre-rechaza (corrección de Reinsel-Ahn).",
    ],
    costo="segundos",
    referencias=["Johansen (1991, 1995)", "Juselius (2006)"],
    etiquetas=["johansen", "vecm", "traza", "máximo autovalor", "cointegración", "alfa", "beta"],
)
def johansen_vecm(sids, freq, transf, rezagos, deterministicos, horizonte, desde, hasta):
    from statsmodels.tsa.vector_ar.vecm import VECM, select_coint_rank

    df, et = panel(sids, freq, transf, desde, hasta, minimo=50)
    nombres = [et[s] for s in sids]
    df.columns = nombres
    det_j = {"n": -1, "co": 0, "ci": 0, "lo": 1, "li": 1}[deterministicos]
    traza = select_coint_rank(df, det_order=det_j, k_ar_diff=rezagos, method="trace", signif=0.05)
    maxe = select_coint_rank(df, det_order=det_j, k_ar_diff=rezagos, method="maxeig", signif=0.05)
    rango = traza.rank
    r = Resultado()
    T = len(df)
    corr = (T - len(sids) * (rezagos + 1)) / T
    r.tabla(
        "Prueba de la traza",
        ["H0: r ≤", "traza", "traza corregida (Reinsel-Ahn)", "crítico 5 %"],
        [
            [i, traza.test_stats[i], traza.test_stats[i] * corr, traza.crit_vals[i]]
            for i in range(len(traza.test_stats))
        ],
    )
    r.tabla(
        "Prueba del máximo autovalor",
        ["H0: r =", "λ máx", "crítico 5 %"],
        [[i, maxe.test_stats[i], maxe.crit_vals[i]] for i in range(len(maxe.test_stats))],
    )
    r.metrica("Rango (traza)", rango)
    r.metrica("Rango (máx. autovalor)", maxe.rank)
    rc = sum(
        1
        for i in range(len(traza.test_stats))
        if traza.test_stats[i] * corr > traza.crit_vals[i]
        and all(traza.test_stats[j] * corr > traza.crit_vals[j] for j in range(i))
    )
    if rc != rango:
        r.advertir(f"Con la corrección de muestra chica el rango baja a {rc}: el resultado es frágil.")
    if rango == 0:
        r.veredicto("No hay cointegración: modelá en diferencias (VAR).", "rojo")
        r.resumen = f"Johansen sobre {', '.join(nombres)}: rango 0 (sin cointegración)."
        return r
    if rango == len(sids):
        r.advertir("Rango completo: las series serían estacionarias; revisá raíz unitaria.")
    res = VECM(df, k_ar_diff=rezagos, coint_rank=rango, deterministic=deterministicos).fit()
    beta = res.beta / res.beta[0]
    r.tabla(
        "Vectores de cointegración β (normalizados en la 1.ª variable)",
        ["variable", *[f"β{i + 1}" for i in range(rango)]],
        [[n, *beta[j]] for j, n in enumerate(nombres)],
    )
    r.tabla(
        "Velocidades de ajuste α",
        ["variable", *[f"α{i + 1}" for i in range(rango)], *[f"p α{i + 1}" for i in range(rango)]],
        [[n, *res.alpha[j], *res.pvalues_alpha[j]] for j, n in enumerate(nombres)],
    )
    ect = df.values @ res.beta
    r.lineas(
        "Desvíos de equilibrio", df.index, {f"ECT{i + 1}": ect[:, i] - ect[:, i].mean() for i in range(rango)}
    )
    for i in range(rango):
        r.serie(
            f"ect{i + 1}_johansen",
            df.index,
            ect[:, i] - ect[:, i].mean(),
            f"Desvío de la relación de cointegración {i + 1}",
        )
    try:
        irf = res.irf(horizonte)
        for j, n in enumerate(nombres):
            r.lineas(
                f"Respuesta de {n} a un shock (Cholesky) en {nombres[0]}",
                list(range(horizonte + 1)),
                {"respuesta": irf.orth_irfs[:, j, 0]},
            )
    except Exception:
        pass
    ajustan = [nombres[j] for j in range(len(nombres)) if res.pvalues_alpha[j, 0] < 0.05]
    debil = [n for n in nombres if n not in ajustan]
    r.veredicto(
        f"Rango {rango}. Se ajustan al desequilibrio: {', '.join(ajustan) or 'ninguna (¿?)'}; débilmente exógenas: {', '.join(debil) or 'ninguna'}.",
        "verde",
    )
    r.resumen = f"Johansen sobre {', '.join(nombres)}: rango {rango} (traza). β₁ = [{', '.join(fmt(b) for b in beta[:, 0])}]; ajustan: {', '.join(ajustan) or 'ninguna'}."
    r.datos = {"rango": rango}
    return r


@metodo(
    "mco_dinamicos",
    "MCO dinámicos de Stock-Watson (DOLS)",
    F,
    "¿Cuál es el coeficiente de largo plazo con errores estándar válidos para inferencia?",
    params=[
        P_SERIE("dep", "Dependiente (Y)"),
        P_SERIES("indeps", "Explicativas (X)", minimo=1, maximo=4),
        P_FREQ,
        P_NIV,
        Param("adelantos_rezagos", "entero", "Adelantos y rezagos de ΔX", defecto=2, minimo=0, maximo=8),
    ],
    cuando="Cuando ya sabés que cointegran y querés testear hipótesis sobre el vector (¿elasticidad = 1?).",
    supuestos=["Series I(1) cointegradas; los adelantos/rezagos de ΔX limpian la endogeneidad."],
    referencias=["Stock y Watson (1993)", "Saikkonen (1991)"],
    etiquetas=["dols", "stock-watson", "largo plazo", "elasticidad", "cointegración"],
    nivel="avanzado",
)
def mco_dinamicos(dep, indeps, freq, transf, adelantos_rezagos):
    import statsmodels.api as sm

    df, et = panel([dep, *indeps], freq, transf, minimo=40)
    k = adelantos_rezagos
    cols = {et[x]: df[x] for x in indeps}
    for x in indeps:
        dx = df[x].diff()
        for j in range(-k, k + 1):
            cols[f"Δ{x}({j:+d})"] = dx.shift(-j)
    X = sm.add_constant(pd.DataFrame(cols)).dropna()
    yv = df[dep].loc[X.index]
    res = sm.OLS(yv, X).fit(cov_type="HAC", cov_kwds={"maxlags": max(2, k + 2)})
    if len(yv) < 20:
        raise ErrorMetodo("Muy pocas observaciones tras adelantos y rezagos.")
    r = Resultado()
    filas = [
        [
            et[x],
            res.params[et[x]],
            res.bse[et[x]],
            res.pvalues[et[x]],
            (res.params[et[x]] - 1) / res.bse[et[x]],
        ]
        for x in indeps
    ]
    r.tabla(
        "Coeficientes de largo plazo (EE Newey-West)",
        ["variable", "coef", "EE", "p (=0)", "t (=1)"],
        filas,
        resaltar_p="p (=0)",
    )
    for f in filas:
        r.metrica(f"β {f[0]}", f[1])
    r.resumen = (
        "DOLS de "
        + et[dep]
        + ": "
        + "; ".join(f"β({f[0]})={fmt(f[1])} (EE {fmt(f[2])})" for f in filas)
        + "."
    )
    return r
