"""Espacio de estados y factores: coeficientes que cambian en el tiempo (Kalman), factores
dinámicos comunes y desagregación temporal (pasar de trimestral a mensual con un indicador)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from cueva.metodos.contrato import ErrorMetodo, Param, Resultado
from cueva.metodos.insumos import P_DESDE, P_FREQ, P_HASTA, P_SERIE, P_SERIES, P_TRANSF, fmt, panel, serie
from cueva.metodos.registro import metodo

F = "estado"


# ──────────────────────────────────────────────────────────────────────────
# Regresión con parámetros que varían en el tiempo (Kalman + suavizador RTS)
# ──────────────────────────────────────────────────────────────────────────
def kalman_tvp(y: np.ndarray, X: np.ndarray, q: float, P0: float = 1e4):
    """β_t = β_{t−1} + η,  y_t = x_t'β_t + ε,  Var(η) = q·σ²·I,  Var(ε) = σ².
    Corre con σ² = 1 (la verosimilitud se concentra en σ²). Devuelve lo necesario para
    suavizar y la log-verosimilitud concentrada."""
    n, k = X.shape
    b = np.zeros(k)
    P = np.eye(k) * P0
    Q = np.eye(k) * q
    bp, Pp, bf, Pf = np.zeros((n, k)), np.zeros((n, k, k)), np.zeros((n, k)), np.zeros((n, k, k))
    v2F, logF = [], []
    for t in range(n):
        Pt = P + Q
        x = X[t]
        Ft = x @ Pt @ x + 1.0
        vt = y[t] - x @ b
        K = Pt @ x / Ft
        bp[t], Pp[t] = b, Pt
        b = b + K * vt
        P = Pt - np.outer(K, x @ Pt)
        bf[t], Pf[t] = b, P
        if t >= k + 2:  # se descartan las primeras (difusas)
            v2F.append(vt * vt / Ft)
            logF.append(np.log(Ft))
    m = len(v2F)
    s2 = float(np.sum(v2F) / m)
    ll = -0.5 * m * np.log(s2) - 0.5 * float(np.sum(logF))
    return {"bp": bp, "Pp": Pp, "bf": bf, "Pf": Pf, "s2": s2, "ll": ll}


def rts(kf: dict):
    bf, Pf, bp, Pp = kf["bf"], kf["Pf"], kf["bp"], kf["Pp"]
    n, k = bf.shape
    bs, Ps = bf.copy(), Pf.copy()
    for t in range(n - 2, -1, -1):
        J = Pf[t] @ np.linalg.pinv(Pp[t + 1])
        bs[t] = bf[t] + J @ (bs[t + 1] - bp[t + 1])
        Ps[t] = Pf[t] + J @ (Ps[t + 1] - Pp[t + 1]) @ J.T
    return bs, Ps


@metodo(
    "tvp_kalman",
    "Regresión con coeficientes que cambian en el tiempo (Kalman)",
    F,
    "¿Cómo evolucionó el efecto de X sobre Y (ej. el traspaso a precios) a lo largo de las décadas?",
    params=[
        P_SERIE("dep", "Dependiente (Y)"),
        P_SERIES("indeps", "Explicativas (X)", minimo=1, maximo=4),
        P_FREQ,
        Param("transf", "opcion", "Transformación", defecto="dif_log", opciones=list(P_TRANSF.opciones)),
        Param("con_constante", "bool", "Constante variable", defecto=True),
        P_DESDE,
        P_HASTA,
    ],
    cuando="Cuando la regresión móvil sugiere inestabilidad y querés una trayectoria suave con bandas, sin elegir ventana.",
    supuestos=[
        "Los coeficientes siguen paseos aleatorios; la razón señal/ruido q se estima por máxima verosimilitud."
    ],
    trampas=["q → 0 ⇒ coeficientes fijos (vuelve a MCO); q grande ⇒ los coeficientes persiguen el ruido."],
    costo="segundos",
    referencias=["Harvey (1989)", "Kim y Nelson (1999), cap. 3", "Durbin y Koopman (2012)"],
    etiquetas=["tvp", "kalman", "coeficientes variables", "suavizador", "espacio de estados", "traspaso"],
    nivel="avanzado",
)
def tvp_kalman(dep, indeps, freq, transf, con_constante, desde, hasta):
    from scipy.optimize import minimize_scalar

    df, et = panel([dep, *indeps], freq, transf, desde, hasta, minimo=40)
    y = df[dep].values
    Xr = df[indeps].values
    mu, sd = Xr.mean(0), Xr.std(0)
    sd[sd == 0] = 1
    Xs = (Xr - mu) / sd
    X = np.column_stack([np.ones(len(y)), Xs]) if con_constante else Xs
    nombres = (["constante"] if con_constante else []) + [et[s] for s in indeps]
    ys = y.std() or 1
    yn = y / ys
    opt = minimize_scalar(lambda lq: -kalman_tvp(yn, X, np.exp(lq))["ll"], bounds=(-14, 2), method="bounded")
    q = float(np.exp(opt.x))
    kf = kalman_tvp(yn, X, q)
    bs, Ps = rts(kf)
    s2 = kf["s2"]
    r = Resultado()
    r.metrica("q (señal/ruido)", q)
    r.metrica("Log-verosimilitud", kf["ll"])
    kf0 = kalman_tvp(yn, X, 1e-8)
    lr = 2 * (kf["ll"] - kf0["ll"])
    r.metrica(
        "LR vs coeficientes fijos",
        lr,
        "> 2,7 ≈ el cambio en el tiempo es relevante (H0 en el borde: χ² mezcla)",
    )
    for j, nm in enumerate(nombres):
        esc = ys if j == 0 and con_constante else ys / sd[j - (1 if con_constante else 0)]
        b = bs[:, j] * esc
        e = np.sqrt(np.maximum(Ps[:, j, j] * s2, 0)) * esc
        ini = len(indeps) + 3
        r.lineas(
            f"Coeficiente de {nm} (suavizado, ±1,96 EE)",
            df.index[ini:],
            {"coef": b[ini:], "IC inf.": (b - 1.96 * e)[ini:], "IC sup.": (b + 1.96 * e)[ini:]},
            estilos={"IC inf.": {"guion": "dot"}, "IC sup.": {"guion": "dot"}},
        )
        r.serie(
            f"tvp_{(indeps[j - 1] if (con_constante and j) or not con_constante else 'const')}"[:40],
            df.index,
            b,
            f"Coeficiente variable de {nm} sobre {et[dep]}",
        )
        if nm != "constante":
            r.metrica(f"{nm}: inicio → final", f"{fmt(b[ini])} → {fmt(b[-1])}")
    cambia = lr > 2.71
    r.veredicto(
        "Los coeficientes cambian significativamente en el tiempo."
        if cambia
        else "No hay evidencia fuerte de coeficientes variables: MCO alcanza.",
        "amarillo" if cambia else "verde",
    )
    r.resumen = f"TVP-Kalman de {et[dep]}: q={fmt(q)}, LR vs fijos={fmt(lr)}. " + "; ".join(
        f"{nm}: {r.metricas.get(nm + ': inicio → final', '')}" for nm in nombres if nm != "constante"
    )
    return r


@metodo(
    "factor_dinamico",
    "Modelo de factores dinámicos",
    F,
    "¿Hay un factor común (un 'índice del ciclo') detrás de muchas series?",
    params=[
        P_SERIES("sids", "Series (3 a 20)", minimo=3, maximo=20),
        P_FREQ,
        Param("transf", "opcion", "Transformación", defecto="dif_log", opciones=list(P_TRANSF.opciones)),
        Param("factores", "entero", "Factores", defecto=1, minimo=1, maximo=3),
        Param("orden_factor", "entero", "Orden AR del factor", defecto=2, minimo=1, maximo=4),
    ],
    cuando="Índices coincidentes de actividad (Stock-Watson), nowcasting, resumir un bloque de indicadores.",
    supuestos=[
        "Series estacionarias y estandarizadas; el factor sigue un VAR; errores idiosincráticos AR(1)."
    ],
    trampas=[
        "El signo del factor no está identificado: se orienta para que correlacione positivo con la primera serie."
    ],
    costo="segundos",
    referencias=["Stock y Watson (2002)", "Bańbura y Modugno (2014)"],
    etiquetas=["factor", "dfm", "índice coincidente", "nowcasting", "stock-watson", "em"],
    nivel="avanzado",
)
def factor_dinamico(sids, freq, transf, factores, orden_factor):
    import warnings

    from statsmodels.tsa.statespace.dynamic_factor_mq import DynamicFactorMQ

    df, et = panel(sids, freq, transf, minimo=40, como="union")
    df = df.dropna(thresh=max(2, len(sids) // 2))
    z = (df - df.mean()) / df.std()
    z.columns = [et[s] for s in sids]
    per = {"mensual": "M", "trimestral": "Q", "anual": "Y"}[freq]
    z.index = pd.DatetimeIndex(z.index).to_period(per)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        mod = DynamicFactorMQ(
            z, factors=factores, factor_orders=orden_factor, idiosyncratic_ar1=True, standardize=False
        )
        res = mod.fit(disp=False, maxiter=300)
    f = np.array(res.factors.smoothed, dtype=float, copy=True)
    if f.ndim == 1:
        f = f[:, None]
    signo = np.sign(np.corrcoef(f[:, 0], z.iloc[:, 0].fillna(0))[0, 1]) or 1
    f[:, 0] *= signo
    r = Resultado()
    idx = df.index
    r.lineas("Factor común suavizado", idx, {f"factor {i + 1}": f[:, i] for i in range(f.shape[1])})
    for i in range(f.shape[1]):
        r.serie(
            f"factor{i + 1}_{sids[0]}"[:40], idx, f[:, i], f"Factor dinámico {i + 1} de {len(sids)} series"
        )
    filas = []
    for c in z.columns:
        cc = pd.Series(f[:, 0], index=z.index).corr(z[c])
        filas.append([c, cc, cc**2 * 100])
    filas.sort(key=lambda x: -abs(x[1]))
    r.tabla(
        "Correlación de cada serie con el factor 1", ["serie", "correlación", "% varianza explicada"], filas
    )
    r.barras(
        "Carga (correlación) con el factor 1",
        [x[0] for x in filas],
        {"correlación": [x[1] for x in filas]},
        horizontal=True,
    )
    prom = float(np.mean([x[2] for x in filas]))
    r.metrica("% varianza explicada (promedio)", prom)
    r.metrica("Log-verosimilitud", res.llf)
    r.resumen = f"Factor dinámico sobre {len(sids)} series: explica en promedio {fmt(prom, 3)} % de la varianza; las más ligadas: {', '.join(x[0] for x in filas[:3])}."
    return r


@metodo(
    "desagregacion_temporal",
    "Desagregación temporal (Chow-Lin / Denton)",
    F,
    "¿Cómo paso una serie trimestral (o anual) a mensual usando un indicador mensual, respetando los totales?",
    params=[
        P_SERIE("sid_baja", "Serie de baja frecuencia (a desagregar)"),
        Param("freq_baja", "opcion", "Su frecuencia", defecto="trimestral", opciones=["trimestral", "anual"]),
        P_SERIES("indicadores", "Indicadores de alta frecuencia", minimo=0, maximo=4, requerido=False),
        Param(
            "freq_alta",
            "opcion",
            "Frecuencia objetivo",
            defecto="mensual",
            opciones=["mensual", "trimestral"],
        ),
        Param("metodo", "opcion", "Método", defecto="chow_lin", opciones=["chow_lin", "denton"]),
        Param(
            "agregacion",
            "opcion",
            "Cómo se agrega",
            defecto="promedio",
            opciones=["promedio", "suma", "ultimo"],
            ayuda="promedio = índices y tasas; suma = flujos; último = stocks",
        ),
    ],
    cuando="PBI mensual a partir del trimestral con el EMAE, series anuales viejas a trimestral, empalmar frecuencias.",
    supuestos=[
        "Chow-Lin: la serie de alta frecuencia = indicadores·β + error AR(1) (ρ por máxima verosimilitud).",
        "Denton: sigue el movimiento del indicador lo más posible respetando los totales.",
    ],
    trampas=[
        "Es una ESTIMACIÓN, no un dato: marcala como tal en el informe (la plataforma ya separa dato oficial de estimación)."
    ],
    referencias=["Chow y Lin (1971)", "Denton (1971)", "Sax y Steiner (2013), tempdisagg"],
    etiquetas=["chow-lin", "denton", "desagregación", "interpolación", "mensualizar", "benchmarking"],
)
def desagregacion_temporal(sid_baja, freq_baja, indicadores, freq_alta, metodo, agregacion):
    from scipy.optimize import minimize_scalar

    orden = {"mensual": 0, "trimestral": 1, "anual": 2}
    if orden[freq_alta] >= orden[freq_baja]:
        raise ErrorMetodo("La frecuencia objetivo tiene que ser más alta que la de la serie.")
    Yl, et_l = serie(sid_baja, freq_baja, "nivel", minimo=8)
    m = {("trimestral", "mensual"): 3, ("anual", "mensual"): 12, ("anual", "trimestral"): 4}[
        (freq_baja, freq_alta)
    ]
    # índice de alta frecuencia que cubre los períodos bajos completos
    fin = Yl.index[-1]
    ini = Yl.index[0]
    paso = {"mensual": "ME", "trimestral": "QE"}[freq_alta]
    alta = pd.date_range(ini - pd.tseries.frequencies.to_offset(paso) * (m - 1), fin, freq=paso)
    if indicadores:
        Xdf, et_x = panel(indicadores, freq_alta, "nivel", minimo=m * 4, como="union")
        Xdf = Xdf.reindex(pd.date_range(min(alta[0], Xdf.index[0]), Xdf.index[-1], freq=paso)).interpolate(
            limit_area="inside"
        )
        Xdf = Xdf.dropna()
        # se recorta a los bajos completamente cubiertos por los indicadores
        cubre = [
            f
            for f in Yl.index
            if (f - pd.tseries.frequencies.to_offset(paso) * (m - 1)) >= Xdf.index[0] and f <= Xdf.index[-1]
        ]
        if len(cubre) < 6:
            raise ErrorMetodo("Los indicadores cubren menos de 6 períodos de la serie de baja frecuencia.")
        Yl = Yl.loc[cubre]
        alta = pd.date_range(
            cubre[0] - pd.tseries.frequencies.to_offset(paso) * (m - 1), Xdf.index[-1], freq=paso
        )
        X = np.column_stack([np.ones(len(alta)), Xdf.reindex(alta).values])
    else:
        X = np.ones((len(alta), 1))
        et_x = {}
    nl, nh = len(Yl), len(alta)
    w = {"promedio": np.full(m, 1 / m), "suma": np.ones(m), "ultimo": np.eye(m)[-1]}[agregacion]
    C = np.zeros((nl, nh))
    for i in range(nl):
        C[i, i * m : (i + 1) * m] = w
    Y = Yl.values
    if metodo == "chow_lin":

        def gls(rho):
            idx = np.arange(nh)
            V = rho ** np.abs(idx[:, None] - idx[None, :]) / (1 - rho**2)
            CV = C @ V
            W = np.linalg.pinv(CV @ C.T)
            CX = C @ X
            beta = np.linalg.pinv(CX.T @ W @ CX) @ CX.T @ W @ Y
            u = Y - CX @ beta
            s2 = float(u @ W @ u / nl)
            sign, logdet = np.linalg.slogdet(CV @ C.T)
            ll = -0.5 * (nl * np.log(max(s2, 1e-300)) + logdet)
            return beta, V, W, u, ll

        opt = minimize_scalar(lambda rr: -gls(rr)[4], bounds=(0.0, 0.99), method="bounded")
        rho = float(opt.x)
        beta, V, W, u, _ = gls(rho)
        yh = X @ beta + V @ C.T @ W @ u
    else:
        # Denton aditivo en primeras diferencias: min Σ(Δ(y − x̃))² s.a. C y = Y
        ref = X @ np.linalg.lstsq(C @ X, Y, rcond=None)[0]
        D = np.eye(nh) - np.eye(nh, k=-1)
        D = D[1:]
        A = np.block([[D.T @ D + 1e-9 * np.eye(nh), C.T], [C, np.zeros((nl, nl))]])
        b = np.concatenate([D.T @ D @ ref, Y])
        sol = np.linalg.lstsq(A, b, rcond=None)[0]
        yh = sol[:nh]
        rho, beta = None, None
    r = Resultado()
    chequeo = float(np.max(np.abs(C @ yh - Y)))
    r.metrica("Obs. de alta frecuencia", nh)
    r.metrica("Error máx. al re-agregar", chequeo, "≈ 0: respeta los totales")
    if rho is not None:
        r.metrica("ρ (AR del error)", rho)
        r.tabla(
            "Coeficientes (MCG)",
            ["término", "β"],
            [["constante", beta[0]], *[[et_x[s], beta[i + 1]] for i, s in enumerate(indicadores or [])]],
        )
    escal = pd.Series(np.repeat(Y, m), index=alta)
    r.lineas(
        f"{et_l} desagregada a {freq_alta} ({metodo})",
        alta,
        {"desagregada": yh, f"{freq_baja} (escalón)": escal.values},
        estilos={f"{freq_baja} (escalón)": {"guion": "dot"}},
    )
    r.serie(
        f"{sid_baja}_{freq_alta[:3]}_{metodo[:6]}"[:40],
        alta,
        yh,
        f"{et_l} desagregada a {freq_alta} por {metodo} (ESTIMACIÓN)",
    )
    r.advertir("La serie desagregada es una estimación: no la mezcles con datos oficiales sin marcarla.")
    r.resumen = (
        f"Desagregación {metodo} de {et_l} ({freq_baja}→{freq_alta}, {agregacion}): {nh} obs.; respeta los totales con error {fmt(chequeo)}"
        + (f"; ρ={fmt(rho)}." if rho is not None else ".")
    )
    return r
