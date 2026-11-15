"""Finanzas cuantitativas y activos: rendimiento y riesgo, Monte Carlo, carteras, backtests de
reglas (cruce de medias, momentum por régimen, pares), regímenes de volatilidad,
estacionalidad de calendario/intradía y neutralidad a factores.

Reglas de la familia:
- Se trabaja con rendimientos logarítmicos de PRECIOS (o niveles de índices).
- Todo backtest descuenta costos de transacción y separa la elección de parámetros (primera
  mitad) de la evaluación (segunda mitad): optimizar y medir sobre los mismos datos es la
  forma más común de fabricar estrategias que no existen (Bailey et al. 2014).
- Las posiciones usan la señal de t para operar en t+1 (sin mirar el cierre que se opera).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from cueva.metodos.contrato import ErrorMetodo, Param, Resultado
from cueva.metodos.insumos import P_SERIE, P_SERIES, fmt
from cueva.metodos.registro import metodo

F = "finanzas"
FREQS = ["diaria", "semanal", "mensual", "trimestral", "nativa"]
ANUAL = {"diaria": 252, "semanal": 52, "mensual": 12, "trimestral": 4, "anual": 1, "nativa": 252}
P_FREQ_F = Param(
    "freq",
    "opcion",
    "Frecuencia",
    defecto="diaria",
    opciones=FREQS,
    ayuda="nativa = como viene el archivo (sirve para datos intradía)",
)
P_COSTO = Param(
    "costo_pb", "real", "Costo por operación (puntos básicos)", defecto=10.0, minimo=0, maximo=500
)


# ── insumos de la familia ────────────────────────────────────────────────
def precios(sids: list[str], freq: str, minimo: int = 30) -> pd.DataFrame:
    from cueva.datos import series as S

    cols = {}
    for s in sids:
        try:
            if freq == "nativa":
                x = S.cargar(s, None)
            elif freq == "semanal":
                x = S.cargar(s, "diaria").resample("W-FRI").last().dropna()
            else:
                x = S.cargar(s, freq)
        except KeyError as e:
            raise ErrorMetodo(f"No existe la serie «{s}».") from e
        cols[s] = x.astype(float)
    df = pd.concat(cols, axis=1).dropna()
    if (df <= 0).any().any():
        raise ErrorMetodo("Hay precios ≤ 0: esta familia trabaja con precios o índices positivos.")
    if len(df) < minimo:
        raise ErrorMetodo(f"Las series comparten {len(df)} fechas; hacen falta al menos {minimo}.")
    return df


def rendimientos(df: pd.DataFrame) -> pd.DataFrame:
    return np.log(df).diff().dropna()


def estadisticas(r: pd.Series | np.ndarray, k: int) -> dict:
    r = pd.Series(np.asarray(r, float)).dropna()
    if not len(r):
        return {}
    eq = np.exp(r.cumsum())
    dd = eq / eq.cummax() - 1
    anios = len(r) / k
    cagr = float(eq.iloc[-1] ** (1 / anios) - 1) if anios > 0 else np.nan
    vol = float(r.std() * np.sqrt(k))
    neg = r[r < 0]
    sharpe = float(r.mean() / r.std() * np.sqrt(k)) if r.std() > 0 else np.nan
    sortino = float(r.mean() / neg.std() * np.sqrt(k)) if len(neg) > 1 and neg.std() > 0 else np.nan
    mdd = float(dd.min())
    return {
        "Rend. anual (CAGR) %": cagr * 100,
        "Volatilidad anual %": vol * 100,
        "Sharpe": sharpe,
        "Sortino": sortino,
        "Caída máxima %": mdd * 100,
        "Calmar": cagr / abs(mdd) if mdd < 0 else np.nan,
        "% períodos positivos": float((r > 0).mean() * 100),
        "Asimetría": float(r.skew()),
        "Curtosis exc.": float(r.kurt()),
    }


def _tabla_stats(res: Resultado, titulo: str, columnas: dict[str, dict]):
    claves = list(next(iter(columnas.values())).keys())
    res.tabla(
        titulo, ["métrica", *columnas.keys()], [[c, *[columnas[n].get(c) for n in columnas]] for c in claves]
    )


def _sharpe(r, k):
    r = np.asarray(r, float)
    return float(r.mean() / r.std() * np.sqrt(k)) if r.std() > 0 else np.nan


# ──────────────────────────────────────────────────────────────────────────
@metodo(
    "metricas_rendimiento",
    "Rendimiento, riesgo y caídas de uno o varios activos",
    F,
    "¿Cuánto rindió, con cuánto riesgo, y cuáles fueron sus peores caídas?",
    clase="diagnosticar",
    params=[P_SERIES("sids", "Precios / índices", minimo=1, maximo=10), P_FREQ_F],
    cuando="La ficha básica de cualquier activo o estrategia antes de compararlos.",
    trampas=["El Sharpe supone rendimientos normales: con colas pesadas, mirá Sortino y la caída máxima."],
    referencias=["Bacon (2008), Practical Portfolio Performance Measurement"],
    etiquetas=["sharpe", "sortino", "drawdown", "caída máxima", "volatilidad", "cagr", "performance"],
    nivel="basico",
)
def metricas_rendimiento(sids, freq):
    df = precios(sids, freq)
    ret = rendimientos(df)
    k = ANUAL[freq]
    r = Resultado()
    _tabla_stats(r, "Estadísticas (anualizadas)", {s: estadisticas(ret[s], k) for s in sids})
    eq = np.exp(ret.cumsum())
    r.lineas("Valor de $1 invertido", eq.index, {s: eq[s].values for s in sids})
    dd = eq / eq.cummax() - 1
    r.lineas("Caída desde el máximo (underwater)", dd.index, {s: dd[s].values * 100 for s in sids}, eje_y="%")
    s0 = sids[0]
    d0 = dd[s0]
    filas, usados = [], set()
    for f in d0.sort_values().index:
        if len(filas) >= 5:
            break
        pico = eq[s0].loc[:f].idxmax()
        if pico in usados:
            continue
        usados.add(pico)
        post = eq[s0].loc[f:]
        rec = post[post >= eq[s0].loc[pico]]
        filas.append(
            [
                str(pico.date()),
                str(f.date()),
                float(d0.loc[f] * 100),
                str(rec.index[0].date()) if len(rec) else "sin recuperar",
            ]
        )
    r.tabla(f"Peores caídas de {s0}", ["pico", "valle", "caída %", "recuperación"], filas)
    st = estadisticas(ret[s0], k)
    r.resumen = f"{s0}: CAGR {fmt(st['Rend. anual (CAGR) %'], 3)} %, volatilidad {fmt(st['Volatilidad anual %'], 3)} %, Sharpe {fmt(st['Sharpe'])}, caída máxima {fmt(st['Caída máxima %'], 3)} %."
    return r


@metodo(
    "montecarlo_cartera",
    "Riesgo de cartera por Monte Carlo",
    F,
    "¿Qué distribución de resultados puede tener la cartera en el horizonte, y cuánto se puede perder?",
    clase="simular",
    params=[
        P_SERIES("sids", "Activos (precios)", minimo=1, maximo=20),
        Param("pesos", "texto", "Pesos", ayuda="Ej. 0.5,0.3,0.2 (vacío = iguales)"),
        P_FREQ_F,
        Param("horizonte", "entero", "Horizonte (períodos)", defecto=21, minimo=1, maximo=756),
        Param("simulaciones", "entero", "Simulaciones", defecto=5000, minimo=500, maximo=50000),
        Param(
            "metodo",
            "opcion",
            "Generador",
            defecto="bootstrap_bloques",
            opciones=["normal", "t_student", "bootstrap_bloques"],
            ayuda="El bootstrap por bloques conserva colas pesadas, correlaciones y agrupamiento de volatilidad",
        ),
        Param("nivel", "real", "Nivel del VaR", defecto=0.95, minimo=0.8, maximo=0.999),
    ],
    cuando="Riesgo de una cartera concreta: VaR, CVaR, probabilidad de perder más que X.",
    supuestos=["El futuro se parece a la historia usada (en distribución y correlaciones)."],
    trampas=[
        "La normal subestima las colas.",
        "Con pocos años de historia, el bootstrap no contiene crisis que nunca vio.",
    ],
    referencias=["Glasserman (2003)", "Jorion (2006)", "Politis y Romano (1994)"],
    etiquetas=["monte carlo", "simulación", "var", "cvar", "cartera", "riesgo", "bootstrap", "escenarios"],
    costo="segundos",
)
def montecarlo_cartera(sids, pesos, freq, horizonte, simulaciones, metodo, nivel):
    from scipy import stats

    df = precios(sids, freq, minimo=60)
    R = rendimientos(df).values
    n, k = R.shape
    w = np.array([float(x) for x in pesos.split(",")]) if pesos else np.full(k, 1 / k)
    if len(w) != k:
        raise ErrorMetodo(f"Hay {k} activos y {len(w)} pesos.")
    w = w / w.sum()
    rng = np.random.default_rng(0)
    H, S = horizonte, simulaciones
    mu, cov = R.mean(0), np.cov(R.T).reshape(k, k)
    if metodo == "normal":
        sims = rng.multivariate_normal(mu, cov, size=(S, H))
    elif metodo == "t_student":
        nu = 5
        z = rng.multivariate_normal(np.zeros(k), cov * (nu - 2) / nu, size=(S, H))
        g = rng.chisquare(nu, size=(S, H, 1)) / nu
        sims = mu + z / np.sqrt(g)
    else:
        L = max(5, int(round(n ** (1 / 3))))
        nb = int(np.ceil(H / L))
        ini = rng.integers(0, n - L, size=(S, nb))
        idx = (ini[:, :, None] + np.arange(L)[None, None, :]).reshape(S, -1)[:, :H]
        sims = R[idx]
    # rendimiento simple de la cartera con rebalanceo en cada período
    port = np.log((np.exp(sims) * w).sum(axis=2))
    acum = port.cumsum(axis=1)
    final = np.exp(acum[:, -1]) - 1
    a = 1 - nivel
    var = float(np.quantile(final, a))
    cvar = float(final[final <= var].mean())
    r = Resultado()
    r.metrica(f"VaR {nivel:.0%} a {H} períodos %", var * 100)
    r.metrica("CVaR (pérdida esperada en la cola) %", cvar * 100)
    r.metrica("Rendimiento mediano %", float(np.median(final) * 100))
    r.metrica("P(pérdida) %", float((final < 0).mean() * 100))
    r.metrica("P(pérdida > 10 %) %", float((final < -0.10).mean() * 100))
    pcts = np.percentile(np.exp(acum), [5, 25, 50, 75, 95], axis=0)
    r.lineas(
        f"Abanico de valor de $1 ({S} simulaciones, {metodo})",
        list(range(1, H + 1)),
        {"p5": pcts[0], "p25": pcts[1], "mediana": pcts[2], "p75": pcts[3], "p95": pcts[4]},
        estilos={"p5": {"guion": "dot"}, "p95": {"guion": "dot"}},
    )
    cnt, bordes = np.histogram(final * 100, bins=60)
    r.barras(
        f"Distribución del rendimiento a {H} períodos (%)",
        [fmt((x + y) / 2, 3) for x, y in zip(bordes[:-1], bordes[1:], strict=True)],
        {"simulaciones": cnt},
    )
    r.tabla(
        "Cartera",
        ["activo", "peso", "vol. anual %", "contribución al riesgo %"],
        [
            [
                s,
                w[i],
                float(np.sqrt(cov[i, i] * ANUAL[freq]) * 100),
                float(w[i] * (cov @ w)[i] / (w @ cov @ w) * 100),
            ]
            for i, s in enumerate(sids)
        ],
    )
    hist_var = float(np.quantile(R @ w, a))
    r.metrica("VaR histórico a 1 período %", hist_var * 100)
    r.metrica("Curtosis de la cartera", float(stats.kurtosis(R @ w)))
    r.resumen = f"Monte Carlo ({metodo}, {S} sims) de {len(sids)} activos a {H} períodos: VaR {nivel:.0%} {fmt(var * 100, 3)} %, CVaR {fmt(cvar * 100, 3)} %, P(pérdida) {fmt(float((final < 0).mean() * 100), 3)} %."
    return r


@metodo(
    "montecarlo_umbral",
    "Probabilidad de cruzar un nivel (Monte Carlo de trayectorias)",
    F,
    "¿Qué probabilidad hay de que el precio (o el riesgo país, o el dólar) toque un nivel antes de cierta fecha?",
    clase="simular",
    params=[
        P_SERIE("sid", "Serie (positiva)"),
        P_FREQ_F,
        Param("nivel_objetivo", "real", "Nivel a cruzar", requerido=True),
        Param("horizonte", "entero", "Horizonte (períodos)", defecto=63, minimo=1, maximo=1000),
        Param("simulaciones", "entero", "Simulaciones", defecto=10000, minimo=500, maximo=100000),
        Param(
            "metodo",
            "opcion",
            "Generador",
            defecto="bootstrap_bloques",
            opciones=["gbm", "bootstrap_bloques", "garch"],
        ),
        Param("ventana", "entero", "Historia usada (períodos, 0 = toda)", defecto=0, minimo=0, maximo=10000),
    ],
    cuando="Mercados de predicción (Kalshi, Polymarket), coberturas con opciones, alertas de riesgo.",
    supuestos=[
        "Los rendimientos futuros se parecen a los de la ventana (GBM: lognormales i.i.d.; GARCH: volatilidad que se agrupa)."
    ],
    trampas=[
        "La probabilidad de TOCAR un nivel es mucho mayor que la de TERMINAR por encima: se reportan las dos.",
        "No incorpora información nueva (anuncios, elecciones): combinalo con el juicio.",
    ],
    deps=["arch"],
    costo="segundos",
    referencias=["Hull (2018), cap. 21", "Glasserman (2003)"],
    etiquetas=[
        "monte carlo",
        "probabilidad",
        "barrera",
        "kalshi",
        "polymarket",
        "mercado de predicción",
        "gbm",
        "umbral",
    ],
)
def montecarlo_umbral(sid, freq, nivel_objetivo, horizonte, simulaciones, metodo, ventana):
    df = precios([sid], freq, minimo=60)
    p0 = float(df[sid].iloc[-1])
    R = rendimientos(df)[sid].values
    if ventana:
        R = R[-ventana:]
    rng = np.random.default_rng(1)
    H, S = horizonte, simulaciones
    if metodo == "gbm":
        sims = rng.normal(R.mean(), R.std(ddof=1), size=(S, H))
    elif metodo == "bootstrap_bloques":
        L = max(5, int(round(len(R) ** (1 / 3))))
        ini = rng.integers(0, len(R) - L, size=(S, int(np.ceil(H / L))))
        idx = (ini[:, :, None] + np.arange(L)).reshape(S, -1)[:, :H]
        sims = R[idx]
    else:
        from arch import arch_model

        res = arch_model(R * 100, mean="Constant", vol="GARCH", p=1, q=1, dist="t").fit(disp="off")
        f = res.forecast(horizon=H, method="simulation", simulations=min(S, 5000), reindex=False)
        sims = f.simulations.values[-1] / 100
        S = sims.shape[0]
    tray = p0 * np.exp(np.cumsum(sims, axis=1))
    arriba = nivel_objetivo >= p0
    toca = (tray.max(1) >= nivel_objetivo) if arriba else (tray.min(1) <= nivel_objetivo)
    termina = (tray[:, -1] >= nivel_objetivo) if arriba else (tray[:, -1] <= nivel_objetivo)
    p_toca, p_term = float(toca.mean()), float(termina.mean())
    ee = np.sqrt(p_toca * (1 - p_toca) / S)
    r = Resultado()
    r.metrica("Último valor", p0)
    r.metrica(f"P(toca {fmt(nivel_objetivo)} en {H} períodos) %", p_toca * 100)
    r.metrica("P(termina más allá del nivel) %", p_term * 100)
    r.metrica("Error de simulación (±1,96 EE) pp", ee * 196)
    if toca.any():
        cuando_ = (
            np.argmax((tray >= nivel_objetivo) if arriba else (tray <= nivel_objetivo), axis=1)[toca] + 1
        )
        r.metrica("Mediana de períodos hasta tocar", float(np.median(cuando_)))
    pc = np.percentile(tray, [5, 25, 50, 75, 95], axis=0)
    xs = list(range(1, H + 1))
    r.lineas(
        f"Trayectorias simuladas de {sid} ({metodo})",
        xs,
        {
            "p5": pc[0],
            "p25": pc[1],
            "mediana": pc[2],
            "p75": pc[3],
            "p95": pc[4],
            "nivel objetivo": np.full(H, nivel_objetivo),
        },
        estilos={"nivel objetivo": {"guion": "dash"}, "p5": {"guion": "dot"}, "p95": {"guion": "dot"}},
    )
    curva = [
        float(
            (
                (tray[:, :h].max(1) >= nivel_objetivo) if arriba else (tray[:, :h].min(1) <= nivel_objetivo)
            ).mean()
            * 100
        )
        for h in xs
    ]
    r.lineas("Probabilidad acumulada de tocar el nivel", xs, {"P(toca) %": curva})
    r.resumen = f"{sid} (último {fmt(p0)}): probabilidad de tocar {fmt(nivel_objetivo)} en {H} períodos = {fmt(p_toca * 100, 3)} % (de terminar más allá: {fmt(p_term * 100, 3)} %), método {metodo}."
    r.datos = {"p_toca": p_toca, "p_termina": p_term}
    return r


@metodo(
    "frontera_eficiente",
    "Carteras: Markowitz, mínima varianza, paridad de riesgo y HRP (con evaluación fuera de muestra)",
    F,
    "¿Cómo repartir entre activos, y qué regla de asignación funciona mejor FUERA de muestra?",
    clase="evaluar",
    params=[
        P_SERIES("sids", "Activos", minimo=2, maximo=30),
        Param("freq", "opcion", "Frecuencia", defecto="mensual", opciones=["diaria", "semanal", "mensual"]),
        Param("ventana", "entero", "Ventana de estimación (períodos)", defecto=60, minimo=20, maximo=2000),
        Param("rebalanceo", "entero", "Rebalancear cada (períodos)", defecto=1, minimo=1, maximo=252),
        Param("solo_largos", "bool", "Sólo posiciones largas", defecto=True),
    ],
    cuando="Asignación de activos: la frontera in-sample es optimista; la evaluación rodante muestra qué se sostiene.",
    supuestos=[
        "Covarianza encogida (Ledoit-Wolf) para que la optimización no amplifique errores de estimación."
    ],
    trampas=[
        "Máximo Sharpe in-sample es la cartera más sobreajustada que existe (DeMiguel et al. 2009: 1/N es difícil de batir)."
    ],
    deps=["sklearn"],
    costo="segundos",
    referencias=[
        "Markowitz (1952)",
        "DeMiguel, Garlappi y Uppal (2009)",
        "Ledoit y Wolf (2004)",
        "López de Prado (2016)",
    ],
    etiquetas=[
        "markowitz",
        "frontera eficiente",
        "mínima varianza",
        "paridad de riesgo",
        "hrp",
        "asignación",
        "1/n",
        "cartera",
    ],
)
def frontera_eficiente(sids, freq, ventana, rebalanceo, solo_largos):
    from scipy.optimize import minimize
    from sklearn.covariance import LedoitWolf

    df = precios(sids, freq, minimo=ventana + 20)
    R = rendimientos(df)
    k = len(sids)
    A = ANUAL[freq]

    def opt(mu, S, objetivo):
        b = [(0, 1)] * k if solo_largos else [(-1, 1)] * k
        cons = [{"type": "eq", "fun": lambda w: w.sum() - 1}]
        if objetivo == "minvar":
            f = lambda w: w @ S @ w  # noqa: E731
        elif objetivo == "sharpe":
            f = lambda w: -(w @ mu) / np.sqrt(w @ S @ w + 1e-12)  # noqa: E731
        else:  # paridad de riesgo
            f = lambda w: np.sum((w * (S @ w) / (w @ S @ w + 1e-12) - 1 / k) ** 2)  # noqa: E731
        res = minimize(
            f, np.full(k, 1 / k), method="SLSQP", bounds=b, constraints=cons, options={"maxiter": 300}
        )
        return res.x if res.success else np.full(k, 1 / k)

    def hrp(S):
        from scipy.cluster.hierarchy import leaves_list, linkage
        from scipy.spatial.distance import squareform

        sd = np.sqrt(np.diag(S))
        C = S / np.outer(sd, sd)
        D = np.sqrt(np.clip(0.5 * (1 - C), 0, None))
        np.fill_diagonal(D, 0)
        orden = list(leaves_list(linkage(squareform(D, checks=False), "single")))
        w = np.ones(k)
        grupos = [orden]
        while grupos:
            nuevo = []
            for g in grupos:
                if len(g) < 2:
                    continue
                a, b = g[: len(g) // 2], g[len(g) // 2 :]

                def vg(idx):
                    s = S[np.ix_(idx, idx)]
                    iv = 1 / np.diag(s)
                    iv /= iv.sum()
                    return iv @ s @ iv

                va, vb = vg(a), vg(b)
                al = 1 - va / (va + vb)
                w[a] *= al
                w[b] *= 1 - al
                nuevo += [a, b]
            grupos = nuevo
        return w / w.sum()

    reglas = ["1/N", "Mínima varianza", "Máximo Sharpe", "Paridad de riesgo", "HRP"]
    pesos_t = {n: np.full(k, 1 / k) for n in reglas}
    rets = {n: [] for n in reglas}
    fechas = []
    Rv = R.values
    for t in range(ventana, len(R)):
        if (t - ventana) % rebalanceo == 0:
            hist = Rv[t - ventana : t]
            S = LedoitWolf().fit(hist).covariance_
            mu = hist.mean(0)
            pesos_t = {
                "1/N": np.full(k, 1 / k),
                "Mínima varianza": opt(mu, S, "minvar"),
                "Máximo Sharpe": opt(mu, S, "sharpe"),
                "Paridad de riesgo": opt(mu, S, "rp"),
                "HRP": hrp(S),
            }
        for n in reglas:
            rets[n].append(float(np.log(np.exp(Rv[t]) @ pesos_t[n])))
        fechas.append(R.index[t])
    r = Resultado()
    st = {n: estadisticas(np.array(v), A) for n, v in rets.items()}
    _tabla_stats(r, f"Evaluación FUERA de muestra (ventana {ventana}, rebalanceo cada {rebalanceo})", st)
    eq = {n: np.exp(np.cumsum(v)) for n, v in rets.items()}
    r.lineas("Valor de $1 con cada regla (fuera de muestra)", fechas, eq)
    S_all = LedoitWolf().fit(Rv[-ventana:]).covariance_
    mu_all = Rv[-ventana:].mean(0)
    r.tabla(
        "Pesos actuales (con la última ventana)",
        ["activo", *reglas],
        [[s, *[pesos_t[n][i] for n in reglas]] for i, s in enumerate(sids)],
    )
    # frontera in-sample con carteras aleatorias
    rng = np.random.default_rng(0)
    W = rng.dirichlet(np.ones(k), size=3000)
    mus = W @ mu_all * A * 100
    vols = np.sqrt(np.einsum("ij,jk,ik->i", W, S_all, W) * A) * 100
    r.dispersion(
        "Carteras aleatorias (última ventana): volatilidad vs rendimiento esperado",
        vols,
        mus,
        "volatilidad anual %",
        "rendimiento esperado anual %",
    )
    mejor = max(st, key=lambda n: st[n]["Sharpe"] if st[n]["Sharpe"] == st[n]["Sharpe"] else -9)
    r.metrica("Mejor Sharpe fuera de muestra", mejor)
    r.veredicto(
        f"Fuera de muestra gana «{mejor}» (Sharpe {fmt(st[mejor]['Sharpe'])}) contra 1/N ({fmt(st['1/N']['Sharpe'])}).",
        "verde" if mejor != "Máximo Sharpe" else "amarillo",
    )
    r.resumen = (
        f"Asignación entre {k} activos, evaluada fuera de muestra: "
        + "; ".join(f"{n} Sharpe {fmt(st[n]['Sharpe'])}" for n in reglas)
        + "."
    )
    return r


@metodo(
    "cruce_medias",
    "Backtest de cruce de medias móviles (con robustez y fuera de muestra)",
    F,
    "¿Una regla de cruce de medias le gana a comprar y mantener después de costos, y sin sobreoptimizar?",
    clase="evaluar",
    params=[
        P_SERIE("sid", "Precio"),
        P_FREQ_F,
        Param("rapida", "entero", "Media rápida", defecto=20, minimo=2, maximo=250),
        Param("lenta", "entero", "Media lenta", defecto=100, minimo=5, maximo=500),
        Param(
            "modo",
            "opcion",
            "Posiciones",
            defecto="largo_o_afuera",
            opciones=["largo_o_afuera", "largo_corto"],
        ),
        P_COSTO,
    ],
    cuando="Evaluar seguimiento de tendencia en un activo; la grilla muestra si el resultado depende de los parámetros exactos.",
    supuestos=["Se opera al cierre siguiente a la señal; costos proporcionales al cambio de posición."],
    trampas=[
        "El mejor par (rápida, lenta) de la grilla está sobreajustado: se elige en la primera mitad y se evalúa en la segunda.",
        "Pocas operaciones ⇒ Sharpe muy ruidoso.",
    ],
    referencias=["Brock, Lakonishok y LeBaron (1992)", "Bailey, Borwein, López de Prado y Zhu (2014)"],
    etiquetas=["medias móviles", "cruce", "backtest", "trading", "tendencia", "estrategia", "sma"],
    costo="segundos",
)
def cruce_medias(sid, freq, rapida, lenta, modo, costo_pb):
    if rapida >= lenta:
        raise ErrorMetodo("La media rápida tiene que ser más corta que la lenta.")
    p = precios([sid], freq, minimo=lenta + 60)[sid]
    ret = np.log(p).diff()
    A = ANUAL[freq]
    c = costo_pb / 1e4

    def correr(f, s, desde=0, hasta=None):
        sig = (p.rolling(f).mean() > p.rolling(s).mean()).astype(float)
        if modo == "largo_corto":
            sig = sig * 2 - 1
        pos = sig.shift(1)  # señal de t, se opera en t+1
        neto = pos * ret - c * pos.diff().abs()
        neto = neto.iloc[s:]
        return neto.iloc[desde:hasta], pos.iloc[s:].iloc[desde:hasta]

    neto, pos = correr(rapida, lenta)
    bh = ret.loc[neto.index]
    r = Resultado()
    _tabla_stats(
        r,
        "Estrategia vs comprar y mantener (después de costos)",
        {"cruce de medias": estadisticas(neto, A), "comprar y mantener": estadisticas(bh, A)},
    )
    r.lineas(
        "Valor de $1",
        neto.index,
        {"cruce de medias": np.exp(neto.cumsum()).values, "comprar y mantener": np.exp(bh.cumsum()).values},
    )
    ops = int((pos.diff().abs() > 0).sum())
    r.metrica("Operaciones", ops)
    r.metrica("% del tiempo invertido", float((pos > 0).mean() * 100))
    # grilla de robustez
    rs = [x for x in (5, 10, 20, 30, 50) if x < max(lenta, 60)]
    ls = [x for x in (50, 100, 150, 200, 250) if x <= len(p) // 3]
    grilla = np.full((len(rs), len(ls)), np.nan)
    mitad = len(p) // 2
    mejor_is = (-np.inf, None)
    for i, f in enumerate(rs):
        for j, s in enumerate(ls):
            if f >= s:
                continue
            n_full, _ = correr(f, s)
            grilla[i, j] = _sharpe(n_full.fillna(0), A)
            n_is, _ = correr(f, s, 0, mitad - s)
            sh = _sharpe(n_is.fillna(0), A)
            if sh > mejor_is[0]:
                mejor_is = (sh, (f, s))
    r.mapa_calor(
        "Sharpe en toda la muestra según (rápida, lenta): ¿una isla o una meseta?",
        [f"rápida {f}" for f in rs],
        [f"lenta {s}" for s in ls],
        grilla,
        rango=None,
    )
    if mejor_is[1]:
        f, s = mejor_is[1]
        n_oos, _ = correr(f, s, mitad - s)
        bh_oos = ret.loc[n_oos.index]
        sh_oos, sh_bh = _sharpe(n_oos.fillna(0), A), _sharpe(bh_oos.fillna(0), A)
        r.metrica("Mejor par en la 1.ª mitad", f"{f}/{s}")
        r.metrica("Su Sharpe en la 1.ª mitad", mejor_is[0])
        r.metrica("Su Sharpe en la 2.ª mitad (fuera de muestra)", sh_oos)
        r.metrica("Comprar y mantener, 2.ª mitad", sh_bh)
        degr = mejor_is[0] - sh_oos
        if sh_oos > sh_bh:
            r.veredicto(
                f"Elegida en la 1.ª mitad, la regla {f}/{s} sigue ganándole a comprar y mantener fuera de muestra (Sharpe {fmt(sh_oos)} vs {fmt(sh_bh)}).",
                "verde",
            )
        else:
            r.veredicto(
                f"Fuera de muestra, la mejor regla de la 1.ª mitad ({f}/{s}) NO le gana a comprar y mantener (Sharpe {fmt(sh_oos)} vs {fmt(sh_bh)}; se degrada {fmt(degr)}).",
                "rojo",
            )
    st = estadisticas(neto, A)
    r.resumen = f"Cruce {rapida}/{lenta} en {sid} ({modo}, {costo_pb} pb): Sharpe {fmt(st['Sharpe'])} vs {fmt(estadisticas(bh, A)['Sharpe'])} de comprar y mantener; {ops} operaciones."
    return r


@metodo(
    "momentum_regimen",
    "Momentum dependiente del régimen",
    F,
    "¿El momentum (comprar lo que viene subiendo) funciona igual en calma que en turbulencia, en tendencia que en lateralidad?",
    clase="evaluar",
    params=[
        P_SERIES("sids", "Activos (1 = series de tiempo; varios = transversal)", minimo=1, maximo=50),
        P_FREQ_F,
        Param("formacion", "entero", "Período de formación", defecto=12, minimo=1, maximo=252),
        Param("salto", "entero", "Períodos que se saltean", defecto=1, minimo=0, maximo=21),
        Param(
            "regimen",
            "opcion",
            "Cómo se define el régimen",
            defecto="volatilidad",
            opciones=["volatilidad", "tendencia", "serie_externa"],
        ),
        Param("sid_regimen", "serie", "Serie externa para el régimen (opcional)"),
        Param("ventana_regimen", "entero", "Ventana del régimen", defecto=12, minimo=3, maximo=252),
        P_COSTO,
    ],
    cuando="Antes de aplicar momentum: los colapsos de momentum ocurren en rebotes después de crisis (Daniel y Moskowitz 2016).",
    supuestos=[
        "Régimen observable en t (sin mirar el futuro): volatilidad realizada vs su mediana, o precio vs su media."
    ],
    trampas=[
        "Con pocos activos el momentum transversal es muy ruidoso.",
        "Definir el régimen con información futura (ej. mediana de toda la muestra) es fuga leve: se usa la mediana expansiva.",
    ],
    referencias=[
        "Jegadeesh y Titman (1993)",
        "Moskowitz, Ooi y Pedersen (2012)",
        "Daniel y Moskowitz (2016)",
    ],
    etiquetas=["momentum", "régimen", "tendencia", "time series momentum", "cross-sectional", "volatilidad"],
    costo="segundos",
)
def momentum_regimen(sids, freq, formacion, salto, regimen, sid_regimen, ventana_regimen, costo_pb):
    p = precios(sids, freq, minimo=formacion + ventana_regimen + 40)
    ret = np.log(p).diff()
    A = ANUAL[freq]
    c = costo_pb / 1e4
    se = np.log(p).shift(salto) - np.log(p).shift(salto + formacion)
    if len(sids) == 1:
        pos = np.sign(se)
    else:
        rk = se.rank(axis=1, pct=True)
        pos = (rk > 0.7).astype(float) - (rk <= 0.3).astype(float)
        pos = pos.div(pos.abs().sum(axis=1).replace(0, np.nan), axis=0)
    pos = pos.shift(1)
    est = (pos * ret).sum(axis=1) - c * pos.diff().abs().sum(axis=1)
    est = est.dropna()
    mercado = ret.mean(axis=1)
    if regimen == "volatilidad":
        vol = mercado.rolling(ventana_regimen).std()
        alto = vol > vol.expanding(ventana_regimen * 2).median()
        nombres = ("volatilidad baja", "volatilidad alta")
    elif regimen == "tendencia":
        idx = np.exp(mercado.cumsum())
        alto = idx > idx.rolling(ventana_regimen).mean()
        nombres = ("mercado bajo su media", "mercado sobre su media")
    else:
        if not sid_regimen:
            raise ErrorMetodo("Elegí la serie externa que define el régimen.")
        from cueva.datos import series as S

        ext = S.cargar(sid_regimen, "diaria" if freq in ("diaria", "nativa", "semanal") else freq).reindex(
            p.index, method="ffill"
        )
        alto = ext > ext.expanding(ventana_regimen * 2).median()
        nombres = (f"{sid_regimen} bajo", f"{sid_regimen} alto")
    alto = alto.shift(1).reindex(est.index).fillna(False).astype(bool)
    r = Resultado()
    filas = []
    for nm, msk in ((nombres[0], ~alto), (nombres[1], alto)):
        x = est[msk]
        t = x.mean() / x.std() * np.sqrt(len(x)) if len(x) > 2 and x.std() > 0 else np.nan
        filas.append(
            [
                nm,
                int(msk.sum()),
                float(x.mean() * A * 100),
                _sharpe(x, A),
                float(t),
                float((x > 0).mean() * 100),
            ]
        )
    r.tabla(
        "Momentum según el régimen",
        ["régimen", "períodos", "rend. anual %", "Sharpe", "t", "% positivos"],
        filas,
    )
    _tabla_stats(r, "Momentum en toda la muestra", {"momentum": estadisticas(est, A)})
    r.lineas("Valor de $1 en momentum", est.index, {"momentum": np.exp(est.cumsum()).values})
    r.lineas("Régimen (1 = alto)", alto.index, {"régimen": alto.astype(int).values})
    dif = filas[1][3] - filas[0][3]
    r.metrica("Diferencia de Sharpe (alto − bajo)", dif)
    # diferencia de medias (Welch)
    from scipy import stats

    tt = stats.ttest_ind(est[alto], est[~alto], equal_var=False)
    r.metrica("p de la diferencia (Welch)", float(tt.pvalue))
    r.veredicto(
        f"El momentum rinde Sharpe {fmt(filas[0][3])} en «{nombres[0]}» y {fmt(filas[1][3])} en «{nombres[1]}» (p={fmt(float(tt.pvalue))}).",
        "verde" if tt.pvalue < 0.1 else "amarillo",
    )
    r.serie(
        "momentum_regimen",
        alto.index,
        alto.astype(int).values,
        f"Régimen ({regimen}) usado para condicionar el momentum",
    )
    r.resumen = f"Momentum ({formacion}-{salto}) en {len(sids)} activo(s) por régimen de {regimen}: Sharpe {fmt(filas[0][3])} ({nombres[0]}) vs {fmt(filas[1][3])} ({nombres[1]}); p={fmt(float(tt.pvalue))}."
    return r


@metodo(
    "pares_trading",
    "Trading de pares (cointegración + reversión a la media)",
    F,
    "¿Dos activos tienen un diferencial que revierte, y se puede operar ese diferencial fuera de muestra?",
    clase="evaluar",
    params=[
        P_SERIE("sid_a", "Activo A"),
        P_SERIE("sid_b", "Activo B"),
        P_FREQ_F,
        Param("formacion", "real", "Fracción de formación", defecto=0.5, minimo=0.2, maximo=0.8),
        Param("entrada", "real", "Entrada (|z|)", defecto=2.0, minimo=0.5, maximo=4),
        Param("salida", "real", "Salida (|z|)", defecto=0.5, minimo=0, maximo=2),
        Param("ventana_z", "entero", "Ventana del z-score", defecto=60, minimo=10, maximo=500),
        P_COSTO,
    ],
    cuando="Arbitraje estadístico: ADRs vs acciones locales, bonos de curva parecida, activos del mismo sector.",
    supuestos=[
        "La relación de cointegración estimada en la formación sigue valiendo en el período de operación."
    ],
    trampas=[
        "Buscar el mejor par entre cientos y testearlo con los mismos datos garantiza falsos positivos.",
        "Las relaciones de cointegración se rompen (cambios regulatorios, cepos): la vida media manda.",
    ],
    referencias=["Gatev, Goetzmann y Rouwenhorst (2006)", "Vidyamurthy (2004)", "Engle y Granger (1987)"],
    etiquetas=[
        "pares",
        "pairs trading",
        "arbitraje estadístico",
        "spread",
        "cointegración",
        "reversión a la media",
        "ornstein-uhlenbeck",
    ],
)
def pares_trading(sid_a, sid_b, freq, formacion, entrada, salida, ventana_z, costo_pb):
    import statsmodels.api as sm
    from statsmodels.tsa.stattools import coint

    p = precios([sid_a, sid_b], freq, minimo=ventana_z * 3)
    la, lb = np.log(p[sid_a]), np.log(p[sid_b])
    cut = int(len(p) * formacion)
    _, pv, _ = coint(la.iloc[:cut], lb.iloc[:cut])
    ols = sm.OLS(la.iloc[:cut], sm.add_constant(lb.iloc[:cut])).fit()
    beta = float(ols.params.iloc[1])
    spread = la - beta * lb
    ds = spread.diff().iloc[1:cut]
    lag = spread.shift(1).iloc[1:cut]
    phi = float(sm.OLS(ds, sm.add_constant(lag)).fit().params.iloc[1])
    vida = float(-np.log(2) / np.log(1 + phi)) if -1 < phi < 0 else np.inf
    z = (spread - spread.rolling(ventana_z).mean()) / spread.rolling(ventana_z).std()
    pos = np.zeros(len(z))
    for t in range(1, len(z)):
        prev = pos[t - 1]
        zt = z.iloc[t]
        if np.isnan(zt):
            pos[t] = 0
        elif prev == 0:
            pos[t] = -1 if zt > entrada else (1 if zt < -entrada else 0)
        elif abs(zt) < salida:
            pos[t] = 0
        else:
            pos[t] = prev
    pos = pd.Series(pos, index=z.index).shift(1).fillna(0)
    ra, rb = la.diff(), lb.diff()
    bruto = pos * (ra - beta * rb) / (1 + abs(beta))
    neto = bruto - (costo_pb / 1e4) * pos.diff().abs() * 2
    A = ANUAL[freq]
    oos = neto.iloc[cut:]
    ins = neto.iloc[ventana_z:cut]
    r = Resultado()
    r.metrica("Cointegración en formación (p)", pv)
    r.metrica("β de cobertura", beta)
    r.metrica("Vida media del diferencial (períodos)", vida)
    _tabla_stats(
        r,
        "Resultados (después de costos)",
        {"formación (in-sample)": estadisticas(ins, A), "operación (fuera de muestra)": estadisticas(oos, A)},
    )
    r.lineas(
        "z-score del diferencial",
        z.index,
        {"z": z.values, "entrada +": np.full(len(z), entrada), "entrada −": np.full(len(z), -entrada)},
        estilos={"entrada +": {"guion": "dash"}, "entrada −": {"guion": "dash"}},
        marcas=[{"x": str(p.index[cut].date()), "texto": "empieza fuera de muestra"}],
    )
    r.lineas("Valor de $1 (fuera de muestra)", oos.index, {"pares": np.exp(oos.cumsum()).values})
    r.serie(
        f"spread_{sid_a}_{sid_b}"[:40],
        spread.index,
        spread.values,
        f"Diferencial log({sid_a}) − β·log({sid_b})",
    )
    sh = estadisticas(oos, A).get("Sharpe")
    if pv > 0.05:
        r.veredicto(
            f"Los activos NO cointegran en la formación (p={fmt(pv)}): el diferencial no tiene por qué revertir.",
            "rojo",
        )
    elif sh is not None and sh == sh and sh > 0.5:
        r.veredicto(
            f"Cointegran (p={fmt(pv)}, vida media {fmt(vida, 3)}) y la estrategia rinde fuera de muestra (Sharpe {fmt(sh)}).",
            "verde",
        )
    else:
        r.veredicto(
            f"Cointegran en la formación pero fuera de muestra la estrategia no rinde (Sharpe {fmt(sh)}).",
            "amarillo",
        )
    r.resumen = f"Pares {sid_a}/{sid_b}: cointegración p={fmt(pv)}, β={fmt(beta)}, vida media {fmt(vida, 3)}; Sharpe fuera de muestra {fmt(sh)}."
    return r


@metodo(
    "regimenes_volatilidad",
    "Clusters y regímenes de volatilidad",
    F,
    "¿En qué régimen de volatilidad está el activo, cuánto suelen durar, y la volatilidad se agrupa?",
    clase="diagnosticar",
    params=[
        P_SERIE("sid", "Precio"),
        P_FREQ_F,
        Param("ventana", "entero", "Ventana de volatilidad realizada", defecto=21, minimo=5, maximo=252),
        Param("regimenes", "entero", "Regímenes", defecto=3, minimo=2, maximo=5),
    ],
    cuando="Ajustar tamaño de posición, stops o coberturas al régimen de riesgo vigente.",
    supuestos=["La volatilidad realizada (log) es una mezcla de regímenes gaussianos."],
    trampas=[
        "La volatilidad realizada en ventana se superpone: los regímenes salen persistentes por construcción en parte."
    ],
    deps=["sklearn"],
    referencias=["Mandelbrot (1963)", "Engle (1982)", "Ang y Timmermann (2012)"],
    etiquetas=["volatilidad", "clusters", "regímenes", "volatility clustering", "riesgo", "gmm"],
)
def regimenes_volatilidad(sid, freq, ventana, regimenes):
    from sklearn.mixture import GaussianMixture
    from statsmodels.tsa.stattools import acf

    p = precios([sid], freq, minimo=ventana * 5)[sid]
    ret = np.log(p).diff().dropna()
    A = ANUAL[freq]
    rv = (ret.rolling(ventana).std() * np.sqrt(A) * 100).dropna()
    x = np.log(rv.values).reshape(-1, 1)
    gm = GaussianMixture(regimenes, random_state=0, n_init=5).fit(x)
    lab = gm.predict(x)
    orden = np.argsort(gm.means_.ravel())
    mapa = {o: i for i, o in enumerate(orden)}
    lab = np.array([mapa[v] for v in lab])
    etiquetas = (
        ["calma", "normal", "tensión", "crisis", "pánico"][:regimenes]
        if regimenes <= 5
        else [f"R{i}" for i in range(regimenes)]
    )
    if regimenes == 2:
        etiquetas = ["calma", "tensión"]
    r = Resultado()
    filas = []
    for g in range(regimenes):
        msk = lab == g
        durs, run = [], 0
        for v in lab:
            if v == g:
                run += 1
            elif run:
                durs.append(run)
                run = 0
        if run:
            durs.append(run)
        rr = ret.loc[rv.index][msk]
        filas.append(
            [
                etiquetas[g],
                float(rv[msk].mean()),
                float(msk.mean() * 100),
                float(np.mean(durs)) if durs else None,
                float(rr.mean() * A * 100),
                _sharpe(rr, A),
            ]
        )
    r.tabla(
        "Regímenes de volatilidad",
        ["régimen", "vol. anual media %", "% del tiempo", "duración media", "rend. anual %", "Sharpe"],
        filas,
    )
    r.lineas(
        f"Volatilidad realizada de {sid} ({ventana} períodos, anualizada)",
        rv.index,
        {"vol. realizada %": rv.values, "régimen": lab + 1},
        y2=["régimen"],
    )
    a_r = acf(ret.values, nlags=20)[1:]
    a_abs = acf(np.abs(ret.values), nlags=20)[1:]
    r.barras(
        "Agrupamiento: autocorrelación de r y de |r|",
        list(range(1, 21)),
        {"r": a_r, "|r|": a_abs},
        banda=1.96 / np.sqrt(len(ret)),
    )
    r.metrica("Régimen actual", etiquetas[lab[-1]])
    r.metrica("Vol. realizada actual %", float(rv.iloc[-1]))
    r.metrica("ACF(1) de |r|", float(a_abs[0]))
    r.serie(f"regvol_{sid}"[:40], rv.index, lab + 1, f"Régimen de volatilidad de {sid}")
    r.resumen = f"{sid}: {regimenes} regímenes de volatilidad; hoy «{etiquetas[lab[-1]]}» (vol. {fmt(float(rv.iloc[-1]), 3)} %). ACF(1) de |r| = {fmt(float(a_abs[0]))} → {'hay' if a_abs[0] > 2 / np.sqrt(len(ret)) else 'no hay'} agrupamiento."
    return r


@metodo(
    "estacionalidad_calendario",
    "Mapa de estacionalidad (intradía, día de la semana, mes)",
    F,
    "¿Hay horas, días o meses en los que el activo rinde (o se mueve) sistemáticamente distinto?",
    clase="mirar",
    params=[
        P_SERIE("sid", "Precio"),
        Param(
            "mapa",
            "opcion",
            "Mapa",
            defecto="dia_x_mes",
            opciones=["hora_x_dia", "dia_x_mes", "mes_x_anio"],
            ayuda="hora_x_dia requiere datos intradía (frecuencia nativa)",
        ),
        Param(
            "medida",
            "opcion",
            "Qué se mide",
            defecto="rendimiento",
            opciones=["rendimiento", "volatilidad", "acierto"],
        ),
    ],
    cuando="Efectos calendario (lunes, fin de mes, enero), patrones intradía de volumen/volatilidad.",
    trampas=[
        "Con muchas celdas, alguna sale 'significativa' por azar (comparaciones múltiples): mirá el test conjunto."
    ],
    referencias=["French (1980)", "Andersen y Bollerslev (1997)"],
    etiquetas=[
        "estacionalidad",
        "intradía",
        "calendario",
        "día de la semana",
        "efecto enero",
        "heatmap",
        "mapa",
    ],
    nivel="basico",
)
def estacionalidad_calendario(sid, mapa, medida):
    from scipy import stats

    from cueva.datos import series as S

    p = S.cargar(sid, None).astype(float)
    p = p[p > 0]
    if mapa == "mes_x_anio":
        p = p.resample("ME").last().dropna()
    ret = np.log(p).diff().dropna()
    if mapa == "hora_x_dia":
        if len(set(ret.index.hour)) < 3:
            raise ErrorMetodo(
                "La serie no tiene datos intradía (todas las observaciones son a la misma hora)."
            )
        fil, col = ret.index.dayofweek, ret.index.hour
        nf = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]
        nc = None
    elif mapa == "dia_x_mes":
        fil, col = ret.index.dayofweek, ret.index.month
        nf = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]
        nc = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
    else:
        fil, col = ret.index.year, ret.index.month
        nf = None
        nc = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
    d = pd.DataFrame({"r": ret.values, "f": fil, "c": col})
    # lo que se compara entre celdas tiene que ser lo que se mide: la magnitud para la
    # volatilidad, el signo para el acierto (comparar r crudos sólo testea la media ≈ 0)
    d["z"] = {"rendimiento": d["r"], "volatilidad": d["r"].abs(), "acierto": (d["r"] > 0).astype(float)}[
        medida
    ]
    agg = {
        "rendimiento": lambda x: x.mean() * 100,
        "volatilidad": lambda x: x.std() * 100,
        "acierto": lambda x: (x > 0).mean() * 100,
    }[medida]
    tab = d.pivot_table(index="f", columns="c", values="r", aggfunc=agg)
    filas_n = [nf[i] if nf else str(i) for i in tab.index]
    cols_n = [nc[c - 1] if nc else f"{c}h" for c in tab.columns]
    r = Resultado()
    r.mapa_calor(
        f"{medida.capitalize()} de {sid} ({'%' if medida != 'acierto' else '% de positivos'})",
        filas_n,
        cols_n,
        tab.values,
        rango=None,
    )
    por_f = d.groupby("f")["r"]
    grupos = [g.values for _, g in d.groupby("f")["z"] if len(g) > 2]
    kw = stats.kruskal(*grupos) if len(grupos) > 1 else None
    r.tabla(
        "Por fila (promedio)",
        ["", "n", "rend. medio %", "vol. %", "% positivos"],
        [
            [filas_n[i], len(g), float(g.mean() * 100), float(g.std() * 100), float((g > 0).mean() * 100)]
            for i, (_, g) in enumerate(por_f)
        ],
    )
    if kw:
        r.metrica(
            "Kruskal-Wallis por fila (p)",
            float(kw.pvalue),
            "H0: todas las filas tienen la misma distribución",
        )
    g2 = [g.values for _, g in d.groupby("c")["z"] if len(g) > 2]
    if len(g2) > 1:
        r.metrica("Kruskal-Wallis por columna (p)", float(stats.kruskal(*g2).pvalue))
    r.resumen = (
        f"Mapa {mapa} de {sid} ({medida}): Kruskal-Wallis por fila p={fmt(float(kw.pvalue)) if kw else '—'}."
    )
    return r


@metodo(
    "neutralidad_factores",
    "Chequeo de neutralidad a factores (betas, alfa y exposición en el tiempo)",
    F,
    "¿La estrategia o el activo gana por habilidad (alfa) o porque está expuesto a factores (mercado, dólar, tasa)?",
    clase="diagnosticar",
    params=[
        P_SERIE("sid", "Activo o estrategia (precio / índice)"),
        P_SERIES("factores", "Factores (precios / índices)", minimo=1, maximo=8),
        P_FREQ_F,
        Param("ventana", "entero", "Ventana de betas móviles", defecto=60, minimo=15, maximo=1000),
        Param("tolerancia", "real", "|β| que se considera neutral", defecto=0.1, minimo=0.01, maximo=1),
    ],
    cuando="Validar que una estrategia 'neutral al mercado' realmente lo es, y descomponer el rendimiento.",
    supuestos=["Relación lineal entre rendimientos; errores Newey-West."],
    trampas=["Neutral en promedio no es neutral siempre: mirá las betas móviles en las crisis."],
    referencias=["Fama y French (1993)", "Carhart (1997)", "Grinold y Kahn (2000)"],
    etiquetas=[
        "factores",
        "beta",
        "alfa",
        "neutralidad",
        "market neutral",
        "exposición",
        "capm",
        "fama-french",
    ],
)
def neutralidad_factores(sid, factores, freq, ventana, tolerancia):
    import statsmodels.api as sm
    from statsmodels.regression.rolling import RollingOLS

    p = precios([sid, *factores], freq, minimo=ventana + 30)
    ret = rendimientos(p)
    A = ANUAL[freq]
    X = sm.add_constant(ret[factores])
    res = sm.OLS(ret[sid], X).fit(cov_type="HAC", cov_kwds={"maxlags": 5})
    r = Resultado()
    filas = [
        [
            "alfa (anualizado %)",
            res.params["const"] * A * 100,
            res.bse["const"] * A * 100,
            res.pvalues["const"],
            "—",
        ]
    ]
    for f in factores:
        neutral = abs(res.params[f]) <= tolerancia or res.pvalues[f] > 0.1
        filas.append(
            [f"β {f}", res.params[f], res.bse[f], res.pvalues[f], "neutral" if neutral else "EXPUESTO"]
        )
    r.tabla("Exposición a factores", ["término", "coef", "EE", "p", "veredicto"], filas, resaltar_p="p")
    r.metrica("R² (varianza explicada por factores)", res.rsquared)
    r.metrica("Alfa anual %", res.params["const"] * A * 100)
    r.metrica("Ratio de información", float(res.params["const"] / res.resid.std() * np.sqrt(A)))
    rol = RollingOLS(ret[sid], X, window=ventana).fit()
    r.lineas(
        f"Betas móviles ({ventana} períodos)",
        rol.params.index,
        {f"β {f}": rol.params[f].values for f in factores}
        | {"+tol": np.full(len(rol.params), tolerancia), "−tol": np.full(len(rol.params), -tolerancia)},
        estilos={"+tol": {"guion": "dot"}, "−tol": {"guion": "dot"}},
    )
    contrib = {f: float(res.params[f] * ret[f].mean() * A * 100) for f in factores}
    r.barras(
        "Descomposición del rendimiento anual (%)",
        ["alfa", *factores, "total"],
        {"aporte": [res.params["const"] * A * 100, *contrib.values(), ret[sid].mean() * A * 100]},
    )
    expuestos = [f for f in factores if not (abs(res.params[f]) <= tolerancia or res.pvalues[f] > 0.1)]
    r.veredicto(
        ("Neutral a todos los factores." if not expuestos else f"Expuesto a: {', '.join(expuestos)}.")
        + f" Alfa {fmt(res.params['const'] * A * 100, 3)} % anual (p={fmt(res.pvalues['const'])}).",
        "verde" if not expuestos else "amarillo",
    )
    r.resumen = f"{sid} vs {', '.join(factores)}: R²={fmt(res.rsquared)}, alfa {fmt(res.params['const'] * A * 100, 3)} %/año (p={fmt(res.pvalues['const'])}); expuesto a {', '.join(expuestos) or 'ninguno'}."
    return r
