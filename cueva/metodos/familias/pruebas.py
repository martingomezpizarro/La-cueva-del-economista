"""Pruebas sobre las series: raíz unitaria, quiebres, normalidad, no linealidad, memoria larga."""

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
    evento_cercano,
    fmt,
    panel,
    serie,
)
from cueva.metodos.registro import metodo

F = "pruebas"


# ──────────────────────────────────────────────────────────────────────────
# Raíz unitaria: la batería completa
# ──────────────────────────────────────────────────────────────────────────
def _bateria(v: np.ndarray, tendencia: str):
    from arch.unitroot import DFGLS, KPSS, PhillipsPerron, ZivotAndrews
    from statsmodels.tsa.stattools import adfuller

    out = {}
    adf = adfuller(v, regression=tendencia, autolag="AIC")
    out["ADF"] = (adf[0], adf[1], "raíz unitaria")
    try:
        pp = PhillipsPerron(v, trend=tendencia)
        out["Phillips-Perron"] = (pp.stat, pp.pvalue, "raíz unitaria")
    except Exception:
        pass
    try:
        g = DFGLS(v, trend=tendencia if tendencia in ("c", "ct") else "c")
        out["DF-GLS (ERS)"] = (g.stat, g.pvalue, "raíz unitaria")
    except Exception:
        pass
    try:
        k = KPSS(v, trend=tendencia if tendencia in ("c", "ct") else "c")
        out["KPSS"] = (k.stat, k.pvalue, "estacionariedad")
    except Exception:
        pass
    try:
        za = ZivotAndrews(v, trend="c" if tendencia == "c" else "ct", trim=0.15)
        out["Zivot-Andrews"] = (za.stat, za.pvalue, "raíz unitaria (con 1 quiebre)")
    except Exception:
        pass
    return out


def _veredicto_bateria(b: dict) -> str:
    """'estacionaria' | 'raiz_unitaria' | 'ambiguo' por voto de los tests."""
    rech = [p < 0.05 for nombre, (_, p, h0) in b.items() if h0.startswith("raíz") and p == p]
    kpss = b.get("KPSS")
    votos_est = sum(rech)
    votos_ru = len(rech) - votos_est
    if kpss and kpss[1] == kpss[1]:
        if kpss[1] < 0.05:
            votos_ru += 1
        else:
            votos_est += 1
    if votos_est >= votos_ru + 2:
        return "estacionaria"
    if votos_ru >= votos_est + 2:
        return "raiz_unitaria"
    return "ambiguo"


