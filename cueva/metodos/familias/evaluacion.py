"""Evaluación y combinación: el torneo de modelos y la curva de especificaciones.

El torneo es el lugar donde se cruzan las tradiciones: un ARIMA-equivalente (AR lineal), un
Lasso, un bosque, un boosting y una red compiten en la MISMA matriz de diseño, con el MISMO
protocolo fuera de muestra, contra los MISMOS benchmarks. Y se reporta la combinación simple,
que en la práctica (Bates-Granger, competencias M) es difícil de batir.
"""

from __future__ import annotations

import itertools

import numpy as np

from cueva.metodos import validacion as V
from cueva.metodos.contrato import ErrorMetodo, Param, Resultado
from cueva.metodos.familias.ml import armar_diseno, evaluar, fabrica, params_diseno
from cueva.metodos.insumos import P_SERIE, P_SERIES, P_TRANSF, fila_p, fmt, panel
from cueva.metodos.registro import faltantes, metodo, obtener

F = "evaluacion"

CANDIDATOS = ["ar_lineal", "ridge", "lasso", "elastic_net", "knn", "svr", "arbol", "random_forest", "extra_trees", "hist_gbm", "xgboost", "lightgbm", "mlp"]
NOMBRES = {
    "ar_lineal": "AR lineal (MCO)",
    "ridge": "Ridge",
    "lasso": "Lasso",
    "elastic_net": "Elastic Net",
    "knn": "K vecinos",
    "svr": "SVR",
    "arbol": "Árbol",
    "random_forest": "Bosque aleatorio",
    "extra_trees": "Extra Trees",
    "hist_gbm": "Boosting (hist.)",
    "xgboost": "XGBoost",
    "lightgbm": "LightGBM",
    "mlp": "Red densa (MLP)",
}


def _disponible(nombre: str) -> bool:
    mid = {"ar_lineal": "ml_ridge"}.get(nombre, f"ml_{nombre}")
    try:
        return not faltantes(obtener(mid))
    except KeyError:
        return False


