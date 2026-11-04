"""Volatilidad y riesgo: familia GARCH completa y valor en riesgo."""

from __future__ import annotations

import numpy as np

from cueva.metodos.contrato import ErrorMetodo, Param, Resultado
from cueva.metodos.insumos import P_DESDE, P_FREQ, P_HASTA, P_SERIE, P_TRANSF, fmt, serie
from cueva.metodos.registro import metodo

F = "volatilidad"
P_RET = Param("transf", "opcion", "Transformación", defecto="dif_log", opciones=list(P_TRANSF.opciones), ayuda="GARCH se aplica a rendimientos: dif_log (Δlog) es lo usual")


@metodo(
    "garch_familia",
    "Familia GARCH (GARCH, GJR, EGARCH, APARCH) con comparación",
    F,
    "¿La volatilidad se agrupa en el tiempo? ¿Los shocks negativos la suben más que los positivos?",
    params=[
        P_SERIE(),
        P_FREQ,
        P_RET,
        Param("modelos", "opciones", "Modelos a comparar", defecto=["GARCH", "GJR", "EGARCH"], opciones=["GARCH", "GJR", "EGARCH", "APARCH", "FIGARCH"]),
        Param("distribucion", "opcion", "Distribución de errores", defecto="t", opciones=["normal", "t", "skewt", "ged"]),
        Param("media", "opcion", "Ecuación de media", defecto="AR", opciones=["Constant", "Zero", "AR"]),
        P_DESDE,
        P_HASTA,
    ],
    cuando="Tipo de cambio, brecha, riesgo país, rendimientos: cuando ARCH-LM rechaza homocedasticidad.",
    supuestos=["Rendimientos estacionarios; la varianza condicional sigue la recursión del modelo."],
    trampas=[
        "Aplicar GARCH a niveles (no rendimientos) no tiene sentido.",
        "α + β ≈ 1 puede ser un quiebre en la varianza no modelado (Lamoureux y Lastrapes 1990).",
        "Con datos mensuales el agrupamiento de volatilidad es mucho más débil que en diarios.",
    ],
    deps=["arch"],
    costo="segundos",
    referencias=["Engle (1982)", "Bollerslev (1986)", "Glosten, Jagannathan y Runkle (1993)", "Nelson (1991)"],
    etiquetas=["garch", "egarch", "gjr", "volatilidad", "apalancamiento", "arch"],
)
def garch_familia(sid, freq, transf, modelos, distribucion, media, desde, hasta):
    from arch import arch_model

    s, et = serie(sid, freq, transf, desde, hasta, minimo=60)
    y = s.values
    escala = 100 if transf in ("dif_log",) and np.std(y) < 1 else 1
    y = y * escala
    dist = {"normal": "normal", "t": "t", "skewt": "skewt", "ged": "ged"}[distribucion]
    specs = {
        "GARCH": dict(vol="GARCH", p=1, o=0, q=1),
        "GJR": dict(vol="GARCH", p=1, o=1, q=1),
        "EGARCH": dict(vol="EGARCH", p=1, o=1, q=1),
        "APARCH": dict(vol="APARCH", p=1, o=1, q=1),
        "FIGARCH": dict(vol="FIGARCH", p=1, q=1),
    }
    filas, ajustes = [], {}
    for nm in modelos or ["GARCH"]:
        try:
            am = arch_model(y, mean=media, lags=1 if media == "AR" else 0, dist=dist, **specs[nm])
            res = am.fit(disp="off", show_warning=False)
            ajustes[nm] = res
            filas.append([nm, res.loglikelihood, res.aic, res.bic])
        except Exception as e:
            filas.append([nm, None, None, f"no convergió: {e}"[:60]])
    if not ajustes:
        raise ErrorMetodo("Ningún modelo de la familia GARCH convergió.")
    mejor = min(ajustes, key=lambda k: ajustes[k].bic)
    res = ajustes[mejor]
    r = Resultado()
    r.tabla("Comparación (menor BIC = mejor)", ["modelo", "log-veros.", "AIC", "BIC"], filas)
    r.tabla(f"Parámetros de {mejor}", ["parámetro", "coef", "EE", "p"], [[n, c, e, p] for n, c, e, p in zip(res.params.index, res.params.values, res.std_err.values, res.pvalues.values, strict=True)], resaltar_p="p")
    vol = res.conditional_volatility / escala
    r.lineas(f"Volatilidad condicional de {et} ({mejor})", s.index, {"|rendimiento|": np.abs(s.values), "volatilidad condicional": vol}, estilos={"|rendimiento|": {"guion": "dot"}})
    r.serie(f"{sid}_vol_{mejor.lower()}", s.index, vol, f"Volatilidad condicional de {et} ({mejor})")
    pars = res.params
    alpha = sum(v for k, v in pars.items() if k.startswith("alpha"))
    beta = sum(v for k, v in pars.items() if k.startswith("beta"))
    gamma = sum(v for k, v in pars.items() if k.startswith("gamma"))
    r.metrica("Mejor modelo (BIC)", mejor)
    if mejor in ("GARCH", "GJR"):
        pers = alpha + beta + gamma / 2
        r.metrica("Persistencia α+β(+γ/2)", pers)
        if pers < 1:
            r.metrica("Vida media de un shock (períodos)", np.log(0.5) / np.log(pers) if pers > 0 else None)
        if pers > 0.98:
            r.advertir("Persistencia ≈ 1 (IGARCH): puede ser un quiebre en la varianza; corré cambio_de_punto con costo 'normal'.")
    if gamma and "gamma[1]" in res.pvalues and res.pvalues["gamma[1]"] < 0.05:
        r.veredicto(f"Hay efecto asimétrico (γ={fmt(gamma)}): los shocks {'negativos' if gamma > 0 else 'positivos'} suben más la volatilidad.", "amarillo")
    else:
        r.veredicto(f"{mejor} es el mejor por BIC; no hay asimetría significativa.", "verde")
    try:
        fc = res.forecast(horizon=12, reindex=False)
    except ValueError:  # EGARCH/APARCH: sin fórmula analítica a más de 1 paso
        fc = res.forecast(horizon=12, reindex=False, method="simulation", simulations=500)
    r.metrica("Volatilidad pronosticada a 12 períodos", float(np.sqrt(fc.variance.values[-1, -1])) / escala)
    r.resumen = f"Familia GARCH sobre {et} (dist. {distribucion}): gana {mejor} por BIC; α={fmt(alpha)}, β={fmt(beta)}{', γ=' + fmt(gamma) if gamma else ''}."
    r.codigo = f"from arch import arch_model\nres = arch_model(100*r, mean='{media}', vol='GARCH', p=1, o=1, q=1, dist='{dist}').fit()"
    return r


