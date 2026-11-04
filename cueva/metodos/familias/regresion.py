"""Regresión y estimación: MCO con todas las correcciones, cuantílica, robusta, móvil, MCG,
variables instrumentales y rezagos distribuidos."""

from __future__ import annotations

import numpy as np
import pandas as pd

from cueva.metodos.contrato import ErrorMetodo, Param, Resultado
from cueva.metodos.insumos import (
    P_DESDE,
    P_FREQ,
    P_HASTA,
    P_SERIE,
    P_SERIES,
    P_TRANSF,
    PERIODO,
    fila_p,
    fmt,
    panel,
)
from cueva.metodos.registro import metodo

F = "regresion"
P_DEP = P_SERIE("dep", "Dependiente (Y)")
P_IND = P_SERIES("indeps", "Explicativas (X)", minimo=1, maximo=10)


def _tabla_coef(r, res, nombres, titulo="Coeficientes"):
    filas = []
    for i, n in enumerate(nombres):
        filas.append([n, res.params[i], res.bse[i], res.tvalues[i], res.pvalues[i], fila_p(res.pvalues[i])])
    r.tabla(titulo, ["variable", "coef", "EE", "t", "p", ""], filas, resaltar_p="p")
    r.barras("Coeficientes con IC 95 %", nombres[1:] if nombres[0] == "const" else nombres, {"coef": res.params[1:] if nombres[0] == "const" else res.params}, horizontal=True)


def _diseno(df, dep, indeps, rezagos_x, rezagos_y, et):
    cols = {}
    for s in indeps:
        cols[et[s]] = df[s]
        for k in range(1, rezagos_x + 1):
            cols[f"{et[s]} (t−{k})"] = df[s].shift(k)
    for k in range(1, rezagos_y + 1):
        cols[f"{et[dep]} (t−{k})"] = df[dep].shift(k)
    X = pd.DataFrame(cols, index=df.index)
    d = pd.concat([df[dep].rename("__y"), X], axis=1).dropna()
    return d["__y"], d.drop(columns="__y")


