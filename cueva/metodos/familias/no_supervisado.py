"""No supervisado: componentes principales, agrupamiento de series y de PERÍODOS (regímenes
sin etiqueta), y detección de anomalías cruzada con la Línea de Tiempo."""

from __future__ import annotations

import numpy as np

from cueva.metodos.contrato import Param, Resultado
from cueva.metodos.insumos import (
    P_SERIE,
    P_SERIES,
    P_TRANSF,
    PERIODO,
    evento_cercano,
    eventos_en,
    fmt,
    panel,
    serie,
)
from cueva.metodos.registro import metodo

F = "no_supervisado"
P_DLOG = Param("transf", "opcion", "Transformación", defecto="dif_log", opciones=list(P_TRANSF.opciones))
FREQS = ["diaria", "mensual", "trimestral", "anual"]


@metodo(
    "componentes_principales",
    "Componentes principales (PCA)",
    F,
    "¿Cuántas fuerzas comunes mueven a un grupo de series y cuál es su 'índice' resumen?",
    params=[
        P_SERIES("sids", "Series (3 a 40)", minimo=3, maximo=40),
        Param("freq", "opcion", "Frecuencia", defecto="mensual", opciones=FREQS),
        P_DLOG,
        Param("componentes", "entero", "Componentes a mostrar", defecto=3, minimo=1, maximo=10),
    ],
    cuando="Curva de rendimientos (nivel, pendiente, curvatura), índices de condiciones financieras, reducir 30 predictores a 3.",
    supuestos=["Relaciones lineales; se estandariza cada serie (si no, manda la de mayor varianza)."],
    trampas=[
        "Los componentes no tienen nombre económico garantizado: interpretalos por las cargas.",
        "En niveles con tendencia, el primer componente es 'la tendencia' y no dice nada.",
    ],
    deps=["sklearn"],
    referencias=["Jolliffe (2002)", "Litterman y Scheinkman (1991)"],
    etiquetas=["pca", "componentes principales", "factores", "reducción de dimensión", "cargas"],
    nivel="basico",
)
def componentes_principales(sids, freq, transf, componentes):
    from sklearn.decomposition import PCA

    df, et = panel(sids, freq, transf, minimo=24)
    z = (df - df.mean()) / df.std()
    k = min(componentes, len(sids))
    pca = PCA(n_components=min(len(sids), len(df))).fit(z.values)
    var = pca.explained_variance_ratio_
    r = Resultado()
    r.barras(
        "Varianza explicada por componente",
        [f"CP{i + 1}" for i in range(len(var))],
        {"individual %": var * 100, "acumulada %": np.cumsum(var) * 100},
    )
    nombres = [et[s] for s in sids]
    r.mapa_calor(
        "Cargas (cómo pesa cada serie en cada componente)",
        nombres,
        [f"CP{i + 1}" for i in range(k)],
        pca.components_[:k].T,
        rango=None,
    )
    sc = pca.transform(z.values)[:, :k]
    r.lineas("Componentes en el tiempo", df.index, {f"CP{i + 1}": sc[:, i] for i in range(k)})
    for i in range(k):
        r.serie(
            f"cp{i + 1}_{sids[0]}"[:40],
            df.index,
            sc[:, i],
            f"Componente principal {i + 1} de {len(sids)} series",
        )
    kaiser = int(np.sum(pca.explained_variance_ > 1))
    r.metrica("CP1 explica %", var[0] * 100)
    r.metrica(f"Primeros {k} explican %", float(np.sum(var[:k]) * 100))
    r.metrica("Componentes con autovalor > 1 (Kaiser)", kaiser)
    top = np.argsort(np.abs(pca.components_[0]))[::-1][:3]
    r.resumen = f"PCA de {len(sids)} series: CP1 explica {fmt(var[0] * 100, 3)} % (pesan sobre todo {', '.join(nombres[i] for i in top)}); {kaiser} componentes pasan el criterio de Kaiser."
    return r


