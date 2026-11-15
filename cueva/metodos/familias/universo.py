"""El universo de modelos: estimar TODAS las especificaciones razonables y mirar qué sobrevive.

Es el método del Trabajo Final de Martín («Un popurrí de determinantes: riesgo país
idiosincrático argentino», 222.671 regresiones): en vez de defender una especificación, se
iteran combinaciones de explicativas en ARDL, VAR y VECM, se filtran por diagnóstico de
residuos y se estudia la DISTRIBUCIÓN de los resultados (qué variable es significativa en qué
porcentaje de modelos, con qué signo y magnitud).

Lo que devuelve son sobre todo DATOS (`Resultado.conjunto`): la tabla de modelos y la tabla
larga modelo × variable. Los bloques son la vista sugerida; la pantalla puede volver a
graficarlos como quiera y convertir cualquier columna en serie.

Las funciones de cálculo (`iterar`, `granger_nxn`) son puras: también las usa
scripts/mockup_mesa_investigacion_datos.py, así no hay dos implementaciones.
"""

from __future__ import annotations

import inspect
import warnings
from itertools import combinations

import numpy as np
import pandas as pd

from cueva.metodos.contrato import ErrorMetodo, Param, Resultado
from cueva.metodos.insumos import P_FREQ, P_SERIE, P_SERIES, fmt, panel
from cueva.metodos.registro import metodo

MODELOS = ("ARDL", "VAR", "VECM")


