"""Exploración y descriptivos: mirar la serie antes de modelarla."""

from __future__ import annotations

import numpy as np
import pandas as pd

from cueva.metodos.contrato import Param, Resultado
from cueva.metodos.insumos import (
    P_DESDE,
    P_FREQ,
    P_HASTA,
    P_SERIE,
    P_SERIES,
    P_TRANSF,
    PERIODO,
    fmt,
    panel,
    serie,
)
from cueva.metodos.registro import metodo

F = "exploratorio"


@metodo(
    "estadisticos",
    "Estadísticos descriptivos y distribución",
    F,
    "¿Cómo es la serie: nivel, dispersión, asimetría, colas, extremos?",
    params=[P_SERIE(), P_FREQ, P_TRANSF, P_DESDE, P_HASTA],
    cuando="Siempre, como primer paso: define qué transformación y qué modelo tienen sentido.",
    trampas=[
        "Comparar medias de series no estacionarias: la media de un paseo aleatorio depende de la muestra.",
        "Leer la curtosis de una serie en niveles: miden algo útil sobre cambios o tasas, no sobre niveles.",
    ],
    etiquetas=["media", "desvío", "histograma", "curtosis", "asimetría", "percentiles"],
    nivel="basico",
)
def estadisticos(sid, freq, transf, desde, hasta):
    from scipy import stats

    s, et = serie(sid, freq, transf, desde, hasta, minimo=5)
    r = Resultado()
    v = s.values
    r.metrica("Obs.", len(s))
    r.metrica("Media", v.mean())
    r.metrica("Desvío", v.std(ddof=1))
    r.metrica("Mín", v.min())
    r.metrica("Máx", v.max())
    r.metrica("Asimetría", stats.skew(v))
    r.metrica("Curtosis exc.", stats.kurtosis(v))
    q = np.percentile(v, [1, 5, 25, 50, 75, 95, 99])
    r.tabla(
        "Percentiles",
        ["p1", "p5", "p25", "mediana", "p75", "p95", "p99"],
        [list(q)],
    )
    imax, imin = s.idxmax(), s.idxmin()
    r.tabla(
        "Extremos",
        ["", "fecha", "valor"],
        [["máximo", str(imax.date()), s.max()], ["mínimo", str(imin.date()), s.min()]],
    )
    cuentas, bordes = np.histogram(v, bins=min(40, max(8, int(np.sqrt(len(v))))))
    centros = [fmt((a + b) / 2, 3) for a, b in zip(bordes[:-1], bordes[1:], strict=True)]
    r.barras("Histograma", centros, {"frecuencia": cuentas}, eje_y="casos")
    r.lineas(et, s.index, {et: s.values})
    jb_p = stats.jarque_bera(v).pvalue
    cola = "colas pesadas" if stats.kurtosis(v) > 1 else "colas cercanas a la normal"
    r.resumen = (
        f"{et} ({freq}, {s.index[0].date()}→{s.index[-1].date()}, n={len(s)}): media {fmt(v.mean())}, "
        f"desvío {fmt(v.std(ddof=1))}, asimetría {fmt(stats.skew(v), 2)}, curtosis exc. "
        f"{fmt(stats.kurtosis(v), 2)} ({cola}; Jarque-Bera p={fmt(jb_p)})."
    )
    r.codigo = f"s = cargar('{sid}', freq='{freq}')\ns.describe(); s.skew(); s.kurt()"
    return r


