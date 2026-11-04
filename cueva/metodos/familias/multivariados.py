"""Sistemas multivariados: VAR con impulso-respuesta y descomposición de varianza, proyecciones
locales de Jordà, causalidad de Toda-Yamamoto y BVAR con prior de Minnesota."""

from __future__ import annotations

import numpy as np
import pandas as pd

from cueva.metodos.contrato import ErrorMetodo, Param, Resultado
from cueva.metodos.insumos import P_DESDE, P_FREQ, P_HASTA, P_SERIE, P_SERIES, P_TRANSF, fmt, panel
from cueva.metodos.registro import metodo

F = "multivariados"
P_SIS = P_SERIES("sids", "Series del sistema (el orden importa para Cholesky)", minimo=2, maximo=6)
P_DIF = Param("transf", "opcion", "Transformación", defecto="dif_log", opciones=list(P_TRANSF.opciones))


@metodo(
    "var_completo",
    "VAR: impulso-respuesta, descomposición de varianza y Granger",
    F,
    "¿Cómo se propaga un shock de una variable al resto del sistema, y cuánto explica de cada una?",
    params=[
        P_SIS,
        P_FREQ,
        P_DIF,
        Param("rezagos", "entero", "Rezagos (0 = por criterio)", defecto=0, minimo=0, maximo=24),
        Param("criterio", "opcion", "Criterio", defecto="aic", opciones=["aic", "bic", "hqic", "fpe"]),
        Param("horizonte", "entero", "Horizonte IRF", defecto=24, minimo=4, maximo=60),
        Param("identificacion", "opcion", "Identificación", defecto="cholesky", opciones=["cholesky", "generalizada"], ayuda="Cholesky depende del orden; la generalizada (Pesaran-Shin) no"),
        P_DESDE,
        P_HASTA,
    ],
    cuando="Política monetaria y cambiaria: shocks de tasa, tipo de cambio o emisión y su efecto sobre precios y actividad.",
    supuestos=["Variables estacionarias (o un VECM si cointegran).", "Cholesky: la primera variable no reacciona en el período a las demás."],
    trampas=[
        "Con Cholesky el ORDEN es un supuesto económico: escribilo y defendelo.",
        "Demasiadas variables × rezagos agotan los grados de libertad (k²p parámetros).",
        "Un VAR en diferencias de series cointegradas descarta la información de largo plazo.",
    ],
    costo="segundos",
    referencias=["Sims (1980)", "Lütkepohl (2005)", "Pesaran y Shin (1998)", "Kilian y Lütkepohl (2017)"],
    etiquetas=["var", "irf", "impulso respuesta", "fevd", "cholesky", "granger", "shock"],
)
def var_completo(sids, freq, transf, rezagos, criterio, horizonte, identificacion, desde, hasta):
    from statsmodels.tsa.api import VAR

    df, et = panel(sids, freq, transf, desde, hasta, minimo=40)
    df.columns = [et[s] for s in sids]
    mod = VAR(df.values)
    maxl = max(1, min(12, len(df) // (5 * len(sids))))
    if rezagos:
        p = rezagos
    else:
        sel = mod.select_order(maxlags=maxl)
        p = max(1, int(sel.selected_orders[criterio]))
    res = mod.fit(p)
    nombres = list(df.columns)
    k = len(nombres)
    r = Resultado()
    r.metrica("Rezagos", p)
    r.metrica("Obs.", res.nobs)
    r.metrica("Estable", "sí" if res.is_stable() else "NO")
    if not res.is_stable():
        r.advertir("El VAR no es estable (raíces fuera del círculo unitario): las IRF no convergen. Diferenciá o bajá rezagos.")
    # Granger por pares
    filas_g = []
    for i, causa in enumerate(nombres):
        for j, efecto in enumerate(nombres):
            if i == j:
                continue
            t = res.test_causality(j, [i], kind="f")
            filas_g.append([causa, efecto, t.test_statistic, t.pvalue])
    r.tabla("Causalidad de Granger (¿la fila precede a la columna?)", ["causa", "efecto", "F", "p"], filas_g, resaltar_p="p")
    # IRF
    irf = res.irf(horizonte)
    if identificacion == "cholesky":
        resp = irf.orth_irfs
        try:
            lo, hi = irf.errband_mc(orth=True, repl=200, signif=0.05, seed=1)
        except Exception:
            lo = hi = None
    else:
        # generalizada (Pesaran-Shin): Θ_h Σ e_j / sqrt(σ_jj)
        S = res.sigma_u
        resp = np.stack([irf.irfs[h] @ S / np.sqrt(np.diag(S)) for h in range(horizonte + 1)])
        lo = hi = None
    hs = list(range(horizonte + 1))
    shock = 0
    for j, efecto in enumerate(nombres):
        series = {f"shock {nombres[shock]}": resp[:, j, shock]}
        est = {}
        if lo is not None:
            series["IC inf."] = lo[:, j, shock]
            series["IC sup."] = hi[:, j, shock]
            est = {"IC inf.": {"guion": "dot"}, "IC sup.": {"guion": "dot"}}
        r.lineas(f"Respuesta de {efecto} a un shock en {nombres[shock]}", hs, series, estilos=est)
    # FEVD
    fe = res.fevd(horizonte)
    filas_f = []
    for h in sorted({1, 4, 12, horizonte} & set(range(1, horizonte + 1))):
        for j, v in enumerate(nombres):
            filas_f.append([h, v, *[fe.decomp[j, h - 1, i] * 100 for i in range(k)]])
    r.tabla("Descomposición de la varianza del error de pronóstico (%)", ["horizonte", "variable", *[f"por {n}" for n in nombres]], filas_f)
    # todas las IRF como datos (para que el agente las lea)
    r.datos = {"irf": resp.tolist(), "nombres": nombres, "rezagos": p}
    sig = [f"{f[0]}→{f[1]}" for f in filas_g if f[3] < 0.05]
    r.veredicto(f"VAR({p}) {'estable' if res.is_stable() else 'INESTABLE'}; Granger significativo: {', '.join(sig) or 'ninguno'}.", "verde" if res.is_stable() else "rojo")
    r.resumen = f"VAR({p}) con {', '.join(nombres)} (n={res.nobs}, {identificacion}): Granger significativo en {', '.join(sig) or 'ningún par'}. A {horizonte} períodos, {nombres[shock]} explica {fmt(fe.decomp[-1, -1, 0] * 100, 2)} % de la varianza de {nombres[-1]}."
    r.codigo = f"from statsmodels.tsa.api import VAR\nres = VAR(df).fit({p})\nres.irf({horizonte}).plot(orth=True)\nres.fevd({horizonte}).summary()"
    return r


@metodo(
    "proyecciones_locales",
    "Proyecciones locales (Jordà)",
    F,
    "¿Cuál es la respuesta de Y, h períodos después, a un cambio en X, sin imponer la dinámica de un VAR?",
    params=[
        P_SERIE("dep", "Respuesta (Y)"),
        P_SERIE("impulso", "Impulso (X)"),
        P_SERIES("controles", "Controles", minimo=0, maximo=5, requerido=False),
        P_FREQ,
        P_DIF,
        Param("horizonte", "entero", "Horizonte", defecto=24, minimo=2, maximo=60),
        Param("rezagos", "entero", "Rezagos de control", defecto=4, minimo=0, maximo=12),
        Param("acumulada", "bool", "Respuesta acumulada (y_{t+h} − y_{t−1})", defecto=True),
    ],
    cuando="Más robusto a la mala especificación que un VAR; permite no linealidades y estados (Ramey 2016).",
    supuestos=["El impulso es exógeno condicional a los controles (o un shock identificado externamente)."],
    trampas=["Bandas más anchas que el VAR en horizontes largos: es el precio de la robustez.", "Con el impulso contemporáneo endógeno, es una correlación dinámica, no un efecto causal."],
    referencias=["Jordà (2005)", "Plagborg-Møller y Wolf (2021)", "Montiel Olea y Plagborg-Møller (2021)"],
    etiquetas=["local projections", "jordà", "impulso respuesta", "lp", "shock"],
)
def proyecciones_locales(dep, impulso, controles, freq, transf, horizonte, rezagos, acumulada):
    import statsmodels.api as sm

    ctr = controles or []
    df, et = panel([dep, impulso, *ctr], freq, transf, minimo=40)
    y = df[dep]
    base = {"impulso": df[impulso]}
    for k in range(1, rezagos + 1):
        base[f"y_L{k}"] = y.shift(k)
        base[f"x_L{k}"] = df[impulso].shift(k)
        for c in ctr:
            base[f"{c}_L{k}"] = df[c].shift(k)
    for c in ctr:
        base[c] = df[c]
    B = pd.DataFrame(base)
    nivel = y.cumsum() if acumulada else None
    coef, lo, hi, ns = [], [], [], []
    for h in range(horizonte + 1):
        obj = (nivel.shift(-h) - nivel.shift(1)) if acumulada else y.shift(-h)
        d = pd.concat([obj.rename("obj"), B], axis=1).dropna()
        if len(d) < 20:
            break
        res = sm.OLS(d["obj"], sm.add_constant(d.drop(columns="obj"))).fit(cov_type="HAC", cov_kwds={"maxlags": h + 1})
        b, e = res.params["impulso"], res.bse["impulso"]
        coef.append(b)
        lo.append(b - 1.96 * e)
        hi.append(b + 1.96 * e)
        ns.append(len(d))
    if not coef:
        raise ErrorMetodo("Muestra demasiado corta para proyectar.")
    hs = list(range(len(coef)))
    r = Resultado()
    r.lineas(f"Respuesta {'acumulada ' if acumulada else ''}de {et[dep]} a un aumento unitario de {et[impulso]}", hs, {"respuesta": coef, "IC inf.": lo, "IC sup.": hi}, estilos={"IC inf.": {"guion": "dot"}, "IC sup.": {"guion": "dot"}})
    r.tabla("Coeficientes por horizonte (EE Newey-West)", ["h", "respuesta", "IC inf.", "IC sup.", "obs."], [[h, c, a, b, n] for h, c, a, b, n in zip(hs, coef, lo, hi, ns, strict=True)])
    pico = int(np.argmax(np.abs(coef)))
    r.metrica("Impacto (h=0)", coef[0])
    r.metrica("Respuesta máxima", coef[pico])
    r.metrica("Horizonte del máximo", pico)
    r.metrica(f"Respuesta a h={hs[-1]}", coef[-1])
    sig = [h for h in hs if lo[h] > 0 or hi[h] < 0]
    r.veredicto(f"La respuesta es significativa en {len(sig)} de {len(hs)} horizontes." if sig else "La respuesta no es significativa en ningún horizonte.", "verde" if sig else "amarillo")
    r.resumen = f"Proyecciones locales: {et[dep]} responde a {et[impulso]} con {fmt(coef[0])} en el impacto y {fmt(coef[pico])} como máximo (h={pico}); significativa en {len(sig)} horizontes."
    return r


@metodo(
    "toda_yamamoto",
    "Causalidad de Toda-Yamamoto (en niveles, válida con raíces unitarias)",
    F,
    "¿X precede a Y, sin tener que decidir antes si las series son I(0), I(1) o cointegran?",
    params=[P_SERIE("sid_x", "Causa candidata (X)"), P_SERIE("sid_y", "Efecto (Y)"), P_FREQ, Param("transf", "opcion", "Transformación", defecto="log", opciones=["nivel", "log"]), Param("d_max", "entero", "Orden máximo de integración", defecto=1, minimo=1, maximo=2)],
    cuando="Cuando los tests de raíz unitaria son ambiguos (típico en Argentina con quiebres).",
    supuestos=["Se agrega d_max rezagos extra que no se testean: eso restaura la distribución χ² del Wald."],
    referencias=["Toda y Yamamoto (1995)"],
    etiquetas=["toda-yamamoto", "granger", "niveles", "causalidad", "wald"],
    nivel="avanzado",
)
def toda_yamamoto(sid_x, sid_y, freq, transf, d_max):
    import statsmodels.api as sm
    from scipy import stats
    from statsmodels.tsa.api import VAR

    df, et = panel([sid_y, sid_x], freq, transf, minimo=40)
    p = max(1, int(VAR(df.values).select_order(maxlags=min(12, len(df) // 10)).selected_orders["aic"]))
    m = p + d_max
    filas = []
    for causa, efecto in ((sid_x, sid_y), (sid_y, sid_x)):
        cols = {}
        for k in range(1, m + 1):
            cols[f"e_L{k}"] = df[efecto].shift(k)
            cols[f"c_L{k}"] = df[causa].shift(k)
        X = sm.add_constant(pd.DataFrame(cols)).dropna()
        yv = df[efecto].loc[X.index]
        res = sm.OLS(yv, X).fit()
        R = np.zeros((p, len(res.params)))
        for i in range(p):
            R[i, list(res.params.index).index(f"c_L{i + 1}")] = 1
        w = res.wald_test(R, scalar=True)
        stat = float(w.statistic)
        pv = float(stats.chi2.sf(stat, p))
        filas.append([et[causa], et[efecto], stat, pv])
    r = Resultado()
    r.metrica("Rezagos (p, por AIC)", p)
    r.metrica("Rezagos extra (d_max)", d_max)
    r.tabla("Wald sobre los primeros p rezagos (χ²)", ["causa", "efecto", "Wald", "p"], filas, resaltar_p="p")
    d1, d2 = filas[0][3] < 0.05, filas[1][3] < 0.05
    txt = "bidireccional" if d1 and d2 else (f"{et[sid_x]} → {et[sid_y]}" if d1 else (f"{et[sid_y]} → {et[sid_x]}" if d2 else "sin precedencia"))
    r.veredicto(f"Toda-Yamamoto: {txt}. Es precedencia temporal, no causalidad económica.", "verde" if d1 or d2 else "amarillo")
    r.resumen = f"Toda-Yamamoto (p={p}, d_max={d_max}): {txt} (p={fmt(filas[0][3])} y {fmt(filas[1][3])})."
    return r


@metodo(
    "bvar_minnesota",
    "VAR bayesiano con prior de Minnesota",
    F,
    "Un VAR con muchas variables o pocos datos, donde el prior evita el sobreajuste.",
    params=[P_SERIES("sids", "Series del sistema", minimo=2, maximo=8), P_FREQ, P_DIF, Param("rezagos", "entero", "Rezagos", defecto=4, minimo=1, maximo=13), Param("lambda1", "real", "Ajuste general λ₁ (más chico = más prior)", defecto=0.2, minimo=0.01, maximo=5), Param("horizonte", "entero", "Horizonte de pronóstico", defecto=12, minimo=1, maximo=36)],
    cuando="Pronóstico macro con 5-8 variables (Litterman 1986; Bańbura, Giannone y Reichlin 2010).",
    supuestos=["Prior: cada variable es un paseo aleatorio (o ruido, en diferencias) y los rezagos lejanos importan menos."],
    trampas=["El prior manda con pocos datos: mostrá la sensibilidad a λ₁."],
    referencias=["Litterman (1986)", "Bańbura, Giannone y Reichlin (2010)", "Koop y Korobilis (2010)"],
    etiquetas=["bvar", "bayesiano", "minnesota", "litterman", "shrinkage", "pronóstico"],
    nivel="avanzado",
)
def bvar_minnesota(sids, freq, transf, rezagos, lambda1, horizonte):
    from cueva.metodos.insumos import fechas_futuras

    df, et = panel(sids, freq, transf, minimo=40)
    Y = df.values
    T, k = Y.shape
    p = rezagos
    X = np.column_stack([np.ones(T - p)] + [Y[p - L : T - L] for L in range(1, p + 1)])
    Yt = Y[p:]
    # escalas: desvío de un AR(1) por variable
    sig = []
    for i in range(k):
        y = Y[:, i]
        b = np.polyfit(y[:-1], y[1:], 1)
        sig.append(np.std(y[1:] - np.polyval(b, y[:-1])))
    sig = np.array(sig)
    media0 = 1.0 if transf in ("nivel", "log") else 0.0
    B0 = np.zeros((1 + k * p, k))
    V0 = np.zeros(1 + k * p)
    V0[0] = 100.0
    for L in range(1, p + 1):
        for j in range(k):
            V0[1 + (L - 1) * k + j] = (lambda1 / L) ** 2 / sig[j] ** 2
    for i in range(k):
        B0[1 + i, i] = media0
    Bpost = np.zeros_like(B0)
    for i in range(k):
        Vi = V0 * sig[i] ** 2
        prec = np.diag(1 / Vi) + X.T @ X / sig[i] ** 2
        Bpost[:, i] = np.linalg.solve(prec, np.diag(1 / Vi) @ B0[:, i] + X.T @ Yt[:, i] / sig[i] ** 2)
    ols = np.linalg.lstsq(X, Yt, rcond=None)[0]
    # pronóstico iterado (media posterior)
    hist = list(Y[-p:])
    pron = []
    for _ in range(horizonte):
        x = np.concatenate([[1.0]] + [hist[-L] for L in range(1, p + 1)])
        yhat = x @ Bpost
        pron.append(yhat)
        hist.append(yhat)
    pron = np.array(pron)
    fut = fechas_futuras(df.index[-1], horizonte, freq)
    r = Resultado()
    for i, s in enumerate(sids):
        n = {"mensual": 60, "trimestral": 24, "anual": 20}.get(freq, 60)
        r.bandas(f"Pronóstico BVAR de {et[s]}", df.index[-n:], df[s].values[-n:], fut, pron[:, i])
    enc = np.mean(np.abs(Bpost[1:] - ols[1:])) / (np.mean(np.abs(ols[1:])) or 1)
    r.metrica("Rezagos", p)
    r.metrica("λ₁", lambda1)
    r.metrica("Encogimiento medio vs MCO", enc, "cuánto se movieron los coeficientes hacia el prior")
    r.tabla("Pronóstico (media posterior)", ["fecha", *[et[s] for s in sids]], [[str(f.date()), *row] for f, row in zip(fut, pron, strict=True)])
    r.resumen = f"BVAR-Minnesota({p}) con {len(sids)} variables, λ₁={lambda1}: los coeficientes se encogen {fmt(enc * 100, 2)} % hacia el prior en promedio."
    return r