@metodo(
    "valor_en_riesgo",
    "Valor en riesgo y pérdida esperada (VaR / ES)",
    F,
    "¿Cuánto se puede perder en un período malo con una probabilidad dada?",
    params=[
        P_SERIE(),
        P_FREQ,
        P_RET,
        Param("nivel", "real", "Nivel de confianza", defecto=0.95, minimo=0.8, maximo=0.999),
        Param("ventana", "entero", "Ventana móvil (obs.)", defecto=60, minimo=20, maximo=1000),
    ],
    cuando="Riesgo cambiario o de cartera: compara VaR histórico, normal y Cornish-Fisher, y lo evalúa (Kupiec).",
    trampas=["El VaR normal subestima las colas pesadas; el histórico depende de la ventana."],
    referencias=["Jorion (2006)", "Kupiec (1995)"],
    etiquetas=["var", "expected shortfall", "riesgo", "kupiec", "colas"],
)
def valor_en_riesgo(sid, freq, transf, nivel, ventana):
    from scipy import stats

    s, et = serie(sid, freq, transf, minimo=ventana + 20)
    y = s.values
    a = 1 - nivel
    z = stats.norm.ppf(a)
    sk, ku = stats.skew(y), stats.kurtosis(y)
    zcf = z + (z**2 - 1) * sk / 6 + (z**3 - 3 * z) * ku / 24 - (2 * z**3 - 5 * z) * sk**2 / 36
    tabla = []
    var_h = np.quantile(y, a)
    es_h = y[y <= var_h].mean()
    tabla.append(["histórico", var_h, es_h])
    tabla.append(["normal", y.mean() + z * y.std(ddof=1), y.mean() - y.std(ddof=1) * stats.norm.pdf(z) / a])
    tabla.append(["Cornish-Fisher", y.mean() + zcf * y.std(ddof=1), None])
    r = Resultado()
    r.tabla(f"VaR y ES al {nivel:.0%} (toda la muestra)", ["método", "VaR", "ES"], tabla)
    # VaR móvil histórico y backtest de Kupiec
    var_mov = np.full(len(y), np.nan)
    for t in range(ventana, len(y)):
        var_mov[t] = np.quantile(y[t - ventana : t], a)
    viol = (y[ventana:] < var_mov[ventana:]).astype(int)
    n, x = len(viol), int(viol.sum())
    pi = x / n if n else 0
    if 0 < x < n:
        lr = -2 * (np.log((1 - a) ** (n - x) * a**x) - np.log((1 - pi) ** (n - x) * pi**x))
        pk = float(stats.chi2.sf(lr, 1))
    else:
        pk = float("nan")
    r.lineas(f"{et} y VaR móvil histórico ({ventana} obs.)", s.index, {et: y, f"VaR {nivel:.0%}": var_mov}, estilos={f"VaR {nivel:.0%}": {"guion": "dash"}})
    r.metrica("Violaciones", x)
    r.metrica("Esperadas", n * a)
    r.metrica("Kupiec p", pk, "H0: la tasa de violaciones es la nominal")
    r.veredicto("El VaR móvil está bien calibrado (Kupiec no rechaza)." if pk == pk and pk > 0.05 else "El VaR móvil está mal calibrado: hay más (o menos) violaciones que las esperadas.", "verde" if pk == pk and pk > 0.05 else "rojo")
    r.resumen = f"VaR {nivel:.0%} de {et}: histórico {fmt(var_h)}, ES {fmt(es_h)}; {x} violaciones vs {fmt(n * a)} esperadas (Kupiec p={fmt(pk)})."
    return r
