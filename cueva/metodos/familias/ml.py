"""Aprendizaje automático supervisado sobre series de tiempo.

Todos los modelos comparten:
- La MISMA matriz de diseño (`insumos.Diseno`): rezagos de Y y de X, horizonte h, estacionales.
- La MISMA evaluación (`validacion.origen_movil`): ventana expansiva, sin fuga, contra paseo
  aleatorio y media histórica, con Diebold-Mariano.
- La misma lectura: importancia por permutación medida FUERA de muestra y dependencia parcial
  de la variable más importante.

Así, comparar un Lasso con un XGBoost o una LSTM es comparar peras con peras.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from cueva.metodos import validacion as V
from cueva.metodos.contrato import ErrorMetodo, Param, Resultado
from cueva.metodos.insumos import P_SERIE, P_SERIES, P_TRANSF, Diseno, fmt, panel
from cueva.metodos.registro import metodo

F = "ml"
FREQS = ["diaria", "mensual", "trimestral", "anual"]


def params_diseno(horizonte=1) -> list[Param]:
    """Parámetros comunes a todo modelo predictivo."""
    return [
        P_SERIE("dep", "Objetivo (Y)"),
        P_SERIES(
            "indeps",
            "Predictores (X)",
            minimo=0,
            maximo=20,
            requerido=False,
            ayuda="Vacío = sólo la historia de Y",
        ),
        Param("freq", "opcion", "Frecuencia", defecto="mensual", opciones=FREQS),
        Param(
            "transf",
            "opcion",
            "Transformación de Y",
            defecto="dif_log",
            opciones=list(P_TRANSF.opciones),
            ayuda="Los modelos de ML necesitan series estacionarias: dif_log es lo usual",
        ),
        Param(
            "transf_x", "opcion", "Transformación de X", defecto="dif_log", opciones=list(P_TRANSF.opciones)
        ),
        Param("rezagos_y", "entero", "Rezagos de Y", defecto=3, minimo=1, maximo=36),
        Param("rezagos_x", "entero", "Rezagos de cada X", defecto=1, minimo=1, maximo=24),
        Param(
            "horizonte", "entero", "Horizonte h (pronóstico directo)", defecto=horizonte, minimo=1, maximo=36
        ),
        Param("estacionales", "bool", "Dummies estacionales", defecto=False),
        Param("n_test", "entero", "Obs. de prueba (0 = 20 %)", defecto=0, minimo=0, maximo=500),
    ]


def armar_diseno(
    dep, indeps, freq, transf, transf_x, rezagos_y, rezagos_x, horizonte, estacionales
) -> Diseno:
    return Diseno(dep, indeps, freq, transf, rezagos_y, rezagos_x, horizonte, estacionales, transf_x=transf_x)


# ──────────────────────────────────────────────────────────────────────────
# Fábricas de modelos
# ──────────────────────────────────────────────────────────────────────────
def fabrica(nombre: str, hp: dict):
    """Devuelve una función sin argumentos que construye el modelo NUEVO (escalado incluido)."""
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    def con_escala(m):
        return lambda: make_pipeline(StandardScaler(), m())

    if nombre == "ridge":
        from sklearn.linear_model import RidgeCV
        from sklearn.model_selection import TimeSeriesSplit

        return con_escala(lambda: RidgeCV(alphas=np.logspace(-3, 3, 25), cv=TimeSeriesSplit(4)))
    if nombre == "lasso":
        from sklearn.linear_model import LassoCV
        from sklearn.model_selection import TimeSeriesSplit

        return con_escala(lambda: LassoCV(cv=TimeSeriesSplit(4), alphas=40, max_iter=5000))
    if nombre == "elastic_net":
        from sklearn.linear_model import ElasticNetCV
        from sklearn.model_selection import TimeSeriesSplit

        return con_escala(
            lambda: ElasticNetCV(l1_ratio=[0.2, 0.5, 0.8], cv=TimeSeriesSplit(4), alphas=30, max_iter=5000)
        )
    if nombre == "knn":
        from sklearn.neighbors import KNeighborsRegressor

        return con_escala(lambda: KNeighborsRegressor(n_neighbors=hp.get("vecinos", 10), weights="distance"))
    if nombre == "svr":
        from sklearn.svm import SVR

        return con_escala(
            lambda: SVR(kernel=hp.get("kernel", "rbf"), C=hp.get("C", 1.0), epsilon=hp.get("epsilon", 0.1))
        )
    if nombre == "arbol":
        from sklearn.tree import DecisionTreeRegressor

        return lambda: DecisionTreeRegressor(
            max_depth=hp.get("profundidad", 4), min_samples_leaf=hp.get("min_hoja", 5), random_state=0
        )
    if nombre == "random_forest":
        from sklearn.ensemble import RandomForestRegressor

        return lambda: RandomForestRegressor(
            n_estimators=hp.get("arboles", 300),
            max_depth=hp.get("profundidad") or None,
            min_samples_leaf=hp.get("min_hoja", 3),
            max_features=0.5,
            n_jobs=-1,
            random_state=0,
        )
    if nombre == "extra_trees":
        from sklearn.ensemble import ExtraTreesRegressor

        return lambda: ExtraTreesRegressor(
            n_estimators=hp.get("arboles", 300),
            min_samples_leaf=hp.get("min_hoja", 3),
            max_features=0.5,
            n_jobs=-1,
            random_state=0,
        )
    if nombre == "gbm":
        from sklearn.ensemble import GradientBoostingRegressor

        return lambda: GradientBoostingRegressor(
            n_estimators=hp.get("arboles", 300),
            learning_rate=hp.get("tasa", 0.03),
            max_depth=hp.get("profundidad", 3),
            subsample=0.8,
            random_state=0,
        )
    if nombre == "hist_gbm":
        from sklearn.ensemble import HistGradientBoostingRegressor

        return lambda: HistGradientBoostingRegressor(
            max_iter=hp.get("arboles", 300),
            learning_rate=hp.get("tasa", 0.05),
            max_depth=hp.get("profundidad", 3),
            min_samples_leaf=hp.get("min_hoja", 10),
            random_state=0,
        )
    if nombre == "xgboost":
        from xgboost import XGBRegressor

        return lambda: XGBRegressor(
            n_estimators=hp.get("arboles", 300),
            learning_rate=hp.get("tasa", 0.03),
            max_depth=hp.get("profundidad", 3),
            subsample=0.8,
            colsample_bytree=0.8,
            reg_lambda=1.0,
            n_jobs=2,
            random_state=0,
            verbosity=0,
        )
    if nombre == "lightgbm":
        from lightgbm import LGBMRegressor

        return lambda: LGBMRegressor(
            n_estimators=hp.get("arboles", 300),
            learning_rate=hp.get("tasa", 0.03),
            num_leaves=hp.get("hojas", 15),
            min_child_samples=hp.get("min_hoja", 10),
            subsample=0.8,
            subsample_freq=1,
            colsample_bytree=0.8,
            random_state=0,
            verbose=-1,
        )
    if nombre == "proceso_gaussiano":
        from sklearn.gaussian_process import GaussianProcessRegressor
        from sklearn.gaussian_process.kernels import RBF, ConstantKernel, WhiteKernel

        return con_escala(
            lambda: GaussianProcessRegressor(
                kernel=ConstantKernel() * RBF(length_scale=np.ones(1) * 3) + WhiteKernel(),
                normalize_y=True,
                random_state=0,
            )
        )
    if nombre == "mlp":
        from sklearn.neural_network import MLPRegressor

        capas = tuple(int(c) for c in str(hp.get("capas", "32,16")).split(",") if c.strip())
        return con_escala(
            lambda: MLPRegressor(
                hidden_layer_sizes=capas,
                alpha=hp.get("alpha", 1e-3),
                learning_rate_init=1e-3,
                max_iter=2000,
                early_stopping=True,
                validation_fraction=0.15,
                n_iter_no_change=30,
                random_state=0,
            )
        )
    if nombre == "ar_lineal":
        from sklearn.linear_model import LinearRegression

        return lambda: LinearRegression()
    raise ErrorMetodo(f"Modelo desconocido: {nombre}")


CADA = {
    "ridge": 3,
    "lasso": 3,
    "elastic_net": 3,
    "random_forest": 6,
    "extra_trees": 6,
    "gbm": 6,
    "hist_gbm": 6,
    "xgboost": 6,
    "lightgbm": 6,
    "proceso_gaussiano": 6,
    "mlp": 6,
    "svr": 2,
}


def evaluar(
    d: Diseno, fab, n_test: int, cada: int | None = None, nombre: str = ""
) -> tuple[V.Backtest, dict]:
    nt = n_test or V.n_test_por_defecto(len(d.X), d.freq)
    nt = min(nt, len(d.X) - d.h - 20)
    y_actual = d.X[d.dep]  # y_t de cada fila (benchmark paseo aleatorio)
    bt = V.origen_movil(d.X, d.y, fab, d.h, nt, y_actual, cada=cada or CADA.get(nombre, 1))
    bt.fechas = d.fechas_objetivo[-nt:]
    return bt, V.resumen_backtest(bt, d.h)


def reportar(r: Resultado, d: Diseno, bt: V.Backtest, res: dict, nombre: str):
    filas = []
    for etq, k in (
        (nombre, "modelo"),
        ("paseo aleatorio", "paseo_aleatorio"),
        ("media histórica", "media_historica"),
    ):
        m = res[k]
        filas.append([etq, m["RMSE"], m["MAE"], m.get("MASE"), m.get("MAPE %")])
    r.tabla(
        f"Evaluación fuera de muestra (origen móvil, h={d.h}, {len(bt.real)} pronósticos)",
        ["modelo", "RMSE", "MAE", "MASE", "MAPE %"],
        filas,
    )
    r.metrica("RMSE fuera de muestra", res["modelo"]["RMSE"])
    r.metrica("R² oos vs paseo", res["r2_oos_vs_rw"], "> 0: le gana al paseo aleatorio")
    r.metrica("R² oos vs media", res["r2_oos_vs_media"], "> 0: le gana a la media histórica")
    r.metrica("Acierto de dirección %", res["direccion_%"])
    dm, p = res["dm_vs_rw"]
    dmm, pm = res["dm_vs_media"]
    r.metrica("DM vs paseo (p)", p)
    r.metrica("DM vs media (p)", pm)
    r.lineas(
        f"Fuera de muestra: {d.etiquetas[d.dep]} a h={d.h}",
        bt.fechas,
        {"realizado": bt.real, nombre: bt.pred, "paseo aleatorio": bt.rw, "media": bt.media},
        estilos={"paseo aleatorio": {"guion": "dot"}, "media": {"guion": "dot"}},
    )
    mejor_bench = min(res["paseo_aleatorio"]["RMSE"], res["media_historica"]["RMSE"])
    gana = res["modelo"]["RMSE"] < mejor_bench
    sig = (p == p and p < 0.1 and dm < 0) or (pm == pm and pm < 0.1 and dmm < 0)
    if gana and sig:
        r.veredicto(
            f"{nombre} le gana a los benchmarks ingenuos fuera de muestra y la diferencia es significativa (DM).",
            "verde",
        )
    elif gana:
        r.veredicto(
            f"{nombre} le gana a los benchmarks pero sin significancia estadística (DM p={fmt(min(p, pm))}): no alcanza para concluir.",
            "amarillo",
        )
    else:
        r.veredicto(
            f"{nombre} NO le gana al mejor benchmark ingenuo fuera de muestra. Más complejidad no está agregando información.",
            "rojo",
        )
    if len(bt.real) < 20:
        r.advertir("Menos de 20 pronósticos fuera de muestra: las métricas son ruidosas.")


def importancia(r: Resultado, d: Diseno, fab, n_test: int, nombre: str):
    """Permutación sobre el tramo de prueba con el modelo entrenado sólo con el pasado."""
    from sklearn.inspection import permutation_importance

    nt = n_test or V.n_test_por_defecto(len(d.X), d.freq)
    corte = len(d.X) - nt
    m = fab()
    m.fit(d.X.values[: corte - d.h + 1], d.y.values[: corte - d.h + 1])
    pi = permutation_importance(
        m,
        d.X.values[corte:],
        d.y.values[corte:],
        n_repeats=8,
        random_state=0,
        scoring="neg_mean_squared_error",
    )
    orden = np.argsort(pi.importances_mean)[::-1][:20]
    cols = d.columnas
    r.barras(
        "Importancia por permutación (aumento del ECM fuera de muestra al desordenar)",
        [cols[i] for i in orden],
        {"importancia": pi.importances_mean[orden]},
        horizontal=True,
    )
    return [cols[i] for i in orden]


def dependencia_parcial(r: Resultado, modelo, d: Diseno, variable: str):
    from sklearn.inspection import partial_dependence

    j = d.columnas.index(variable)
    try:
        pdp = partial_dependence(modelo, d.X.values, [j], grid_resolution=30, kind="average")
        grid = pdp["grid_values"][0] if "grid_values" in pdp else pdp["values"][0]
        r.lineas(
            f"Dependencia parcial: efecto de {variable} sobre la predicción",
            [fmt(g, 3) for g in grid],
            {"predicción media": pdp["average"][0]},
        )
    except Exception:
        pass


def pronostico_final(r: Resultado, d: Diseno, fab):
    m = fab()
    m.fit(d.X.values, d.y.values)
    pred = float(np.ravel(m.predict(d.X_ult.values))[0])
    r.metrica(f"Pronóstico para {d.fecha_pron.date()}", pred)
    return m, pred


def correr_modelo(
    nombre,
    etiqueta,
    dep,
    indeps,
    freq,
    transf,
    transf_x,
    rezagos_y,
    rezagos_x,
    horizonte,
    estacionales,
    n_test,
    hp=None,
    interpretar=True,
):
    d = armar_diseno(dep, indeps, freq, transf, transf_x, rezagos_y, rezagos_x, horizonte, estacionales)
    fab = fabrica(nombre, hp or {})
    bt, res = evaluar(d, fab, n_test, nombre=nombre)
    r = Resultado()
    reportar(r, d, bt, res, etiqueta)
    modelo, pred = pronostico_final(r, d, fab)
    top = []
    if interpretar:
        top = importancia(r, d, fab, n_test, etiqueta)
        if top:
            dependencia_parcial(r, modelo, d, top[0])
    _coeficientes(r, modelo, d)
    r.serie(
        f"oos_{nombre}_{dep}"[:40],
        bt.fechas,
        bt.pred,
        f"Pronósticos fuera de muestra de {etiqueta} para {d.etiquetas[d.dep]}",
    )
    r.resumen = (
        f"{etiqueta} para {d.etiquetas[d.dep]} (h={d.h}, {len(d.columnas)} variables, n={len(d.X)}): RMSE oos {fmt(res['modelo']['RMSE'])} vs paseo {fmt(res['paseo_aleatorio']['RMSE'])} y media {fmt(res['media_historica']['RMSE'])}; "
        f"R² oos vs media {fmt(res['r2_oos_vs_media'])}; DM p={fmt(res['dm_vs_media'][1])}. Pronóstico {d.fecha_pron.date()}: {fmt(pred)}."
        + (f" Variables más importantes: {', '.join(top[:3])}." if top else "")
    )
    r.datos = {
        "rmse": res["modelo"]["RMSE"],
        "r2_oos_media": res["r2_oos_vs_media"],
        "r2_oos_rw": res["r2_oos_vs_rw"],
        "pronostico": pred,
    }
    r.codigo = f"# Validación honesta: origen móvil expansivo\nfrom sklearn.model_selection import TimeSeriesSplit\n# modelo: {nombre}, h={d.h}, columnas: {d.columnas[:6]}…"
    return r


def _coeficientes(r, modelo, d):
    est = modelo.steps[-1][1] if hasattr(modelo, "steps") else modelo
    coef = getattr(est, "coef_", None)
    if coef is not None and np.ndim(coef) == 1 and len(coef) == len(d.columnas):
        orden = np.argsort(np.abs(coef))[::-1][:20]
        r.barras(
            "Coeficientes estandarizados",
            [d.columnas[i] for i in orden],
            {"coef": np.asarray(coef)[orden]},
            horizontal=True,
        )
        if hasattr(est, "alpha_"):
            r.metrica("Penalización elegida (α)", float(est.alpha_))
        nulos = int(np.sum(np.abs(coef) < 1e-10))
        if nulos:
            r.metrica("Variables descartadas (coef = 0)", nulos)


# ──────────────────────────────────────────────────────────────────────────
# Registro de un método por modelo
# ──────────────────────────────────────────────────────────────────────────
P_ARB = Param("arboles", "entero", "Árboles", defecto=300, minimo=20, maximo=2000)
P_PROF = Param("profundidad", "entero", "Profundidad máx.", defecto=3, minimo=1, maximo=20)
P_HOJA = Param("min_hoja", "entero", "Obs. mínimas por hoja", defecto=5, minimo=1, maximo=100)
P_TASA = Param("tasa", "real", "Tasa de aprendizaje", defecto=0.03, minimo=0.001, maximo=1)

TRAMPAS_ML = [
    "Validación cruzada aleatoria en series de tiempo filtra el futuro: acá sólo se usa origen móvil.",
    "Un modelo que no le gana al paseo aleatorio o a la media no aporta, por más sofisticado que sea.",
    "Con pocas decenas de observaciones, los modelos flexibles sobreajustan: preferí regularizados.",
]

MODELOS = [
    (
        "ml_ridge",
        "ridge",
        "Ridge (regresión penalizada L2)",
        "Muchos predictores correlacionados: encoge todos los coeficientes hacia cero.",
        [],
        "basico",
        ["ridge", "regularización", "l2", "shrinkage"],
        ["Hoerl y Kennard (1970)"],
    ),
    (
        "ml_lasso",
        "lasso",
        "Lasso (selección de variables L1)",
        "Muchos candidatos y pocos relevantes: pone coeficientes exactamente en cero.",
        [],
        "basico",
        ["lasso", "selección", "l1", "sparse"],
        ["Tibshirani (1996)"],
    ),
    (
        "ml_elastic_net",
        "elastic_net",
        "Elastic Net",
        "Mezcla Ridge y Lasso: selecciona sin romperse con predictores correlacionados.",
        [],
        "intermedio",
        ["elastic net", "regularización"],
        ["Zou y Hastie (2005)"],
    ),
    (
        "ml_knn",
        "knn",
        "K vecinos más cercanos (analogías históricas)",
        "Busca los períodos pasados más parecidos al actual y promedia lo que pasó después.",
        [Param("vecinos", "entero", "Vecinos", defecto=10, minimo=1, maximo=100)],
        "basico",
        ["knn", "vecinos", "análogos", "patrones"],
        ["Cover y Hart (1967)"],
    ),
    (
        "ml_svr",
        "svr",
        "Máquina de vectores de soporte (SVR)",
        "Relaciones no lineales suaves con pocos datos; robusta a outliers por el margen ε.",
        [
            Param("kernel", "opcion", "Núcleo", defecto="rbf", opciones=["rbf", "linear", "poly"]),
            Param("C", "real", "C (costo)", defecto=1.0, minimo=0.001, maximo=1000),
            Param("epsilon", "real", "ε (margen)", defecto=0.1, minimo=0, maximo=10),
        ],
        "intermedio",
        ["svm", "svr", "support vector", "kernel"],
        ["Drucker et al. (1997)", "Vapnik (1995)"],
    ),
    (
        "ml_arbol",
        "arbol",
        "Árbol de decisión",
        "Reglas legibles del tipo «si la brecha > 50 % y la inflación > 3 %, entonces…».",
        [P_PROF, P_HOJA],
        "basico",
        ["árbol", "cart", "reglas", "decision tree"],
        ["Breiman et al. (1984)"],
    ),
    (
        "ml_random_forest",
        "random_forest",
        "Bosque aleatorio (random forest)",
        "No linealidades e interacciones sin especificarlas; muy robusto con poca afinación.",
        [
            P_ARB,
            Param(
                "profundidad", "entero", "Profundidad máx. (0 = sin límite)", defecto=0, minimo=0, maximo=30
            ),
            P_HOJA,
        ],
        "intermedio",
        ["random forest", "bosque", "bagging", "ensamble"],
        ["Breiman (2001)"],
    ),
    (
        "ml_extra_trees",
        "extra_trees",
        "Árboles extremadamente aleatorios",
        "Como el bosque aleatorio pero con cortes al azar: más varianza reducida, entrena más rápido.",
        [P_ARB, P_HOJA],
        "intermedio",
        ["extra trees", "ensamble", "aleatorio"],
        ["Geurts, Ernst y Wehenkel (2006)"],
    ),
    (
        "ml_gbm",
        "gbm",
        "Gradient boosting (sklearn)",
        "Árboles chicos en secuencia, cada uno corrige el error del anterior.",
        [P_ARB, P_PROF, P_TASA],
        "intermedio",
        ["boosting", "gbm", "gradient boosting"],
        ["Friedman (2001)"],
    ),
    (
        "ml_hist_gbm",
        "hist_gbm",
        "Gradient boosting por histogramas",
        "Boosting rápido que tolera faltantes (estilo LightGBM, incluido en sklearn).",
        [P_ARB, P_PROF, P_TASA, P_HOJA],
        "intermedio",
        ["boosting", "histograma", "faltantes"],
        ["Ke et al. (2017)"],
    ),
    (
        "ml_xgboost",
        "xgboost",
        "XGBoost",
        "El boosting regularizado de referencia en competencias de datos tabulares.",
        [P_ARB, P_PROF, P_TASA],
        "intermedio",
        ["xgboost", "boosting", "árboles"],
        ["Chen y Guestrin (2016)"],
    ),
    (
        "ml_lightgbm",
        "lightgbm",
        "LightGBM",
        "Boosting por hojas, muy rápido; bueno con muchos predictores.",
        [
            P_ARB,
            Param("hojas", "entero", "Hojas por árbol", defecto=15, minimo=2, maximo=255),
            P_TASA,
            P_HOJA,
        ],
        "intermedio",
        ["lightgbm", "boosting", "árboles"],
        ["Ke et al. (2017)"],
    ),
    (
        "ml_proceso_gaussiano",
        "proceso_gaussiano",
        "Proceso gaussiano",
        "Regresión no paramétrica bayesiana: da incertidumbre además de la predicción.",
        [],
        "avanzado",
        ["gaussian process", "kriging", "bayesiano", "kernel"],
        ["Rasmussen y Williams (2006)"],
    ),
    (
        "ml_mlp",
        "mlp",
        "Red neuronal densa (perceptrón multicapa)",
        "Aproximador universal sobre la ventana de rezagos; necesita más datos que los árboles.",
        [
            Param(
                "capas",
                "texto",
                "Capas ocultas",
                defecto="32,16",
                ayuda="Unidades por capa, separadas por coma",
            ),
            Param("alpha", "real", "Regularización L2", defecto=0.001, minimo=0, maximo=10),
        ],
        "intermedio",
        ["red neuronal", "mlp", "perceptrón", "deep learning"],
        ["Goodfellow, Bengio y Courville (2016)"],
    ),
]

DEPS = {"xgboost": ["sklearn", "xgboost"], "lightgbm": ["sklearn", "lightgbm"]}


def _registrar(mid, nombre_modelo, etiqueta, cuando, extra, nivel, etiquetas, refs):
    hp_nombres = [p.nombre for p in extra]
    familia = "redes" if nombre_modelo == "mlp" else F

    def fn(dep, indeps, freq, transf, transf_x, rezagos_y, rezagos_x, horizonte, estacionales, n_test, **hp):
        hp = {k: v for k, v in hp.items() if k in hp_nombres}
        return correr_modelo(
            nombre_modelo,
            etiqueta.split(" (")[0],
            dep,
            indeps,
            freq,
            transf,
            transf_x,
            rezagos_y,
            rezagos_x,
            horizonte,
            estacionales,
            n_test,
            hp,
        )

    metodo(
        mid,
        etiqueta,
        familia,
        f"¿Cuánto se puede predecir {('Y a h períodos')} con {etiqueta.split(' (')[0]}, y le gana a los benchmarks?",
        params=params_diseno() + extra,
        cuando=cuando,
        supuestos=[
            "La relación aprendida en el pasado sigue valiendo en el tramo de prueba (estacionariedad del proceso)."
        ],
        trampas=TRAMPAS_ML,
        deps=DEPS.get(nombre_modelo, ["sklearn"]),
        costo="segundos",
        referencias=refs,
        etiquetas=[*etiquetas, "pronóstico", "machine learning", "predicción"],
        nivel=nivel,
    )(fn)


for _m in MODELOS:
    _registrar(*_m)


# ──────────────────────────────────────────────────────────────────────────
# SHAP exacto para árboles (vía XGBoost)
# ──────────────────────────────────────────────────────────────────────────
@metodo(
    "ml_shap",
    "Explicación SHAP de un modelo de árboles",
    F,
    "¿Qué variables empujan la predicción hacia arriba o hacia abajo, y por qué el modelo pronostica lo que pronostica HOY?",
    params=params_diseno() + [P_ARB, P_PROF, P_TASA],
    cuando="Después de que un modelo de árboles le gane a los benchmarks: para entenderlo y contarlo.",
    supuestos=[
        "Valores de Shapley exactos para árboles (TreeSHAP): reparten la predicción entre las variables."
    ],
    trampas=[
        "SHAP explica el MODELO, no la economía: una variable importante puede ser un proxy de otra.",
        "Con predictores correlacionados, el reparto entre ellos es arbitrario.",
    ],
    deps=["sklearn", "xgboost"],
    costo="segundos",
    referencias=["Lundberg y Lee (2017)", "Lundberg et al. (2020)"],
    etiquetas=["shap", "interpretabilidad", "explicabilidad", "xai", "shapley"],
    nivel="intermedio",
)
def ml_shap(
    dep,
    indeps,
    freq,
    transf,
    transf_x,
    rezagos_y,
    rezagos_x,
    horizonte,
    estacionales,
    n_test,
    arboles,
    profundidad,
    tasa,
):
    import xgboost as xgb

    d = armar_diseno(dep, indeps, freq, transf, transf_x, rezagos_y, rezagos_x, horizonte, estacionales)
    fab = fabrica("xgboost", {"arboles": arboles, "profundidad": profundidad, "tasa": tasa})
    bt, res = evaluar(d, fab, n_test, nombre="xgboost")
    r = Resultado()
    reportar(r, d, bt, res, "XGBoost")
    m = fab()
    m.fit(d.X.values, d.y.values)
    booster = m.get_booster()
    Xall = pd.concat([d.X, d.X_ult])
    contrib = booster.predict(xgb.DMatrix(Xall.values), pred_contribs=True)
    sv, base = contrib[:, :-1], contrib[0, -1]
    cols = d.columnas
    imp = np.abs(sv[:-1]).mean(0)
    orden = np.argsort(imp)[::-1][:15]
    r.barras("Importancia SHAP media |φ|", [cols[i] for i in orden], {"|SHAP|": imp[orden]}, horizontal=True)
    ult = sv[-1]
    o2 = np.argsort(np.abs(ult))[::-1][:12]
    r.barras(
        f"¿Por qué el pronóstico para {d.fecha_pron.date()}? Contribución de cada variable",
        [cols[i] for i in o2],
        {"contribución": ult[o2]},
        horizontal=True,
    )
    pred = float(base + ult.sum())
    r.metrica("Valor base (promedio)", float(base))
    r.metrica(f"Pronóstico {d.fecha_pron.date()}", pred)
    j = orden[0]
    r.dispersion(f"Dependencia SHAP de {cols[j]}", d.X.values[:, j], sv[:-1, j], cols[j], "SHAP")
    r.tabla(
        "Contribuciones del último pronóstico",
        ["variable", "valor actual", "SHAP"],
        [[cols[i], float(d.X_ult.values[0, i]), float(ult[i])] for i in o2],
    )
    r.resumen = f"SHAP (XGBoost) para {d.etiquetas[d.dep]}: las variables que más mueven la predicción son {', '.join(cols[i] for i in orden[:3])}. El pronóstico {fmt(pred)} parte de {fmt(float(base))} y lo empujan sobre todo {', '.join(cols[i] + ' (' + fmt(float(ult[i])) + ')' for i in o2[:3])}."
    return r


# ──────────────────────────────────────────────────────────────────────────
# Probabilidad de eventos (clasificación calibrada)
# ──────────────────────────────────────────────────────────────────────────
@metodo(
    "probabilidad_evento",
    "Probabilidad de un evento (clasificador calibrado)",
    F,
    "¿Qué probabilidad hay de que, en h períodos, Y suba/baje más que un umbral (ej. el riesgo país sube más de 10 %)?",
    params=[
        P_SERIE("dep", "Serie sobre la que se define el evento"),
        P_SERIES("indeps", "Predictores", minimo=0, maximo=20, requerido=False),
        Param("freq", "opcion", "Frecuencia", defecto="mensual", opciones=FREQS),
        Param(
            "evento",
            "opcion",
            "Evento",
            defecto="sube_mas_de",
            opciones=["sube_mas_de", "baja_mas_de", "supera_nivel", "queda_debajo_de"],
        ),
        Param(
            "umbral",
            "real",
            "Umbral",
            defecto=0.05,
            ayuda="Para sube/baja: cambio log acumulado (0,05 ≈ 5 %). Para niveles: el valor de la serie",
        ),
        Param("horizonte", "entero", "Horizonte h", defecto=3, minimo=1, maximo=36),
        Param(
            "modelo",
            "opcion",
            "Clasificador",
            defecto="logit",
            opciones=["logit", "random_forest", "gbm", "svm", "knn"],
        ),
        Param("rezagos", "entero", "Rezagos de cada variable (en dif_log)", defecto=3, minimo=1, maximo=24),
        Param("n_test", "entero", "Obs. de prueba (0 = 25 %)", defecto=0, minimo=0, maximo=500),
    ],
    cuando="Para mercados de predicción y gestión de riesgo: lo que importa es una probabilidad bien calibrada, no un pronóstico puntual.",
    supuestos=["El evento ocurrió suficientes veces en la muestra para aprender (al menos ~15 casos)."],
    trampas=[
        "Con eventos raros, 'nunca pasa' tiene acierto alto: por eso se mide con Brier y contra la frecuencia histórica.",
        "Una probabilidad alta pero mal calibrada es peor que una prudente bien calibrada.",
    ],
    deps=["sklearn"],
    costo="segundos",
    referencias=["Brier (1950)", "Gneiting y Raftery (2007)", "Niculescu-Mizil y Caruana (2005)"],
    etiquetas=[
        "probabilidad",
        "evento",
        "clasificación",
        "calibración",
        "brier",
        "auc",
        "kalshi",
        "mercado de predicción",
        "logit",
    ],
)
def probabilidad_evento(dep, indeps, freq, evento, umbral, horizonte, modelo, rezagos, n_test):
    from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score

    indeps = [s for s in (indeps or []) if s != dep]
    nivel_df, et = panel([dep, *indeps], freq, "nivel", minimo=40)
    if evento in ("sube_mas_de", "baja_mas_de") and (nivel_df[dep] <= 0).any():
        raise ErrorMetodo("Para eventos de suba/baja la serie tiene que ser positiva (se usa el cambio log).")
    h = horizonte
    y = nivel_df[dep]
    if evento == "sube_mas_de":
        obj = (np.log(y.shift(-h)) - np.log(y)) > umbral
    elif evento == "baja_mas_de":
        obj = (np.log(y.shift(-h)) - np.log(y)) < -abs(umbral)
    elif evento == "supera_nivel":
        obj = y.shift(-h) > umbral
    else:
        obj = y.shift(-h) < umbral
    obj = obj.astype(float).where(y.shift(-h).notna())
    feats = {}
    for s in [dep, *indeps]:
        v = nivel_df[s]
        base = np.log(v).diff() if (v > 0).all() else v.diff()
        for k in range(rezagos):
            feats[f"{et[s]} Δ(t−{k})" if k else f"{et[s]} Δ"] = base.shift(k)
        if s == dep and evento in ("supera_nivel", "queda_debajo_de"):
            feats[f"{et[s]} nivel"] = v
    X = pd.DataFrame(feats).dropna()
    Xc = X[obj.loc[X.index].notna()]
    yc = obj.loc[Xc.index].astype(int)
    n = len(Xc)
    if yc.sum() < 8 or (n - yc.sum()) < 8:
        raise ErrorMetodo(
            f"El evento ocurrió {int(yc.sum())} veces de {n}: muy pocas para aprender. Cambiá el umbral o el horizonte."
        )
    nt = n_test or int(min(150, max(12, round(n * 0.25))))
    clf = _clasificador(modelo)
    probs, reales, base_rate, fechas = [], [], [], []
    cada = 1 if modelo == "logit" else 6
    m = None
    for k, i in enumerate(range(n - nt, n)):
        fin = i - h + 1
        if m is None or k % cada == 0:
            ytr = yc.values[:fin]
            if ytr.min() == ytr.max():
                continue
            m = clf()
            m.fit(Xc.values[:fin], ytr)
        probs.append(float(m.predict_proba(Xc.values[i : i + 1])[0, 1]))
        reales.append(int(yc.values[i]))
        base_rate.append(float(yc.values[:fin].mean()))
        fechas.append(Xc.index[i])
    probs, reales, base_rate = np.array(probs), np.array(reales), np.array(base_rate)
    r = Resultado()
    bs = brier_score_loss(reales, probs)
    bs0 = brier_score_loss(reales, base_rate)
    bss = 1 - bs / bs0 if bs0 > 0 else float("nan")
    try:
        auc = roc_auc_score(reales, probs)
    except ValueError:
        auc = float("nan")
    r.metrica("Frecuencia histórica del evento %", float(yc.mean() * 100))
    r.metrica("Brier del modelo", bs, "0 = perfecto")
    r.metrica("Brier de la frecuencia histórica", bs0)
    r.metrica("Brier skill score", bss, "> 0: mejor que usar la frecuencia histórica")
    r.metrica("AUC", auc, "0,5 = azar; 1 = discrimina perfecto")
    try:
        r.metrica("Log loss", log_loss(reales, np.clip(probs, 1e-6, 1 - 1e-6)))
    except ValueError:
        pass
    # calibración por quintiles de probabilidad
    bins = np.unique(np.quantile(probs, np.linspace(0, 1, 6)))
    filas_c = []
    for a, b in zip(bins[:-1], bins[1:], strict=True):
        msk = (probs >= a) & (probs <= b)
        if msk.sum():
            filas_c.append(
                [f"{a:.2f}–{b:.2f}", int(msk.sum()), float(probs[msk].mean()), float(reales[msk].mean())]
            )
    r.tabla(
        "Calibración (prob. prevista vs frecuencia observada)",
        ["tramo", "casos", "prob. media prevista", "frecuencia observada"],
        filas_c,
    )
    r.dispersion(
        "Curva de calibración (sobre la diagonal = bien calibrado)",
        [f[2] for f in filas_c],
        [f[3] for f in filas_c],
        "probabilidad prevista",
        "frecuencia observada",
        recta=(1, 0),
    )
    r.lineas(
        "Probabilidad prevista fuera de muestra vs ocurrencia",
        fechas,
        {"P(evento)": probs, "ocurrió": reales, "frecuencia histórica": base_rate},
        estilos={"frecuencia histórica": {"guion": "dot"}},
    )
    final = clf().fit(Xc.values, yc.values)
    p_hoy = float(final.predict_proba(X.values[-1:])[0, 1])
    r.metrica(f"P(evento) desde {X.index[-1].date()} a {h} períodos", p_hoy)
    desc = {
        "sube_mas_de": f"suba más de {umbral:.0%}",
        "baja_mas_de": f"baje más de {abs(umbral):.0%}",
        "supera_nivel": f"supere {umbral}",
        "queda_debajo_de": f"quede debajo de {umbral}",
    }[evento]
    if bss > 0 and auc == auc and auc > 0.6:
        r.veredicto(
            f"El modelo agrega información sobre la frecuencia histórica (BSS={fmt(bss)}, AUC={fmt(auc)}). Hoy: P = {fmt(p_hoy * 100, 2)} %.",
            "verde",
        )
    else:
        r.veredicto(
            f"El modelo no mejora a la frecuencia histórica ({fmt(yc.mean() * 100, 2)} %): no uses su probabilidad (BSS={fmt(bss)}, AUC={fmt(auc)}).",
            "rojo",
        )
    r.serie(
        f"prob_{evento[:8]}_{dep}"[:40],
        fechas,
        probs,
        f"P({et[dep]} {desc} en {h} períodos), fuera de muestra",
    )
    r.resumen = f"Probabilidad de que {et[dep]} {desc} en {h} períodos ({modelo}): Brier {fmt(bs)} vs {fmt(bs0)} de la frecuencia histórica (BSS {fmt(bss)}), AUC {fmt(auc)}. P actual = {fmt(p_hoy * 100, 2)} %."
    r.datos = {"p_hoy": p_hoy, "bss": bss, "auc": auc}
    return r


def _clasificador(nombre):
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    if nombre == "logit":
        from sklearn.linear_model import LogisticRegression

        return lambda: make_pipeline(StandardScaler(), LogisticRegression(C=0.5, max_iter=2000))
    if nombre == "random_forest":
        from sklearn.ensemble import RandomForestClassifier

        return lambda: RandomForestClassifier(
            n_estimators=300, min_samples_leaf=5, max_features=0.5, n_jobs=-1, random_state=0
        )
    if nombre == "gbm":
        from sklearn.ensemble import HistGradientBoostingClassifier

        return lambda: HistGradientBoostingClassifier(
            max_iter=200, learning_rate=0.05, max_depth=3, min_samples_leaf=10, random_state=0
        )
    if nombre == "svm":
        from sklearn.svm import SVC

        return lambda: make_pipeline(StandardScaler(), SVC(C=1.0, probability=True, random_state=0))
    from sklearn.neighbors import KNeighborsClassifier

    return lambda: make_pipeline(StandardScaler(), KNeighborsClassifier(n_neighbors=15, weights="distance"))


# ──────────────────────────────────────────────────────────────────────────
# Selección de variables entre muchas candidatas
# ──────────────────────────────────────────────────────────────────────────
@metodo(
    "seleccion_variables",
    "Selección de predictores entre muchas series (estabilidad Lasso + bosque)",
    F,
    "De 10-40 series candidatas del catálogo, ¿cuáles ayudan de verdad a predecir Y?",
    params=[
        P_SERIE("dep", "Objetivo (Y)"),
        P_SERIES("candidatas", "Candidatas", minimo=2, maximo=40),
        Param("freq", "opcion", "Frecuencia", defecto="mensual", opciones=FREQS),
        Param("transf", "opcion", "Transformación", defecto="dif_log", opciones=list(P_TRANSF.opciones)),
        Param("horizonte", "entero", "Horizonte h", defecto=1, minimo=1, maximo=24),
        Param("rezago", "entero", "Rezago de las candidatas", defecto=1, minimo=0, maximo=12),
        Param("submuestras", "entero", "Submuestras", defecto=100, minimo=20, maximo=500),
    ],
    cuando="Al empezar un trabajo con el catálogo entero a disposición: achica la lista antes de modelar.",
    supuestos=[
        "Selección por estabilidad: una variable relevante se elige en la mayoría de las submuestras."
    ],
    trampas=[
        "Elegir variables y evaluar con los mismos datos infla el ajuste: después evaluá fuera de muestra (torneo)."
    ],
    deps=["sklearn"],
    costo="segundos",
    referencias=["Meinshausen y Bühlmann (2010)", "Tibshirani (1996)"],
    etiquetas=["selección de variables", "stability selection", "lasso", "screening", "candidatas"],
)
def seleccion_variables(dep, candidatas, freq, transf, horizonte, rezago, submuestras):
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.inspection import permutation_importance
    from sklearn.linear_model import Lasso, LassoCV
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.preprocessing import StandardScaler

    cands = [c for c in candidatas if c != dep]
    df, et = panel([dep, *cands], freq, transf, minimo=40)
    y = df[dep].shift(-horizonte)
    X = pd.concat({et[c]: df[c].shift(rezago) for c in cands}, axis=1)
    X[f"{et[dep]} (propio)"] = df[dep]
    d = pd.concat([y.rename("__y"), X], axis=1).dropna()
    Yv, Xv = d["__y"].values, StandardScaler().fit_transform(d.drop(columns="__y").values)
    cols = list(d.drop(columns="__y").columns)
    alfa = LassoCV(cv=TimeSeriesSplit(5), alphas=50, max_iter=10000).fit(Xv, Yv).alpha_
    rng = np.random.default_rng(0)
    n = len(Yv)
    cuenta = np.zeros(len(cols))
    L = max(6, n // 10)
    for _ in range(submuestras):
        bloques = rng.choice(np.arange(0, n - L), size=max(1, n // (2 * L)), replace=False)
        idx = np.unique(np.concatenate([np.arange(b, b + L) for b in bloques]))
        m = Lasso(alpha=alfa * 1.5, max_iter=10000).fit(Xv[idx], Yv[idx])
        cuenta += np.abs(m.coef_) > 1e-8
    frec = cuenta / submuestras
    corte = int(n * 0.75)
    rf = RandomForestRegressor(
        n_estimators=300, min_samples_leaf=5, max_features=0.5, random_state=0, n_jobs=-1
    ).fit(Xv[:corte], Yv[:corte])
    pi = permutation_importance(rf, Xv[corte:], Yv[corte:], n_repeats=10, random_state=0).importances_mean
    orden = np.argsort(frec + pi / (np.abs(pi).max() or 1) * 0.01)[::-1]
    r = Resultado()
    r.barras(
        "Frecuencia de selección (Lasso en submuestras por bloques)",
        [cols[i] for i in orden],
        {"frecuencia": frec[orden]},
        banda=0.6,
        horizontal=True,
    )
    r.tabla(
        "Ranking",
        ["variable", "frec. selección", "importancia bosque (fuera de muestra)", "corr. con Y(t+h)"],
        [[cols[i], frec[i], pi[i], float(np.corrcoef(Xv[:, i], Yv)[0, 1])] for i in orden],
    )
    elegidas = [cols[i] for i in orden if frec[i] >= 0.6]
    r.metrica("Variables estables (frec. ≥ 0,6)", len(elegidas))
    r.metrica("Obs.", n)
    r.veredicto(
        f"Predictores estables: {', '.join(elegidas) or 'ninguno'}. Llevalos a un torneo para evaluarlos fuera de muestra.",
        "verde" if elegidas else "amarillo",
    )
    r.resumen = f"Selección entre {len(cands)} candidatas para predecir {et[dep]} a h={horizonte}: estables {', '.join(elegidas) or 'ninguna'}."
    r.datos = {"elegidas": elegidas}
    return r
