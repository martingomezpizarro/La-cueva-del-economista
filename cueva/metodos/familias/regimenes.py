"""No linealidad y regímenes: cambio de régimen de Markov, umbrales (SETAR) y transición suave."""

from __future__ import annotations

import numpy as np

from cueva.metodos.contrato import ErrorMetodo, Param, Resultado
from cueva.metodos.insumos import P_DESDE, P_FREQ, P_HASTA, P_SERIE, P_TRANSF, eventos_en, fmt, serie
from cueva.metodos.registro import metodo

F = "regimenes"
P_TR = Param("transf", "opcion", "Transformación", defecto="dif_log", opciones=list(P_TRANSF.opciones))


@metodo(
    "markov_switching",
    "Cambio de régimen de Markov (Hamilton)",
    F,
    "¿La economía alterna entre estados (expansión/recesión, inflación alta/baja) y en cuál está hoy?",
    params=[
        P_SERIE(),
        P_FREQ,
        P_TR,
        Param("regimenes", "entero", "Regímenes", defecto=2, minimo=2, maximo=3),
        Param("rezagos_ar", "entero", "Rezagos AR (0 = sólo media)", defecto=0, minimo=0, maximo=4),
        Param("varianza_cambia", "bool", "La varianza también cambia", defecto=True),
        P_DESDE,
        P_HASTA,
    ],
    cuando="Ciclos con fases asimétricas, regímenes de inflación o de volatilidad cambiaria.",
    supuestos=["Los regímenes siguen una cadena de Markov con probabilidades de transición constantes."],
    trampas=[
        "La verosimilitud tiene muchos máximos locales: el resultado puede depender del arranque.",
        "Con 3 regímenes y pocos datos, uno suele quedar con 2-3 observaciones (un outlier, no un régimen).",
    ],
    costo="segundos",
    referencias=["Hamilton (1989)", "Kim y Nelson (1999)"],
    etiquetas=["markov", "hamilton", "regímenes", "recesión", "probabilidad suavizada"],
)
def markov_switching(sid, freq, transf, regimenes, rezagos_ar, varianza_cambia, desde, hasta):
    import statsmodels.api as sm

    s, et = serie(sid, freq, transf, desde, hasta, minimo=50)
    y = s.values
    sd = y.std() or 1
    z = (y - y.mean()) / sd
    mejor = None
    for intento in range(4):
        try:
            if rezagos_ar:
                mod = sm.tsa.MarkovAutoregression(
                    z, k_regimes=regimenes, order=rezagos_ar, switching_variance=varianza_cambia
                )
            else:
                mod = sm.tsa.MarkovRegression(z, k_regimes=regimenes, switching_variance=varianza_cambia)
            res = mod.fit(search_reps=10 if intento else 0, disp=False)
            if mejor is None or res.llf > mejor.llf:
                mejor = res
        except Exception:
            continue
    if mejor is None:
        raise ErrorMetodo("El modelo de Markov no convergió.")
    res = mejor
    nombres = res.model.param_names
    k = regimenes
    medias = [res.params[nombres.index(f"const[{i}]")] * sd + y.mean() for i in range(k)]
    orden = np.argsort(medias)
    etiq = ["bajo", "alto"] if k == 2 else ["bajo", "medio", "alto"]
    P = res.regime_transition[:, :, 0] if res.regime_transition.ndim == 3 else res.regime_transition
    prob = res.smoothed_marginal_probabilities
    prob = np.asarray(prob)
    idx = s.index[len(s) - prob.shape[0] :]
    r = Resultado()
    filas = []
    for pos, i in enumerate(orden):
        p_ii = P[i, i]
        var = (
            res.params[nombres.index(f"sigma2[{i}]")] * sd**2
            if varianza_cambia
            else res.params[nombres.index("sigma2")] * sd**2
        )
        filas.append(
            [
                etiq[pos],
                medias[i],
                np.sqrt(var),
                p_ii,
                1 / (1 - p_ii) if p_ii < 1 else None,
                float((prob[:, i] > 0.5).mean() * 100),
            ]
        )
    r.tabla(
        "Regímenes", ["régimen", "media", "desvío", "P(quedarse)", "duración esperada", "% del tiempo"], filas
    )
    alto = orden[-1]
    r.lineas(f"{et}", idx, {et: y[-len(idx) :]})
    r.lineas(
        f"Probabilidad suavizada del régimen «{etiq[-1]}»", idx, {f"P(régimen {etiq[-1]})": prob[:, alto]}
    )
    r.serie(
        f"{sid}_prob_reg_alto"[:40], idx, prob[:, alto], f"Probabilidad del régimen alto de {et} (Markov)"
    )
    # episodios del régimen alto, cruzados con eventos
    en = prob[:, alto] > 0.5
    episodios, i = [], 0
    while i < len(en):
        if en[i]:
            j = i
            while j + 1 < len(en) and en[j + 1]:
                j += 1
            evs = eventos_en(idx[i], idx[j])
            episodios.append(
                [
                    str(idx[i].date()),
                    str(idx[j].date()),
                    j - i + 1,
                    "; ".join(e["titulo"] for e in evs[:3]) or "—",
                ]
            )
            i = j + 1
        else:
            i += 1
    if episodios:
        r.tabla(
            f"Episodios del régimen «{etiq[-1]}» y eventos de la Línea de Tiempo",
            ["desde", "hasta", "obs.", "eventos en el período"],
            episodios[:25],
        )
    hoy = prob[-1, alto]
    r.metrica(f"P(régimen {etiq[-1]}) hoy", hoy)
    r.metrica("Log-verosimilitud", res.llf)
    r.metrica("AIC", res.aic)
    r.veredicto(
        f"Último dato: probabilidad {fmt(hoy * 100, 2)} % de estar en el régimen «{etiq[-1]}» (media {fmt(medias[alto])}).",
        "amarillo" if hoy > 0.5 else "verde",
    )
    r.resumen = (
        f"Markov con {k} regímenes sobre {et}: medias "
        + ", ".join(f"{f[0]} {fmt(f[1])} (dura ≈{fmt(f[4], 2)})" for f in filas)
        + f". P(alto) hoy = {fmt(hoy)}; {len(episodios)} episodios."
    )
    r.codigo = f"import statsmodels.api as sm\nres = sm.tsa.MarkovRegression(y, k_regimes={k}, switching_variance={varianza_cambia}).fit(search_reps=10)\nres.smoothed_marginal_probabilities"
    return r


