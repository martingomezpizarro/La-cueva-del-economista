"""Fase M1 (docs/INVESTIGACION_METODOS.md §7): activos, eventos y robustez.

- Burbujas: SADF/GSADF de Phillips-Shi-Yu con fechado BSADF y valores críticos por Monte Carlo.
- Sobreajuste de backtests: PBO por CSCV, Sharpe deflactado y reality check de White.
- Apuesta binaria (Kalshi/Polymarket): valor esperado, Kelly y riesgo de ruina.
- Triple barrera + meta-etiquetado (López de Prado).
- Estudio de eventos de mercado (retornos anormales, CAR).
- Contagio de Diebold-Yilmaz, correlaciones dinámicas DCC, colas extremas (EVT).
- Curva de rendimientos de Nelson-Siegel.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from cueva.metodos.contrato import ErrorMetodo, Param, Resultado
from cueva.metodos.familias.finanzas import ANUAL, FREQS, P_COSTO, P_FREQ_F, precios, rendimientos
from cueva.metodos.insumos import (
    P_FREQ,
    P_SERIE,
    P_SERIES,
    P_TRANSF,
    evento_cercano,
    eventos_en,
    fmt,
    panel,
    serie,
)
from cueva.metodos.registro import metodo


# ──────────────────────────────────────────────────────────────────────────
# Burbujas: SADF / GSADF / BSADF (Phillips, Shi y Yu 2015)
# ──────────────────────────────────────────────────────────────────────────
def _matrices_adf(y: np.ndarray, k: int):
    """Regresores del ADF con k rezagos: Δy_t ~ [1, y_{t−1}, Δy_{t−1}, …, Δy_{t−k}]."""
    dy = np.diff(y)
    n = len(dy)
    filas = np.arange(k, n)
    X = np.column_stack([np.ones(len(filas)), y[:-1][filas]] + [dy[filas - j] for j in range(1, k + 1)])
    return X, dy[filas]


def _adf_ventanas(y: np.ndarray, r0: int, k: int = 1) -> np.ndarray:
    """t del coeficiente de y_{t−1} del ADF con constante y k rezagos para TODAS las ventanas
    [i, j) de largo ≥ r0. Productos cruzados acumulados + resolución en lote: O(n²·m³)."""
    X, z = _matrices_adf(y, k)
    n, m = X.shape
    C = np.concatenate([np.zeros((1, m, m)), np.cumsum(X[:, :, None] * X[:, None, :], axis=0)])
    Cz = np.concatenate([np.zeros((1, m)), np.cumsum(X * z[:, None], axis=0)])
    Czz = np.concatenate([[0.0], np.cumsum(z * z)])
    T = np.full((n + 1, n + 1), np.nan)
    for i in range(0, n - r0 + 1):
        j = np.arange(i + r0, n + 1)
        XtX = C[j] - C[i]
        Xtz = Cz[j] - Cz[i]
        ztz = Czz[j] - Czz[i]
        try:
            inv = np.linalg.inv(XtX)
        except np.linalg.LinAlgError:
            continue
        beta = np.einsum("aij,aj->ai", inv, Xtz)
        ssr = ztz - np.einsum("ai,ai->a", beta, Xtz)
        gl = (j - i) - m
        with np.errstate(divide="ignore", invalid="ignore"):
            T[i, j] = beta[:, 1] / np.sqrt(np.maximum(ssr, 1e-300) / gl * inv[:, 1, 1])
    return T


def _psy(y, r0, k=1):
    T = _adf_ventanas(y, r0, k)
    n = T.shape[0] - 1
    sadf = np.nanmax(T[0, r0:])
    bsadf = np.full(n + 1, np.nan)
    for j in range(r0, n + 1):
        bsadf[j] = np.nanmax(T[: j - r0 + 1, j])
    # bsadf[j] corresponde a la observación j+k+1 de y (se pierden 1 + k al diferenciar y rezagar)
    return sadf, np.nanmax(bsadf), np.concatenate([np.full(k + 1, np.nan), bsadf])[: len(y)]


@metodo(
    "burbuja_gsadf",
    "Prueba de burbujas (SADF / GSADF de Phillips-Shi-Yu) con fechado",
    "pruebas",
    "¿La serie tuvo episodios explosivos (burbujas, corridas) y cuándo empezaron y terminaron?",
    params=[
        P_SERIE(),
        Param(
            "freq",
            "opcion",
            "Frecuencia",
            defecto="mensual",
            opciones=["diaria", "mensual", "trimestral", "anual"],
        ),
        Param("transf", "opcion", "Transformación", defecto="log", opciones=["nivel", "log"]),
        Param(
            "ventana_min",
            "real",
            "Ventana mínima (fracción, 0 = regla PSY)",
            defecto=0.0,
            minimo=0,
            maximo=0.5,
        ),
        Param("rezagos", "entero", "Rezagos del ADF", defecto=1, minimo=0, maximo=6),
        Param("simulaciones", "entero", "Simulaciones para los críticos", defecto=199, minimo=49, maximo=999),
    ],
    cuando="Dólar paralelo, brecha, precios de activos, riesgo país: distingue una suba fuerte de una dinámica explosiva.",
    supuestos=[
        "H0: raíz unitaria con deriva despreciable; H1: tramos con raíz > 1 (explosiva).",
        "ADF con constante y k rezagos en cada ventana; críticos por wild bootstrap con la dinámica de corto plazo impuesta bajo H0 (robustos a autocorrelación y heterocedasticidad).",
    ],
    trampas=[
        "Un explosivo no es necesariamente una burbuja de precios: puede ser un fundamento explosivo (inflación que se acelera).",
        "La serie tiene que ir en log: en niveles, cualquier crecimiento exponencial parece explosivo.",
    ],
    costo="segundos",
    referencias=[
        "Phillips, Shi y Yu (2015)",
        "Phillips, Wu y Yu (2011)",
        "Harvey, Leybourne, Sollis y Taylor (2016)",
        "Phillips y Shi (2020)",
    ],
    etiquetas=["burbuja", "explosivo", "gsadf", "sadf", "psy", "corrida", "dólar"],
)
def burbuja_gsadf(sid, freq, transf, ventana_min, rezagos, simulaciones):
    s, et = serie(sid, freq, transf, minimo=40)
    if len(s) > 1500:
        raise ErrorMetodo("Más de 1.500 observaciones: pasá a una frecuencia más baja (el GSADF es O(n²)).")
    y = s.values.astype(float)
    n = len(y) - 1
    r0 = int(np.ceil((ventana_min or (0.01 + 1.8 / np.sqrt(len(y)))) * n))
    r0 = max(r0, 12)
    k = rezagos
    sadf, gsadf, bsadf = _psy(y, r0, k)
    rng = np.random.default_rng(0)
    sims_s, sims_g, sims_b = [], [], []
    # Wild bootstrap con la dinámica de corto plazo impuesta bajo H0 (Phillips y Shi 2020):
    # se estima el ADF de muestra completa, se toman sus φ (rezagos de Δy, estimados
    # CONDICIONALES al nivel, así la burbuja no se cuela como dinámica) y sus residuos, y se
    # simula Δy* = Σ φ_j Δy*_{t−j} + w_t·e_t con w = ±1. Conserva autocorrelación y
    # heterocedasticidad; con críticos de ruido i.i.d. aparecen burbujas falsas.
    Xf, zf = _matrices_adf(y, k)
    bf, *_ = np.linalg.lstsq(Xf, zf, rcond=None)
    phi = bf[2:]
    e = zf - Xf @ bf
    for _ in range(simulaciones):
        eb = e * rng.choice([-1.0, 1.0], size=len(e))
        d_sim = np.zeros(len(e) + k)
        for t in range(k, len(d_sim)):
            d_sim[t] = (phi @ d_sim[t - k : t][::-1] if k else 0.0) + eb[t - k]
        z = y[0] + np.concatenate([[0.0], np.cumsum(d_sim)])
        a, g, b = _psy(z, r0, k)
        sims_s.append(a)
        sims_g.append(g)
        sims_b.append(b)
    cs = np.percentile(sims_s, [90, 95, 99])
    cg = np.percentile(sims_g, [90, 95, 99])
    cb = np.nanpercentile(np.array(sims_b), 95, axis=0)  # crítico secuencial al 95 %
    r = Resultado()
    r.tabla(
        "Estadísticos y valores críticos (Monte Carlo)",
        ["prueba", "estadístico", "crítico 90 %", "crítico 95 %", "crítico 99 %", "p"],
        [
            ["SADF", sadf, *cs, float(np.mean(np.array(sims_s) >= sadf))],
            ["GSADF", gsadf, *cg, float(np.mean(np.array(sims_g) >= gsadf))],
        ],
        resaltar_p="p",
    )
    idx = s.index
    bs = pd.Series(bsadf, index=idx)
    crit = pd.Series(cb, index=idx)
    # se fecha sólo si la prueba global rechaza (si no, los rechazos fecha a fecha son el 5 %
    # esperable por azar en cada una de cientos de fechas)
    explosivo = (bs > crit).fillna(False) & bool(gsadf > cg[1])
    episodios, i, minimo_dur = [], 0, max(2, int(np.log(len(y))))
    while i < len(explosivo):
        if explosivo.iloc[i]:
            j = i
            while j + 1 < len(explosivo) and explosivo.iloc[j + 1]:
                j += 1
            if j - i + 1 >= minimo_dur:
                ev = evento_cercano(idx[i], 6)
                episodios.append(
                    [str(idx[i].date()), str(idx[j].date()), j - i + 1, ev["titulo"] if ev else "—"]
                )
            i = j + 1
        else:
            i += 1
    r.lineas(f"{et}", idx, {et: y})
    r.lineas(
        "BSADF vs crítico 95 % (arriba = explosivo)",
        idx,
        {"BSADF": bs.values, "crítico 95 %": crit.values},
        estilos={"crítico 95 %": {"guion": "dash"}},
        marcas=[{"x": e[0], "texto": e[3] if e[3] != "—" else "inicio"} for e in episodios[:10]],
    )
    if episodios:
        r.tabla(
            f"Episodios explosivos (≥ {minimo_dur} períodos) y evento cercano",
            ["inicio", "fin", "duración", "evento ±6 meses"],
            episodios,
        )
    r.serie(
        f"{sid}_explosivo"[:40],
        idx,
        explosivo.astype(int).values,
        f"1 = tramo explosivo de {et} (BSADF > crítico 95 %)",
    )
    r.metrica("GSADF", gsadf)
    r.metrica("Crítico 95 %", cg[1])
    r.metrica("Episodios", len(episodios))
    r.metrica("¿Explosivo hoy?", "sí" if explosivo.iloc[-1] else "no")
    hay = gsadf > cg[1]
    r.veredicto(
        f"{'Hay' if hay else 'No hay'} evidencia de dinámica explosiva (GSADF {fmt(gsadf)} vs crítico {fmt(cg[1])}); {len(episodios)} episodio(s).",
        "amarillo" if hay else "verde",
    )
    r.resumen = (
        f"GSADF sobre {et}: {fmt(gsadf)} (crítico 95 % {fmt(cg[1])}); episodios: "
        + ("; ".join(f"{e[0]}→{e[1]}" for e in episodios[:6]) or "ninguno")
        + f". Hoy {'explosivo' if explosivo.iloc[-1] else 'no explosivo'}."
    )
    return r


# ──────────────────────────────────────────────────────────────────────────
# Sobreajuste de backtests
# ──────────────────────────────────────────────────────────────────────────
def _sharpe(r):
    r = np.asarray(r, float)
    return r.mean() / r.std(ddof=1) if r.std(ddof=1) > 0 else 0.0


def _bootstrap_estacionario(n, L, rng):
    idx = np.empty(n, dtype=int)
    idx[0] = rng.integers(n)
    for t in range(1, n):
        idx[t] = rng.integers(n) if rng.random() < 1 / L else (idx[t - 1] + 1) % n
    return idx


@metodo(
    "sobreajuste_backtest",
    "¿La mejor estrategia es suerte? (PBO, Sharpe deflactado, reality check de White)",
    "evaluacion",
    "Si probé muchas variantes de una regla y me quedé con la mejor, ¿cuánto de su rendimiento es sobreajuste?",
    params=[
        P_SERIE("sid", "Precio del activo"),
        P_FREQ_F,
        Param(
            "familia_reglas",
            "opcion",
            "Reglas a probar",
            defecto="cruce_medias",
            opciones=["cruce_medias", "momentum", "reversion"],
        ),
        Param("bloques", "entero", "Bloques del CSCV (par)", defecto=10, minimo=4, maximo=16),
        Param("bootstrap", "entero", "Réplicas del reality check", defecto=300, minimo=100, maximo=2000),
        P_COSTO,
    ],
    cuando="Siempre que se elija una estrategia entre muchas probadas (parámetros, activos, reglas).",
    supuestos=[
        "Las variantes se evalúan sobre el mismo período; el CSCV parte la muestra en S bloques y prueba todas las combinaciones S/2 de entrenamiento y prueba."
    ],
    trampas=[
        "Reportar el Sharpe de la mejor de N variantes sin deflactar es la forma estándar de engañarse (Bailey et al. 2014)."
    ],
    costo="segundos",
    referencias=[
        "Bailey, Borwein, López de Prado y Zhu (2017), PBO",
        "Bailey y López de Prado (2014), Sharpe deflactado",
        "White (2000)",
        "Politis y Romano (1994)",
    ],
    etiquetas=[
        "sobreajuste",
        "pbo",
        "cscv",
        "sharpe deflactado",
        "reality check",
        "data snooping",
        "backtest",
    ],
)
def sobreajuste_backtest(sid, freq, familia_reglas, bloques, bootstrap, costo_pb):
    import itertools

    from scipy import stats

    p = precios([sid], freq, minimo=300)[sid]
    ret = np.log(p).diff()
    c = costo_pb / 1e4
    variantes = {}
    if familia_reglas == "cruce_medias":
        for f, s in itertools.product([5, 10, 20, 30, 50], [50, 100, 150, 200, 250]):
            if f < s:
                pos = (p.rolling(f).mean() > p.rolling(s).mean()).astype(float).shift(1)
                variantes[f"MA {f}/{s}"] = pos * ret - c * pos.diff().abs()
    elif familia_reglas == "momentum":
        for k in [5, 10, 20, 40, 60, 120, 250]:
            for salto in [0, 5]:
                pos = np.sign(np.log(p).shift(salto) - np.log(p).shift(salto + k)).shift(1)
                variantes[f"mom {k}-{salto}"] = pos * ret - c * pos.diff().abs()
    else:
        for k in [5, 10, 20, 40]:
            for z in [1.0, 1.5, 2.0]:
                zz = (p - p.rolling(k).mean()) / p.rolling(k).std()
                pos = (-np.sign(zz) * (zz.abs() > z)).astype(float).shift(1)
                variantes[f"rev {k} z{z}"] = pos * ret - c * pos.diff().abs()
    M = pd.DataFrame(variantes).dropna()
    M = M.iloc[len(M) % bloques :]
    T, N = M.shape
    A = ANUAL.get(freq, 252)
    sh = M.apply(_sharpe).values * np.sqrt(A)
    mejor = int(np.argmax(sh))
    # CSCV → PBO
    partes = np.array_split(np.arange(T), bloques)
    logits = []
    for comb in itertools.combinations(range(bloques), bloques // 2):
        ins = np.concatenate([partes[k] for k in comb])
        oos = np.concatenate([partes[k] for k in range(bloques) if k not in comb])
        sh_in = M.iloc[ins].apply(_sharpe).values
        sh_oos = M.iloc[oos].apply(_sharpe).values
        n_star = int(np.argmax(sh_in))
        rango = stats.rankdata(sh_oos)[n_star] / (N + 1)
        logits.append(np.log(rango / (1 - rango)))
    logits = np.array(logits)
    pbo = float(np.mean(logits <= 0))
    # Sharpe deflactado (Bailey y López de Prado 2014), en unidades por período
    sr = sh / np.sqrt(A)
    var_sr = np.var(sr, ddof=1)
    em = 0.5772156649
    sr0 = np.sqrt(var_sr) * ((1 - em) * stats.norm.ppf(1 - 1 / N) + em * stats.norm.ppf(1 - 1 / (N * np.e)))
    rb = M.iloc[:, mejor].values
    g3, g4 = stats.skew(rb), stats.kurtosis(rb, fisher=False)
    srb = sr[mejor]
    dsr = float(stats.norm.cdf((srb - sr0) * np.sqrt(T - 1) / np.sqrt(1 - g3 * srb + (g4 - 1) / 4 * srb**2)))
    psr = float(stats.norm.cdf(srb * np.sqrt(T - 1) / np.sqrt(1 - g3 * srb + (g4 - 1) / 4 * srb**2)))
    # Reality check de White contra no operar (benchmark = 0)
    rng = np.random.default_rng(0)
    medias = M.values.mean(0)
    V = np.sqrt(T) * medias.max()
    L = max(5, int(T ** (1 / 3)))
    cuenta = 0
    Mc = M.values - medias
    for _ in range(bootstrap):
        idx = _bootstrap_estacionario(T, L, rng)
        if np.sqrt(T) * Mc[idx].mean(0).max() >= V:
            cuenta += 1
    p_white = (cuenta + 1) / (bootstrap + 1)
    r = Resultado()
    r.metrica("Variantes probadas", N)
    r.metrica("Mejor variante", M.columns[mejor])
    r.metrica("Sharpe de la mejor (anual)", sh[mejor])
    r.metrica(
        "PBO (prob. de sobreajuste)",
        pbo,
        "> 0,5: la mejor in-sample tiende a quedar en la mitad de abajo fuera de muestra",
    )
    r.metrica("Sharpe probabilístico (vs 0)", psr)
    r.metrica(
        "Sharpe deflactado",
        dsr,
        "probabilidad de que el Sharpe verdadero supere al máximo esperable por azar entre N variantes",
    )
    r.metrica("Reality check de White (p)", p_white, "H0: ninguna variante le gana a no operar")
    r.barras("Sharpe anual de cada variante", list(M.columns), {"Sharpe": sh}, horizontal=True)
    cnt, bordes = np.histogram(logits, bins=20)
    r.barras(
        "Distribución del logit del rango fuera de muestra (izquierda de 0 = sobreajuste)",
        [fmt((a + b) / 2, 2) for a, b in zip(bordes[:-1], bordes[1:], strict=True)],
        {"combinaciones": cnt},
    )
    if pbo > 0.5 or dsr < 0.5:
        r.veredicto(
            f"La mejor variante ({M.columns[mejor]}) es probablemente sobreajuste: PBO {fmt(pbo)}, Sharpe deflactado {fmt(dsr)}.",
            "rojo",
        )
    elif p_white < 0.05 and dsr > 0.95:
        r.veredicto(
            f"La mejor variante resiste: PBO {fmt(pbo)}, Sharpe deflactado {fmt(dsr)}, White p={fmt(p_white)}.",
            "verde",
        )
    else:
        r.veredicto(
            f"Evidencia mixta: PBO {fmt(pbo)}, Sharpe deflactado {fmt(dsr)}, White p={fmt(p_white)}.",
            "amarillo",
        )
    r.resumen = f"Sobreajuste de {N} variantes de {familia_reglas} en {sid}: la mejor es {M.columns[mejor]} (Sharpe {fmt(sh[mejor])}); PBO={fmt(pbo)}, Sharpe deflactado={fmt(dsr)}, White p={fmt(p_white)}."
    r.datos = {"pbo": pbo, "dsr": dsr, "p_white": p_white}
    return r


# ──────────────────────────────────────────────────────────────────────────
# Apuesta binaria (mercados de predicción)
# ──────────────────────────────────────────────────────────────────────────
@metodo(
    "apuesta_binaria",
    "Contrato binario (Kalshi / Polymarket): valor esperado, Kelly y riesgo de ruina",
    "finanzas",
    "Si mi modelo dice p y el contrato cotiza a precio q, ¿conviene, cuánto apostar y qué tan sensible es a errores en p?",
    params=[
        Param(
            "probabilidad",
            "real",
            "Probabilidad del modelo (p)",
            requerido=True,
            minimo=0.001,
            maximo=0.999,
            ayuda="Ej. la que da probabilidad_evento o montecarlo_umbral",
        ),
        Param(
            "precio",
            "real",
            "Precio del contrato SÍ (q, entre 0 y 1)",
            requerido=True,
            minimo=0.01,
            maximo=0.99,
        ),
        Param("comision", "real", "Comisión por contrato", defecto=0.01, minimo=0, maximo=0.2),
        Param(
            "incertidumbre", "real", "Desvío de tu p (error del modelo)", defecto=0.05, minimo=0, maximo=0.4
        ),
        Param("fraccion_kelly", "real", "Fracción de Kelly", defecto=0.5, minimo=0.05, maximo=1),
        Param("apuestas", "entero", "Apuestas simuladas", defecto=100, minimo=10, maximo=2000),
    ],
    cuando="Antes de entrar a un contrato: la ventaja tiene que sobrevivir a la comisión y a la incertidumbre de tu propia probabilidad.",
    supuestos=["Apuestas independientes con la misma ventaja; p bien calibrada (medila con Brier antes)."],
    trampas=[
        "Kelly completo con una p sobreestimada lleva a la ruina: por eso se usa Kelly fraccional.",
        "En eventos muy improbables los contratos suelen estar caros (sesgo favorito-longshot).",
    ],
    referencias=["Kelly (1956)", "Thorp (2006)", "Wolfers y Zitzewitz (2004)", "Snowberg y Wolfers (2010)"],
    etiquetas=[
        "kalshi",
        "polymarket",
        "mercado de predicción",
        "kelly",
        "valor esperado",
        "binaria",
        "apuesta",
    ],
    nivel="basico",
)
def apuesta_binaria(probabilidad, precio, comision, incertidumbre, fraccion_kelly, apuestas):
    p, q, f = probabilidad, precio, comision
    lado = "SÍ" if p > q else "NO"
    pp, qq = (p, q) if lado == "SÍ" else (1 - p, 1 - q)
    costo = qq + f
    ev = pp * 1 - costo
    b = (1 - costo) / costo  # ganancia neta por peso arriesgado
    kelly = max(0.0, (pp * b - (1 - pp)) / b) if b > 0 else 0.0
    k = kelly * fraccion_kelly
    rng = np.random.default_rng(0)
    sims = 4000
    # en cada camino la p verdadera difiere de la del modelo (incertidumbre)
    p_real = np.clip(pp + rng.normal(0, incertidumbre, size=sims), 0.001, 0.999)
    gana = rng.random((sims, apuestas)) < p_real[:, None]
    banca = np.ones(sims)
    minimo = np.ones(sims)
    for t in range(apuestas):
        banca = banca * np.where(gana[:, t], 1 + k * b, 1 - k)
        minimo = np.minimum(minimo, banca)
    r = Resultado()
    r.metrica("Lado conveniente", lado)
    r.metrica("Ventaja (p − precio)", pp - qq)
    r.metrica("Valor esperado por contrato", ev)
    r.metrica("Rendimiento esperado %", ev / costo * 100)
    r.metrica("Kelly completo (% de la banca)", kelly * 100)
    r.metrica(f"Kelly × {fraccion_kelly}", k * 100)
    r.metrica(f"Banca mediana tras {apuestas} apuestas", float(np.median(banca)))
    r.metrica("P(perder más del 50 % en algún momento) %", float(np.mean(minimo < 0.5) * 100))
    r.metrica("P(terminar abajo) %", float(np.mean(banca < 1) * 100))
    ps = np.linspace(
        max(0.01, pp - 3 * max(incertidumbre, 0.02)), min(0.99, pp + 3 * max(incertidumbre, 0.02)), 13
    )
    r.lineas(
        "Valor esperado según cuál sea la p verdadera",
        [fmt(x, 3) for x in ps],
        {"VE por contrato": ps - costo, "cero": np.zeros(len(ps))},
        estilos={"cero": {"guion": "dash"}},
    )
    pcts = np.percentile(np.log(banca), [5, 25, 50, 75, 95])
    r.tabla(
        "Distribución de la banca final (múltiplo de la inicial)",
        ["p5", "p25", "mediana", "p75", "p95"],
        [list(np.exp(pcts))],
    )
    umbral = costo  # p mínima para que valga la pena
    r.metrica("p mínima para que convenga", umbral)
    if ev <= 0:
        r.veredicto(f"Después de la comisión no hay ventaja (VE {fmt(ev)}): no conviene.", "rojo")
    elif pp - incertidumbre < umbral:
        r.veredicto(
            f"Hay ventaja ({fmt(ev)} por contrato) pero no sobrevive a la incertidumbre de tu p (±{fmt(incertidumbre)}): apostá chico o no apuestes.",
            "amarillo",
        )
    else:
        r.veredicto(
            f"Ventaja robusta: VE {fmt(ev)} por contrato en el lado {lado}; tamaño sugerido {fmt(k * 100, 3)} % de la banca (Kelly × {fraccion_kelly}).",
            "verde",
        )
    r.resumen = f"Contrato a {fmt(q)} con p={fmt(p)}: lado {lado}, VE {fmt(ev)} por contrato, Kelly {fmt(kelly * 100, 3)} % (usar {fmt(k * 100, 3)} %); P(caída > 50 %) {fmt(float(np.mean(minimo < 0.5) * 100), 3)} %."
    return r


# ──────────────────────────────────────────────────────────────────────────
# Triple barrera + meta-etiquetado
# ──────────────────────────────────────────────────────────────────────────
@metodo(
    "triple_barrera",
    "Triple barrera y meta-etiquetado (¿toca el objetivo antes que el stop?)",
    "finanzas",
    "Desde hoy, ¿qué es más probable: subir X desvíos, bajar Y desvíos, o que no pase nada en h períodos? ¿Algún patrón lo anticipa?",
    params=[
        P_SERIE("sid", "Precio"),
        P_FREQ_F,
        Param("objetivo", "real", "Toma de ganancia (× volatilidad)", defecto=1.0, minimo=0.25, maximo=10),
        Param("stop", "real", "Stop (× volatilidad)", defecto=1.0, minimo=0.25, maximo=10),
        Param("horizonte", "entero", "Barrera vertical (períodos)", defecto=20, minimo=2, maximo=250),
        Param("ventana_vol", "entero", "Ventana de volatilidad", defecto=20, minimo=5, maximo=250),
        P_SERIES("contexto", "Series de contexto (features extra)", minimo=0, maximo=8, requerido=False),
        Param(
            "modelo",
            "opcion",
            "Clasificador",
            defecto="random_forest",
            opciones=["logit", "random_forest", "gbm"],
        ),
    ],
    cuando="Activos: convierte el pronóstico en la pregunta que importa para operar, con barreras escaladas por volatilidad.",
    supuestos=[
        "Las etiquetas se solapan en el tiempo: la evaluación usa entrenamiento purgado (deja h períodos de margen)."
    ],
    trampas=[
        "Validación cruzada común con etiquetas solapadas filtra el futuro (López de Prado 2018, cap. 7).",
        "Con pocas barreras tocadas, las tasas por clase son ruidosas.",
        "Anticipar que se TOCA una barrera no es anticipar la dirección: si la volatilidad vuelve a su media, tocar arriba y tocar abajo son igual de predecibles. Compará con la P de tocar el stop.",
    ],
    deps=["sklearn"],
    costo="segundos",
    referencias=["López de Prado (2018), caps. 3 y 7"],
    etiquetas=["triple barrera", "meta-labeling", "take profit", "stop loss", "etiquetado", "lópez de prado"],
)
def triple_barrera(sid, freq, objetivo, stop, horizonte, ventana_vol, contexto, modelo):
    from sklearn.metrics import roc_auc_score

    from cueva.metodos.familias.ml import _clasificador

    p = precios([sid], freq, minimo=ventana_vol + horizonte + 120)[sid]
    lp = np.log(p.values)
    ret = np.diff(lp, prepend=np.nan)
    vol = pd.Series(ret).rolling(ventana_vol).std().values
    n = len(p)
    etiqueta = np.full(n, np.nan)
    tiempo = np.full(n, np.nan)
    rend = np.full(n, np.nan)
    for t in range(ventana_vol, n - 1):
        if not np.isfinite(vol[t]):
            continue
        up, dn = objetivo * vol[t] * np.sqrt(horizonte), -stop * vol[t] * np.sqrt(horizonte)
        fin = min(n - 1, t + horizonte)
        camino = lp[t + 1 : fin + 1] - lp[t]
        if t + horizonte >= n:
            break
        tu = np.argmax(camino >= up) if (camino >= up).any() else None
        td = np.argmax(camino <= dn) if (camino <= dn).any() else None
        if tu is not None and (td is None or tu < td):
            etiqueta[t], tiempo[t], rend[t] = 1, tu + 1, camino[tu]
        elif td is not None:
            etiqueta[t], tiempo[t], rend[t] = -1, td + 1, camino[td]
        else:
            etiqueta[t], tiempo[t], rend[t] = 0, horizonte, camino[-1]
    lab = pd.Series(etiqueta, index=p.index)
    validos = lab.dropna()
    r = Resultado()
    filas = []
    for v, nom in ((1, "toca objetivo"), (-1, "toca stop"), (0, "vence sin tocar")):
        m = validos == v
        filas.append(
            [
                nom,
                int(m.sum()),
                float(m.mean() * 100),
                float(np.nanmean(tiempo[lab.values == v])) if m.any() else None,
                float(np.nanmean(rend[lab.values == v]) * 100) if m.any() else None,
            ]
        )
    r.tabla(
        f"Resultados históricos (barreras ±{objetivo}/{stop} × vol × √h, h={horizonte})",
        ["resultado", "casos", "%", "períodos promedio", "rend. medio %"],
        filas,
    )
    # meta-etiquetado: ¿se puede anticipar "toca objetivo"?
    feats = {
        "mom_5": pd.Series(lp, index=p.index).diff(5),
        "mom_20": pd.Series(lp, index=p.index).diff(20),
        "mom_60": pd.Series(lp, index=p.index).diff(60),
        "vol": pd.Series(vol, index=p.index),
        "vol_rel": pd.Series(vol, index=p.index) / pd.Series(vol, index=p.index).rolling(120).mean(),
        "dist_max_60": pd.Series(lp, index=p.index) - pd.Series(lp, index=p.index).rolling(60).max(),
    }
    for c in contexto or []:
        from cueva.datos import series as S

        x = S.cargar(c, "diaria" if freq in ("diaria", "nativa") else freq).reindex(p.index, method="ffill")
        feats[f"{c}_Δ20"] = np.log(x.where(x > 0)).diff(20) if (x > 0).all() else x.diff(20)
    X = pd.DataFrame(feats)
    y = (lab == 1).astype(float).where(lab.notna())
    d = pd.concat([X, y.rename("y")], axis=1).dropna()
    if len(d) < 150 or d["y"].nunique() < 2:
        r.advertir("No hay suficientes casos para el meta-etiquetado.")
        r.resumen = f"Triple barrera en {sid}: " + ", ".join(f"{f[0]} {fmt(f[2], 3)} %" for f in filas) + "."
        return r
    clf = _clasificador(modelo)
    n_d = len(d)
    corte = int(n_d * 0.6)
    probs, reales = [], []
    paso = max(1, (n_d - corte) // 8)
    for ini in range(corte, n_d, paso):
        fin_train = ini - horizonte  # purga: las etiquetas de train no pisan el tramo de prueba
        if fin_train < 100:
            continue
        m = clf().fit(d.iloc[:fin_train, :-1].values, d["y"].values[:fin_train])
        bloque = d.iloc[ini : ini + paso]
        probs.extend(m.predict_proba(bloque.iloc[:, :-1].values)[:, 1])
        reales.extend(bloque["y"].values)
    probs, reales = np.array(probs), np.array(reales)
    base = float(d["y"].values[:corte].mean())
    auc = float(roc_auc_score(reales, probs)) if len(set(reales)) > 1 else float("nan")
    brier = float(np.mean((probs - reales) ** 2))
    brier0 = float(np.mean((base - reales) ** 2))
    r.metrica("P histórica de tocar el objetivo %", float((validos == 1).mean() * 100))
    r.metrica("AUC fuera de muestra (purgado)", auc)
    r.metrica("Brier skill vs frecuencia histórica", 1 - brier / brier0 if brier0 > 0 else None)
    final = clf().fit(d.iloc[:, :-1].values, d["y"].values)
    p_hoy = float(final.predict_proba(X.iloc[[-1]].fillna(0).values)[0, 1])
    r.metrica("P(toca el objetivo primero) hoy %", p_hoy * 100)
    # lift por quintil de probabilidad
    q = pd.qcut(probs, 5, labels=False, duplicates="drop")
    filas_q = [
        [
            f"Q{k + 1}",
            int((q == k).sum()),
            float(probs[q == k].mean() * 100),
            float(reales[q == k].mean() * 100),
        ]
        for k in sorted(set(q))
    ]
    r.tabla(
        "¿El modelo separa? Frecuencia real por quintil de probabilidad prevista",
        ["quintil", "casos", "P prevista %", "frecuencia real %"],
        filas_q,
    )
    r.lineas(
        f"{sid} y etiquetas",
        p.index,
        {sid: p.values, "etiqueta (+1/0/−1)": lab.values},
        y2=["etiqueta (+1/0/−1)"],
    )
    sirve = auc == auc and auc > 0.55 and (1 - brier / brier0) > 0
    r.veredicto(
        f"El meta-etiquetado {'anticipa' if sirve else 'NO anticipa'} cuándo se toca el objetivo (AUC {fmt(auc)}).",
        "verde" if sirve else "amarillo",
    )
    r.resumen = f"Triple barrera en {sid} (±{objetivo}/{stop} vol, h={horizonte}): objetivo {fmt(filas[0][2], 3)} %, stop {fmt(filas[1][2], 3)} %, vence {fmt(filas[2][2], 3)} %. Meta-etiquetado AUC {fmt(auc)}; P(objetivo primero) hoy {fmt(p_hoy * 100, 3)} %."
    return r


# ──────────────────────────────────────────────────────────────────────────
# Estudio de eventos de mercado (retornos anormales)
# ──────────────────────────────────────────────────────────────────────────
@metodo(
    "eventos_mercado",
    "Estudio de eventos de mercado (retornos anormales acumulados)",
    "causal",
    "¿Cómo reaccionó el activo a anuncios o eventos, descontando lo que hizo el mercado?",
    params=[
        P_SERIE("sid", "Activo"),
        P_SERIE("mercado", "Índice de mercado"),
        Param("freq", "opcion", "Frecuencia", defecto="diaria", opciones=["diaria", "semanal", "mensual"]),
        Param(
            "fechas",
            "texto",
            "Fechas de los eventos",
            ayuda="Separadas por coma (si se deja vacío usa la categoría de la Línea de Tiempo)",
        ),
        Param(
            "categoria",
            "opcion",
            "…o categoría de la Línea de Tiempo",
            defecto="monetario",
            opciones=["monetario", "fiscal", "crisis", "politico", "internacional", "externo"],
        ),
        Param("estimacion", "entero", "Ventana de estimación", defecto=120, minimo=20, maximo=500),
        Param("antes", "entero", "Períodos antes", defecto=5, minimo=0, maximo=60),
        Param("despues", "entero", "Períodos después", defecto=10, minimo=1, maximo=120),
    ],
    cuando="Anuncios de política, licitaciones, balances, elecciones: el efecto propio del evento sobre un activo.",
    supuestos=[
        "Modelo de mercado r_i = α + β r_m estimado antes del evento; la ventana de estimación no se solapa con el evento."
    ],
    trampas=[
        "Eventos anticipados por el mercado muestran el efecto ANTES de la fecha: mirá los períodos previos.",
        "Con pocos eventos, el test transversal es débil.",
    ],
    referencias=["MacKinlay (1997)", "Campbell, Lo y MacKinlay (1997), cap. 4"],
    etiquetas=["event study", "retornos anormales", "car", "anuncios", "modelo de mercado"],
)
def eventos_mercado(sid, mercado, freq, fechas, categoria, estimacion, antes, despues):
    from scipy import stats

    p = precios([sid, mercado], freq, minimo=estimacion + antes + despues + 10)
    R = rendimientos(p)
    if fechas:
        lista = [(f.strip(), f.strip()) for f in fechas.split(",") if f.strip()]
    else:
        lista = [(e["fecha"], e["titulo"]) for e in eventos_en(R.index[0], R.index[-1], [categoria])]
    if not lista:
        raise ErrorMetodo("No hay eventos en el rango: cargá fechas propias.")
    rel = list(range(-antes, despues + 1))
    cars, filas = [], []
    for f, tit in lista:
        t0 = int(np.searchsorted(R.index.values, np.datetime64(pd.Timestamp(f))))
        if t0 - antes - estimacion < 0 or t0 + despues >= len(R):
            filas.append([f, tit, "fuera de rango", None, None])
            continue
        est = R.iloc[t0 - antes - estimacion : t0 - antes]
        b, a = np.polyfit(est[mercado].values, est[sid].values, 1)
        sd = np.std(est[sid].values - (a + b * est[mercado].values), ddof=2)
        ven = R.iloc[t0 - antes : t0 + despues + 1]
        ar = ven[sid].values - (a + b * ven[mercado].values)
        car = np.cumsum(ar)
        cars.append(car)
        t = car[-1] / (sd * np.sqrt(len(ar)))
        filas.append([f, tit, "incluido", float(car[-1] * 100), float(2 * stats.norm.sf(abs(t)))])
    if not cars:
        raise ErrorMetodo("Ningún evento tiene ventanas completas.")
    C = np.array(cars) * 100
    media = C.mean(0)
    ee = C.std(0, ddof=1) / np.sqrt(len(C)) if len(C) > 1 else np.zeros_like(media)
    r = Resultado()
    r.lineas(
        f"Retorno anormal acumulado promedio (%), n={len(C)}",
        rel,
        {"CAR medio": media, "IC inf.": media - 1.96 * ee, "IC sup.": media + 1.96 * ee},
        estilos={"IC inf.": {"guion": "dot"}, "IC sup.": {"guion": "dot"}},
        marcas=[{"x": 0, "texto": "evento"}],
    )
    r.tabla("Eventos", ["fecha", "evento", "estado", "CAR %", "p"], filas, resaltar_p="p")
    tt = stats.ttest_1samp(C[:, -1], 0) if len(C) > 1 else None
    r.metrica("Eventos", len(C))
    r.metrica(f"CAR medio a +{despues} %", float(media[-1]))
    r.metrica("CAR medio en t=0 %", float(media[antes]))
    if tt is not None:
        r.metrica("p (t transversal)", float(tt.pvalue))
    r.resumen = (
        f"Eventos de mercado sobre {sid} vs {mercado}: {len(C)} eventos, CAR medio {fmt(float(media[-1]), 3)} % a +{despues}"
        + (f" (p={fmt(float(tt.pvalue))})." if tt is not None else ".")
    )
    return r


# ──────────────────────────────────────────────────────────────────────────
# Contagio: índice de Diebold-Yilmaz
# ──────────────────────────────────────────────────────────────────────────
def _fevd_generalizada(res, h):
    S = res.sigma_u
    k = S.shape[0]
    Phi = res.ma_rep(h - 1)
    num = np.zeros((k, k))
    den = np.zeros(k)
    for H_ in range(h):
        A = Phi[H_]
        num += (A @ S) ** 2 / np.diag(S)[None, :]
        den += np.diag(A @ S @ A.T)
    th = num / den[:, None]
    return th / th.sum(1, keepdims=True)


@metodo(
    "contagio_diebold_yilmaz",
    "Contagio y derrames de volatilidad (Diebold-Yilmaz)",
    "multivariados",
    "¿Cuánto de lo que le pasa a cada mercado viene de los otros, quién transmite y quién recibe, y cómo cambió en el tiempo?",
    params=[
        P_SERIES("sids", "Mercados / activos (2 a 10)", minimo=2, maximo=10),
        P_FREQ,
        Param("transf", "opcion", "Transformación", defecto="dif_log", opciones=list(P_TRANSF.opciones)),
        Param("rezagos", "entero", "Rezagos del VAR", defecto=2, minimo=1, maximo=12),
        Param("horizonte", "entero", "Horizonte H", defecto=10, minimo=2, maximo=40),
        Param("ventana", "entero", "Ventana móvil (0 = sin)", defecto=0, minimo=0, maximo=1000),
    ],
    cuando="Contagio entre países, entre activos argentinos (bonos, acciones, dólar), o entre sectores.",
    supuestos=["Descomposición generalizada (Pesaran-Shin): no depende del orden de las variables."],
    trampas=["En ventanas cortas el VAR está mal estimado: el índice móvil es ruidoso."],
    costo="segundos",
    referencias=["Diebold y Yilmaz (2009, 2012, 2014)"],
    etiquetas=["contagio", "spillover", "diebold-yilmaz", "derrames", "conectividad", "red"],
)
def contagio_diebold_yilmaz(sids, freq, transf, rezagos, horizonte, ventana):
    from statsmodels.tsa.api import VAR

    df, et = panel(sids, freq, transf, minimo=rezagos * len(sids) + 40)
    nombres = [et[s] for s in sids]
    res = VAR(df.values).fit(rezagos)
    th = _fevd_generalizada(res, horizonte) * 100
    k = len(sids)
    total = (th.sum() - np.trace(th)) / k
    desde = th.sum(1) - np.diag(th)  # recibe de otros
    hacia = th.sum(0) - np.diag(th)  # transmite a otros
    r = Resultado()
    r.mapa_calor(
        "Matriz de derrames (% de la varianza de la fila explicada por la columna)",
        nombres,
        nombres,
        th,
        rango=None,
    )
    r.tabla(
        "Transmisores y receptores",
        ["mercado", "recibe de otros %", "transmite a otros %", "neto"],
        sorted(
            [[nombres[i], desde[i], hacia[i], hacia[i] - desde[i]] for i in range(k)], key=lambda f: -f[3]
        ),
    )
    r.metrica("Índice total de derrames %", total)
    r.barras("Derrame neto (transmite − recibe)", nombres, {"neto": hacia - desde})
    if ventana:
        tot = []
        fechas = []
        paso = max(1, (len(df) - ventana) // 120)
        for t in range(ventana, len(df) + 1, paso):
            try:
                rr = VAR(df.values[t - ventana : t]).fit(rezagos)
                tt = _fevd_generalizada(rr, horizonte) * 100
                tot.append((tt.sum() - np.trace(tt)) / k)
                fechas.append(df.index[t - 1])
            except Exception:
                continue
        if tot:
            r.lineas(f"Índice total de derrames en ventanas de {ventana}", fechas, {"derrames %": tot})
            r.serie(
                f"spillover_{sids[0]}"[:40], fechas, tot, "Índice total de derrames de Diebold-Yilmaz (móvil)"
            )
    top = int(np.argmax(hacia - desde))
    r.resumen = f"Derrames entre {', '.join(nombres)}: índice total {fmt(total, 3)} %; principal transmisor neto {nombres[top]} ({fmt(float(hacia[top] - desde[top]), 3)} pp)."
    return r


# ──────────────────────────────────────────────────────────────────────────
# DCC-GARCH: correlaciones dinámicas
# ──────────────────────────────────────────────────────────────────────────
@metodo(
    "dcc_garch",
    "Correlaciones dinámicas (DCC-GARCH)",
    "volatilidad",
    "¿La correlación entre dos activos sube en las crisis (cuando más falta hace la diversificación)?",
    params=[P_SERIES("sids", "Activos (2 a 6)", minimo=2, maximo=6), P_FREQ_F],
    cuando="Diversificación, coberturas, contagio: la correlación promedio esconde que en las crisis todo se mueve junto.",
    supuestos=[
        "GARCH(1,1) con t por activo; DCC(1,1) de Engle (2002) estimado en dos etapas por cuasi-máxima verosimilitud."
    ],
    trampas=[
        "a + b cerca de 1 ⇒ correlaciones muy persistentes; con a ≈ 0 la correlación es constante (CCC)."
    ],
    deps=["arch"],
    costo="segundos",
    referencias=["Engle (2002)", "Engle y Sheppard (2001)"],
    etiquetas=["dcc", "garch multivariado", "correlación dinámica", "contagio", "diversificación"],
    nivel="avanzado",
)
def dcc_garch(sids, freq):
    from arch import arch_model
    from scipy.optimize import minimize

    p = precios(sids, freq if freq != "nativa" else "diaria", minimo=200)
    R = rendimientos(p) * 100
    Z, vols = [], []
    for s in sids:
        res = arch_model(R[s].values, mean="Constant", vol="GARCH", p=1, q=1, dist="t").fit(disp="off")
        Z.append(res.std_resid)
        vols.append(res.conditional_volatility)
    Z = np.column_stack(Z)
    T, k = Z.shape
    Qbar = np.cov(Z.T)

    def correr(a, b):
        Q = Qbar.copy()
        ll = 0.0
        Rs = np.empty((T, k, k))
        for t in range(T):
            if t:
                z = Z[t - 1][:, None]
                Q = (1 - a - b) * Qbar + a * (z @ z.T) + b * Q
            d = np.sqrt(np.diag(Q))
            Rt = Q / np.outer(d, d)
            Rs[t] = Rt
            sign, logdet = np.linalg.slogdet(Rt)
            ll += -0.5 * (logdet + Z[t] @ np.linalg.solve(Rt, Z[t]) - Z[t] @ Z[t])
        return ll, Rs

    def obj(th):
        a, b = th
        if a < 0 or b < 0 or a + b >= 0.999:
            return 1e10
        return -correr(a, b)[0]

    opt = minimize(
        obj, [0.03, 0.95], method="Nelder-Mead", options={"maxiter": 300, "xatol": 1e-4, "fatol": 1e-3}
    )
    a, b = opt.x
    _, Rs = correr(a, b)
    r = Resultado()
    r.metrica("a (reacción)", a)
    r.metrica("b (persistencia)", b)
    r.metrica("a + b", a + b)
    series = {}
    filas = []
    for i in range(k):
        for j in range(i + 1, k):
            rho = Rs[:, i, j]
            series[f"{sids[i]}–{sids[j]}"] = rho
            alta = np.concatenate([vols[i], [np.nan]])[:T] > np.nanpercentile(vols[i], 80)
            filas.append(
                [
                    f"{sids[i]}–{sids[j]}",
                    float(np.corrcoef(Z[:, i], Z[:, j])[0, 1]),
                    float(rho.mean()),
                    float(rho[alta].mean()),
                    float(rho[~alta].mean()),
                    float(rho[-1]),
                ]
            )
    r.lineas("Correlaciones condicionales", R.index, series)
    r.tabla(
        "Correlación: promedio, en alta volatilidad (top 20 %) y en calma",
        ["par", "incondicional", "DCC media", "en alta vol.", "en calma", "hoy"],
        filas,
    )
    for nom, v in list(series.items())[:3]:
        r.serie(f"dcc_{nom}".replace("–", "_")[:40], R.index, v, f"Correlación dinámica DCC {nom}")
    sube = [f[0] for f in filas if f[3] - f[4] > 0.1]
    r.veredicto(
        (
            f"La correlación sube en alta volatilidad en: {', '.join(sube)}. La diversificación falla cuando más se la necesita."
            if sube
            else "La correlación no sube sistemáticamente en alta volatilidad."
        ),
        "amarillo" if sube else "verde",
    )
    r.resumen = (
        f"DCC-GARCH entre {', '.join(sids)}: a={fmt(a)}, b={fmt(b)}; "
        + "; ".join(f"{f[0]} calma {fmt(f[4])} vs tensión {fmt(f[3])}" for f in filas[:3])
        + "."
    )
    return r


# ──────────────────────────────────────────────────────────────────────────
# Colas extremas (EVT, picos sobre umbral)
# ──────────────────────────────────────────────────────────────────────────
@metodo(
    "colas_extremas",
    "Colas extremas (teoría de valores extremos, picos sobre umbral)",
    "volatilidad",
    "¿Qué tan grande puede ser la peor caída de cada cuántos años (devaluaciones, crashes)?",
    params=[
        P_SERIE("sid", "Serie (precio o nivel)"),
        Param("freq", "opcion", "Frecuencia", defecto="diaria", opciones=FREQS),
        Param("cola", "opcion", "Cola", defecto="perdidas", opciones=["perdidas", "ganancias"]),
        Param("umbral", "real", "Umbral (cuantil)", defecto=0.95, minimo=0.8, maximo=0.995),
    ],
    cuando="Riesgo de cola: la normal subestima la frecuencia de saltos como los de 2002, 2014, 2018, 2019.",
    supuestos=["Los excesos sobre un umbral alto siguen una Pareto generalizada (Pickands-Balkema-de Haan)."],
    trampas=[
        "El resultado depende del umbral: mirá la estabilidad de ξ (gráfico de Hill).",
        "Con agrupamiento de volatilidad conviene aplicarlo a residuos estandarizados de un GARCH.",
    ],
    referencias=["McNeil, Frey y Embrechts (2015), cap. 5", "Coles (2001)"],
    etiquetas=["evt", "valores extremos", "colas", "pareto generalizada", "hill", "devaluación", "crash"],
)
def colas_extremas(sid, freq, cola, umbral):
    from scipy import stats

    if freq in ("diaria", "semanal", "nativa"):
        p = precios([sid], freq, minimo=250)[sid]
        x = np.log(p).diff().dropna().values
    else:
        s, _ = serie(sid, freq, "dif_log", minimo=100)
        x = s.values
    perd = -x if cola == "perdidas" else x
    u = np.quantile(perd, umbral)
    exc = perd[perd > u] - u
    if len(exc) < 20:
        raise ErrorMetodo("Menos de 20 excedentes: bajá el umbral.")
    xi, _, beta = stats.genpareto.fit(exc, floc=0)
    n, nu = len(perd), len(exc)
    A = ANUAL.get(freq, 12)
    filas = []
    for q in (0.99, 0.995, 0.999):
        var_q = (
            u + beta / xi * (((n / nu) * (1 - q)) ** (-xi) - 1)
            if xi != 0
            else u - beta * np.log((n / nu) * (1 - q))
        )
        es = (var_q + beta - xi * u) / (1 - xi) if xi < 1 else np.nan
        filas.append(
            [
                f"{q:.1%}",
                float(var_q * 100),
                float(es * 100),
                float(np.quantile(perd, q) * 100),
                float(stats.norm.ppf(q, perd.mean(), perd.std()) * 100),
            ]
        )
    r = Resultado()
    r.tabla(
        f"VaR y ES en la cola de {cola} (%, por período)",
        ["nivel", "VaR (EVT)", "ES (EVT)", "VaR empírico", "VaR normal"],
        filas,
    )
    niveles = []
    for anios in (1, 5, 10, 25, 50):
        m = anios * A
        z = u + beta / xi * (((n / nu) / m) ** (-xi) - 1) if xi != 0 else u + beta * np.log(m * nu / n)
        niveles.append([f"cada {anios} años", float(z * 100)])
    r.tabla(
        "Niveles de retorno: la peor variación esperable…", ["período de retorno", "variación %"], niveles
    )
    r.metrica("ξ (índice de cola)", xi, "> 0: cola pesada (Pareto); = 0: exponencial; < 0: acotada")
    r.metrica("β (escala)", beta)
    r.metrica("Umbral %", u * 100)
    r.metrica("Excedentes", nu)
    orden = np.sort(perd[perd > 0])[::-1]
    ks = np.arange(10, min(len(orden) - 1, 400), max(1, min(len(orden), 400) // 60))
    hill = [1 / np.mean(np.log(orden[:k] / orden[k])) for k in ks]
    r.lineas("Estimador de Hill del índice de cola α (buscá una zona estable)", list(ks), {"α de Hill": hill})
    teo = stats.genpareto.ppf((np.arange(1, nu + 1) - 0.5) / nu, xi, scale=beta)
    r.dispersion(
        "QQ de los excedentes contra la Pareto generalizada",
        teo,
        np.sort(exc),
        "cuantil teórico",
        "excedente observado",
        recta=(1, 0),
    )
    r.veredicto(
        f"Cola {'pesada' if xi > 0.05 else 'liviana'} (ξ={fmt(xi)}): el VaR 99,9 % por EVT es {fmt(filas[2][1], 3)} % contra {fmt(filas[2][4], 3)} % de la normal.",
        "amarillo" if xi > 0.05 else "verde",
    )
    r.resumen = f"EVT en la cola de {cola} de {sid}: ξ={fmt(xi)}; VaR 99 % {fmt(filas[0][1], 3)} %, 99,9 % {fmt(filas[2][1], 3)} %; peor variación esperable cada 10 años {fmt(niveles[2][1], 3)} %."
    return r


# ──────────────────────────────────────────────────────────────────────────
# Curva de rendimientos: Nelson-Siegel
# ──────────────────────────────────────────────────────────────────────────
def _numeros(texto: str) -> list[float]:
    """«0.25, 1, 2» o «0,25; 1; 2» o «0.25 1 2» → [0.25, 1, 2]."""
    if ";" in texto:
        partes = [x.strip().replace(",", ".") for x in texto.split(";")]
    elif "," in texto and "." in texto or texto.count(",") >= 1 and " " not in texto.strip():
        partes = [x.strip() for x in texto.split(",")]
    else:
        partes = texto.replace(",", " ").split()
    return [float(x) for x in partes if x]


@metodo(
    "curva_nelson_siegel",
    "Curva de rendimientos (Nelson-Siegel): nivel, pendiente y curvatura",
    "finanzas",
    "¿Cómo se movió la curva de tasas (o de rendimientos de bonos) en sus tres factores?",
    params=[
        P_SERIES("sids", "Tasas / TIR por plazo (3 a 15)", minimo=3, maximo=15),
        Param(
            "plazos",
            "texto",
            "Plazos en años, mismo orden",
            requerido=True,
            ayuda="Ej. 0.25, 0.5, 1, 2, 5, 10",
        ),
        Param("freq", "opcion", "Frecuencia", defecto="mensual", opciones=["diaria", "semanal", "mensual"]),
        Param("lambda_ns", "real", "λ (decaimiento; 0 = 0,0609×12)", defecto=0.0, minimo=0, maximo=5),
    ],
    cuando="Bonos soberanos, curva de LECAPs/BONCAPs, tasas del BCRA por plazo.",
    supuestos=["λ fijo (Diebold-Li): los factores se estiman por MCO fecha a fecha."],
    trampas=["Con pocos plazos (3-4), la curvatura está mal identificada."],
    referencias=["Nelson y Siegel (1987)", "Diebold y Li (2006)"],
    etiquetas=[
        "curva de rendimientos",
        "nelson-siegel",
        "bonos",
        "tasas",
        "diebold-li",
        "nivel",
        "pendiente",
    ],
)
def curva_nelson_siegel(sids, plazos, freq, lambda_ns):
    try:
        tau = np.array(_numeros(plazos))
    except ValueError as e:
        raise ErrorMetodo("Plazos inválidos: números separados por coma.") from e
    if len(tau) != len(sids):
        raise ErrorMetodo(f"Hay {len(sids)} series y {len(tau)} plazos.")
    df, et = panel(sids, freq if freq != "semanal" else "diaria", "nivel", minimo=12)
    if freq == "semanal":
        df = df.resample("W-FRI").last().dropna()
    lam = lambda_ns or 0.0609 * 12
    L1 = (1 - np.exp(-lam * tau)) / (lam * tau)
    X = np.column_stack([np.ones_like(tau), L1, L1 - np.exp(-lam * tau)])
    B = np.linalg.lstsq(X, df.values.T, rcond=None)[0].T
    ajuste = B @ X.T
    rmse = float(np.sqrt(np.mean((df.values - ajuste) ** 2)))
    r = Resultado()
    r.lineas(
        "Factores de Nelson-Siegel",
        df.index,
        {"nivel (β₀)": B[:, 0], "pendiente (β₁)": B[:, 1], "curvatura (β₂)": B[:, 2]},
    )
    grilla = np.linspace(tau.min(), tau.max(), 40)
    Lg = (1 - np.exp(-lam * grilla)) / (lam * grilla)
    Xg = np.column_stack([np.ones_like(grilla), Lg, Lg - np.exp(-lam * grilla)])
    hace = min(len(df) - 1, {"diaria": 252, "semanal": 52, "mensual": 12}.get(freq, 12))
    r.lineas(
        "Curva ajustada: hoy vs hace un año",
        [fmt(g, 2) for g in grilla],
        {"hoy": Xg @ B[-1], "hace un año": Xg @ B[-1 - hace]},
    )
    r.tabla(
        "Ajuste del último dato",
        ["plazo", "observado", "ajustado"],
        [[t_, float(o), float(a_)] for t_, o, a_ in zip(tau, df.values[-1], ajuste[-1], strict=True)],
    )
    for i, nom in enumerate(("nivel", "pendiente", "curvatura")):
        r.serie(f"ns_{nom}", df.index, B[:, i], f"Factor {nom} de Nelson-Siegel")
    r.metrica("Nivel hoy", B[-1, 0])
    r.metrica("Pendiente hoy (−β₁ = largo − corto)", -B[-1, 1])
    r.metrica("RMSE del ajuste", rmse)
    r.resumen = f"Nelson-Siegel con {len(sids)} plazos (λ={fmt(lam)}): nivel {fmt(B[-1, 0])}, pendiente {fmt(-B[-1, 1])}, curvatura {fmt(B[-1, 2])}; RMSE {fmt(rmse)}."
    return r