@metodo(
    "clusters_series",
    "Agrupamiento de series por comportamiento",
    F,
    "¿Qué series se mueven parecido y forman grupos (ej. activos que conviene no tener juntos)?",
    params=[
        P_SERIES("sids", "Series (4 a 60)", minimo=4, maximo=60),
        Param("freq", "opcion", "Frecuencia", defecto="mensual", opciones=FREQS),
        P_DLOG,
        Param("grupos", "entero", "Grupos (0 = elegir por silueta)", defecto=0, minimo=0, maximo=12),
        Param(
            "enlace",
            "opcion",
            "Enlace jerárquico",
            defecto="average",
            opciones=["average", "complete", "single", "ward"],
        ),
    ],
    cuando="Diversificación de cartera, armar bloques temáticos, encontrar series redundantes.",
    supuestos=["Distancia de correlación d = √(2(1−ρ)) sobre las series transformadas."],
    trampas=[
        "La correlación cambia con los regímenes: agrupá por subperíodos para ver si los grupos son estables."
    ],
    deps=["sklearn"],
    referencias=["Mantegna (1999)", "López de Prado (2016), HRP"],
    etiquetas=["cluster", "clustering", "jerárquico", "dendrograma", "correlación", "diversificación"],
)
def clusters_series(sids, freq, transf, grupos, enlace):
    from scipy.cluster.hierarchy import fcluster, leaves_list, linkage
    from scipy.spatial.distance import squareform
    from sklearn.metrics import silhouette_score

    df, et = panel(sids, freq, transf, minimo=24)
    c = df.corr().values
    D = np.sqrt(np.clip(2 * (1 - c), 0, None))
    np.fill_diagonal(D, 0)
    Z = linkage(squareform(D, checks=False), method=enlace if enlace != "ward" else "ward")
    if grupos:
        k = grupos
    else:
        mejor = (-1, 2)
        for kk in range(2, min(10, len(sids) - 1) + 1):
            lab = fcluster(Z, kk, "maxclust")
            if len(set(lab)) > 1:
                s = silhouette_score(D, lab, metric="precomputed")
                if s > mejor[0]:
                    mejor = (s, kk)
        k = mejor[1]
    lab = fcluster(Z, k, "maxclust")
    orden = leaves_list(Z)
    nombres = [et[s] for s in sids]
    r = Resultado()
    r.mapa_calor(
        "Correlaciones ordenadas por el árbol (los bloques son los grupos)",
        [nombres[i] for i in orden],
        [nombres[i] for i in orden],
        c[np.ix_(orden, orden)],
    )
    filas = []
    for g in sorted(set(lab)):
        miembros = [i for i in range(len(sids)) if lab[i] == g]
        sub = c[np.ix_(miembros, miembros)]
        intra = (sub.sum() - len(miembros)) / max(1, len(miembros) * (len(miembros) - 1))
        filas.append([g, len(miembros), ", ".join(nombres[i] for i in miembros), intra])
    r.tabla("Grupos", ["grupo", "series", "miembros", "correlación media interna"], filas)
    r.metrica("Grupos", k)
    try:
        r.metrica("Silueta", silhouette_score(D, lab, metric="precomputed"))
    except ValueError:
        pass
    r.resumen = f"{len(sids)} series en {k} grupos: " + " | ".join(f[2] for f in filas) + "."
    r.datos = {"grupos": {nombres[i]: int(lab[i]) for i in range(len(sids))}}
    return r