@metodo(
    "raiz_unitaria",
    "Batería de raíz unitaria (ADF, PP, DF-GLS, KPSS, Zivot-Andrews)",
    F,
    "¿La serie es estacionaria o tiene raíz unitaria? ¿Cuál es su orden de integración?",
    params=[
        P_SERIE(),
        P_FREQ,
        P_TRANSF,
        Param(
            "tendencia",
            "opcion",
            "Determinísticos",
            defecto="c",
            opciones=["c", "ct", "n"],
            ayuda="c = constante, ct = constante y tendencia, n = ninguno",
        ),
        P_DESDE,
        P_HASTA,
    ],
    cuando="Antes de cualquier regresión entre series: define si se trabaja en niveles, diferencias o con cointegración.",
    supuestos=[
        "ADF/PP/DF-GLS: H0 = raíz unitaria. KPSS: H0 = estacionariedad (por eso se combinan).",
        "Zivot-Andrews permite un quiebre endógeno en nivel/tendencia bajo la alternativa.",
    ],
    trampas=[
        "Un quiebre estructural no modelado hace que ADF no rechace aunque la serie sea estacionaria por tramos.",
        "La potencia es baja con muestras cortas: 'no rechazo' no es 'acepto'.",
        "Elegir los determinísticos mirando el p-valor es pescar: decidilos mirando el gráfico.",
    ],
    referencias=["Enders (2015), cap. 4", "Elliott, Rothenberg y Stock (1996)", "Zivot y Andrews (1992)"],
    deps=["arch"],
    etiquetas=["estacionariedad", "adf", "kpss", "dickey-fuller", "phillips-perron", "integración", "I(1)"],
    nivel="basico",
)
def raiz_unitaria(sid, freq, transf, tendencia, desde, hasta):
    s, et = serie(sid, freq, transf, desde, hasta, minimo=25)
    r = Resultado()
    filas = []
    veredictos = {}
    for nombre_d, d in (("nivel", 0), ("Δ", 1), ("Δ²", 2)):
        v = np.diff(s.values, n=d) if d else s.values
        if len(v) < 20:
            break
        b = _bateria(v, tendencia if d == 0 else "c")
        ver = _veredicto_bateria(b)
        veredictos[d] = ver
        for test, (stat, p, h0) in b.items():
            filas.append([nombre_d, test, h0, stat, p])
        if ver == "estacionaria":
            break
    r.tabla(
        "Resultados (H0 en la tercera columna)",
        ["sobre", "test", "H0", "estadístico", "p"],
        filas,
        resaltar_p="p",
    )
    orden = next((d for d, v in veredictos.items() if v == "estacionaria"), None)
    if orden is None:
        orden_txt = "indeterminado (mixto)"
        sem = "amarillo"
    else:
        orden_txt = f"I({orden})"
        sem = "verde" if orden == 0 else "amarillo"
    r.metrica("Orden de integración", orden_txt)
    za = [f for f in filas if f[1] == "Zivot-Andrews" and f[0] == "nivel"]
    if veredictos.get(0) != "estacionaria" and za and za[0][4] < 0.05:
        r.advertir(
            "Zivot-Andrews rechaza raíz unitaria permitiendo un quiebre: la serie puede ser estacionaria "
            "alrededor de un cambio de nivel/tendencia. Corré «quiebres_estructurales»."
        )
    texto = {
        0: f"{et} es estacionaria en niveles (I(0)): se puede modelar sin diferenciar.",
        1: f"{et} es I(1): trabajá en diferencias, o en niveles sólo si cointegra con otras series.",
        2: f"{et} es I(2): inusual en economía; revisá la transformación (¿usaste log?).",
    }.get(orden, f"Resultados mixtos para {et}: probá con otros determinísticos o buscá quiebres.")
    r.veredicto(texto, sem)
    r.resumen = texto + " Tests: " + "; ".join(f"{f[0]} {f[1]} p={fmt(f[4])}" for f in filas)
    r.datos = {"orden": orden, "veredictos": veredictos}
    r.codigo = (
        "from statsmodels.tsa.stattools import adfuller\nfrom arch.unitroot import PhillipsPerron, DFGLS, KPSS, ZivotAndrews\n"
        f"adfuller(s, regression='{tendencia}', autolag='AIC'); KPSS(s); ZivotAndrews(s)"
    )
    return r


# ──────────────────────────────────────────────────────────────────────────
# Quiebres estructurales: Bai-Perron por programación dinámica
# ──────────────────────────────────────────────────────────────────────────
def _ssr_segmentos(y: np.ndarray, modelo: str, h: int) -> np.ndarray:
    """SSR[i, j] = suma de residuos² de ajustar el modelo al tramo y[i:j] (j exclusivo).
    Usa sumas acumuladas: O(n²) en memoria y tiempo, vectorizado por fila."""
    n = len(y)
    t = np.arange(n, dtype=float)
    c = lambda a: np.concatenate([[0.0], np.cumsum(a)])  # noqa: E731
    Sy, Syy = c(y), c(y * y)
    if modelo == "tendencia":
        St, Stt, Sty = c(t), c(t * t), c(t * y)
    ssr = np.full((n + 1, n + 1), np.inf)
    for i in range(0, n - h + 1):
        j = np.arange(i + h, n + 1)
        m = (j - i).astype(float)
        sy, syy = Sy[j] - Sy[i], Syy[j] - Syy[i]
        if modelo == "media":
            ssr[i, j] = syy - sy * sy / m
        else:
            st, stt, sty = St[j] - St[i], Stt[j] - Stt[i], Sty[j] - Sty[i]
            vt = stt - st * st / m
            cty = sty - st * sy / m
            vy = syy - sy * sy / m
            with np.errstate(divide="ignore", invalid="ignore"):
                ssr[i, j] = np.where(vt > 0, vy - cty * cty / vt, vy)
    return np.maximum(ssr, 0)