@metodo(
    "torneo_modelos",
    "Torneo de modelos (econometría vs ML vs redes) con combinación",
    F,
    "De todos los modelos, ¿cuál predice mejor fuera de muestra, y alguno le gana de verdad al resto?",
    params=params_diseno() + [Param("modelos", "opciones", "Competidores", defecto=["ar_lineal", "ridge", "lasso", "random_forest", "hist_gbm", "svr", "knn"], opciones=CANDIDATOS)],
    cuando="Siempre antes de elegir un modelo para pronosticar o para un informe: es la prueba de fuego.",
    supuestos=["Todos los competidores ven exactamente la misma información en cada origen."],
    trampas=[
        "Elegir el ganador y reportar SU error sobreestima la precisión (sesgo de selección): mirá si la diferencia con el segundo es significativa.",
        "La combinación simple suele ganar o empatar: si un modelo complejo no le gana, no lo uses solo.",
    ],
    deps=["sklearn"],
    costo="minutos",
    referencias=["Bates y Granger (1969)", "Diebold y Mariano (1995)", "Makridakis, Spiliotis y Assimakopoulos (2020), M4", "Stock y Watson (2004)"],
    etiquetas=["torneo", "comparación", "benchmark", "combinación", "diebold-mariano", "ensamble", "horse race"],
    nivel="intermedio",
)
def torneo_modelos(dep, indeps, freq, transf, transf_x, rezagos_y, rezagos_x, horizonte, estacionales, n_test, modelos):
    d = armar_diseno(dep, indeps, freq, transf, transf_x, rezagos_y, rezagos_x, horizonte, estacionales)
    corridas = {}
    omitidos = []
    for m in modelos or ["ar_lineal", "ridge", "random_forest"]:
        if not _disponible(m):
            omitidos.append(m)
            continue
        try:
            bt, res = evaluar(d, fabrica(m, {}), n_test, nombre=m)
            corridas[m] = (bt, res)
        except Exception as e:  # un competidor que falla no tira el torneo
            omitidos.append(f"{m} ({type(e).__name__})")
    if not corridas:
        raise ErrorMetodo("Ningún competidor pudo correr.")
    ref = next(iter(corridas.values()))[0]
    real, rw, med = ref.real, ref.rw, ref.media
    preds = {NOMBRES[m]: bt.pred for m, (bt, _) in corridas.items()}
    preds["Combinación (promedio simple)"] = np.mean(list(preds.values()), axis=0)
    preds["Paseo aleatorio"] = rw
    preds["Media histórica"] = med
    filas = []
    for nombre, p in preds.items():
        m = V.metricas(real, p, ref.escala_mase)
        filas.append([nombre, m["RMSE"], m["MAE"], m.get("MASE"), V.r2_fuera_de_muestra(real, p, med), V.acierto_direccion(real, p, rw)])
    filas.sort(key=lambda f: f[1])
    mejor = filas[0][0]
    r = Resultado()
    r.tabla(f"Ranking fuera de muestra (h={d.h}, {len(real)} pronósticos, mismo diseño para todos)", ["modelo", "RMSE", "MAE", "MASE", "R² oos vs media", "acierto dirección %"], filas)
    dm_filas = []
    for nombre, p in preds.items():
        if nombre == mejor:
            continue
        st, pv = V.diebold_mariano(real - preds[mejor], real - p, d.h)
        dm_filas.append([nombre, st, pv, fila_p(pv)])
    r.tabla(f"Diebold-Mariano: {mejor} contra cada uno (estadístico < 0 ⇒ gana {mejor})", ["rival", "DM", "p", ""], dm_filas, resaltar_p="p")
    empatados = [f[0] for f in dm_filas if not (f[2] == f[2] and f[2] < 0.1)]
    r.barras("RMSE fuera de muestra (menor es mejor)", [f[0] for f in filas], {"RMSE": [f[1] for f in filas]}, horizontal=True)
    top = [f[0] for f in filas[:4]]
    r.lineas("Pronósticos fuera de muestra de los mejores", ref.fechas, {"realizado": real, **{n: preds[n] for n in top}}, estilos={n: {"guion": "dot"} for n in top})
    r.metrica("Ganador", mejor)
    r.metrica("RMSE del ganador", filas[0][1])
    r.metrica("Empatados con el ganador (DM p ≥ 0,1)", len(empatados))
    if omitidos:
        r.advertir("No corrieron: " + ", ".join(omitidos))
    bench = [f for f in filas if f[0] in ("Paseo aleatorio", "Media histórica")]
    if mejor in ("Paseo aleatorio", "Media histórica"):
        r.veredicto(f"Gana un benchmark ingenuo ({mejor}): con esta información, ningún modelo agrega capacidad predictiva.", "rojo")
    elif len(empatados) >= 3:
        r.veredicto(f"{mejor} queda primero, pero {len(empatados)} rivales no se distinguen estadísticamente: elegí por simplicidad o usá la combinación.", "amarillo")
    else:
        r.veredicto(f"{mejor} gana y la diferencia con la mayoría de los rivales es significativa.", "verde")
    r.resumen = f"Torneo de {len(corridas)} modelos para {d.etiquetas[d.dep]} (h={d.h}): gana {mejor} (RMSE {fmt(filas[0][1])}); benchmarks: " + ", ".join(f"{b[0]} {fmt(b[1])}" for b in bench) + f". Empatados estadísticamente con el ganador: {', '.join(empatados[:5]) or 'ninguno'}."
    r.datos = {"ranking": [[f[0], f[1]] for f in filas]}
    return r