@metodo(
    "mco",
    "Regresión lineal (MCO) con errores robustos y diagnóstico completo",
    F,
    "¿Cuánto cambia Y cuando cambia X, manteniendo lo demás constante?",
    params=[
        P_DEP,
        P_IND,
        P_FREQ,
        P_TRANSF,
        Param("rezagos_x", "entero", "Rezagos de cada X", defecto=0, minimo=0, maximo=12),
        Param("rezagos_y", "entero", "Rezagos de Y (dinámica)", defecto=0, minimo=0, maximo=12),
        Param("errores", "opcion", "Errores estándar", defecto="HAC", opciones=["clasicos", "HC3", "HAC"], ayuda="HAC = Newey-West: robustos a heterocedasticidad y autocorrelación"),
        Param("estacionales", "bool", "Dummies estacionales", defecto=False),
        P_DESDE,
        P_HASTA,
    ],
    cuando="El punto de partida de cualquier relación. Con series de tiempo, siempre con HAC y en variables estacionarias.",
    supuestos=["Exogeneidad: E[u|X]=0.", "Variables estacionarias (o cointegradas).", "Sin multicolinealidad perfecta."],
    trampas=[
        "Regresión espuria: dos I(1) independientes dan R² alto y t significativos (Granger-Newbold 1974).",
        "Rezagos de Y con errores autocorrelacionados ⇒ MCO inconsistente.",
        "Significativo ≠ causal: la exogeneidad es un supuesto, no un resultado.",
    ],
    referencias=["Wooldridge (2020), caps. 10-12", "Newey y West (1987)"],
    etiquetas=["ols", "mco", "regresión", "newey-west", "hac", "ardl", "vif"],
    nivel="basico",
)
def mco(dep, indeps, freq, transf, rezagos_x, rezagos_y, errores, estacionales, desde, hasta):
    import statsmodels.api as sm
    from statsmodels.stats.diagnostic import acorr_breusch_godfrey, het_breuschpagan, linear_reset
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    from statsmodels.stats.stattools import durbin_watson, jarque_bera

    df, et = panel([dep, *indeps], freq, transf, desde, hasta, minimo=20)
    y, X = _diseno(df, dep, indeps, rezagos_x, rezagos_y, et)
    if estacionales and PERIODO.get(freq, 1) > 1:
        mes = X.index.month if freq == "mensual" else X.index.quarter
        for m in range(2, PERIODO[freq] + 1):
            X[f"est_{m}"] = (mes == m).astype(float)
    Xc = sm.add_constant(X)
    kw = {"cov_type": "HAC", "cov_kwds": {"maxlags": int(4 * (len(y) / 100) ** (2 / 9))}} if errores == "HAC" else ({"cov_type": "HC3"} if errores == "HC3" else {})
    res = sm.OLS(y.values, Xc.values).fit(**kw)
    nombres = list(Xc.columns)
    r = Resultado()
    r.metrica("R²", res.rsquared)
    r.metrica("R² ajustado", res.rsquared_adj)
    r.metrica("Obs.", int(res.nobs))
    r.metrica("F (p)", res.f_pvalue)
    r.metrica("AIC", res.aic)
    _tabla_coef(r, res, nombres)
    ols = sm.OLS(y.values, Xc.values).fit()
    bg = acorr_breusch_godfrey(ols, nlags=min(12, len(y) // 5))
    bp = het_breuschpagan(ols.resid, Xc.values)
    jb = jarque_bera(ols.resid)
    try:
        reset = linear_reset(ols, power=2, use_f=True).pvalue
    except Exception:
        reset = np.nan
    diag = [
        ["Durbin-Watson", durbin_watson(ols.resid), None, "≈2 sin autocorrelación"],
        ["Breusch-Godfrey", bg[0], bg[1], "autocorrelación de residuos"],
        ["Breusch-Pagan", bp[0], bp[1], "heterocedasticidad"],
        ["Jarque-Bera", jb[0], jb[1], "normalidad"],
        ["RESET de Ramsey", None, reset, "forma funcional"],
    ]
    r.tabla("Diagnóstico de residuos", ["test", "estadístico", "p", "qué mira"], diag, resaltar_p="p")
    if X.shape[1] > 1:
        vif = [[c, variance_inflation_factor(Xc.values, i + 1)] for i, c in enumerate(X.columns)]
        r.tabla("Multicolinealidad (VIF > 10 es problema)", ["variable", "VIF"], vif)
        if max(v[1] for v in vif) > 10:
            r.advertir("Hay VIF > 10: los coeficientes individuales están mal identificados.")
    r.lineas(f"{et[dep]}: observado y ajustado", y.index, {"observado": y.values, "ajustado": ols.fittedvalues}, estilos={"ajustado": {"guion": "dash"}})
    r.lineas("Residuos", y.index, {"residuo": ols.resid})
    r.serie(f"resid_{dep}"[:40], y.index, ols.resid, f"Residuos de la regresión de {et[dep]}")
    malos = [d[0] for d in diag if d[2] is not None and d[2] == d[2] and d[2] < 0.05]
    if transf in ("nivel", "log") and not rezagos_y:
        r.advertir("Regresión en niveles: si las series son I(1) y no cointegran, es espuria. Corré raiz_unitaria y engle_granger.")
    r.veredicto("Diagnóstico limpio." if not malos else f"Problemas en: {', '.join(malos)}.", "verde" if not malos else ("amarillo" if len(malos) == 1 else "rojo"))
    sig = [f"{n} ({fmt(res.params[i])}{fila_p(res.pvalues[i])})" for i, n in enumerate(nombres) if n != "const" and res.pvalues[i] < 0.1]
    r.resumen = f"MCO de {et[dep]} (n={int(res.nobs)}, errores {errores}): R²={fmt(res.rsquared)}; significativas: {', '.join(sig) or 'ninguna'}. Diagnóstico: {', '.join(malos) or 'limpio'}."
    r.datos = {"coef": dict(zip(nombres, res.params, strict=True)), "p": dict(zip(nombres, res.pvalues, strict=True))}
    r.codigo = "import statsmodels.api as sm\nres = sm.OLS(y, sm.add_constant(X)).fit(cov_type='HAC', cov_kwds={'maxlags': 4})\nprint(res.summary())"
    return r


@metodo(
    "regresion_cuantilica",
    "Regresión cuantílica",
    F,
    "¿El efecto de X es el mismo en los meses malos (cola baja) que en los buenos (cola alta)?",
    params=[P_DEP, P_IND, P_FREQ, Param("transf", "opcion", "Transformación", defecto="dif_log", opciones=list(P_TRANSF.opciones)), Param("cuantiles", "opciones", "Cuantiles", defecto=["0.1", "0.25", "0.5", "0.75", "0.9"], opciones=["0.05", "0.1", "0.25", "0.5", "0.75", "0.9", "0.95"])],
    cuando="Growth-at-risk (Adrian et al. 2019): condiciones financieras que mueven la cola baja del crecimiento.",
    trampas=["Con pocos datos, los cuantiles extremos (5 %, 95 %) son muy imprecisos."],
    referencias=["Koenker y Bassett (1978)", "Adrian, Boyarchenko y Giannone (2019)"],
    etiquetas=["cuantil", "growth at risk", "colas", "koenker", "mediana"],
)
def regresion_cuantilica(dep, indeps, freq, transf, cuantiles):
    import statsmodels.api as sm

    df, et = panel([dep, *indeps], freq, transf, minimo=30)
    X = sm.add_constant(df[indeps])
    qs = sorted(float(q) for q in cuantiles)
    filas, curvas = [], {et[s]: [] for s in indeps}
    for q in qs:
        res = sm.QuantReg(df[dep], X).fit(q=q)
        for s in indeps:
            filas.append([f"{q:.2f}", et[s], res.params[s], res.bse[s], res.pvalues[s]])
            curvas[et[s]].append(res.params[s])
    mco_ = sm.OLS(df[dep], X).fit()
    r = Resultado()
    r.tabla("Coeficientes por cuantil", ["cuantil", "variable", "coef", "EE", "p"], filas, resaltar_p="p")
    r.lineas("Coeficiente según el cuantil (línea plana = efecto homogéneo)", [f"{q:.2f}" for q in qs], {**curvas, **{f"MCO {et[s]}": [mco_.params[s]] * len(qs) for s in indeps}}, estilos={f"MCO {et[s]}": {"guion": "dash"} for s in indeps})
    s0 = indeps[0]
    rango = max(curvas[et[s0]]) - min(curvas[et[s0]])
    r.metrica(f"Rango del efecto de {et[s0]}", rango)
    r.resumen = f"Regresión cuantílica de {et[dep]}: el efecto de {et[s0]} va de {fmt(min(curvas[et[s0]]))} a {fmt(max(curvas[et[s0]]))} según el cuantil (MCO: {fmt(mco_.params[s0])})."
    return r


@metodo(
    "regresion_robusta",
    "Regresión robusta a outliers (Huber / Tukey)",
    F,
    "¿Los resultados dependen de unos pocos meses extremos (2002, 2020)?",
    params=[P_DEP, P_IND, P_FREQ, Param("transf", "opcion", "Transformación", defecto="dif_log", opciones=list(P_TRANSF.opciones)), Param("norma", "opcion", "Función de pérdida", defecto="huber", opciones=["huber", "tukey"])],
    cuando="Cuando la muestra tiene crisis que dominan la estimación MCO.",
    referencias=["Huber (1964)", "Maronna, Martin y Yohai (2006)"],
    etiquetas=["robusta", "huber", "tukey", "outliers", "m-estimador"],
)
def regresion_robusta(dep, indeps, freq, transf, norma):
    import statsmodels.api as sm

    df, et = panel([dep, *indeps], freq, transf, minimo=25)
    X = sm.add_constant(df[indeps])
    n = sm.robust.norms.HuberT() if norma == "huber" else sm.robust.norms.TukeyBiweight()
    rob = sm.RLM(df[dep], X, M=n).fit()
    ols = sm.OLS(df[dep], X).fit()
    r = Resultado()
    r.tabla("MCO vs robusta", ["variable", "MCO", "robusta", "diferencia %", "p robusta"], [[c, ols.params[c], rob.params[c], (rob.params[c] / ols.params[c] - 1) * 100 if ols.params[c] else None, rob.pvalues[c]] for c in X.columns], resaltar_p="p robusta")
    w = pd.Series(rob.weights, index=df.index)
    bajos = w[w < 0.5].sort_values()
    r.lineas("Peso de cada observación (1 = normal; cerca de 0 = outlier descontado)", df.index, {"peso": w.values})
    if len(bajos):
        r.tabla("Observaciones descontadas", ["fecha", "peso"], [[str(f.date()), v] for f, v in bajos.head(15).items()])
    cambio = max(abs(rob.params[c] / ols.params[c] - 1) for c in indeps if ols.params[c]) if any(ols.params[c] for c in indeps) else 0
    r.veredicto("Los coeficientes cambian más de 30 % al descontar outliers: el resultado MCO depende de pocos datos." if cambio > 0.3 else "Los resultados son robustos a outliers.", "amarillo" if cambio > 0.3 else "verde")
    r.resumen = f"Regresión robusta ({norma}) de {et[dep]}: {len(bajos)} observaciones con peso < 0,5; cambio máximo de coeficientes vs MCO {fmt(cambio * 100, 2)} %."
    return r


@metodo(
    "regresion_movil",
    "Regresión en ventanas móviles (coeficientes en el tiempo)",
    F,
    "¿El efecto de X sobre Y es estable o cambió con los regímenes?",
    params=[P_DEP, P_IND, P_FREQ, Param("transf", "opcion", "Transformación", defecto="dif_log", opciones=list(P_TRANSF.opciones)), Param("ventana", "entero", "Ventana (obs.)", defecto=60, minimo=15, maximo=400)],
    cuando="Primera mirada a la inestabilidad de parámetros, antes de un TVP con Kalman.",
    trampas=["Las ventanas se superponen: los coeficientes sucesivos no son independientes."],
    etiquetas=["rolling", "ventana móvil", "coeficientes variables", "inestabilidad"],
    nivel="basico",
)
def regresion_movil(dep, indeps, freq, transf, ventana):
    import statsmodels.api as sm
    from statsmodels.regression.rolling import RollingOLS

    df, et = panel([dep, *indeps], freq, transf, minimo=ventana + 10)
    X = sm.add_constant(df[indeps])
    res = RollingOLS(df[dep], X, window=ventana).fit()
    r = Resultado()
    ci = res.conf_int()
    for s in indeps:
        lo = ci[s]["lower"] if isinstance(ci.columns, pd.MultiIndex) else ci.xs(s, axis=1, level=0).iloc[:, 0]
        hi = ci[s]["upper"] if isinstance(ci.columns, pd.MultiIndex) else ci.xs(s, axis=1, level=0).iloc[:, 1]
        r.lineas(f"Coeficiente de {et[s]} en ventanas de {ventana}", df.index, {"coef": res.params[s].values, "IC inf.": lo.values, "IC sup.": hi.values}, estilos={"IC inf.": {"guion": "dot"}, "IC sup.": {"guion": "dot"}})
        b = res.params[s].dropna()
        r.metrica(f"{et[s]}: mín", b.min())
        r.metrica(f"{et[s]}: máx", b.max())
        r.serie(f"coef_movil_{s}"[:40], b.index, b.values, f"Coeficiente móvil de {et[s]} sobre {et[dep]}")
    r.resumen = f"Regresión móvil ({ventana} obs.) de {et[dep]}: " + "; ".join(f"{et[s]} entre {fmt(res.params[s].min())} y {fmt(res.params[s].max())}" for s in indeps) + "."
    return r


@metodo(
    "variables_instrumentales",
    "Variables instrumentales (MC2E) con pruebas de instrumentos",
    F,
    "¿Cuál es el efecto de X sobre Y si X es endógena, usando un instrumento Z?",
    params=[P_DEP, P_SERIES("endogenas", "Endógenas (X)", minimo=1, maximo=3), P_SERIES("instrumentos", "Instrumentos (Z)", minimo=1, maximo=6), P_SERIES("exogenas", "Controles exógenos", minimo=0, maximo=6, requerido=False), P_FREQ, Param("transf", "opcion", "Transformación", defecto="dif_log", opciones=list(P_TRANSF.opciones))],
    cuando="Simultaneidad (precio y cantidad), error de medida, variable omitida correlacionada con X.",
    supuestos=["Relevancia: Z correlaciona con X (F de primera etapa > 10).", "Exclusión: Z afecta a Y sólo vía X (no se testea con exactitud)."],
    trampas=["Instrumentos débiles sesgan MC2E hacia MCO y rompen la inferencia (Stock-Yogo).", "Con series de tiempo, rezagos como instrumentos sólo valen si los errores no están autocorrelacionados."],
    referencias=["Angrist y Pischke (2009), cap. 4", "Stock y Yogo (2005)"],
    etiquetas=["iv", "mc2e", "2sls", "endogeneidad", "instrumentos", "hausman"],
    nivel="avanzado",
)
def variables_instrumentales(dep, endogenas, instrumentos, exogenas, freq, transf):
    import statsmodels.api as sm
    from scipy import stats

    exo = exogenas or []
    df, et = panel([dep, *endogenas, *instrumentos, *exo], freq, transf, minimo=25)
    if len(instrumentos) < len(endogenas):
        raise ErrorMetodo("Hacen falta al menos tantos instrumentos como endógenas.")
    W = sm.add_constant(df[exo]) if exo else pd.DataFrame({"const": np.ones(len(df))}, index=df.index)
    Z = pd.concat([W, df[instrumentos]], axis=1)
    r = Resultado()
    filas1, Xhat = [], {}
    for x in endogenas:
        fs = sm.OLS(df[x], Z).fit()
        rest = sm.OLS(df[x], W).fit()
        q = len(instrumentos)
        Fst = ((rest.ssr - fs.ssr) / q) / (fs.ssr / (len(df) - Z.shape[1]))
        filas1.append([et[x], fs.rsquared, Fst, stats.f.sf(Fst, q, len(df) - Z.shape[1])])
        Xhat[x] = fs.fittedvalues
    r.tabla("Primera etapa (F > 10: instrumentos relevantes)", ["endógena", "R²", "F instrumentos", "p"], filas1)
    X2 = pd.concat([W, pd.DataFrame(Xhat)], axis=1)
    seg = sm.OLS(df[dep], X2).fit()
    Xorig = pd.concat([W, df[endogenas]], axis=1)
    u = df[dep] - Xorig.values @ seg.params.values
    s2 = (u**2).sum() / (len(df) - X2.shape[1])
    cov = s2 * np.linalg.inv(X2.T.values @ X2.values)
    ee = np.sqrt(np.diag(cov))
    t = seg.params.values / ee
    p = 2 * stats.t.sf(np.abs(t), len(df) - X2.shape[1])
    mco_ = sm.OLS(df[dep], Xorig).fit()
    nombres = list(X2.columns)
    r.tabla("Segunda etapa (MC2E) vs MCO", ["variable", "MC2E", "EE", "p", "MCO"], [[et.get(n, n), seg.params.values[i], ee[i], p[i], mco_.params.values[i]] for i, n in enumerate(nombres)], resaltar_p="p")
    # Hausman (regresión aumentada / Durbin-Wu-Hausman)
    v = pd.DataFrame({f"v_{x}": df[x] - Xhat[x] for x in endogenas})
    aug = sm.OLS(df[dep], pd.concat([Xorig, v], axis=1)).fit()
    ph = float(aug.f_test(np.eye(aug.params.size)[-len(endogenas):]).pvalue)
    r.metrica("Durbin-Wu-Hausman p", ph, "H0: X es exógena (MCO consistente)")
    debil = min(f[2] for f in filas1) < 10
    if debil:
        r.advertir("Instrumentos débiles (F < 10): el estimador MC2E está sesgado y sus p-valores no son confiables.")
    if len(instrumentos) > len(endogenas):
        J = len(df) * sm.OLS(u, Z).fit().rsquared
        pj = stats.chi2.sf(J, len(instrumentos) - len(endogenas))
        r.metrica("Sargan (sobreidentificación) p", pj, "H0: instrumentos válidos")
    r.veredicto(("Instrumentos débiles: no concluyas con MC2E. " if debil else "") + ("Hausman rechaza exogeneidad: preferí MC2E." if ph < 0.05 else "Hausman no rechaza exogeneidad: MCO es consistente y más eficiente."), "rojo" if debil else ("amarillo" if ph < 0.05 else "verde"))
    r.resumen = f"MC2E de {et[dep]} sobre {', '.join(et[x] for x in endogenas)} con {len(instrumentos)} instrumentos: F primera etapa mín {fmt(min(f[2] for f in filas1))}; Hausman p={fmt(ph)}."
    return r


@metodo(
    "rezagos_distribuidos",
    "Rezagos distribuidos (polinomio de Almon)",
    F,
    "¿Cómo se reparte en el tiempo el efecto de X sobre Y (traspaso, pass-through)?",
    params=[P_DEP, P_SERIE("sid_x", "Impulso (X)"), P_FREQ, Param("transf", "opcion", "Transformación", defecto="dif_log", opciones=list(P_TRANSF.opciones)), Param("rezagos", "entero", "Rezagos", defecto=12, minimo=2, maximo=36), Param("grado", "entero", "Grado del polinomio", defecto=2, minimo=1, maximo=4)],
    cuando="Traspaso del tipo de cambio a precios, efecto de la tasa sobre la actividad: interesa la forma y el efecto acumulado.",
    trampas=["El polinomio impone suavidad: comparalo con los rezagos libres."],
    referencias=["Almon (1965)"],
    etiquetas=["almon", "pass-through", "traspaso", "rezagos", "efecto acumulado", "multiplicador"],
)
def rezagos_distribuidos(dep, sid_x, freq, transf, rezagos, grado):
    import statsmodels.api as sm

    df, et = panel([dep, sid_x], freq, transf, minimo=rezagos + 20)
    L = pd.concat({k: df[sid_x].shift(k) for k in range(rezagos + 1)}, axis=1).dropna()
    y = df[dep].loc[L.index]
    ks = np.arange(rezagos + 1)
    B = np.column_stack([ks**g for g in range(grado + 1)])
    Zm = L.values @ B
    res = sm.OLS(y.values, sm.add_constant(Zm)).fit(cov_type="HAC", cov_kwds={"maxlags": 6})
    gam = res.params[1:]
    cg = res.cov_params()[1:, 1:]
    w = B @ gam
    ee = np.sqrt(np.diag(B @ cg @ B.T))
    libre = sm.OLS(y.values, sm.add_constant(L.values)).fit()
    acum = np.cumsum(w)
    r = Resultado()
    r.barras(f"Efecto de {et[sid_x]} sobre {et[dep]} por rezago", list(ks), {"Almon": w, "libre": libre.params[1:]})
    r.lineas("Efecto acumulado", list(ks), {"acumulado (Almon)": acum, "acumulado (libre)": np.cumsum(libre.params[1:])})
    r.tabla("Coeficientes por rezago", ["rezago", "Almon", "EE", "acumulado"], [[int(k), w[k], ee[k], acum[k]] for k in ks])
    r.metrica("Efecto de impacto", w[0])
    r.metrica("Efecto de largo plazo (suma)", acum[-1])
    medio = int(np.argmax(np.abs(acum) >= abs(acum[-1]) / 2)) if acum[-1] else None
    r.metrica("Rezago medio (mitad del efecto)", medio)
    r.resumen = f"Rezagos distribuidos de {et[sid_x]} sobre {et[dep]} ({rezagos} rezagos, Almon grado {grado}): impacto {fmt(w[0])}, largo plazo {fmt(acum[-1])}; la mitad del efecto llega en {medio} períodos."
    return r
