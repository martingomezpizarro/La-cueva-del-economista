"""validacion — Protocolo de evaluación fuera de muestra, común a TODO método predictivo.

Por qué existe: con series de tiempo, la validación cruzada aleatoria de los manuales de ML
filtra el futuro hacia el entrenamiento y da errores falsamente bajos. Acá sólo hay una forma
de evaluar, y es la honesta:

- **Origen móvil con ventana expansiva** (rolling origin): en cada origen T se entrena con las
  filas cuyo objetivo y_{t+h} ya se conocía en T (t ≤ T − h) y se pronostica la fila T.
- El escalado y cualquier ajuste viven DENTRO del modelo (pipelines de sklearn), así que se
  re-estiman en cada origen con datos del pasado.
- Todo modelo se compara contra dos benchmarks ingenuos: **paseo aleatorio** (ŷ_{t+h} = y_t) y
  **media histórica**. Un modelo que no les gana no aporta.
- La comparación es formal: **Diebold-Mariano** con la corrección de Harvey-Leybourne-Newbold
  para muestras chicas, y R² fuera de muestra de Campbell-Thompson.

Qué NO hace: no elige modelos (eso es del torneo en `familias/evaluacion.py`).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from cueva.metodos.contrato import ErrorMetodo


@dataclass
class Backtest:
    fechas: pd.DatetimeIndex  # fecha del objetivo pronosticado
    real: np.ndarray
    pred: np.ndarray
    rw: np.ndarray  # benchmark paseo aleatorio
    media: np.ndarray  # benchmark media histórica
    escala_mase: float
    extra: dict = field(default_factory=dict)

    def errores(self) -> np.ndarray:
        return self.real - self.pred


def origen_movil(
    X: pd.DataFrame,
    y: pd.Series,
    fabrica: Callable[[], object],
    h: int,
    n_test: int,
    y_actual: pd.Series,
    cada: int = 1,
    ajustar: Callable | None = None,
    predecir: Callable | None = None,
) -> Backtest:
    """Evalúa un modelo con origen móvil expansivo.

    X, y      — filas t con objetivo y_{t+h} (ver `insumos.Diseno`).
    fabrica   — devuelve un modelo NUEVO sin entrenar (con fit/predict).
    y_actual  — el valor y_t de cada fila (para el benchmark de paseo aleatorio).
    cada      — re-entrena cada `cada` orígenes (los intermedios usan el último modelo).
    """
    n = len(X)
    if n_test < 4:
        raise ErrorMetodo("El tramo de prueba necesita al menos 4 observaciones.")
    if n - n_test - h < 20:
        raise ErrorMetodo(
            f"Con {n} filas, horizonte {h} y {n_test} de prueba quedan menos de 20 para entrenar."
        )
    ajustar = ajustar or (lambda m, Xa, ya: m.fit(Xa, ya))
    predecir = predecir or (lambda m, Xp: m.predict(Xp))
    Xv, yv = X.values, y.values
    preds, reales, rws, medias, fechas = [], [], [], [], []
    modelo = None
    for k, i in enumerate(range(n - n_test, n)):
        fin_train = i - h + 1  # filas 0..i-h tienen objetivo conocido en el origen i
        if modelo is None or k % cada == 0:
            modelo = fabrica()
            ajustar(modelo, Xv[:fin_train], yv[:fin_train])
        preds.append(float(np.ravel(predecir(modelo, Xv[i : i + 1]))[0]))
        reales.append(float(yv[i]))
        rws.append(float(y_actual.iloc[i]))
        medias.append(float(np.mean(yv[:fin_train])))
        fechas.append(y.index[i])
    # escala del MASE: error medio absoluto del paseo aleatorio a h pasos dentro del train
    ytr = y_actual.values[: n - n_test]
    escala = float(np.mean(np.abs(ytr[h:] - ytr[:-h]))) if len(ytr) > h + 1 else float("nan")
    return Backtest(
        fechas=pd.DatetimeIndex(fechas),
        real=np.array(reales),
        pred=np.array(preds),
        rw=np.array(rws),
        media=np.array(medias),
        escala_mase=escala,
    )


def metricas(real, pred, escala_mase: float | None = None) -> dict:
    real, pred = np.asarray(real, float), np.asarray(pred, float)
    e = real - pred
    out = {
        "RMSE": float(np.sqrt(np.mean(e**2))),
        "MAE": float(np.mean(np.abs(e))),
    }
    if np.all(np.abs(real) > 1e-9):
        out["MAPE %"] = float(np.mean(np.abs(e / real)) * 100)
    if escala_mase and np.isfinite(escala_mase) and escala_mase > 0:
        out["MASE"] = out["MAE"] / escala_mase
    return out


def acierto_direccion(real, pred, base) -> float:
    """% de veces que el modelo acierta el signo del cambio respecto del último valor."""
    real, pred, base = (np.asarray(v, float) for v in (real, pred, base))
    return float(np.mean(np.sign(real - base) == np.sign(pred - base)) * 100)


def r2_fuera_de_muestra(real, pred, bench) -> float:
    """R² fuera de muestra (Campbell-Thompson 2008): 1 − ECM_modelo / ECM_benchmark.
    > 0 ⇒ el modelo le gana al benchmark."""
    real, pred, bench = (np.asarray(v, float) for v in (real, pred, bench))
    den = np.sum((real - bench) ** 2)
    return float(1 - np.sum((real - pred) ** 2) / den) if den > 0 else float("nan")


def diebold_mariano(e1, e2, h: int = 1, potencia: int = 2) -> tuple[float, float]:
    """Diebold-Mariano (1995) con la corrección de Harvey, Leybourne y Newbold (1997).

    H0: igual precisión. Estadístico negativo ⇒ el modelo 1 tiene menor pérdida.
    Devuelve (estadístico, p-valor bilateral con t de Student n−1)."""
    from scipy import stats

    e1, e2 = np.asarray(e1, float), np.asarray(e2, float)
    d = np.abs(e1) ** potencia - np.abs(e2) ** potencia
    n = len(d)
    if n < 5 or np.allclose(d, 0):
        return float("nan"), float("nan")
    dm = d.mean()
    # varianza de largo plazo con h−1 autocovarianzas (rectangular, como DM)
    gamma = [np.sum((d[k:] - dm) * (d[: n - k] - dm)) / n for k in range(h)]
    var = (gamma[0] + 2 * sum(gamma[1:])) / n
    if var <= 0:
        var = gamma[0] / n
    if var <= 0:
        return float("nan"), float("nan")
    stat = dm / np.sqrt(var)
    hln = np.sqrt((n + 1 - 2 * h + h * (h - 1) / n) / n)
    stat *= hln
    p = 2 * stats.t.sf(abs(stat), df=n - 1)
    return float(stat), float(p)


def resumen_backtest(bt: Backtest, h: int) -> dict:
    """Métricas del modelo y de los benchmarks + tests formales contra ambos."""
    m = metricas(bt.real, bt.pred, bt.escala_mase)
    m_rw = metricas(bt.real, bt.rw, bt.escala_mase)
    m_med = metricas(bt.real, bt.media, bt.escala_mase)
    dm_rw = diebold_mariano(bt.real - bt.pred, bt.real - bt.rw, h)
    dm_med = diebold_mariano(bt.real - bt.pred, bt.real - bt.media, h)
    return {
        "modelo": m,
        "paseo_aleatorio": m_rw,
        "media_historica": m_med,
        "r2_oos_vs_rw": r2_fuera_de_muestra(bt.real, bt.pred, bt.rw),
        "r2_oos_vs_media": r2_fuera_de_muestra(bt.real, bt.pred, bt.media),
        "dm_vs_rw": dm_rw,
        "dm_vs_media": dm_med,
        "direccion_%": acierto_direccion(bt.real, bt.pred, bt.rw),
    }


def n_test_por_defecto(n: int, freq: str) -> int:
    """Tamaño del tramo de prueba: ~20 % de la muestra, entre 8 y 60 observaciones."""
    return int(min(60, max(8, round(n * 0.2))))