def _ljung_box_p(resid, lags=12) -> float:
    from statsmodels.stats.diagnostic import acorr_ljungbox

    r = np.asarray(resid, float)
    r = r[np.isfinite(r)]
    return float(acorr_ljungbox(r, lags=[min(lags, len(r) // 5)], return_df=True)["lb_pvalue"].iloc[0])


def _ardl_largo_plazo(df, dep, xs, p, q):
    """ARDL en niveles; θ_x = Σβ_x / (1 − Σφ) con EE por método delta."""
    from scipy import stats
    from statsmodels.tsa.ardl import ARDL

    res = ARDL(df[dep], lags=p, exog=df[xs], order={x: q for x in xs}, trend="c").fit()
    nombres = list(res.params.index)
    b, V = res.params.values, res.cov_params().values
    iy = [i for i, n in enumerate(nombres) if n.startswith(f"{dep}.L")]
    den = 1 - b[iy].sum()
    out = {}
    for x in xs:
        ix = [i for i, n in enumerate(nombres) if n.startswith(f"{x}.L")]
        num = b[ix].sum()
        g = np.zeros(len(b))
        g[ix] = 1 / den
        g[iy] = num / den**2
        se = float(np.sqrt(max(g @ V @ g, 1e-300)))
        th = num / den
        out[x] = (float(th), float(2 * stats.norm.sf(abs(th / se))))
    return res, out


def estacionarias(df: pd.DataFrame, orden: dict[str, str] | None = None) -> pd.DataFrame:
    """Δ para lo I(1) (según `orden`, o por ADF al 5 % si no se informa), nivel para lo I(0)."""
    from statsmodels.tsa.stattools import adfuller

    cols = {}
    for c in df.columns:
        o = (orden or {}).get(c)
        if not o:
            o = "I(0)" if adfuller(df[c].values, autolag="AIC")[1] < 0.05 else "I(1)"
        cols[c] = df[c] if o == "I(0)" else df[c].diff()
    return pd.DataFrame(cols).dropna()


def iterar(
    df: pd.DataFrame,
    dep: str,
    xs: list[str],
    tamanos=(1, 2, 3),
    modelos=MODELOS,
    orden=None,
    max_por_modelo=5000,
    semilla=0,
    ardl_pq=((1, 1), (1, 2), (2, 1), (2, 2)),
    vecm_max=2,
):
    """Estima el universo. Devuelve (modelos, efectos):
    modelos: [tipo, [idx de xs], spec, r2, aic, bic, nobs, lb_p, pasa_filtro]
    efectos: [id_modelo, idx de x, coef de largo plazo (o acumulado), p-valor]"""
    from statsmodels.tsa.api import VAR
    from statsmodels.tsa.vector_ar.vecm import VECM, coint_johansen

    rng = np.random.default_rng(semilla)
    idx = {v: i for i, v in enumerate(xs)}
    combos = [list(c) for r in tamanos for c in combinations(xs, r)]
    est = estacionarias(df[[dep, *xs]], orden)
    mods, efs = [], []

    def reg(tipo, cx, spec, r2, aic, bic, nobs, lbp, e):
        mid = len(mods)
        mods.append(
            [
                tipo,
                [idx[x] for x in cx],
                spec,
                round(float(r2), 4),
                aic,
                bic,
                int(nobs),
                round(lbp, 4),
                int(lbp > 0.05),
            ]
        )
        for x, (c, p) in e.items():
            if np.isfinite(c) and np.isfinite(p):
                efs.append([mid, idx[x], float(f"{c:.6g}"), float(f"{p:.4g}")])

    def muestra(lista):
        if len(lista) <= max_por_modelo:
            return lista
        return [lista[i] for i in sorted(rng.choice(len(lista), max_por_modelo, replace=False))]

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if "ARDL" in modelos:
            for cx, (p, q) in muestra([(c, pq) for c in combos for pq in ardl_pq]):
                try:
                    res, lr = _ardl_largo_plazo(df, dep, cx, p, q)
                    r2 = 1 - np.var(res.resid) / np.var(df[dep].iloc[-len(res.resid) :])
                    reg(
                        "ARDL",
                        cx,
                        f"p{p}q{q}",
                        r2,
                        round(res.aic, 2),
                        round(res.bic, 2),
                        res.nobs,
                        _ljung_box_p(res.resid),
                        lr,
                    )
                except Exception:
                    continue
        if "VAR" in modelos:
            for cx in muestra(combos):
                try:
                    sub = est[[dep, *cx]].values
                    k = max(1, int(VAR(sub).select_order(maxlags=4).selected_orders["aic"]))
                    res = VAR(sub).fit(k)
                    e = {
                        x: (
                            float(sum(res.coefs[L][0, j] for L in range(k))),
                            float(res.test_causality(0, [j], kind="f").pvalue),
                        )
                        for j, x in enumerate(cx, start=1)
                    }
                    e0 = res.resid[:, 0]
                    reg(
                        "VAR",
                        cx,
                        f"k{k}",
                        1 - np.var(e0) / np.var(sub[k:, 0]),
                        round(float(res.aic), 3),
                        round(float(res.bic), 3),
                        res.nobs,
                        _ljung_box_p(e0),
                        e,
                    )
                except Exception:
                    continue
        if "VECM" in modelos:
            for cx in muestra([c for c in combos if len(c) <= vecm_max]):
                sub = df[[dep, *cx]]
                try:
                    jo = coint_johansen(sub.values, det_order=0, k_ar_diff=1)
                    rango = int(sum(jo.lr1 > jo.cvt[:, 1]))
                    if rango < 1:
                        continue
                    res = VECM(sub.values, k_ar_diff=1, coint_rank=1, deterministic="ci").fit()
                    beta = res.beta[:, 0] / res.beta[0, 0]
                    pv = np.ravel(getattr(res, "pvalues_beta", np.full(len(cx), np.nan)))
                    e = {
                        x: (float(-beta[j]), float(pv[j - 1]) if pv.size >= j else float("nan"))
                        for j, x in enumerate(cx, start=1)
                    }
                    e0 = res.resid[:, 0]
                    reg(
                        "VECM",
                        cx,
                        f"r{rango}",
                        1 - np.var(e0) / np.var(np.diff(sub.values[:, 0])),
                        None,
                        None,
                        res.nobs,
                        _ljung_box_p(e0),
                        e,
                    )
                except Exception:
                    continue
    return mods, efs


def granger_nxn(est: pd.DataFrame, max_lag: int = 6):
    """p-valores de Granger fila → columna, rezago por AIC (≤ max_lag), sobre series estacionarias."""
    from statsmodels.tsa.api import VAR
    from statsmodels.tsa.stattools import grangercausalitytests

    kw = {"verbose": False} if "verbose" in inspect.signature(grangercausalitytests).parameters else {}
    cols = list(est.columns)
    P = [[None] * len(cols) for _ in cols]
    L = [[None] * len(cols) for _ in cols]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for i, causa in enumerate(cols):
            for j, efecto in enumerate(cols):
                if i == j:
                    continue
                sub = est[[efecto, causa]].values
                k = max(1, int(VAR(sub).select_order(maxlags=max_lag).selected_orders["aic"]))
                r = grangercausalitytests(sub, maxlag=[k], **kw)
                P[i][j] = float(f"{float(r[k][0]['ssr_ftest'][1]):.4g}")
                L[i][j] = k
    return P, L


def pct_significativos(mods, efs, n_x, alpha=0.05, solo_limpios=True):
    """{modelo: [(n, % sig, % positivos entre sig)] por variable}."""
    out = {m: [[0, 0, 0] for _ in range(n_x)] for m in MODELOS}
    for mid, v, c, p in efs:
        mo = mods[mid]
        if solo_limpios and not mo[8]:
            continue
        o = out[mo[0]][v]
        o[0] += 1
        if p < alpha:
            o[1] += 1
            o[2] += c > 0
    return {
        m: [(n, 100 * s / n if n else None, 100 * pos / s if s else None) for n, s, pos in filas]
        for m, filas in out.items()
    }


@metodo(
    "universo_modelos",
    "Universo de modelos (ARDL · VAR · VECM sobre todas las combinaciones)",
    "evaluacion",
    "¿Qué determinantes sobreviven a TODAS las especificaciones razonables, y con qué signo?",
    params=[
        P_SERIE("dep", "Dependiente (Y)"),
        P_SERIES("candidatas", "Explicativas candidatas", minimo=2, maximo=20),
        P_FREQ,
        Param(
            "tamanos",
            "opciones",
            "Cantidad de explicativas por modelo",
            defecto=["1", "2", "3"],
            opciones=["1", "2", "3", "4"],
        ),
        Param("modelos", "opciones", "Modelos", defecto=list(MODELOS), opciones=list(MODELOS)),
        Param("alpha", "real", "Nivel de significancia", defecto=0.05, minimo=0.001, maximo=0.2),
        Param("solo_limpios", "bool", "Sólo modelos con residuos limpios (Ljung-Box)", defecto=True),
        Param(
            "max_por_modelo",
            "entero",
            "Tope de especificaciones por tipo de modelo",
            defecto=3000,
            minimo=50,
            maximo=50000,
            ayuda="Si hay más, se toma una muestra aleatoria con semilla fija",
        ),
    ],
    cuando="Cuando la teoría admite muchos determinantes y ninguna especificación es obviamente la correcta (Leamer, Sala-i-Martin).",
    supuestos=[
        "ARDL en niveles (largo plazo por método delta); VAR sobre series estacionarias (Δ para lo I(1)); VECM con rango ≥ 1 por Johansen."
    ],
    trampas=[
        "Un % de significatividad cerca de α es lo que da el azar: no es evidencia.",
        "Con pocos modelos en una celda (VECM suele tener pocos) el porcentaje no dice nada: mirá el n.",
        "Filtrar por residuos limpios cambia la muestra de modelos: reportá con y sin filtro.",
    ],
    costo="minutos",
    referencias=[
        "Leamer (1983)",
        "Sala-i-Martin (1997), «I just ran two million regressions»",
        "Simonsohn, Simmons y Nelson (2020)",
    ],
    etiquetas=[
        "universo",
        "iterar",
        "ardl",
        "var",
        "vecm",
        "robustez",
        "meta-análisis",
        "combinaciones",
        "trabajo final",
    ],
)
def universo_modelos(dep, candidatas, freq, tamanos, modelos, alpha, solo_limpios, max_por_modelo):
    xs = [c for c in candidatas if c != dep]
    df, et = panel([dep, *xs], freq, "nivel", minimo=60)
    mods, efs = iterar(
        df, dep, xs, tuple(int(t) for t in tamanos), tuple(modelos), max_por_modelo=max_por_modelo
    )
    if not mods:
        raise ErrorMetodo("Ningún modelo pudo estimarse.")
    por = pct_significativos(mods, efs, len(xs), alpha, solo_limpios)
    r = Resultado()
    n_tipo = {m: sum(1 for x in mods if x[0] == m) for m in MODELOS}
    n_ok = {m: sum(1 for x in mods if x[0] == m and x[8]) for m in MODELOS}
    for m in MODELOS:
        if n_tipo[m]:
            r.metrica(f"{m}: estimados / con residuos limpios", f"{n_tipo[m]} / {n_ok[m]}")
    nombres = [et[x] for x in xs]
    filas = []
    for i, nom in enumerate(nombres):
        fila = [nom]
        for m in modelos:
            n, ps, pos = por[m][i]
            fila += [n, ps, pos]
        filas.append(fila)
    filas.sort(key=lambda f: -sum((f[2 + 3 * k] or 0) for k in range(len(modelos))))
    cols = ["variable"] + [c for m in modelos for c in (f"{m} n", f"{m} % sig.", f"{m} % positivos")]
    r.tabla(
        f"Significatividad por variable (α={alpha}{', residuos limpios' if solo_limpios else ''})",
        cols,
        filas,
        nota="Las celdas con n < 10 no son concluyentes.",
    )
    r.barras(
        "% de modelos con efecto significativo",
        [f[0] for f in filas],
        {m: [f[2 + 3 * k] for f in filas] for k, m in enumerate(modelos)},
        banda=alpha * 100,
        horizontal=True,
        eje_y="%",
    )
    # tablas DESNORMALIZADAS: se filtran y agrupan por nombre («=ITCRM», «=ARDL») sin cruzar tablas
    r.conjunto(
        "efectos",
        ["modelo", "tipo", "spec", "variable", "coef_lp", "p", "residuos_limpios", "k"],
        [
            [m, mods[m][0], mods[m][2], nombres[v], c, p, "sí" if mods[m][8] else "no", len(mods[m][1])]
            for m, v, c, p in efs
        ],
        "Una fila por modelo × variable: coeficiente de largo plazo (ARDL, VECM) o acumulado (VAR) y su p-valor.",
    )
    r.conjunto(
        "modelos",
        [
            "modelo",
            "tipo",
            "explicativas",
            "spec",
            "r2",
            "aic",
            "bic",
            "nobs",
            "ljung_box_p",
            "residuos_limpios",
        ],
        [
            [
                i,
                m[0],
                ", ".join(nombres[j] for j in m[1]),
                m[2],
                m[3],
                m[4],
                m[5],
                m[6],
                m[7],
                "sí" if m[8] else "no",
            ]
            for i, m in enumerate(mods)
        ],
        "Un modelo por fila.",
    )
    robustas = [
        f[0]
        for f in filas
        if all((f[2 + 3 * k] or 0) >= 50 and f[1 + 3 * k] >= 10 for k in range(len(modelos)) if f[1 + 3 * k])
    ]
    r.veredicto(
        ("Robustas (≥ 50 % de modelos significativos en todos los tipos con n ≥ 10): " + ", ".join(robustas))
        if robustas
        else "Ninguna variable es significativa en la mayoría de los modelos de todos los tipos.",
        "verde" if robustas else "amarillo",
    )
    r.resumen = f"Universo de {len(mods)} modelos para {et[dep]} con {len(xs)} candidatas ({', '.join(f'{m} {n_tipo[m]}' for m in MODELOS if n_tipo[m])}). Robustas: {', '.join(robustas) or 'ninguna'}."
    r.datos = {"n": len(mods), "robustas": robustas}
    return r


@metodo(
    "granger_matriz",
    "Causalidad de Granger N × N",
    "pruebas",
    "Entre muchas series, ¿cuál precede a cuál? El mapa completo de precedencias.",
    params=[
        P_SERIES("sids", "Series (3 a 25)", minimo=3, maximo=25),
        P_FREQ,
        Param("max_rezago", "entero", "Rezago máximo (se elige por AIC)", defecto=6, minimo=1, maximo=24),
        Param("alpha", "real", "Nivel de significancia", defecto=0.05, minimo=0.001, maximo=0.2),
    ],
    cuando="Para un primer mapa de relaciones dinámicas antes de elegir un sistema (VAR) o un orden de Cholesky.",
    supuestos=["Series estacionarias: se diferencia lo I(1) por ADF."],
    trampas=[
        "Con N series hay N(N−1) pruebas: alguna sale significativa por azar.",
        "Es precedencia temporal, no causalidad económica.",
    ],
    costo="segundos",
    referencias=["Granger (1969)"],
    etiquetas=["granger", "matriz", "heatmap", "precedencia", "red", "causalidad"],
)
def granger_matriz(sids, freq, max_rezago, alpha):
    df, et = panel(sids, freq, "nivel", minimo=40)
    est = estacionarias(df)
    P, L = granger_nxn(est, max_rezago)
    nombres = [et[s] for s in sids]
    r = Resultado()
    r.mapa_calor(
        "p-valor de Granger (fila precede a columna)",
        nombres,
        nombres,
        [[p if p is not None else None for p in fila] for fila in P],
        rango=(0, 1),
    )
    pares = sorted(
        [
            [nombres[i], nombres[j], P[i][j], L[i][j]]
            for i in range(len(sids))
            for j in range(len(sids))
            if i != j
        ],
        key=lambda f: f[2],
    )
    r.tabla("Pares ordenados por p-valor", ["precede", "a", "p", "rezagos"], pares[:60], resaltar_p="p")
    r.conjunto("granger (pares)", ["precede", "a", "p", "rezagos"], pares)
    r.conjunto(
        "granger (matriz)",
        ["", *nombres],
        [[nombres[i], *P[i]] for i in range(len(sids))],
        "Fila = la que precede; columna = la precedida; celda = p-valor.",
    )
    n_sig = sum(1 for f in pares if f[2] < alpha)
    esperados = alpha * len(pares)
    r.metrica("Pares significativos", n_sig)
    r.metrica("Esperables por azar", esperados)
    salen = {}
    for f in pares:
        if f[2] < alpha:
            salen[f[0]] = salen.get(f[0], 0) + 1
    if salen:
        r.barras(
            "Cuántas series precede cada una (p < α)",
            list(salen),
            {"precede a": list(salen.values())},
            horizontal=True,
        )
    r.veredicto(
        f"{n_sig} de {len(pares)} pares con p < {alpha} (por azar se esperarían ≈{fmt(esperados, 2)}).",
        "verde" if n_sig > 2 * esperados else "amarillo",
    )
    r.resumen = f"Granger N×N entre {len(sids)} series: {n_sig} pares significativos de {len(pares)}; la que más precede: {max(salen, key=salen.get) if salen else '—'}."
    return r
