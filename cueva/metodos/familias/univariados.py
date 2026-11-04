"""Modelos univariados y pronóstico: benchmarks, (S)ARIMA, suavizado exponencial, Theta.

Todo pronóstico de esta familia se evalúa igual: origen móvil sobre el último tramo con
parámetros fijos (se estiman una vez con el tramo de entrenamiento y se re-filtran con cada
dato nuevo), contra el paseo aleatorio.
"""

from __future__ import annotations

import itertools
import warnings

import numpy as np
import pandas as pd

from cueva.metodos import validacion as V
from cueva.metodos.contrato import ErrorMetodo, Param, Resultado
from cueva.metodos.insumos import (
    P_DESDE,
    P_FREQ,
    P_HASTA,
    P_HORIZONTE,
    P_SERIE,
    P_TRANSF,
    PERIODO,
    fechas_futuras,
    fmt,
    serie,
)
from cueva.metodos.registro import metodo

F = "univariados"
P_TEST = Param("n_test", "entero", "Obs. de prueba (0 = 20 %)", defecto=0, minimo=0, maximo=120)


_PER = {"mensual": "M", "trimestral": "Q", "anual": "Y"}


def _con_periodo(s, freq) -> pd.Series:
    """La serie con PeriodIndex de frecuencia explícita (lo que statsmodels necesita para
    pronosticar con fechas)."""
    y = pd.Series(s.values.astype(float), index=pd.DatetimeIndex(s.index).to_period(_PER[freq]))
    return y


def _a_fecha(f):
    return f.to_timestamp(how="end").normalize() if isinstance(f, pd.Period) else f


def _historia_corta(s, freq):
    n = {"mensual": 120, "trimestral": 48, "anual": 40}.get(freq, 120)
    return s.iloc[-n:]


def _backtest_fijo(y: pd.Series, h: int, n_test: int, ajustar, pronosticar):
    """Origen móvil con parámetros fijos: `ajustar(y_train)` → res; `pronosticar(res, y_hasta)`
    → array de h pasos con el modelo re-filtrado hasta el origen."""
    n = len(y)
    corte = n - n_test - h + 1
    if corte < 24:
        raise ErrorMetodo("Muestra corta para evaluar fuera de muestra: bajá n_test u horizonte.")
    res = ajustar(y.iloc[:corte])
    reales, preds, rws, fechas = [], [], [], []
    for o in range(corte, n - h + 1):
        f = pronosticar(res, y.iloc[:o])
        reales.append(y.iloc[o + h - 1])
        preds.append(float(np.asarray(f)[h - 1]))
        rws.append(y.iloc[o - 1])
        fechas.append(_a_fecha(y.index[o + h - 1]))
    tr = y.values[:corte]
    esc = float(np.mean(np.abs(tr[h:] - tr[:-h])))
    return V.Backtest(
        pd.DatetimeIndex(fechas),
        np.array(reales),
        np.array(preds),
        np.array(rws),
        np.full(len(reales), tr.mean()),
        esc,
    )


def _reportar_backtest(r: Resultado, bt: V.Backtest, h: int, nombre: str):
    res = V.resumen_backtest(bt, h)
    filas = []
    for etiqueta, clave in (
        (nombre, "modelo"),
        ("paseo aleatorio", "paseo_aleatorio"),
        ("media histórica", "media_historica"),
    ):
        m = res[clave]
        filas.append([etiqueta, m["RMSE"], m["MAE"], m.get("MASE"), m.get("MAPE %")])
    r.tabla(
        f"Evaluación fuera de muestra (origen móvil, h={h}, {len(bt.real)} pronósticos)",
        ["modelo", "RMSE", "MAE", "MASE", "MAPE %"],
        filas,
    )
    dm, p = res["dm_vs_rw"]
    r.metrica("RMSE fuera de muestra", res["modelo"]["RMSE"])
    r.metrica("R² fuera de muestra vs paseo", res["r2_oos_vs_rw"], "> 0: le gana al paseo aleatorio")
    r.metrica("Diebold-Mariano vs paseo (p)", p)
    r.lineas(
        "Pronósticos fuera de muestra vs realizados",
        bt.fechas,
        {"realizado": bt.real, nombre: bt.pred, "paseo aleatorio": bt.rw},
        estilos={"paseo aleatorio": {"guion": "dot"}},
    )
    gana = res["r2_oos_vs_rw"] > 0
    sig = p == p and p < 0.1
    if gana and sig:
        r.veredicto(
            f"{nombre} le gana al paseo aleatorio y la diferencia es significativa (DM p={fmt(p)}).", "verde"
        )
    elif gana:
        r.veredicto(
            f"{nombre} le gana al paseo aleatorio, pero la diferencia NO es significativa (DM p={fmt(p)}).",
            "amarillo",
        )
    else:
        r.veredicto(
            f"{nombre} NO le gana al paseo aleatorio fuera de muestra (R² oos = {fmt(res['r2_oos_vs_rw'])}).",
            "rojo",
        )
    return res