def _ar_matriz(y, p):
    n = len(y)
    X = np.column_stack([np.ones(n - p)] + [y[p - j : n - j] for j in range(1, p + 1)])
    return X, y[p:]


@metodo(
    "umbral_setar",
    "Autorregresivo con umbral (SETAR) y prueba de Hansen",
    F,
    "¿La dinámica cambia cuando la variable cruza un umbral (ej. inflación por encima de cierto nivel)?",
    params=[
        P_SERIE(),
        P_FREQ,
        P_TR,
        Param("p", "entero", "Rezagos AR", defecto=2, minimo=1, maximo=8),
        Param("d", "entero", "Rezago del umbral (d)", defecto=1, minimo=1, maximo=6),
        Param("bootstrap", "entero", "Réplicas bootstrap", defecto=199, minimo=49, maximo=999),
    ],
    cuando="Persistencia asimétrica: la inflación alta se autoalimenta más que la baja; el tipo de cambio sólo corrige pasada cierta brecha.",
    supuestos=[
        "Dos regímenes con corte abrupto en y_{t−d} = umbral.",
        "El umbral no está identificado bajo H0: por eso el p-valor es por bootstrap (Hansen 1996).",
    ],
    trampas=["Cada régimen necesita observaciones suficientes (se recorta 15 % en cada cola)."],
    costo="segundos",
    referencias=["Tong (1990)", "Hansen (1996, 1997)"],
    etiquetas=["setar", "tar", "umbral", "threshold", "no lineal", "asimetría"],
    nivel="avanzado",
)
def umbral_setar(sid, freq, transf, p, d, bootstrap):
    s, et = serie(sid, freq, transf, minimo=60)
    y = s.values
    m = max(p, d)
    X, Y = _ar_matriz(y, m)
    X = X[:, : p + 1]
    q = y[m - d : len(y) - d]
    n = len(Y)
    cand = np.sort(q)[int(0.15 * n) : int(0.85 * n)]
    cand = np.unique(cand)
    if len(cand) > 150:
        cand = cand[np.linspace(0, len(cand) - 1, 150).astype(int)]

    def ssr_umbral(Yv):
        mejor = (np.inf, None)
        for c in cand:
            ab = q <= c
            Xt = np.column_stack([X * ab[:, None], X * (~ab)[:, None]])
            b, *_ = np.linalg.lstsq(Xt, Yv, rcond=None)
            e = Yv - Xt @ b
            sse = e @ e
            if sse < mejor[0]:
                mejor = (sse, c)
        return mejor

    b0, *_ = np.linalg.lstsq(X, Y, rcond=None)
    e0 = Y - X @ b0
    s0 = e0 @ e0
    s1, umbral = ssr_umbral(Y)
    Fst = n * (s0 - s1) / s1
    rng = np.random.default_rng(0)
    cuenta = 0
    for _ in range(bootstrap):
        Yb = rng.normal(size=n) * e0  # bootstrap de regresores fijos (Hansen 1996), heterocedástico
        bb, *_ = np.linalg.lstsq(X, Yb, rcond=None)
        eb = Yb - X @ bb
        sb1, _ = ssr_umbral(Yb)
        if n * (eb @ eb - sb1) / sb1 >= Fst:
            cuenta += 1
    pval = (cuenta + 1) / (bootstrap + 1)
    ab = q <= umbral
    r = Resultado()
    filas = []
    for nombre_r, mask in (("bajo el umbral", ab), ("sobre el umbral", ~ab)):
        b, *_ = np.linalg.lstsq(X[mask], Y[mask], rcond=None)
        persist = b[1:].sum()
        filas.append([nombre_r, int(mask.sum()), b[0], *b[1:], persist])
    r.tabla(
        f"Regímenes (umbral en y(t−{d}) = {fmt(umbral)})",
        ["régimen", "obs.", "constante", *[f"φ{j}" for j in range(1, p + 1)], "persistencia Σφ"],
        filas,
    )
    r.metrica("Umbral", umbral)
    r.metrica("F sup (Hansen)", Fst)
    r.metrica("p bootstrap", pval, "H0: lineal (sin umbral)")
    r.lineas(
        f"{et} y el umbral",
        s.index,
        {et: y, "umbral": np.full(len(y), umbral)},
        estilos={"umbral": {"guion": "dash"}},
    )
    hay = pval < 0.05
    r.veredicto(
        f"{'Hay' if hay else 'No hay'} evidencia de no linealidad por umbral (p={fmt(pval)}). Persistencia: {fmt(filas[0][-1])} bajo vs {fmt(filas[1][-1])} sobre el umbral.",
        "amarillo" if hay else "verde",
    )
    r.resumen = f"SETAR(2; {p}, {p}) con d={d} sobre {et}: umbral {fmt(umbral)}, F={fmt(Fst)}, p bootstrap={fmt(pval)}."
    return r