def bai_perron(y: np.ndarray, max_quiebres: int, modelo: str = "media", recorte: float = 0.15):
    """Devuelve {m: (ssr_total, [índices de quiebre])} para m = 0..max_quiebres."""
    n = len(y)
    h = max(int(np.floor(recorte * n)), 3 if modelo == "media" else 4)
    ssr = _ssr_segmentos(y, modelo, h)
    out = {0: (ssr[0, n], [])}
    # V[k][j]: mejor SSR de y[0:j] con k quiebres; P guarda el último quiebre
    V = [ssr[0, :].copy()]
    P = [np.zeros(n + 1, dtype=int)]
    for k in range(1, max_quiebres + 1):
        Vk = np.full(n + 1, np.inf)
        Pk = np.zeros(n + 1, dtype=int)
        for j in range((k + 1) * h, n + 1):
            cand = np.arange(k * h, j - h + 1)
            if not len(cand):
                continue
            tot = V[k - 1][cand] + ssr[cand, j]
            a = int(np.argmin(tot))
            Vk[j], Pk[j] = tot[a], cand[a]
        V.append(Vk)
        P.append(Pk)
        if not np.isfinite(Vk[n]):
            break
        qs, j = [], n
        for kk in range(k, 0, -1):
            j = P[kk][j]
            qs.append(int(j))
        out[k] = (Vk[n], sorted(qs))
    return out


@metodo(
    "quiebres_estructurales",
    "Quiebres estructurales múltiples (Bai-Perron)",
    F,
    "¿Cuándo cambió el nivel o la tendencia de la serie, y coincide con algún evento histórico?",
    params=[
        P_SERIE(),
        P_FREQ,
        P_TRANSF,
        Param("modelo", "opcion", "Qué cambia", defecto="media", opciones=["media", "tendencia"]),
        Param("max_quiebres", "entero", "Máx. quiebres", defecto=5, minimo=1, maximo=8),
        Param("recorte", "real", "Tramo mínimo (% de la muestra)", defecto=0.15, minimo=0.05, maximo=0.3),
        Param(
            "criterio",
            "opcion",
            "Criterio para elegir cuántos",
            defecto="BIC",
            opciones=["BIC", "LWZ"],
            ayuda="LWZ (Liu-Wu-Zidek) penaliza más: menos quiebres",
        ),
        P_DESDE,
        P_HASTA,
    ],
    cuando="Argentina es un catálogo de quiebres: corrélo antes de cualquier modelo de parámetros fijos.",
    supuestos=[
        "Errores sin autocorrelación fuerte dentro de cada tramo (si no, el BIC sobreestima quiebres).",
        "Cada tramo tiene al menos el recorte mínimo de la muestra.",
    ],
    trampas=[
        "Con la serie en niveles I(1), Bai-Perron 'encuentra' quiebres que son sólo deriva estocástica: aplicalo a tasas.",
        "La fecha estimada tiene incertidumbre: un evento a ±6 meses es 'coincidente', no 'la causa'.",
    ],
    referencias=["Bai y Perron (1998, 2003)", "Liu, Wu y Zidek (1997)"],
    etiquetas=["bai-perron", "cambio estructural", "quiebre", "régimen", "línea de tiempo"],
)
def quiebres_estructurales(sid, freq, transf, modelo, max_quiebres, recorte, criterio, desde, hasta):
    s, et = serie(sid, freq, transf, desde, hasta, minimo=30)
    y = s.values.astype(float)
    n = len(y)
    if n > 1500:
        raise ErrorMetodo("Más de 1.500 observaciones: bajá a mensual o recortá la muestra.")
    res = bai_perron(y, max_quiebres, modelo, recorte)
    kparam = 1 if modelo == "media" else 2
    crit = {}
    for m, (ssr, _) in res.items():
        npar = (m + 1) * kparam + m
        sigma2 = max(ssr / n, 1e-300)
        pen = np.log(n) if criterio == "BIC" else 0.299 * (np.log(n) ** 2.1)
        crit[m] = n * np.log(sigma2) + npar * pen
    m_opt = min(crit, key=crit.get)
    qs = res[m_opt][1]
    r = Resultado()
    r.tabla(
        f"Selección del número de quiebres ({criterio})",
        ["quiebres", "SSR", criterio],
        [[m, res[m][0], crit[m]] for m in sorted(res)],
    )
    # ajuste por tramos
    ajuste = np.empty(n)
    bordes = [0, *qs, n]
    filas_tramos = []
    for a, b in zip(bordes[:-1], bordes[1:], strict=True):
        seg = y[a:b]
        if modelo == "media":
            ajuste[a:b] = seg.mean()
            filas_tramos.append(
                [str(s.index[a].date()), str(s.index[b - 1].date()), b - a, seg.mean(), seg.std(ddof=1)]
            )
        else:
            tt = np.arange(a, b)
            pend, ord_ = np.polyfit(tt, seg, 1)
            ajuste[a:b] = ord_ + pend * tt
            filas_tramos.append([str(s.index[a].date()), str(s.index[b - 1].date()), b - a, seg.mean(), pend])
    r.tabla(
        "Tramos",
        ["desde", "hasta", "obs.", "media", "desvío" if modelo == "media" else "pendiente"],
        filas_tramos,
    )
    filas_q, marcas = [], []
    for q in qs:
        f = s.index[q]
        ev = evento_cercano(f, ventana_meses=6 if freq == "mensual" else 12)
        filas_q.append([str(f.date()), ev["titulo"] if ev else "—", ev["fecha"] if ev else ""])
        marcas.append({"x": str(f.date()), "texto": ev["titulo"] if ev else "quiebre"})
    if filas_q:
        r.tabla(
            "Quiebres y evento coincidente de la Línea de Tiempo (±6 meses)",
            ["fecha", "evento", "fecha del evento"],
            filas_q,
        )
    r.lineas(
        f"{et} con ajuste por tramos",
        s.index,
        {et: y, "ajuste por tramos": ajuste},
        estilos={"ajuste por tramos": {"ancho": 2.5}},
        marcas=marcas,
    )
    r.serie(f"{sid}_tramos", s.index, ajuste, f"Ajuste por tramos de {et} (Bai-Perron, {m_opt} quiebres)")
    r.metrica("Quiebres elegidos", m_opt)
    if transf in ("nivel", "log"):
        r.advertir(
            "Serie en niveles: si es I(1), parte de los quiebres pueden ser deriva estocástica. Probá con dif_log."
        )
    fechas = ", ".join(f[0] for f in filas_q) or "ninguno"
    coinc = sum(1 for f in filas_q if f[1] != "—")
    r.veredicto(
        f"{m_opt} quiebre(s) en {et}: {fechas}. {coinc} coinciden con eventos de la Línea de Tiempo.",
        "verde" if m_opt == 0 else "amarillo",
    )
    r.resumen = f"Bai-Perron ({modelo}, {criterio}) sobre {et}: {m_opt} quiebre(s) en {fechas}; {coinc} con evento coincidente."
    r.datos = {"quiebres": [f[0] for f in filas_q]}
    return r