def _cerrar_pronostico(r, s, et, freq, media, inf, sup, nombre):
    fut = fechas_futuras(s.index[-1], len(media), freq)
    hc = _historia_corta(s, freq)
    r.bandas(f"Pronóstico {nombre} de {et}", hc.index, hc.values, fut, media, inf, sup)
    r.tabla(
        "Pronóstico",
        ["fecha", "media", "IC inf.", "IC sup."],
        [
            [str(f.date()), m, a, b]
            for f, m, a, b in zip(
                fut,
                media,
                inf if inf is not None else [None] * len(media),
                sup if sup is not None else [None] * len(media),
                strict=True,
            )
        ],
    )
    r.serie(f"pron_{nombre.lower().replace(' ', '_')[:12]}", fut, media, f"Pronóstico {nombre} de {et}")


@metodo(
    "benchmarks",
    "Pronósticos ingenuos de referencia",
    F,
    "¿Qué error tiene el pronóstico más tonto? Es la vara contra la que se mide todo lo demás.",
    params=[P_SERIE(), P_FREQ, P_TRANSF, P_HORIZONTE(12), P_TEST],
    cuando="Siempre que se pronostique: un modelo que no le gana al paseo aleatorio no aporta.",
    trampas=["Comparar modelos sin benchmark ingenuo es la forma más común de engañarse con ML."],
    referencias=["Hyndman y Athanasopoulos (2021), FPP3, cap. 5"],
    etiquetas=["naive", "paseo aleatorio", "estacional ingenuo", "drift", "benchmark"],
    nivel="basico",
)
def benchmarks(sid, freq, transf, horizonte, n_test):
    s, et = serie(sid, freq, transf, minimo=30)
    h = horizonte
    per = PERIODO.get(freq, 1)
    nt = n_test or V.n_test_por_defecto(len(s), freq)
    y = s.values
    reglas = {
        "paseo aleatorio": lambda hist, k: hist[-1],
        "media histórica": lambda hist, k: hist.mean(),
        "deriva (drift)": lambda hist, k: hist[-1] + k * (hist[-1] - hist[0]) / (len(hist) - 1),
    }
    if per > 1:
        reglas["estacional ingenuo"] = lambda hist, k: hist[-per + ((k - 1) % per)]
    filas = []
    n = len(y)
    res_pron = {}
    for nombre, fn in reglas.items():
        errs = []
        for o in range(n - nt - h + 1, n - h + 1):
            errs.append(y[o + h - 1] - fn(y[:o], h))
        e = np.array(errs)
        filas.append([nombre, np.sqrt(np.mean(e**2)), np.mean(np.abs(e)), np.mean(e)])
        res_pron[nombre] = [fn(y, k) for k in range(1, h + 1)]
    filas.sort(key=lambda f: f[1])
    r = Resultado()
    r.tabla(f"Error fuera de muestra a h={h} ({nt} orígenes)", ["benchmark", "RMSE", "MAE", "sesgo"], filas)
    fut = fechas_futuras(s.index[-1], h, freq)
    hc = _historia_corta(s, freq)
    r.bandas(
        f"Benchmarks para {et}",
        hc.index,
        hc.values,
        fut,
        res_pron[filas[0][0]],
        extra={k: (fut, v) for k, v in res_pron.items() if k != filas[0][0]},
    )
    r.metrica("Mejor benchmark", filas[0][0])
    r.metrica("RMSE del mejor", filas[0][1])
    r.resumen = f"Benchmarks para {et} (h={h}): el mejor es «{filas[0][0]}» con RMSE {fmt(filas[0][1])}. Cualquier modelo tiene que bajar ese error."
    r.datos = {"rmse": {f[0]: f[1] for f in filas}}
    return r