@metodo(
    "acf_pacf",
    "Correlograma (ACF / PACF) y Ljung-Box",
    F,
    "¿Cuánta memoria tiene la serie y qué orden AR/MA sugiere?",
    params=[
        P_SERIE(),
        P_FREQ,
        P_TRANSF,
        Param("rezagos", "entero", "Rezagos", defecto=24, minimo=4, maximo=60),
        P_DESDE,
        P_HASTA,
    ],
    cuando="Para identificar un ARIMA (Box-Jenkins) o chequear si los residuos quedaron sin estructura.",
    supuestos=["Las bandas ±1,96/√n valen bajo ruido blanco y estacionariedad."],
    trampas=[
        "Una ACF que decae muy lento es señal de raíz unitaria: diferenciá antes de leer órdenes.",
        "Con muchos rezagos, alguno 'sale' significativo por azar (5 de cada 100).",
    ],
    etiquetas=["autocorrelación", "box-jenkins", "ruido blanco", "ljung-box", "correlograma"],
    nivel="basico",
)
def acf_pacf(sid, freq, transf, rezagos, desde, hasta):
    from statsmodels.stats.diagnostic import acorr_ljungbox
    from statsmodels.tsa.stattools import acf, pacf

    s, et = serie(sid, freq, transf, desde, hasta, minimo=20)
    k = int(min(rezagos, len(s) // 2 - 1))
    a = acf(s, nlags=k, fft=True)[1:]
    p = pacf(s, nlags=k, method="ywm")[1:]
    banda = 1.96 / np.sqrt(len(s))
    r = Resultado()
    lags = list(range(1, k + 1))
    r.barras("ACF", lags, {"ACF": a}, banda=banda)
    r.barras("PACF", lags, {"PACF": p}, banda=banda)
    puntos = [x for x in (1, 4, 6, 12, 24, 36) if x <= k]
    lb = acorr_ljungbox(s, lags=puntos, return_df=True)
    r.tabla(
        "Ljung-Box (H0: sin autocorrelación hasta el rezago)",
        ["rezago", "Q", "p"],
        [[int(i), row.lb_stat, row.lb_pvalue] for i, row in lb.iterrows()],
        resaltar_p="p",
    )
    fuera_acf = [lag for lag, v in zip(lags, a, strict=True) if abs(v) > banda]
    fuera_pacf = [lag for lag, v in zip(lags, p, strict=True) if abs(v) > banda]
    lento = len(a) > 10 and a[9] > 0.5
    r.metrica("ACF(1)", a[0])
    r.metrica("Rezagos ACF fuera de banda", len(fuera_acf))
    r.metrica("Rezagos PACF fuera de banda", len(fuera_pacf))
    sug = ""
    if lento:
        r.veredicto(
            "La ACF decae muy lento (ACF(10) > 0,5): típico de raíz unitaria. Diferenciá la serie antes "
            "de identificar órdenes.",
            "rojo",
        )
    else:
        corte_p = max([x for x in fuera_pacf if x <= 6], default=0)
        corte_q = max([x for x in fuera_acf if x <= 6], default=0)
        sug = f"Sugerencia Box-Jenkins: AR({corte_p}) / MA({corte_q}) como punto de partida."
        r.veredicto(sug, "verde" if lb["lb_pvalue"].min() > 0.05 else "amarillo")
    per = PERIODO.get(freq, 1)
    if not lento and per > 1 and per <= k and abs(a[per - 1]) > banda:
        r.advertir(f"Pico en el rezago {per}: hay estacionalidad que conviene modelar (SARIMA) o quitar.")
    r.resumen = (
        f"Correlograma de {et}: ACF(1)={fmt(a[0])}; {len(fuera_acf)} rezagos ACF y {len(fuera_pacf)} PACF "
        f"fuera de ±{fmt(banda)}. Ljung-Box p mín={fmt(lb['lb_pvalue'].min())}. {sug}"
    )
    r.datos = {"acf": a, "pacf": p}
    r.codigo = "from statsmodels.graphics.tsaplots import plot_acf, plot_pacf\nplot_acf(s); plot_pacf(s)"
    return r


@metodo(
    "correlacion_cruzada",
    "Correlación cruzada (adelantos y rezagos)",
    F,
    "¿X adelanta o sigue a Y, y con cuántos períodos?",
    params=[
        P_SERIE("sid_x", "Serie X"),
        P_SERIE("sid_y", "Serie Y"),
        P_FREQ,
        Param("transf", "opcion", "Transformación", defecto="dif_log", opciones=list(P_TRANSF.opciones)),
        Param("rezagos", "entero", "Rezagos máximos", defecto=12, minimo=1, maximo=36),
    ],
    cuando="Para encontrar indicadores líderes antes de una regresión o un VAR.",
    trampas=[
        "Correlación cruzada en niveles de series con tendencia es casi siempre espuria: usá tasas.",
        "Que X adelante a Y no es causalidad; es precedencia.",
    ],
    etiquetas=["indicador líder", "adelanto", "rezago", "ccf"],
    nivel="basico",
)
def correlacion_cruzada(sid_x, sid_y, freq, transf, rezagos):
    df, et = panel([sid_x, sid_y], freq, transf, minimo=20)
    x, y = df[sid_x], df[sid_y]
    ks = list(range(-rezagos, rezagos + 1))
    corr = [x.shift(k).corr(y) for k in ks]  # k>0: X en t−k contra Y en t → X adelanta
    banda = 1.96 / np.sqrt(len(df))
    r = Resultado()
    r.barras(f"corr({et[sid_x]} en t−k, {et[sid_y]} en t)", ks, {"correlación": corr}, banda=banda)
    i = int(np.nanargmax(np.abs(corr)))
    kmax, cmax = ks[i], corr[i]
    r.metrica("Rezago de máx. |corr|", kmax)
    r.metrica("Correlación máxima", cmax)
    r.metrica("Correlación contemporánea", corr[rezagos])
    if kmax > 0:
        txt = f"{et[sid_x]} ADELANTA a {et[sid_y]} en {kmax} períodos (corr {fmt(cmax)})."
    elif kmax < 0:
        txt = f"{et[sid_x]} SIGUE a {et[sid_y]} con {-kmax} períodos de rezago (corr {fmt(cmax)})."
    else:
        txt = f"La relación más fuerte es contemporánea (corr {fmt(cmax)})."
    r.veredicto(txt, "verde" if abs(cmax) > banda else "amarillo")
    if transf in ("nivel", "log"):
        r.advertir("Estás correlacionando niveles: con tendencias comunes la correlación es espuria.")
    r.resumen = txt + f" Banda de significancia ±{fmt(banda)} (n={len(df)})."
    return r


@metodo(
    "periodograma",
    "Periodograma y ciclos dominantes",
    F,
    "¿Qué ciclos (en períodos) dominan la variabilidad de la serie?",
    params=[
        P_SERIE(),
        P_FREQ,
        Param("transf", "opcion", "Transformación", defecto="dif_log", opciones=list(P_TRANSF.opciones)),
    ],
    cuando="Para detectar estacionalidad y ciclos económicos sin suponer un modelo.",
    supuestos=["Estacionariedad: aplicalo sobre tasas o diferencias, no sobre niveles con tendencia."],
    trampas=["El periodograma crudo es ruidoso: se suaviza con la ventana de Welch."],
    etiquetas=["espectral", "frecuencia", "ciclo", "fourier", "welch"],
)
def periodograma(sid, freq, transf):
    from scipy import signal

    s, et = serie(sid, freq, transf, minimo=32)
    v = s.values - s.values.mean()
    f, pxx = signal.welch(v, fs=1.0, nperseg=min(len(v), 128), detrend="linear")
    f, pxx = f[1:], pxx[1:]
    periodos = 1 / f
    orden = np.argsort(pxx)[::-1][:5]
    r = Resultado()
    r.lineas(
        "Densidad espectral (Welch) por período",
        [fmt(p, 3) for p in periodos[::-1]],
        {"densidad": pxx[::-1]},
        eje_y="densidad",
    )
    r.tabla(
        "Ciclos dominantes",
        ["período (obs.)", "en años", "% de la varianza"],
        [[periodos[i], periodos[i] / PERIODO.get(freq, 1), pxx[i] / pxx.sum() * 100] for i in orden],
    )
    top = periodos[orden[0]]
    r.metrica("Ciclo dominante (obs.)", top)
    r.resumen = (
        f"Espectro de {et}: el ciclo dominante dura ≈{fmt(top, 3)} períodos "
        f"(≈{fmt(top / PERIODO.get(freq, 1), 2)} años) y explica {fmt(pxx[orden[0]] / pxx.sum() * 100, 2)} % "
        "de la varianza espectral."
    )
    return r


@metodo(
    "perfil_estacional",
    "Perfil estacional",
    F,
    "¿Hay meses (o trimestres) sistemáticamente distintos?",
    params=[
        P_SERIE(),
        Param("freq", "opcion", "Frecuencia", defecto="mensual", opciones=["mensual", "trimestral"]),
        Param("transf", "opcion", "Transformación", defecto="dif_log", opciones=list(P_TRANSF.opciones)),
    ],
    cuando="Antes de decidir si desestacionalizar, usar dummies estacionales o un SARIMA.",
    trampas=["En niveles con tendencia, el perfil confunde estacionalidad con crecimiento."],
    etiquetas=["estacionalidad", "kruskal-wallis", "mes", "trimestre"],
    nivel="basico",
)
def perfil_estacional(sid, freq, transf):
    from scipy import stats

    s, et = serie(sid, freq, transf, minimo=24)
    clave = s.index.month if freq == "mensual" else s.index.quarter
    grupos = [s[clave == k].values for k in sorted(set(clave))]
    etiquetas = (
        ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
        if freq == "mensual"
        else ["T1", "T2", "T3", "T4"]
    )
    medias = [g.mean() for g in grupos]
    mediana = [np.median(g) for g in grupos]
    kw = stats.kruskal(*grupos)
    r = Resultado()
    r.barras("Promedio por período del año", etiquetas[: len(medias)], {"media": medias, "mediana": mediana})
    r.tabla(
        "Por período del año",
        ["período", "media", "mediana", "desvío", "n"],
        [[etiquetas[i], g.mean(), np.median(g), g.std(ddof=1), len(g)] for i, g in enumerate(grupos)],
    )
    r.metrica("Kruskal-Wallis p", kw.pvalue, "H0: todos los períodos tienen la misma distribución")
    hay = kw.pvalue < 0.05
    r.veredicto(
        "Hay estacionalidad significativa: modelala (dummies, SARIMA) o desestacionalizá."
        if hay
        else "No se detecta estacionalidad significativa.",
        "amarillo" if hay else "verde",
    )
    r.resumen = f"Perfil estacional de {et}: Kruskal-Wallis p={fmt(kw.pvalue)} → {'hay' if hay else 'no hay'} estacionalidad."
    return r


@metodo(
    "ventanas_moviles",
    "Estadísticos en ventanas móviles",
    F,
    "¿La media, la volatilidad o la correlación cambiaron con el tiempo?",
    params=[
        P_SERIES("sids", "Series (1 o 2)", minimo=1, maximo=2),
        P_FREQ,
        P_TRANSF,
        Param("ventana", "entero", "Ventana (obs.)", defecto=24, minimo=4, maximo=240),
    ],
    cuando="Para ver inestabilidad antes de estimar un modelo de parámetros fijos.",
    trampas=["La ventana define lo que ves: probá dos tamaños antes de concluir."],
    etiquetas=["rolling", "media móvil", "volatilidad", "correlación móvil", "inestabilidad"],
    nivel="basico",
)
def ventanas_moviles(sids, freq, transf, ventana):
    df, et = panel(sids, freq, transf, minimo=ventana + 5)
    r = Resultado()
    a = sids[0]
    r.lineas(
        f"{et[a]}: media y desvío móviles ({ventana} obs.)",
        df.index,
        {
            et[a]: df[a],
            "media móvil": df[a].rolling(ventana).mean(),
            "desvío móvil": df[a].rolling(ventana).std(),
        },
        estilos={"media móvil": {"guion": "dash"}, "desvío móvil": {"guion": "dot"}},
        y2=["desvío móvil"],
    )
    sd = df[a].rolling(ventana).std().dropna()
    r.metrica("Desvío móvil mín", sd.min())
    r.metrica("Desvío móvil máx", sd.max())
    r.metrica("Máx / mín", sd.max() / sd.min() if sd.min() > 0 else None)
    txt = f"La volatilidad de {et[a]} en ventanas de {ventana} va de {fmt(sd.min())} a {fmt(sd.max())}"
    if len(sids) == 2:
        b = sids[1]
        rc = df[a].rolling(ventana).corr(df[b])
        r.lineas(f"Correlación móvil {et[a]} vs {et[b]}", df.index, {"correlación": rc})
        rc = rc.dropna()
        r.metrica("Corr. móvil mín", rc.min())
        r.metrica("Corr. móvil máx", rc.max())
        txt += f"; la correlación con {et[b]} oscila entre {fmt(rc.min())} y {fmt(rc.max())}"
        if rc.max() - rc.min() > 1:
            r.advertir("La correlación cambia de signo: una regresión de coeficiente fijo la promedia mal.")
    r.resumen = txt + "."
    return r


@metodo(
    "dispersion",
    "Diagrama de dispersión y correlaciones",
    F,
    "¿Qué forma tiene la relación entre X e Y (lineal, monótona, con outliers)?",
    params=[
        P_SERIE("sid_x", "Serie X"),
        P_SERIE("sid_y", "Serie Y"),
        P_FREQ,
        Param("transf", "opcion", "Transformación", defecto="dif_log", opciones=list(P_TRANSF.opciones)),
        Param("rezago_x", "entero", "Rezago de X", defecto=0, minimo=0, maximo=24),
    ],
    cuando="Antes de una regresión: Pearson mide lo lineal, Spearman y Kendall lo monótono.",
    trampas=["Un solo outlier (2002, 2020) puede fabricar o destruir una correlación de Pearson."],
    etiquetas=["scatter", "pearson", "spearman", "kendall", "outliers"],
    nivel="basico",
)
def dispersion(sid_x, sid_y, freq, transf, rezago_x):
    from scipy import stats

    df, et = panel([sid_x, sid_y], freq, transf, minimo=10)
    x = df[sid_x].shift(rezago_x)
    d = pd.concat([x, df[sid_y]], axis=1).dropna()
    xv, yv = d.iloc[:, 0].values, d.iloc[:, 1].values
    pe = stats.pearsonr(xv, yv)
    sp = stats.spearmanr(xv, yv)
    ke = stats.kendalltau(xv, yv)
    b, a = np.polyfit(xv, yv, 1)
    ex = et[sid_x] + (f" (t−{rezago_x})" if rezago_x else "")
    r = Resultado()
    r.dispersion(f"{et[sid_y]} vs {ex}", xv, yv, ex, et[sid_y], recta=(b, a), textos=[str(f.date()) for f in d.index])
    r.tabla(
        "Correlaciones",
        ["medida", "coeficiente", "p"],
        [["Pearson (lineal)", pe.statistic, pe.pvalue], ["Spearman (rangos)", sp.statistic, sp.pvalue], ["Kendall τ", ke.statistic, ke.pvalue]],
        resaltar_p="p",
    )
    r.metrica("Pendiente MCO", b)
    r.metrica("Pearson", pe.statistic)
    r.metrica("Spearman", sp.statistic)
    z = np.abs(stats.zscore(yv - (a + b * xv)))
    outl = d.index[z > 3]
    if len(outl):
        r.advertir(f"{len(outl)} observaciones con residuo > 3 desvíos: {', '.join(str(f.date()) for f in outl[:6])}.")
    if abs(pe.statistic - sp.statistic) > 0.2:
        r.advertir("Pearson y Spearman difieren mucho: la relación no es lineal o la dominan outliers.")
    r.resumen = (
        f"{et[sid_y]} vs {ex} (n={len(d)}): Pearson {fmt(pe.statistic)} (p={fmt(pe.pvalue)}), "
        f"Spearman {fmt(sp.statistic)}, pendiente {fmt(b)}."
    )
    return r


@metodo(
    "matriz_correlacion",
    "Matriz de correlaciones con significancia",
    F,
    "¿Cómo se mueven juntas varias series?",
    params=[
        P_SERIES("sids", "Series", minimo=2, maximo=15),
        P_FREQ,
        Param("transf", "opcion", "Transformación", defecto="dif_log", opciones=list(P_TRANSF.opciones)),
        Param("metodo", "opcion", "Medida", defecto="pearson", opciones=["pearson", "spearman", "kendall"]),
    ],
    cuando="Para mapear un conjunto de candidatas antes de elegir regresores o armar un factor.",
    trampas=[
        "En niveles, todas las series con tendencia correlacionan alto (regresión espuria de Granger-Newbold).",
        "Muchas parejas ⇒ muchas comparaciones: alguna sale significativa por azar.",
    ],
    etiquetas=["correlación", "heatmap", "multicolinealidad"],
    nivel="basico",
)
def matriz_correlacion(sids, freq, transf, metodo):
    from scipy import stats

    df, et = panel(sids, freq, transf, minimo=10)
    c = df.corr(method=metodo)
    fn = {"pearson": stats.pearsonr, "spearman": stats.spearmanr, "kendall": stats.kendalltau}[metodo]
    filas = []
    for i, a in enumerate(sids):
        for b in sids[i + 1 :]:
            res = fn(df[a], df[b])
            filas.append([et[a], et[b], res.statistic, res.pvalue])
    filas.sort(key=lambda f: -abs(f[2]))
    labels = [et[s] for s in sids]
    r = Resultado()
    r.mapa_calor(f"Correlación de {metodo.capitalize()} (n={len(df)})", labels, labels, c.values)
    r.tabla("Pares ordenados por |correlación|", ["A", "B", "corr", "p"], filas, resaltar_p="p")
    r.metrica("Pares", len(filas))
    r.metrica("Pares con p<0,05", sum(1 for f in filas if f[3] < 0.05))
    if transf in ("nivel", "log"):
        r.advertir("Correlaciones en niveles: con tendencias comunes son espurias. Usá dif_log.")
    top = filas[0]
    r.resumen = (
        f"Matriz de {metodo} entre {len(sids)} series (n={len(df)}): el par más asociado es "
        f"{top[0]}–{top[1]} ({fmt(top[2])}); {sum(1 for f in filas if f[3] < 0.05)} de {len(filas)} pares con p<0,05."
    )
    r.datos = {"matriz": c.values, "labels": labels}
    return r