@metodo(
    "cambio_de_punto",
    "Detección de cambios de régimen (PELT)",
    F,
    "¿En qué fechas cambió la distribución (media o varianza) de la serie?",
    params=[
        P_SERIE(),
        P_FREQ,
        Param("transf", "opcion", "Transformación", defecto="dif_log", opciones=list(P_TRANSF.opciones)),
        Param(
            "costo",
            "opcion",
            "Qué cambia",
            defecto="normal",
            opciones=["l2", "normal", "rbf"],
            ayuda="l2 = media; normal = media y varianza; rbf = cualquier cambio de distribución",
        ),
        Param(
            "penalidad",
            "real",
            "Penalidad (más alta = menos cambios)",
            defecto=0.0,
            minimo=0,
            maximo=1000,
            ayuda="0 = automática (BIC)",
        ),
    ],
    cuando="Para encontrar cambios de volatilidad (ej. regímenes de alta inflación) que Bai-Perron en media no ve.",
    trampas=["La penalidad manda: mostrá el resultado con dos penalidades antes de concluir."],
    deps=["ruptures"],
    referencias=["Killick, Fearnhead y Eckley (2012)", "Truong, Oudre y Vayatis (2020)"],
    etiquetas=["changepoint", "pelt", "ruptures", "varianza", "régimen"],
)
def cambio_de_punto(sid, freq, transf, costo, penalidad):
    import ruptures as rpt

    s, et = serie(sid, freq, transf, minimo=30)
    y = s.values.reshape(-1, 1)
    yz = (y - y.mean()) / (y.std() or 1)
    pen = penalidad or 3 * np.log(len(y))
    algo = rpt.Pelt(model=costo, min_size=max(3, len(y) // 40)).fit(yz)
    bk = [b for b in algo.predict(pen=pen) if b < len(y)]
    r = Resultado()
    filas, marcas = [], []
    bordes = [0, *bk, len(y)]
    for a, b in zip(bordes[:-1], bordes[1:], strict=True):
        seg = s.values[a:b]
        filas.append(
            [
                str(s.index[a].date()),
                str(s.index[b - 1].date()),
                b - a,
                seg.mean(),
                seg.std(ddof=1) if b - a > 1 else None,
            ]
        )
    for b in bk:
        ev = evento_cercano(s.index[b])
        marcas.append({"x": str(s.index[b].date()), "texto": ev["titulo"] if ev else "cambio"})
    r.tabla("Regímenes detectados", ["desde", "hasta", "obs.", "media", "desvío"], filas)
    r.lineas(et, s.index, {et: s.values}, marcas=marcas)
    r.metrica("Cambios", len(bk))
    r.metrica("Penalidad usada", pen)
    r.resumen = (
        f"PELT ({costo}) sobre {et}: {len(bk)} cambios en " + (", ".join(m["x"] for m in marcas) or "—") + "."
    )
    return r


@metodo(
    "prueba_chow",
    "Prueba de Chow en una fecha",
    F,
    "¿La relación entre Y y X cambió en una fecha que elijo (una reforma, una crisis)?",
    params=[
        P_SERIE("dep", "Dependiente (Y)"),
        P_SERIES(
            "indeps",
            "Explicativas (X)",
            minimo=0,
            maximo=6,
            requerido=False,
            ayuda="Vacío = sólo constante (cambio de media)",
        ),
        Param("fecha", "fecha", "Fecha del quiebre", requerido=True),
        P_FREQ,
        Param("transf", "opcion", "Transformación", defecto="dif_log", opciones=list(P_TRANSF.opciones)),
    ],
    cuando="Cuando la fecha del cambio la da la historia (una ley, un plan), no los datos.",
    supuestos=["La fecha es exógena: elegirla mirando el gráfico invalida el p-valor (usá Bai-Perron)."],
    trampas=["Con heterocedasticidad entre tramos la F de Chow se distorsiona."],
    referencias=["Chow (1960)"],
    etiquetas=["chow", "quiebre conocido", "reforma", "estabilidad"],
    nivel="basico",
)
def prueba_chow(dep, indeps, fecha, freq, transf):
    import statsmodels.api as sm
    from scipy import stats

    df, et = panel([dep, *(indeps or [])], freq, transf, minimo=20)
    y = df[dep].values
    X = sm.add_constant(df[indeps].values) if indeps else np.ones((len(df), 1))
    corte = int(np.searchsorted(df.index.values, np.datetime64(pd.Timestamp(fecha))))
    k = X.shape[1]
    if corte < k + 3 or len(df) - corte < k + 3:
        raise ErrorMetodo("La fecha deja un tramo demasiado corto a uno de los lados.")
    ssr = lambda yy, XX: float(sm.OLS(yy, XX).fit().ssr)  # noqa: E731
    s_tot, s1, s2 = ssr(y, X), ssr(y[:corte], X[:corte]), ssr(y[corte:], X[corte:])
    n = len(y)
    Fst = ((s_tot - s1 - s2) / k) / ((s1 + s2) / (n - 2 * k))
    p = stats.f.sf(Fst, k, n - 2 * k)
    r = Resultado()
    r.metrica("F de Chow", Fst)
    r.metrica("p", p)
    r.tabla(
        "Tramos",
        ["tramo", "desde", "hasta", "obs.", "SSR"],
        [
            ["antes", str(df.index[0].date()), str(df.index[corte - 1].date()), corte, s1],
            ["después", str(df.index[corte].date()), str(df.index[-1].date()), n - corte, s2],
        ],
    )
    ev = evento_cercano(df.index[corte])
    r.lineas(
        et[dep],
        df.index,
        {et[dep]: y},
        marcas=[{"x": str(df.index[corte].date()), "texto": ev["titulo"] if ev else fecha}],
    )
    hay = p < 0.05
    r.veredicto(
        f"{'Hay' if hay else 'No hay'} evidencia de cambio estructural en {fecha} (F={fmt(Fst)}, p={fmt(p)}).",
        "amarillo" if hay else "verde",
    )
    r.resumen = f"Chow en {fecha} para {et[dep]}: F={fmt(Fst)}, p={fmt(p)}."
    return r


@metodo(
    "cusum",
    "CUSUM de residuos recursivos",
    F,
    "¿Los coeficientes de la regresión son estables a lo largo de la muestra?",
    params=[
        P_SERIE("dep", "Dependiente (Y)"),
        P_SERIES("indeps", "Explicativas (X)", minimo=0, maximo=6, requerido=False),
        P_FREQ,
        Param("transf", "opcion", "Transformación", defecto="dif_log", opciones=list(P_TRANSF.opciones)),
    ],
    cuando="Como diagnóstico de estabilidad sin fijar fecha de quiebre (Brown, Durbin y Evans).",
    trampas=["CUSUM tiene poca potencia contra cambios que se compensan; mirá también CUSUM²."],
    referencias=["Brown, Durbin y Evans (1975)"],
    etiquetas=["cusum", "estabilidad", "residuos recursivos"],
)
def cusum(dep, indeps, freq, transf):
    import statsmodels.api as sm
    from statsmodels.stats.diagnostic import recursive_olsresiduals

    df, et = panel([dep, *(indeps or [])], freq, transf, minimo=25)
    X = sm.add_constant(df[indeps]) if indeps else pd.DataFrame({"const": np.ones(len(df))}, index=df.index)
    res = sm.OLS(df[dep], X).fit()
    rr = recursive_olsresiduals(res, skip=None, alpha=0.95)
    rresid, cus, ci = rr[3], rr[5], rr[6]
    k = X.shape[1]
    idx = df.index[k:]
    cus = np.asarray(cus)[-len(idx) :]
    lo, hi = np.asarray(ci[0])[-len(idx) :], np.asarray(ci[1])[-len(idx) :]
    w = np.asarray(rresid)[k:]
    w = w[np.isfinite(w)]
    cs2 = np.cumsum(w**2) / np.sum(w**2)
    sale = bool(np.any(cus > hi) or np.any(cus < lo))
    r = Resultado()
    r.lineas(
        "CUSUM con bandas al 5 %",
        idx,
        {"CUSUM": cus, "banda sup.": hi, "banda inf.": lo},
        estilos={"banda sup.": {"guion": "dash"}, "banda inf.": {"guion": "dash"}},
    )
    r.lineas(
        "CUSUM² (debería seguir la diagonal)",
        idx[-len(cs2) :],
        {"CUSUM²": cs2, "diagonal": np.linspace(0, 1, len(cs2))},
        estilos={"diagonal": {"guion": "dot"}},
    )
    r.metrica("¿Sale de las bandas?", "sí" if sale else "no")
    if sale:
        primera = idx[int(np.argmax((cus > hi) | (cus < lo)))]
        r.veredicto(
            f"El CUSUM sale de las bandas (primera vez en {primera.date()}): los coeficientes NO son estables.",
            "rojo",
        )
    else:
        r.veredicto("El CUSUM queda dentro de las bandas: no hay evidencia de inestabilidad.", "verde")
    r.resumen = f"CUSUM de {et[dep]}: {'inestable' if sale else 'estable'}."
    return r


@metodo(
    "normalidad",
    "Pruebas de normalidad",
    F,
    "¿La distribución es normal o tiene colas pesadas / asimetría?",
    params=[
        P_SERIE(),
        P_FREQ,
        Param("transf", "opcion", "Transformación", defecto="dif_log", opciones=list(P_TRANSF.opciones)),
    ],
    cuando="Para elegir distribución de errores (normal vs t en un GARCH) o justificar intervalos.",
    trampas=["Con n grande, cualquier desvío mínimo rechaza normalidad: mirá también el QQ."],
    etiquetas=["jarque-bera", "shapiro", "anderson", "qq", "colas pesadas"],
    nivel="basico",
)
def normalidad(sid, freq, transf):
    from scipy import stats

    s, et = serie(sid, freq, transf, minimo=20)
    v = s.values
    jb = stats.jarque_bera(v)
    sw = stats.shapiro(v[:5000])
    dk = stats.normaltest(v)
    ad = stats.anderson(v)
    r = Resultado()
    r.tabla(
        "H0: la distribución es normal",
        ["test", "estadístico", "p"],
        [
            ["Jarque-Bera", jb.statistic, jb.pvalue],
            ["Shapiro-Wilk", sw.statistic, sw.pvalue],
            ["D'Agostino K²", dk.statistic, dk.pvalue],
            ["Anderson-Darling (crítico 5 %: " + fmt(ad.critical_values[2]) + ")", ad.statistic, None],
        ],
        resaltar_p="p",
    )
    z = np.sort((v - v.mean()) / v.std(ddof=1))
    teo = stats.norm.ppf((np.arange(1, len(z) + 1) - 0.5) / len(z))
    r.dispersion("QQ normal", teo, z, "cuantil teórico", "cuantil observado (z)", recta=(1, 0))
    rech = jb.pvalue < 0.05
    r.veredicto(
        "Se rechaza normalidad: usá errores t o métodos robustos." if rech else "No se rechaza normalidad.",
        "amarillo" if rech else "verde",
    )
    r.resumen = f"Normalidad de {et}: JB p={fmt(jb.pvalue)}, Shapiro p={fmt(sw.pvalue)}, curtosis exc. {fmt(stats.kurtosis(v), 2)}."
    return r


@metodo(
    "no_linealidad_bds",
    "Prueba BDS de dependencia no lineal",
    F,
    "Después de sacar la estructura lineal, ¿queda dependencia (no linealidad, regímenes, ARCH)?",
    params=[
        P_SERIE(),
        P_FREQ,
        Param("transf", "opcion", "Transformación", defecto="dif_log", opciones=list(P_TRANSF.opciones)),
        Param("rezagos_ar", "entero", "Rezagos del filtro AR", defecto=4, minimo=0, maximo=24),
    ],
    cuando="Antes de saltar a modelos no lineales o redes: si BDS no rechaza, lo lineal alcanza.",
    supuestos=["Se aplica sobre residuos de un AR para no confundir dependencia lineal con no lineal."],
    referencias=["Brock, Dechert, Scheinkman y LeBaron (1996)"],
    etiquetas=["bds", "no lineal", "caos", "iid"],
    nivel="avanzado",
)
def no_linealidad_bds(sid, freq, transf, rezagos_ar):
    from statsmodels.tsa.ar_model import AutoReg
    from statsmodels.tsa.stattools import bds

    s, et = serie(sid, freq, transf, minimo=60)
    e = AutoReg(s.values, lags=rezagos_ar).fit().resid if rezagos_ar else s.values - s.values.mean()
    stat, p = bds(e, max_dim=5)
    r = Resultado()
    r.tabla(
        "BDS sobre residuos AR (H0: i.i.d.)",
        ["dimensión", "estadístico", "p"],
        [[d + 2, st, pv] for d, (st, pv) in enumerate(zip(stat, p, strict=True))],
        resaltar_p="p",
    )
    rech = bool(np.min(p) < 0.05)
    r.veredicto(
        "Queda dependencia no lineal: tiene sentido probar GARCH, regímenes o modelos no lineales (árboles, redes)."
        if rech
        else "No hay evidencia de dependencia no lineal: un modelo lineal es suficiente.",
        "amarillo" if rech else "verde",
    )
    r.resumen = f"BDS sobre {et} (filtro AR({rezagos_ar})): p mín={fmt(float(np.min(p)))}."
    return r


@metodo(
    "memoria_larga",
    "Memoria larga (Hurst y GPH)",
    F,
    "¿Los shocks se disipan rápido, nunca, o lentamente (integración fraccional)?",
    params=[
        P_SERIE(),
        P_FREQ,
        Param("transf", "opcion", "Transformación", defecto="dif_log", opciones=list(P_TRANSF.opciones)),
    ],
    cuando="Inflación, volatilidad y tasas suelen tener memoria larga: ni I(0) ni I(1).",
    supuestos=["GPH usa las frecuencias bajas del periodograma (ancho de banda n^0,5)."],
    trampas=["Quiebres estructurales imitan memoria larga: corré quiebres antes."],
    referencias=["Geweke y Porter-Hudak (1983)", "Hurst (1951)"],
    etiquetas=["hurst", "gph", "arfima", "fraccional", "persistencia"],
    nivel="avanzado",
)
def memoria_larga(sid, freq, transf):
    from scipy import stats

    s, et = serie(sid, freq, transf, minimo=64)
    v = s.values - s.values.mean()
    n = len(v)
    # Hurst por rango reescalado
    tams = np.unique(np.floor(np.logspace(np.log10(8), np.log10(n // 2), 12)).astype(int))
    rs = []
    for m in tams:
        vals = []
        for i in range(0, n - m + 1, m):
            x = v[i : i + m]
            z = np.cumsum(x - x.mean())
            sd = x.std()
            if sd > 0:
                vals.append((z.max() - z.min()) / sd)
        rs.append(np.mean(vals))
    H, _ = np.polyfit(np.log(tams), np.log(rs), 1)
    # GPH
    fr = 2 * np.pi * np.arange(1, n // 2) / n
    perio = np.abs(np.fft.fft(v)[1 : n // 2]) ** 2 / (2 * np.pi * n)
    m = int(n**0.5)
    xr = np.log(4 * np.sin(fr[:m] / 2) ** 2)
    reg = stats.linregress(xr, np.log(perio[:m]))
    d = -reg.slope
    se = np.pi / np.sqrt(24 * m)
    r = Resultado()
    r.metrica("Hurst H", H, "0,5 = sin memoria; >0,5 = persistente; <0,5 = antipersistente")
    r.metrica("d (GPH)", d, "0 = I(0); 0<d<0,5 = memoria larga estacionaria; ≥0,5 = no estacionaria")
    r.metrica("EE de d", se)
    r.dispersion("log R/S vs log tamaño", np.log(tams), np.log(rs), "log tamaño", "log R/S", recta=(H, _))
    if d - 1.96 * se > 0:
        txt = f"Memoria larga: d={fmt(d)} (IC 95 % excluye 0). Los shocks se disipan muy lento: considerá ARFIMA."
        sem = "amarillo"
    else:
        txt = f"Sin evidencia de memoria larga (d={fmt(d)}, H={fmt(H)})."
        sem = "verde"
    r.veredicto(txt, sem)
    r.resumen = txt
    return r


@metodo(
    "heterocedasticidad",
    "Heterocedasticidad (Breusch-Pagan, White, ARCH-LM)",
    F,
    "¿La varianza de los errores cambia con las X o en el tiempo?",
    params=[
        P_SERIE("dep", "Dependiente (Y)"),
        P_SERIES("indeps", "Explicativas (X)", minimo=1, maximo=6),
        P_FREQ,
        Param("transf", "opcion", "Transformación", defecto="dif_log", opciones=list(P_TRANSF.opciones)),
    ],
    cuando="Después de una regresión: si hay heterocedasticidad, usá errores robustos (HAC) o modelá la varianza.",
    referencias=["Breusch y Pagan (1979)", "White (1980)", "Engle (1982)"],
    etiquetas=["heterocedasticidad", "white", "breusch-pagan", "arch", "errores robustos"],
    nivel="basico",
)
def heterocedasticidad(dep, indeps, freq, transf):
    import statsmodels.api as sm
    from statsmodels.stats.diagnostic import het_arch, het_breuschpagan, het_white

    df, et = panel([dep, *indeps], freq, transf, minimo=25)
    X = sm.add_constant(df[indeps])
    res = sm.OLS(df[dep], X).fit()
    bp = het_breuschpagan(res.resid, X)
    try:
        wh = het_white(res.resid, X)
    except Exception:
        wh = (np.nan, np.nan)
    ar = het_arch(res.resid, nlags=min(12, len(df) // 5))
    r = Resultado()
    r.tabla(
        "H0: homocedasticidad",
        ["test", "LM", "p"],
        [["Breusch-Pagan", bp[0], bp[1]], ["White", wh[0], wh[1]], ["ARCH-LM", ar[0], ar[1]]],
        resaltar_p="p",
    )
    r.lineas("Residuos²", df.index, {"residuo²": res.resid.values**2})
    malos = [n for n, p in (("BP", bp[1]), ("White", wh[1]), ("ARCH", ar[1])) if p == p and p < 0.05]
    r.veredicto(
        (
            "Heterocedasticidad ("
            + ", ".join(malos)
            + "): usá errores HAC/robustos; si es ARCH, modelá la varianza."
        )
        if malos
        else "No se rechaza homocedasticidad.",
        "amarillo" if malos else "verde",
    )
    r.resumen = f"Heterocedasticidad en {et[dep]} ~ {', '.join(et[i] for i in indeps)}: BP p={fmt(bp[1])}, White p={fmt(wh[1])}, ARCH p={fmt(ar[1])}."
    return r
