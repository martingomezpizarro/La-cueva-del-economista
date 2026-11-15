"""Redes neuronales recurrentes sobre ventanas de la serie (numpy puro, ver `redes_np`).

La entrada es una ventana de L períodos de [Y, X1, …] transformadas y estandarizadas con
estadísticos del tramo de entrenamiento; el objetivo es y_{t+h}. Se promedia un ensamble de
semillas (las redes chicas son inestables entre inicializaciones) y se evalúa con el mismo
origen móvil que el resto del catálogo.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from cueva.metodos import validacion as V
from cueva.metodos.contrato import ErrorMetodo, Param, Resultado
from cueva.metodos.insumos import P_SERIE, P_SERIES, P_TRANSF, fmt, panel
from cueva.metodos.redes_np import RecurrenteNP, ReservorioNP, ventanas
from cueva.metodos.registro import metodo

F = "redes"
FREQS = ["diaria", "mensual", "trimestral", "anual"]


class _Ensamble:
    """Estandariza con el train, entrena k semillas y promedia."""

    def __init__(self, crear, semillas=3):
        self.crear, self.semillas = crear, semillas

    def fit(self, X, y):
        self.mu = X.reshape(-1, X.shape[2]).mean(0)
        self.sd = X.reshape(-1, X.shape[2]).std(0)
        self.sd[self.sd == 0] = 1
        self.ym, self.ys = y.mean(), y.std() or 1
        Xn = (X - self.mu) / self.sd
        self.mods = [self.crear(s).fit(Xn, (y - self.ym) / self.ys) for s in range(self.semillas)]
        return self

    def predict(self, X):
        Xn = (X - self.mu) / self.sd
        return np.mean([m.predict(Xn) for m in self.mods], axis=0) * self.ys + self.ym


def _datos_secuencia(dep, indeps, freq, transf, ventana, horizonte):
    indeps = [s for s in (indeps or []) if s != dep]
    df, et = panel([dep, *indeps], freq, transf, minimo=60)
    M = df[[dep, *indeps]].values.astype(float)
    W = ventanas(M, ventana)  # ventana i termina en la fila i+L−1
    fin = np.arange(ventana - 1, len(M))
    y = np.full(len(W), np.nan)
    ok = fin + horizonte < len(M)
    y[ok] = M[fin[ok] + horizonte, 0]
    Xc, yc = W[ok], y[ok]
    fechas_obj = df.index[fin[ok] + horizonte]
    actual = M[fin[ok], 0]
    if len(Xc) < 50:
        raise ErrorMetodo(
            f"Quedan {len(Xc)} ventanas; hacen falta al menos 50. Bajá la ventana o usá más historia."
        )
    return df, et, Xc, yc, fechas_obj, actual, W[-1:]


def _correr_red(nombre, crear, dep, indeps, freq, transf, ventana, horizonte, semillas, n_test, refit):
    df, et, X, y, fobj, actual, X_ult = _datos_secuencia(dep, indeps, freq, transf, ventana, horizonte)
    n = len(X)
    nt = n_test or V.n_test_por_defecto(n, freq)
    nt = min(nt, n - horizonte - 40)
    fab = lambda: _Ensamble(crear, semillas)  # noqa: E731
    preds, reales, rws, medias = [], [], [], []
    m = None
    for k, i in enumerate(range(n - nt, n)):
        fin = i - horizonte + 1
        if m is None or k % refit == 0:
            m = fab().fit(X[:fin], y[:fin])
        preds.append(float(m.predict(X[i : i + 1])[0]))
        reales.append(y[i])
        rws.append(actual[i])
        medias.append(float(y[:fin].mean()))
    tr = actual[: n - nt]
    bt = V.Backtest(
        pd.DatetimeIndex(fobj[-nt:]),
        np.array(reales),
        np.array(preds),
        np.array(rws),
        np.array(medias),
        float(np.mean(np.abs(tr[horizonte:] - tr[:-horizonte]))),
    )
    res = V.resumen_backtest(bt, horizonte)
    r = Resultado()
    from cueva.metodos.familias.ml import reportar

    class _D:  # adaptador mínimo para reutilizar `reportar`
        pass

    d = _D()
    d.h, d.dep, d.etiquetas = horizonte, dep, et
    reportar(r, d, bt, res, nombre)
    final = fab().fit(X, y)
    pred = float(final.predict(X_ult)[0])
    from cueva.metodos.insumos import _sumar_periodos

    fpron = _sumar_periodos(df.index[-1], horizonte, freq)
    r.metrica(f"Pronóstico para {fpron.date()}", pred)
    hist = getattr(final.mods[0], "historia", None)
    if hist:
        r.lineas(
            "Curva de aprendizaje (semilla 1)",
            list(range(1, len(hist) + 1)),
            {"error entrenamiento": [h[0] for h in hist], "error validación": [h[1] for h in hist]},
        )
        r.metrica("Épocas (con parada temprana)", len(hist))
    r.serie(
        f"oos_{nombre.lower()[:6]}_{dep}"[:40],
        bt.fechas,
        bt.pred,
        f"Pronósticos fuera de muestra de {nombre} para {et[dep]}",
    )
    r.resumen = f"{nombre} (ventana {ventana}, {semillas} semillas) para {et[dep]} a h={horizonte}: RMSE oos {fmt(res['modelo']['RMSE'])} vs paseo {fmt(res['paseo_aleatorio']['RMSE'])} y media {fmt(res['media_historica']['RMSE'])}; R² oos vs media {fmt(res['r2_oos_vs_media'])}. Pronóstico {fpron.date()}: {fmt(pred)}."
    r.datos = {"rmse": res["modelo"]["RMSE"], "r2_oos_media": res["r2_oos_vs_media"], "pronostico": pred}
    r.advertir(
        "Las redes necesitan muchos datos: con menos de ~300 ventanas, un Ridge o un bosque suelen empatar o ganar."
    )
    return r


def _params_red(extra):
    return [
        P_SERIE("dep", "Objetivo (Y)"),
        P_SERIES("indeps", "Otras series en la ventana", minimo=0, maximo=10, requerido=False),
        Param("freq", "opcion", "Frecuencia", defecto="mensual", opciones=FREQS),
        Param("transf", "opcion", "Transformación", defecto="dif_log", opciones=list(P_TRANSF.opciones)),
        Param("ventana", "entero", "Largo de la ventana (L)", defecto=12, minimo=2, maximo=120),
        Param("horizonte", "entero", "Horizonte h", defecto=1, minimo=1, maximo=36),
        Param("semillas", "entero", "Semillas del ensamble", defecto=3, minimo=1, maximo=10),
        Param("n_test", "entero", "Obs. de prueba (0 = 20 %)", defecto=0, minimo=0, maximo=500),
        *extra,
    ]


TRAMPAS_RED = [
    "Sin estacionariedad (nivel con tendencia), la red extrapola mal fuera del rango visto.",
    "Una curva de validación que sube mientras la de entrenamiento baja es sobreajuste.",
    "Las redes no son mejores por defecto: tienen que ganarle a ARIMA y a un bosque en el torneo.",
]


@metodo(
    "red_lstm",
    "Red recurrente LSTM",
    F,
    "¿Una red con memoria de largo plazo captura dinámicas no lineales que los modelos lineales no ven?",
    params=_params_red(
        [
            Param("ocultas", "entero", "Unidades ocultas", defecto=16, minimo=2, maximo=128),
            Param("epocas", "entero", "Épocas máx.", defecto=300, minimo=20, maximo=3000),
            Param("tasa", "real", "Tasa de aprendizaje", defecto=0.01, minimo=1e-4, maximo=0.5),
        ]
    ),
    cuando="Series largas (diarias, o mensuales con varias décadas) con no linealidades y memoria.",
    supuestos=["La dinámica cabe en una ventana de L períodos."],
    trampas=TRAMPAS_RED,
    costo="minutos",
    referencias=["Hochreiter y Schmidhuber (1997)", "Goodfellow, Bengio y Courville (2016), cap. 10"],
    etiquetas=["lstm", "red recurrente", "rnn", "deep learning", "memoria"],
    nivel="avanzado",
)
def red_lstm(dep, indeps, freq, transf, ventana, horizonte, semillas, n_test, ocultas, epocas, tasa):
    return _correr_red(
        "LSTM",
        lambda s: RecurrenteNP("lstm", ocultas, epocas, tasa, semilla=s),
        dep,
        indeps,
        freq,
        transf,
        ventana,
        horizonte,
        semillas,
        n_test,
        refit=12,
    )


@metodo(
    "red_gru",
    "Red recurrente GRU",
    F,
    "Como la LSTM pero con menos parámetros: suele rendir igual con menos datos.",
    params=_params_red(
        [
            Param("ocultas", "entero", "Unidades ocultas", defecto=16, minimo=2, maximo=128),
            Param("epocas", "entero", "Épocas máx.", defecto=300, minimo=20, maximo=3000),
            Param("tasa", "real", "Tasa de aprendizaje", defecto=0.01, minimo=1e-4, maximo=0.5),
        ]
    ),
    cuando="Igual que la LSTM, con muestras más cortas.",
    trampas=TRAMPAS_RED,
    costo="minutos",
    referencias=["Cho et al. (2014)", "Chung et al. (2014)"],
    etiquetas=["gru", "red recurrente", "rnn", "deep learning"],
    nivel="avanzado",
)
def red_gru(dep, indeps, freq, transf, ventana, horizonte, semillas, n_test, ocultas, epocas, tasa):
    return _correr_red(
        "GRU",
        lambda s: RecurrenteNP("gru", ocultas, epocas, tasa, semilla=s),
        dep,
        indeps,
        freq,
        transf,
        ventana,
        horizonte,
        semillas,
        n_test,
        refit=12,
    )


@metodo(
    "red_reservorio",
    "Red de reservorio (Echo State Network)",
    F,
    "Una red recurrente que entrena en milisegundos: sólo se ajusta la lectura lineal.",
    params=_params_red(
        [
            Param("unidades", "entero", "Neuronas del reservorio", defecto=200, minimo=20, maximo=2000),
            Param("radio", "real", "Radio espectral", defecto=0.9, minimo=0.1, maximo=1.5),
            Param("fuga", "real", "Tasa de fuga", defecto=0.5, minimo=0.05, maximo=1),
        ]
    ),
    cuando="Para probar rápido si hay estructura no lineal aprovechable antes de entrenar una LSTM.",
    supuestos=["Propiedad de eco: radio espectral < 1 (el reservorio olvida las condiciones iniciales)."],
    trampas=TRAMPAS_RED,
    costo="segundos",
    referencias=["Jaeger (2001)", "Lukoševičius (2012)"],
    etiquetas=["esn", "reservorio", "echo state", "reservoir computing"],
    nivel="avanzado",
)
def red_reservorio(dep, indeps, freq, transf, ventana, horizonte, semillas, n_test, unidades, radio, fuga):
    return _correr_red(
        "Reservorio",
        lambda s: ReservorioNP(unidades, radio, fuga, semilla=s),
        dep,
        indeps,
        freq,
        transf,
        ventana,
        horizonte,
        semillas,
        n_test,
        refit=1,
    )