@metodo(
    "clusters_periodos",
    "Agrupamiento de PERÍODOS (regímenes sin etiqueta)",
    F,
    "¿En qué 'climas' estuvo la economía (o el mercado), y en cuál estamos hoy?",
    params=[
        P_SERIES("sids", "Series que describen el clima", minimo=2, maximo=20),
        Param("freq", "opcion", "Frecuencia", defecto="mensual", opciones=FREQS),
        P_DLOG,
        Param("grupos", "entero", "Regímenes (0 = elegir por BIC)", defecto=0, minimo=0, maximo=8),
        Param("suavizado", "entero", "Media móvil previa (obs.)", defecto=3, minimo=1, maximo=24),
        Param(
            "algoritmo",
            "opcion",
            "Algoritmo",
            defecto="mezcla_gaussiana",
            opciones=["mezcla_gaussiana", "kmeans"],
        ),
    ],
    cuando="Para identificar regímenes con varias variables a la vez (inflación + brecha + tasa) sin suponer un modelo dinámico.",
    supuestos=[
        "Cada régimen es una nube de puntos (gaussiana en el caso de la mezcla) en el espacio de las variables."
    ],
    trampas=[
        "No usa el orden temporal: los regímenes pueden 'parpadear'. El suavizado previo ayuda; un Markov los modela de verdad."
    ],
    deps=["sklearn"],
    referencias=["Hamilton (2016), regímenes", "Mulvey y Liu (2016)"],
    etiquetas=["regímenes", "clusters", "gmm", "kmeans", "estados", "clima", "períodos", "momentos"],
)
def clusters_periodos(sids, freq, transf, grupos, suavizado, algoritmo):
    from sklearn.cluster import KMeans
    from sklearn.mixture import GaussianMixture

    df, et = panel(sids, freq, transf, minimo=40)
    df = df.rolling(suavizado).mean().dropna() if suavizado > 1 else df
    z = ((df - df.mean()) / df.std()).values
    if algoritmo == "mezcla_gaussiana":
        if grupos:
            k = grupos
        else:
            bics = {
                kk: GaussianMixture(kk, covariance_type="full", random_state=0, n_init=3).fit(z).bic(z)
                for kk in range(1, 7)
            }
            k = min(bics, key=bics.get)
            k = max(k, 2)
        m = GaussianMixture(k, covariance_type="full", random_state=0, n_init=5).fit(z)
        lab = m.predict(z)
        prob = m.predict_proba(z)
    else:
        k = grupos or 3
        m = KMeans(k, n_init=10, random_state=0).fit(z)
        lab = m.labels_
        prob = None
    r = Resultado()
    nombres = [et[s] for s in sids]
    filas = []
    for g in range(k):
        msk = lab == g
        filas.append(
            [
                f"R{g + 1}",
                int(msk.sum()),
                float(msk.mean() * 100),
                *[float(df.values[msk, j].mean()) for j in range(len(sids))],
            ]
        )
    r.tabla(
        "Perfil de cada régimen (promedio de cada variable)",
        ["régimen", "obs.", "% del tiempo", *nombres],
        filas,
    )
    # duración media de los episodios
    cambios = np.r_[True, lab[1:] != lab[:-1]]
    r.metrica("Regímenes", k)
    r.metrica("Episodios", int(cambios.sum()))
    r.metrica("Régimen actual", f"R{lab[-1] + 1}")
    T = np.zeros((k, k))
    for a, b in zip(lab[:-1], lab[1:], strict=True):
        T[a, b] += 1
    T = T / np.maximum(T.sum(1, keepdims=True), 1)
    r.mapa_calor(
        "Frecuencia de transición entre regímenes (fila → columna)",
        [f"R{i + 1}" for i in range(k)],
        [f"R{i + 1}" for i in range(k)],
        T,
        rango=(0, 1),
    )
    r.lineas("Régimen asignado a cada período", df.index, {"régimen": lab + 1})
    if prob is not None:
        r.lineas("Probabilidad de cada régimen", df.index, {f"P(R{g + 1})": prob[:, g] for g in range(k)})
    # eventos por régimen
    filas_e = []
    i = 0
    while i < len(lab):
        j = i
        while j + 1 < len(lab) and lab[j + 1] == lab[i]:
            j += 1
        if j - i + 1 >= 3:
            evs = eventos_en(df.index[i], df.index[j])
            filas_e.append(
                [
                    f"R{lab[i] + 1}",
                    str(df.index[i].date()),
                    str(df.index[j].date()),
                    j - i + 1,
                    "; ".join(e["titulo"] for e in evs[:2]) or "—",
                ]
            )
        i = j + 1
    r.tabla(
        "Episodios (≥ 3 períodos) y eventos de la Línea de Tiempo",
        ["régimen", "desde", "hasta", "obs.", "eventos"],
        filas_e[-30:],
    )
    r.serie(
        f"regimen_{sids[0]}"[:40],
        df.index,
        lab + 1,
        f"Régimen (clusters de períodos) con {', '.join(nombres)}",
    )
    r.resumen = (
        f"{k} regímenes con {', '.join(nombres)}: hoy en R{lab[-1] + 1} ("
        + ", ".join(f"{nombres[j]}={fmt(filas[lab[-1]][3 + j])}" for j in range(len(sids)))
        + f"); {int(cambios.sum())} episodios."
    )
    return r