def _sarimax(y, orden, est, tendencia, maxiter=200):
    from statsmodels.tsa.statespace.sarimax import SARIMAX

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return SARIMAX(
            y,
            order=orden,
            seasonal_order=est,
            trend=tendencia,
            enforce_stationarity=False,
            enforce_invertibility=False,
        ).fit(disp=False, maxiter=maxiter)


@metodo(
    "sarima",
    "SARIMA (Box-Jenkins con estacionalidad)",
    F,
    "¿Cuál es el pronóstico de la serie con su propia dinámica, con intervalos de confianza?",
    params=[
        P_SERIE(),
        P_FREQ,
        P_TRANSF,
        Param("automatico", "bool", "Elegir órdenes por AIC", defecto=True),
        Param("p", "entero", "p (AR)", defecto=1, minimo=0, maximo=6),
        Param("d", "entero", "d (diferencias)", defecto=1, minimo=0, maximo=2),
        Param("q", "entero", "q (MA)", defecto=1, minimo=0, maximo=6),
        Param("P", "entero", "P estacional", defecto=0, minimo=0, maximo=2),
        Param("D", "entero", "D estacional", defecto=0, minimo=0, maximo=1),
        Param("Q", "entero", "Q estacional", defecto=0, minimo=0, maximo=2),
        P_HORIZONTE(12),
        P_TEST,
        P_DESDE,
        P_HASTA,
    ],
    cuando="Pronóstico de corto plazo de una serie con dinámica estable. Es el benchmark serio de cualquier ML.",
    supuestos=["Tras diferenciar, el proceso es estacionario e invertible; errores ruido blanco."],
    trampas=[
        "Sobrediferenciar (d=2 sin necesidad) mete una raíz MA unitaria y empeora el pronóstico.",
        "Un buen ajuste en muestra no garantiza nada fuera de muestra: mirá la evaluación.",
        "Con quiebres (2002, 2018), los parámetros mezclan regímenes.",
    ],
    costo="segundos",
    referencias=["Box, Jenkins, Reinsel y Ljung (2015)", "Hyndman y Athanasopoulos (2021), cap. 9"],
    etiquetas=["arima", "sarima", "box-jenkins", "pronóstico", "intervalos"],
    nivel="basico",
)
def sarima(sid, freq, transf, automatico, p, d, q, P, D, Q, horizonte, n_test, desde, hasta):
    from statsmodels.stats.diagnostic import acorr_ljungbox
    from statsmodels.tsa.stattools import adfuller

    s, et = serie(sid, freq, transf, desde, hasta, minimo=36)
    per = PERIODO.get(freq, 1)
    y = _con_periodo(s, freq)
    if automatico:
        d = 0
        z = y.values
        while d < 2 and adfuller(z, autolag="AIC")[1] > 0.05:
            z = np.diff(z)
            d += 1
        mejores = []
        estac = [(0, 0, 0, 0)] + ([(1, 0, 0, per), (0, 0, 1, per)] if per > 1 else [])
        for pp, qq, est in itertools.product(range(0, 3), range(0, 3), estac):
            try:
                res = _sarimax(y.values, (pp, d, qq), est, "c" if d == 0 else "n", maxiter=40)
                mejores.append((res.aic, (pp, d, qq), est))
            except Exception:
                continue
        if not mejores:
            raise ErrorMetodo("Ningún SARIMA convergió.")
        mejores.sort(key=lambda m: m[0])
        _, orden, est_orden = mejores[0]
    else:
        orden, est_orden = (p, d, q), ((P, D, Q, per) if per > 1 and (P or D or Q) else (0, 0, 0, 0))
    tend = "c" if orden[1] == 0 and est_orden[1] == 0 else "n"
    res = _sarimax(y.values, orden, est_orden, tend)
    fc = res.get_forecast(horizonte)
    media = fc.predicted_mean
    ic = fc.conf_int(alpha=0.05)
    nombre = f"SARIMA{orden}{est_orden if est_orden[3] else ''}"
    r = Resultado()
    r.metrica("Modelo", nombre)
    r.metrica("AIC", res.aic)
    r.metrica("BIC", res.bic)
    r.tabla(
        "Coeficientes",
        ["parámetro", "coef", "EE", "p"],
        [
            [nm, c, e, pv]
            for nm, c, e, pv in zip(res.model.param_names, res.params, res.bse, res.pvalues, strict=True)
        ],
        resaltar_p="p",
    )
    lb = acorr_ljungbox(
        res.resid[orden[1] + est_orden[1] * per :], lags=[min(12, len(y) // 5)], return_df=True
    )
    lbp = float(lb["lb_pvalue"].iloc[0])
    r.metrica("Ljung-Box residuos (p)", lbp)
    if lbp < 0.05:
        r.advertir("Los residuos tienen autocorrelación: el modelo deja dinámica sin capturar.")
    if automatico:
        r.tabla(
            "Mejores 5 por AIC",
            ["orden", "estacional", "AIC"],
            [[str(o), str(e), a] for a, o, e in mejores[:5]],
        )
    nt = n_test or V.n_test_por_defecto(len(y), freq)
    try:
        bt = _backtest_fijo(
            y,
            horizonte if horizonte <= 12 else 1,
            nt,
            lambda yt: _sarimax(yt.values, orden, est_orden, tend),
            lambda rr, yh: rr.apply(yh.values).forecast(horizonte if horizonte <= 12 else 1),
        )
        _reportar_backtest(r, bt, horizonte if horizonte <= 12 else 1, nombre)
    except ErrorMetodo as e:
        r.advertir(f"Sin evaluación fuera de muestra: {e}")
    _cerrar_pronostico(
        r, s, et, freq, np.asarray(media), np.asarray(ic)[:, 0], np.asarray(ic)[:, 1], "SARIMA"
    )
    r.resumen = f"{nombre} para {et}: AIC {fmt(res.aic)}, Ljung-Box p={fmt(lbp)}. Pronóstico a {horizonte}: {fmt(float(np.asarray(media)[-1]))} (IC {fmt(float(np.asarray(ic)[-1, 0]))} a {fmt(float(np.asarray(ic)[-1, 1]))})."
    r.codigo = f"from statsmodels.tsa.statespace.sarimax import SARIMAX\nres = SARIMAX(s, order={orden}, seasonal_order={est_orden}).fit()\nres.get_forecast({horizonte}).summary_frame()"
    return r


@metodo(
    "suavizado_exponencial",
    "Suavizado exponencial (ETS)",
    F,
    "Pronóstico ponderando más lo reciente, con tendencia y estacionalidad opcionales.",
    params=[
        P_SERIE(),
        P_FREQ,
        P_TRANSF,
        Param("automatico", "bool", "Elegir la forma por AIC", defecto=True),
        Param(
            "tendencia",
            "opcion",
            "Tendencia",
            defecto="ninguna",
            opciones=["ninguna", "aditiva", "amortiguada"],
        ),
        Param(
            "estacional",
            "opcion",
            "Estacionalidad",
            defecto="ninguna",
            opciones=["ninguna", "aditiva", "multiplicativa"],
        ),
        P_HORIZONTE(12),
        P_TEST,
    ],
    cuando="Series con tendencia/estacionalidad cambiantes; muy competitivo en pronóstico de corto plazo (M3, M4).",
    trampas=[
        "Estacionalidad multiplicativa exige valores positivos.",
        "La tendencia sin amortiguar extrapola sin freno.",
    ],
    costo="segundos",
    referencias=["Hyndman, Koehler, Ord y Snyder (2008)", "Gardner (1985)"],
    etiquetas=["ets", "holt", "holt-winters", "suavizado", "exponencial"],
    nivel="basico",
)
def suavizado_exponencial(sid, freq, transf, automatico, tendencia, estacional, horizonte, n_test):
    from statsmodels.tsa.exponential_smoothing.ets import ETSModel

    s, et = serie(sid, freq, transf, minimo=30)
    per = PERIODO.get(freq, 1)
    y = _con_periodo(s, freq)

    def ajustar(yy, tr, da, es):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return ETSModel(
                yy, error="add", trend=tr, damped_trend=da, seasonal=es, seasonal_periods=per if es else None
            ).fit(disp=False, maxiter=500)

    if automatico:
        combos = []
        for tr, da in ((None, False), ("add", False), ("add", True)):
            for es in [None] + (
                ["add"] + (["mul"] if (y > 0).all() else []) if per > 1 and len(y) >= 3 * per else []
            ):
                try:
                    rr = ajustar(y, tr, da, es)
                    combos.append((rr.aic, tr, da, es))
                except Exception:
                    continue
        combos.sort(key=lambda c: c[0])
        if not combos:
            raise ErrorMetodo("Ningún ETS convergió.")
        _, tr, da, es = combos[0]
    else:
        tr = None if tendencia == "ninguna" else "add"
        da = tendencia == "amortiguada"
        es = {"ninguna": None, "aditiva": "add", "multiplicativa": "mul"}[estacional]
        if es and per == 1:
            es = None
    res = ajustar(y, tr, da, es)
    nombre = f"ETS(A,{'N' if not tr else ('Ad' if da else 'A')},{ {None: 'N', 'add': 'A', 'mul': 'M'}[es] })"
    pr = res.get_prediction(start=len(y), end=len(y) + horizonte - 1).summary_frame(alpha=0.05)
    r = Resultado()
    r.metrica("Modelo", nombre)
    r.metrica("AIC", res.aic)
    r.tabla(
        "Parámetros",
        ["parámetro", "valor"],
        [[n, v] for n, v in zip(res.model.param_names, res.params, strict=True)],
    )
    if automatico:
        r.tabla(
            "Formas probadas",
            ["tendencia", "amortiguada", "estacional", "AIC"],
            [[str(t), str(d), str(e), a] for a, t, d, e in combos],
        )
    nt = n_test or V.n_test_por_defecto(len(y), freq)
    try:
        hh = min(horizonte, 12)
        bt = _backtest_fijo(
            y, hh, nt, lambda yt: ajustar(yt, tr, da, es), lambda rr, yh: _ets_refiltrar(rr, yh, hh)
        )
        _reportar_backtest(r, bt, hh, nombre)
    except ErrorMetodo as e:
        r.advertir(f"Sin evaluación fuera de muestra: {e}")
    _cerrar_pronostico(r, s, et, freq, pr["mean"].values, pr["pi_lower"].values, pr["pi_upper"].values, "ETS")
    r.resumen = f"{nombre} para {et}: AIC {fmt(res.aic)}. Pronóstico a {horizonte}: {fmt(float(pr['mean'].values[-1]))}."
    return r


def _ets_refiltrar(res, yh, h):
    """Pronóstico con parámetros fijos re-filtrando hasta el origen."""
    from statsmodels.tsa.exponential_smoothing.ets import ETSModel

    m = res.model
    nuevo = ETSModel(
        yh,
        error=m.error,
        trend=m.trend,
        damped_trend=m.damped_trend,
        seasonal=m.seasonal,
        seasonal_periods=m.seasonal_periods,
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        rr = nuevo.smooth(res.params)
    return np.asarray(rr.forecast(h))


@metodo(
    "theta",
    "Método Theta",
    F,
    "Pronóstico simple y robusto (ganador de la competencia M3).",
    params=[P_SERIE(), P_FREQ, P_TRANSF, P_HORIZONTE(12), P_TEST],
    cuando="Como benchmark fuerte y barato, sobre todo en series anuales y trimestrales.",
    supuestos=["Equivale a suavizado exponencial simple con deriva (Hyndman y Billah 2003)."],
    referencias=["Assimakopoulos y Nikolopoulos (2000)", "Hyndman y Billah (2003)"],
    etiquetas=["theta", "m3", "pronóstico", "benchmark"],
    nivel="basico",
)
def theta(sid, freq, transf, horizonte, n_test):
    from statsmodels.tsa.forecasting.theta import ThetaModel

    s, et = serie(sid, freq, transf, minimo=30)
    per = PERIODO.get(freq, 1)
    y = _con_periodo(s, freq)
    usar_est = per > 1 and len(y) >= 3 * per and (y > 0).all()

    def ajustar(yy):
        return ThetaModel(yy, period=per if usar_est else None, deseasonalize=usar_est).fit()

    res = ajustar(y)
    fc = res.forecast(horizonte)
    pi = res.prediction_intervals(horizonte, alpha=0.05)
    r = Resultado()
    r.metrica("θ (deriva)", float(res.params.get("b0", np.nan)))
    r.metrica("α (suavizado)", float(res.params.get("alpha", np.nan)))
    nt = n_test or V.n_test_por_defecto(len(y), freq)
    try:
        hh = min(horizonte, 12)
        bt = _backtest_fijo(y, hh, nt, lambda yt: None, lambda _rr, yh: ajustar(yh).forecast(hh).values)
        _reportar_backtest(r, bt, hh, "Theta")
    except ErrorMetodo as e:
        r.advertir(f"Sin evaluación fuera de muestra: {e}")
    _cerrar_pronostico(r, s, et, freq, fc.values, pi["lower"].values, pi["upper"].values, "Theta")
    r.resumen = f"Theta para {et}: pronóstico a {horizonte} = {fmt(float(fc.values[-1]))}."
    return r
