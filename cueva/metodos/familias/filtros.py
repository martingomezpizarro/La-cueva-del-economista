"""Filtros y descomposición: tendencia, ciclo y estacionalidad.

Todos producen SERIES DERIVADAS (tendencia, ciclo, desestacionalizada) que quedan disponibles
como insumo de otros pasos: la brecha del producto de un HP puede entrar en una curva de
Phillips, el ciclo de Hamilton en un Markov, etc.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from cueva.metodos.contrato import ErrorMetodo, Param, Resultado
from cueva.metodos.insumos import LAMBDA_HP, P_DESDE, P_FREQ, P_HASTA, P_SERIE, PERIODO, fmt, serie
from cueva.metodos.registro import metodo

F = "filtros"
P_LOG = Param("transf", "opcion", "Transformación", defecto="log", opciones=["nivel", "log"], ayuda="Con log, el ciclo se lee como % de desvío")


def _publicar(r: Resultado, s, et, tendencia, ciclo, nombre_metodo, sid):
    r.lineas(f"{et}: serie y tendencia ({nombre_metodo})", s.index, {et: s.values, "tendencia": tendencia}, estilos={"tendencia": {"ancho": 2.5}})
    c = np.asarray(ciclo, float)
    r.lineas(f"Ciclo ({nombre_metodo})", s.index[-len(c):], {"ciclo": c})
    r.serie(f"{sid}_tend_{nombre_metodo.lower()[:8]}", s.index[-len(tendencia):], tendencia, f"Tendencia de {et} ({nombre_metodo})")
    r.serie(f"{sid}_ciclo_{nombre_metodo.lower()[:8]}", s.index[-len(c):], c, f"Ciclo de {et} ({nombre_metodo})")
    cv = c[np.isfinite(c)]
    r.metrica("Desvío del ciclo", cv.std())
    r.metrica("Ciclo actual", cv[-1])
    r.metrica("Persistencia AR(1) del ciclo", np.corrcoef(cv[1:], cv[:-1])[0, 1])
    return cv


@metodo(
    "filtro_hp",
    "Filtro de Hodrick-Prescott",
    F,
    "¿Cuál es la tendencia y cuál el ciclo (la brecha) de la serie?",
    params=[P_SERIE(), P_FREQ, P_LOG, Param("lamb", "real", "λ (0 = estándar por frecuencia)", defecto=0.0, minimo=0, maximo=1e9), P_DESDE, P_HASTA],
    cuando="Brecha del producto, ciclo económico. Es el estándar de la literatura, con sus defectos conocidos.",
    supuestos=["λ = 1600 trimestral, 129600 mensual (Ravn-Uhlig), 6,25 anual."],
    trampas=[
        "Sesgo de punta: el último tramo del ciclo se revisa mucho al llegar datos nuevos. NO lo uses para 'la brecha de hoy'.",
        "Puede generar ciclos espurios en un paseo aleatorio (Hamilton 2018): contrastá con el filtro de Hamilton.",
    ],
    referencias=["Hodrick y Prescott (1997)", "Ravn y Uhlig (2002)", "Hamilton (2018)"],
    etiquetas=["hp", "brecha del producto", "tendencia", "ciclo", "output gap"],
    nivel="basico",
)
def filtro_hp(sid, freq, transf, lamb, desde, hasta):
    from statsmodels.tsa.filters.hp_filter import hpfilter

    s, et = serie(sid, freq, transf, desde, hasta, minimo=20)
    lam = lamb or LAMBDA_HP.get(freq, 1600)
    ciclo, tend = hpfilter(s.values, lamb=lam)
    r = Resultado()
    escala = 100 if transf == "log" else 1
    _publicar(r, s, et, tend, ciclo * escala, "HP", sid)
    r.metrica("λ", lam)
    r.advertir("El ciclo HP de los últimos 2-3 años se revisa mucho cuando llegan datos nuevos (sesgo de punta).")
    r.resumen = f"HP (λ={fmt(lam)}) sobre {et}: ciclo actual {fmt(ciclo[-1] * escala)}{' %' if escala == 100 else ''}, desvío {fmt(np.std(ciclo) * escala)}."
    r.codigo = f"from statsmodels.tsa.filters.hp_filter import hpfilter\nciclo, tendencia = hpfilter(s, lamb={lam})"
    return r


@metodo(
    "filtro_hamilton",
    "Filtro de Hamilton (regresión)",
    F,
    "¿Cuál es el ciclo, sin los artefactos del HP?",
    params=[P_SERIE(), P_FREQ, P_LOG, Param("h", "entero", "Horizonte h (0 = 2 años)", defecto=0, minimo=0, maximo=60), Param("p", "entero", "Rezagos p (0 = 1 año)", defecto=0, minimo=0, maximo=24), P_DESDE, P_HASTA],
    cuando="Alternativa moderna al HP: el ciclo es el error de pronosticar y_{t+h} con y_t…y_{t−p+1}.",
    supuestos=["h = 2 años y p = 1 año (8 y 4 en trimestral) según Hamilton (2018)."],
    trampas=["Se pierden las primeras h+p observaciones."],
    referencias=["Hamilton (2018), 'Why you should never use the Hodrick-Prescott filter'"],
    etiquetas=["hamilton", "ciclo", "brecha", "alternativa hp"],
)
def filtro_hamilton(sid, freq, transf, h, p, desde, hasta):
    s, et = serie(sid, freq, transf, desde, hasta, minimo=30)
    per = PERIODO.get(freq, 1)
    h = h or 2 * per
    p = p or max(1, per)
    y = s.values
    filas = range(p - 1, len(y) - h)
    X = np.column_stack([np.ones(len(filas))] + [[y[t - j] for t in filas] for j in range(p)])
    obj = np.array([y[t + h] for t in filas])
    beta, *_ = np.linalg.lstsq(X, obj, rcond=None)
    ajuste = X @ beta
    ciclo = obj - ajuste
    idx = s.index[p - 1 + h :]
    escala = 100 if transf == "log" else 1
    tend = pd.Series(np.nan, index=s.index)
    tend.iloc[p - 1 + h :] = ajuste
    r = Resultado()
    _publicar(r, s, et, tend.values, ciclo * escala, "Hamilton", sid)
    r.metrica("h", h)
    r.metrica("p", p)
    r.resumen = f"Filtro de Hamilton (h={h}, p={p}) sobre {et}: ciclo actual {fmt(ciclo[-1] * escala)}, desvío {fmt(ciclo.std() * escala)} (desde {idx[0].date()})."
    return r


@metodo(
    "filtro_bandas",
    "Filtros de banda (Baxter-King y Christiano-Fitzgerald)",
    F,
    "¿Qué parte de la serie oscila con la frecuencia del ciclo económico (1,5 a 8 años)?",
    params=[P_SERIE(), P_FREQ, P_LOG, Param("anios_min", "real", "Ciclo mínimo (años)", defecto=1.5, minimo=0.5, maximo=10), Param("anios_max", "real", "Ciclo máximo (años)", defecto=8.0, minimo=1, maximo=30), P_DESDE, P_HASTA],
    cuando="Para aislar el ciclo de negocios de la tendencia y del ruido de alta frecuencia a la vez.",
    trampas=["BK pierde K observaciones en cada punta; CF no, pero es asimétrico en los extremos."],
    referencias=["Baxter y King (1999)", "Christiano y Fitzgerald (2003)"],
    etiquetas=["baxter-king", "christiano-fitzgerald", "pasabanda", "ciclo de negocios"],
)
def filtro_bandas(sid, freq, transf, anios_min, anios_max, desde, hasta):
    from statsmodels.tsa.filters.bk_filter import bkfilter
    from statsmodels.tsa.filters.cf_filter import cffilter

    s, et = serie(sid, freq, transf, desde, hasta, minimo=40)
    per = PERIODO.get(freq, 1)
    lo, hi = max(2, int(round(anios_min * per))), max(3, int(round(anios_max * per)))
    if lo >= hi:
        raise ErrorMetodo("El ciclo mínimo tiene que ser menor que el máximo.")
    K = min(3 * per, len(s) // 4)
    bk = bkfilter(s.values, low=lo, high=hi, K=K)
    cf, _ = cffilter(s.values, low=lo, high=hi, drift=True)
    escala = 100 if transf == "log" else 1
    bkf = np.full(len(s), np.nan)
    bkf[K : len(s) - K] = bk * escala
    r = Resultado()
    r.lineas(f"Ciclo de {anios_min}-{anios_max} años de {et}", s.index, {"Baxter-King": bkf, "Christiano-Fitzgerald": cf * escala})
    r.serie(f"{sid}_ciclo_cf", s.index, cf * escala, f"Ciclo CF ({anios_min}-{anios_max} años) de {et}")
    r.metrica("Desvío CF", np.std(cf * escala))
    r.metrica("Correlación BK-CF", pd.Series(bkf).corr(pd.Series(cf * escala)))
    r.resumen = f"Pasabanda {anios_min}-{anios_max} años sobre {et}: desvío del ciclo CF {fmt(np.std(cf * escala))}; BK pierde {K} obs. por punta."
    return r


@metodo(
    "descomposicion_stl",
    "Descomposición estacional STL",
    F,
    "¿Cuánto de la serie es tendencia, cuánto estacionalidad y cuánto irregular?",
    params=[P_SERIE(), Param("freq", "opcion", "Frecuencia", defecto="mensual", opciones=["mensual", "trimestral"]), Param("transf", "opcion", "Transformación", defecto="log", opciones=["nivel", "log"]), Param("robusta", "bool", "Robusta a outliers", defecto=True), P_DESDE, P_HASTA],
    cuando="Para desestacionalizar sin X-13 o para ver si la estacionalidad cambió con los años.",
    supuestos=["Estacionalidad aditiva (con log, multiplicativa en niveles)."],
    trampas=["No corrige por días hábiles ni Semana Santa como X-13-ARIMA-SEATS del INDEC."],
    referencias=["Cleveland et al. (1990)"],
    etiquetas=["stl", "desestacionalizar", "estacionalidad", "loess", "x-13"],
    nivel="basico",
)
def descomposicion_stl(sid, freq, transf, robusta, desde, hasta):
    from statsmodels.tsa.seasonal import STL

    s, et = serie(sid, freq, transf, desde, hasta, minimo=3 * PERIODO[freq])
    per = PERIODO[freq]
    res = STL(s, period=per, robust=robusta).fit()
    r = Resultado()
    r.lineas(f"{et}: observada y desestacionalizada", s.index, {et: s.values, "desestacionalizada": (s - res.seasonal).values, "tendencia": res.trend.values}, estilos={"tendencia": {"ancho": 2.5}})
    r.lineas("Componente estacional", s.index, {"estacional": res.seasonal.values})
    r.lineas("Irregular", s.index, {"irregular": res.resid.values})
    var = np.var(s.values)
    fuerza_est = max(0, 1 - np.var(res.resid) / np.var(res.resid + res.seasonal))
    fuerza_tend = max(0, 1 - np.var(res.resid) / np.var(res.resid + res.trend))
    r.metrica("Fuerza de la estacionalidad", fuerza_est, "0 = nada; 1 = toda la variación no tendencial es estacional")
    r.metrica("Fuerza de la tendencia", fuerza_tend)
    r.metrica("% varianza irregular", np.var(res.resid) / var * 100)
    r.serie(f"{sid}_sa_stl", s.index, (s - res.seasonal).values, f"{et} desestacionalizada (STL)")
    r.serie(f"{sid}_tend_stl", s.index, res.trend.values, f"Tendencia STL de {et}")
    r.resumen = f"STL sobre {et}: fuerza estacional {fmt(fuerza_est, 2)}, fuerza de tendencia {fmt(fuerza_tend, 2)}."
    r.codigo = f"from statsmodels.tsa.seasonal import STL\nres = STL(s, period={per}, robust={robusta}).fit()"
    return r


@metodo(
    "beveridge_nelson",
    "Descomposición de Beveridge-Nelson",
    F,
    "¿Cuánto de lo que se ve hoy es permanente y cuánto se va a revertir?",
    params=[P_SERIE(), P_FREQ, P_LOG, Param("p", "entero", "Rezagos del AR sobre Δy", defecto=4, minimo=1, maximo=24), P_DESDE, P_HASTA],
    cuando="Cuando la serie es I(1): la tendencia BN es el nivel al que se espera que converja (pronóstico de largo plazo).",
    supuestos=["Δy sigue un AR(p) estacionario."],
    trampas=["El ciclo BN suele ser chico y ruidoso con AR de bajo orden (Morley, Nelson y Zivot 2003)."],
    referencias=["Beveridge y Nelson (1981)", "Kamber, Morley y Wong (2018)"],
    etiquetas=["beveridge-nelson", "permanente", "transitorio", "tendencia estocástica"],
    nivel="avanzado",
)
def beveridge_nelson(sid, freq, transf, p, desde, hasta):
    s, et = serie(sid, freq, transf, desde, hasta, minimo=40)
    dy = np.diff(s.values)
    mu = dy.mean()
    z = dy - mu
    n = len(z)
    X = np.column_stack([z[p - 1 - j : n - 1 - j] for j in range(p)])
    phi, *_ = np.linalg.lstsq(X, z[p:], rcond=None)
    Fm = np.zeros((p, p))
    Fm[0, :] = phi
    Fm[1:, :-1] = np.eye(p - 1)
    if np.max(np.abs(np.linalg.eigvals(Fm))) >= 1:
        raise ErrorMetodo("El AR estimado sobre Δy no es estacionario: bajá p o revisá la transformación.")
    A = Fm @ np.linalg.inv(np.eye(p) - Fm)
    ciclo = np.full(len(s), np.nan)
    for t in range(p - 1, n):
        estado = z[t - p + 1 : t + 1][::-1]
        ciclo[t + 1] = -(A @ estado)[0]
    tend = s.values - ciclo
    escala = 100 if transf == "log" else 1
    r = Resultado()
    _publicar(r, s, et, tend, ciclo * escala, "BN", sid)
    r.metrica("Deriva media de Δy", mu)
    r.resumen = f"Beveridge-Nelson con AR({p}) sobre Δ{et}: componente transitorio actual {fmt(ciclo[-1] * escala)}, desvío {fmt(np.nanstd(ciclo) * escala)}."
    return r


@metodo(
    "componentes_no_observados",
    "Modelo de componentes no observados (Harvey)",
    F,
    "Tendencia, ciclo y estacionalidad estimados como estados con el filtro de Kalman.",
    params=[
        P_SERIE(),
        P_FREQ,
        P_LOG,
        Param("tendencia", "opcion", "Tendencia", defecto="llevel", opciones=["llevel", "lltrend", "rwdrift", "smooth"], ayuda="llevel = nivel local; lltrend = tendencia lineal local; smooth = tendencia suave"),
        Param("ciclo", "bool", "Ciclo estocástico", defecto=True),
        Param("estacional", "bool", "Estacionalidad", defecto=False),
        P_DESDE,
        P_HASTA,
    ],
    cuando="Cuando querés una descomposición con incertidumbre (IC de la tendencia) y que tolere huecos.",
    supuestos=["Componentes gaussianos independientes; varianzas estimadas por máxima verosimilitud."],
    trampas=["Con poca señal, la varianza del ciclo se va a cero y todo queda en la tendencia (o al revés)."],
    deps=[],
    costo="segundos",
    referencias=["Harvey (1989), Forecasting, structural time series models and the Kalman filter"],
    etiquetas=["kalman", "espacio de estados", "harvey", "ucm", "estructural"],
    nivel="avanzado",
)
def componentes_no_observados(sid, freq, transf, tendencia, ciclo, estacional, desde, hasta):
    import statsmodels.api as sm

    s, et = serie(sid, freq, transf, desde, hasta, minimo=40)
    kw = {"level": tendencia, "cycle": ciclo, "stochastic_cycle": ciclo, "damped_cycle": ciclo}
    if estacional and PERIODO.get(freq, 1) > 1:
        kw["freq_seasonal"] = [{"period": PERIODO[freq], "harmonics": 2}]
    mod = sm.tsa.UnobservedComponents(s.values, **kw)
    res = mod.fit(disp=False, maxiter=500)
    r = Resultado()
    tend = res.level.smoothed
    r.lineas(f"{et}: serie y nivel suavizado", s.index, {et: s.values, "nivel (Kalman)": tend}, estilos={"nivel (Kalman)": {"ancho": 2.5}})
    r.serie(f"{sid}_nivel_ucm", s.index, tend, f"Nivel suavizado de {et} (UCM)")
    escala = 100 if transf == "log" else 1
    if ciclo:
        c = res.cycle.smoothed * escala
        r.lineas("Ciclo suavizado", s.index, {"ciclo": c})
        r.serie(f"{sid}_ciclo_ucm", s.index, c, f"Ciclo de {et} (UCM)")
        per = 2 * np.pi / res.params[mod.param_names.index("frequency.cycle")] if "frequency.cycle" in mod.param_names else None
        if per:
            r.metrica("Período del ciclo (obs.)", per)
            r.metrica("Período del ciclo (años)", per / PERIODO.get(freq, 1))
    r.tabla("Parámetros (máx. verosimilitud)", ["parámetro", "valor"], [[n, v] for n, v in zip(mod.param_names, res.params, strict=True)])
    r.metrica("AIC", res.aic)
    r.resumen = f"Componentes no observados ({tendencia}{', ciclo' if ciclo else ''}{', estacional' if estacional else ''}) sobre {et}: AIC {fmt(res.aic)}."
    return r