@metodo(
    "anomalias",
    "Detección de anomalías (STL robusto + bosque de aislamiento)",
    F,
    "¿Qué períodos fueron atípicos y coinciden con algún evento histórico?",
    params=[
        P_SERIE(),
        Param("freq", "opcion", "Frecuencia", defecto="mensual", opciones=FREQS),
        P_DLOG,
        Param("umbral", "real", "Umbral (desvíos robustos)", defecto=3.5, minimo=2, maximo=10),
        P_SERIES("contexto", "Series de contexto (para el bosque)", minimo=0, maximo=10, requerido=False),
    ],
    cuando="Limpiar datos antes de modelar, o encontrar episodios que merecen una ficha en la Línea de Tiempo.",
    trampas=["En Argentina, lo 'anómalo' a veces es el régimen: corré también quiebres y Markov."],
    deps=["sklearn"],
    referencias=["Liu, Ting y Zhou (2008)", "Cleveland et al. (1990)"],
    etiquetas=["anomalías", "outliers", "isolation forest", "atípicos", "z robusto"],
    nivel="basico",
)
def anomalias(sid, freq, transf, umbral, contexto):
    from sklearn.ensemble import IsolationForest

    s, et = serie(sid, freq, transf, minimo=36)
    per = PERIODO.get(freq, 1)
    if per > 1 and len(s) >= 3 * per:
        from statsmodels.tsa.seasonal import STL

        resid = STL(s, period=per, robust=True).fit().resid
    else:
        resid = s - s.rolling(7, center=True, min_periods=3).median()
    med = np.median(resid)
    mad = np.median(np.abs(resid - med)) * 1.4826 or 1
    z = (resid - med) / mad
    marca = np.abs(z) > umbral
    r = Resultado()
    if contexto:
        df, _ = panel([sid, *contexto], freq, transf, minimo=36)
        iso = IsolationForest(n_estimators=300, contamination="auto", random_state=0).fit(df.values)
        sc = -iso.score_samples(df.values)
        r.lineas("Puntaje de aislamiento multivariado (más alto = más raro)", df.index, {"puntaje": sc})
        top = df.index[np.argsort(sc)[::-1][:10]]
        r.tabla(
            "Períodos más raros (multivariado)",
            ["fecha", "puntaje", "evento cercano"],
            [
                [str(f.date()), float(sc[df.index.get_loc(f)]), (evento_cercano(f) or {}).get("titulo", "—")]
                for f in top
            ],
        )
    filas = []
    for f in s.index[marca]:
        ev = evento_cercano(f, 3)
        filas.append([str(f.date()), float(s.loc[f]), float(z.loc[f]), ev["titulo"] if ev else "—"])
    r.tabla(
        f"Anomalías (|z robusto| > {umbral})", ["fecha", "valor", "z robusto", "evento ±3 meses"], filas[:60]
    )
    r.lineas(
        f"{et} con anomalías marcadas",
        s.index,
        {et: s.values, "anómalo": np.where(marca, s.values, np.nan)},
        marcas=[{"x": f[0], "texto": f[3] if f[3] != "—" else ""} for f in filas[:15]],
    )
    r.metrica("Anomalías", int(marca.sum()))
    r.metrica("Con evento coincidente", sum(1 for f in filas if f[3] != "—"))
    if not len(filas):
        r.veredicto("No hay anomalías con ese umbral.", "verde")
    r.resumen = (
        f"Anomalías en {et}: {int(marca.sum())} períodos con |z| > {umbral}; {sum(1 for f in filas if f[3] != '—')} coinciden con eventos. "
        + ", ".join(f[0] for f in filas[:8])
    )
    return r