@metodo(
    "transicion_suave",
    "Autorregresivo de transición suave (LSTAR)",
    F,
    "Como el umbral, pero el cambio de régimen es gradual: ¿qué tan rápido se pasa de un régimen al otro?",
    params=[
        P_SERIE(),
        P_FREQ,
        P_TR,
        Param("p", "entero", "Rezagos AR", defecto=2, minimo=1, maximo=6),
        Param("d", "entero", "Rezago de la variable de transición", defecto=1, minimo=1, maximo=6),
    ],
    cuando="Ajustes que se aceleran con el tamaño del desvío (tipo de cambio real, brechas).",
    supuestos=["Función de transición logística G = 1/(1+exp(−γ(s−c)/σ_s))."],
    trampas=["γ muy grande ⇒ equivale a un SETAR; γ ≈ 0 ⇒ el modelo es lineal y c no está identificado."],
    costo="segundos",
    referencias=["Teräsvirta (1994)", "van Dijk, Teräsvirta y Franses (2002)"],
    etiquetas=["lstar", "star", "transición suave", "no lineal", "logística"],
    nivel="avanzado",
)
def transicion_suave(sid, freq, transf, p, d):
    from scipy.optimize import least_squares

    s, et = serie(sid, freq, transf, minimo=60)
    y = s.values
    m = max(p, d)
    X, Y = _ar_matriz(y, m)
    X = X[:, : p + 1]
    tr = y[m - d : len(y) - d]
    sd = tr.std() or 1

    def G(g, c):
        return 1 / (1 + np.exp(-np.clip(g * (tr - c) / sd, -50, 50)))

    def coef(g, c):
        gg = G(g, c)
        Xt = np.column_stack([X, X * gg[:, None]])
        b, *_ = np.linalg.lstsq(Xt, Y, rcond=None)
        return b, Y - Xt @ b

    mejor = (np.inf, None)
    for g in (0.5, 1, 2, 5, 10, 25):
        for c in np.quantile(tr, np.linspace(0.15, 0.85, 15)):
            _, e = coef(g, c)
            if e @ e < mejor[0]:
                mejor = (e @ e, (g, c))
    res = least_squares(lambda th: coef(np.exp(th[0]), th[1])[1], x0=[np.log(mejor[1][0]), mejor[1][1]])
    g, c = float(np.exp(res.x[0])), float(res.x[1])
    b, e = coef(g, c)
    b0, *_ = np.linalg.lstsq(X, Y, rcond=None)
    e0 = Y - X @ b0
    # test de linealidad de Luukkonen-Saikkonen-Teräsvirta (LM3)
    from scipy import stats

    Z = np.column_stack([X, X[:, 1:] * tr[:, None], X[:, 1:] * (tr**2)[:, None], X[:, 1:] * (tr**3)[:, None]])
    bz, *_ = np.linalg.lstsq(Z, Y, rcond=None)
    ez = Y - Z @ bz
    q = Z.shape[1] - X.shape[1]
    Flm = ((e0 @ e0 - ez @ ez) / q) / (ez @ ez / (len(Y) - Z.shape[1]))
    plm = float(stats.f.sf(Flm, q, len(Y) - Z.shape[1]))
    r = Resultado()
    r.metrica("γ (velocidad de transición)", g)
    r.metrica("c (centro)", c)
    r.metrica("Test de linealidad LM3 (p)", plm)
    r.metrica("Mejora de SSR vs AR lineal %", (1 - (e @ e) / (e0 @ e0)) * 100)
    k = p + 1
    r.tabla(
        "Coeficientes",
        ["", "régimen G=0", "régimen G=1 (= suma)"],
        [[f"φ{j}" if j else "constante", b[j], b[j] + b[k + j]] for j in range(k)],
    )
    orden = np.argsort(tr)
    r.dispersion("Función de transición estimada", tr[orden], G(g, c)[orden], f"{et} (t−{d})", "G")
    r.veredicto(
        f"Linealidad {'rechazada' if plm < 0.05 else 'no rechazada'} (LM3 p={fmt(plm)}).",
        "amarillo" if plm < 0.05 else "verde",
    )
    r.resumen = f"LSTAR({p}) sobre {et}: γ={fmt(g)}, c={fmt(c)}; test de linealidad p={fmt(plm)}."
    return r