@metodo(
    "curva_especificaciones",
    "Curva de especificaciones (robustez de un coeficiente)",
    F,
    "¿El efecto de X sobre Y sobrevive a todas las especificaciones razonables, o depende de una elección arbitraria?",
    params=[
        P_SERIE("dep", "Dependiente (Y)"),
        P_SERIE("interes", "Variable de interés (X)"),
        P_SERIES("controles", "Controles candidatos (se prueban todas las combinaciones)", minimo=0, maximo=6, requerido=False),
        Param("freq", "opcion", "Frecuencia", defecto="mensual", opciones=["mensual", "trimestral", "anual"]),
        Param("transformaciones", "opciones", "Transformaciones a probar", defecto=["dif_log", "dif", "pct"], opciones=list(P_TRANSF.opciones)),
        Param("rezagos", "opciones", "Rezagos de X a probar", defecto=["0", "1", "3"], opciones=["0", "1", "2", "3", "6", "12"]),
        Param("muestras", "opciones", "Muestras", defecto=["completa", "sin_2002", "desde_2003"], opciones=["completa", "sin_2002", "desde_2003", "sin_2020", "primera_mitad", "segunda_mitad"]),
    ],
    cuando="Antes de escribir 'X afecta a Y' en un informe: muestra cuán frágil es el resultado.",
    supuestos=["Todas las especificaciones probadas son igual de defendibles a priori."],
    trampas=["Reportar sólo la especificación favorable es p-hacking; esta curva es el antídoto."],
    referencias=["Simonsohn, Simmons y Nelson (2020)", "Leamer (1983), 'Let's take the con out of econometrics'"],
    etiquetas=["specification curve", "robustez", "multiverso", "p-hacking", "leamer", "sensibilidad"],
    costo="segundos",
)
def curva_especificaciones(dep, interes, controles, freq, transformaciones, rezagos, muestras):
    import pandas as pd
    import statsmodels.api as sm

    ctr = [c for c in (controles or []) if c not in (dep, interes)]
    combos_c = [list(c) for k in range(len(ctr) + 1) for c in itertools.combinations(ctr, k)]
    filas = []
    for tr in transformaciones:
        try:
            df, et = panel([dep, interes, *ctr], freq, tr, minimo=24)
        except ErrorMetodo:
            continue
        for lag in (int(x) for x in rezagos):
            for mu in muestras:
                sub = df
                if mu == "sin_2002":
                    sub = df[(df.index < "2001-07-01") | (df.index > "2002-12-31")]
                elif mu == "desde_2003":
                    sub = df[df.index >= "2003-01-01"]
                elif mu == "sin_2020":
                    sub = df[(df.index < "2020-03-01") | (df.index > "2020-12-31")]
                elif mu == "primera_mitad":
                    sub = df.iloc[: len(df) // 2]
                elif mu == "segunda_mitad":
                    sub = df.iloc[len(df) // 2 :]
                for cs in combos_c:
                    X = pd.concat([sub[interes].shift(lag).rename("x"), sub[cs]], axis=1)
                    dd = pd.concat([sub[dep].rename("y"), X], axis=1).dropna()
                    if len(dd) < 20:
                        continue
                    res = sm.OLS(dd["y"], sm.add_constant(dd.drop(columns="y"))).fit(cov_type="HAC", cov_kwds={"maxlags": 4})
                    filas.append([tr, lag, mu, ", ".join(cs) or "—", res.params["x"], res.bse["x"], res.pvalues["x"], len(dd)])
    if len(filas) < 3:
        raise ErrorMetodo("Muy pocas especificaciones válidas.")
    filas.sort(key=lambda f: f[4])
    coefs = np.array([f[4] for f in filas])
    ps = np.array([f[6] for f in filas])
    ee = np.array([f[5] for f in filas])
    r = Resultado()
    xs = list(range(1, len(filas) + 1))
    r.lineas("Coeficiente de X en cada especificación (ordenadas)", xs, {"coef": coefs, "IC inf.": coefs - 1.96 * ee, "IC sup.": coefs + 1.96 * ee, "cero": np.zeros(len(xs))}, estilos={"IC inf.": {"guion": "dot"}, "IC sup.": {"guion": "dot"}, "cero": {"guion": "dash"}})
    pos_sig = float(np.mean((coefs > 0) & (ps < 0.05)) * 100)
    neg_sig = float(np.mean((coefs < 0) & (ps < 0.05)) * 100)
    r.metrica("Especificaciones", len(filas))
    r.metrica("Coeficiente mediano", float(np.median(coefs)))
    r.metrica("% positivas y significativas", pos_sig)
    r.metrica("% negativas y significativas", neg_sig)
    r.metrica("% con el signo de la mediana", float(np.mean(np.sign(coefs) == np.sign(np.median(coefs))) * 100))
    r.tabla("Todas las especificaciones", ["transf.", "rezago", "muestra", "controles", "coef", "EE", "p", "n"], filas[:300], resaltar_p="p")
    # qué decisión mueve más el resultado
    df_f = pd.DataFrame(filas, columns=["transf", "rezago", "muestra", "controles", "coef", "ee", "p", "n"])
    infl = []
    for col in ("transf", "rezago", "muestra", "controles"):
        g = df_f.groupby(col)["coef"].median()
        infl.append([col, float(g.max() - g.min()), str(g.idxmax()), str(g.idxmin())])
    infl.sort(key=lambda f: -f[1])
    r.tabla("Qué decisión mueve más el coeficiente", ["decisión", "rango de medianas", "valor que lo maximiza", "valor que lo minimiza"], infl)
    robusto = max(pos_sig, neg_sig) >= 80
    r.veredicto(f"{'Robusto' if robusto else 'Frágil'}: {fmt(max(pos_sig, neg_sig), 3)} % de las especificaciones dan el mismo signo y significancia. La decisión que más pesa es «{infl[0][0]}».", "verde" if robusto else ("amarillo" if max(pos_sig, neg_sig) >= 50 else "rojo"))
    r.resumen = f"Curva de especificaciones del efecto de {interes} sobre {dep}: {len(filas)} especificaciones, mediana {fmt(float(np.median(coefs)))}; {fmt(pos_sig, 3)} % positivas significativas y {fmt(neg_sig, 3)} % negativas significativas. Más influyente: {infl[0][0]}."
    return r
