"""Banco de series sintéticas para los tests del catálogo de métodos.

Cada serie tiene una propiedad CONOCIDA POR CONSTRUCCIÓN (semilla fija), así los tests
validan la conclusión del método y no sólo que "corra".
"""

from __future__ import annotations

import numpy as np
import pandas as pd

N = 240  # 20 años mensuales
INICIO = "2004-01-31"
FECHA_QUIEBRE = "2012-01-31"  # índice 96


def generar(carpeta) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(7)
    t = np.arange(N)
    e = rng.normal(0, 1, N)
    out = {}
    out["paseo"] = 100 + np.cumsum(rng.normal(0, 1, N))
    ar = np.zeros(N)
    for i in range(1, N):
        ar[i] = 0.6 * ar[i - 1] + e[i]
    out["ar1"] = ar
    # nivel con quiebre de media en 2012-01 (índice 96): 0 → 4
    out["quiebre"] = np.where(t >= 96, 4.0, 0.0) + rng.normal(0, 1, N)
    # estacional: patrón mensual fuerte + ruido
    out["estacional"] = 10 + 3 * np.sin(2 * np.pi * t / 12) + rng.normal(0, 0.5, N)
    # cointegradas: x paseo, y = 2 + 0.8 x + ruido estacionario
    x = 50 + np.cumsum(rng.normal(0, 1, N))
    out["coint_x"] = x
    out["coint_y"] = 2 + 0.8 * x + rng.normal(0, 0.7, N)
    # GARCH(1,1) en "retornos" → nivel como índice
    h = np.ones(N)
    ret = np.zeros(N)
    for i in range(1, N):
        h[i] = 0.05 + 0.15 * ret[i - 1] ** 2 + 0.8 * h[i - 1]
        ret[i] = np.sqrt(h[i]) * rng.normal()
    out["garch_ret"] = ret
    # regímenes de Markov en la media (0 / 3), persistentes
    est = np.zeros(N, dtype=int)
    for i in range(1, N):
        est[i] = est[i - 1] if rng.random() < 0.95 else 1 - est[i - 1]
    out["markov"] = np.where(est == 1, 3.0, 0.0) + rng.normal(0, 0.7, N)
    # objetivo predecible no lineal: y_t = sin(x_{t-1}) * 2 + 0.5 y_{t-1} + ruido
    xx = rng.normal(0, 1.5, N)
    yy = np.zeros(N)
    for i in range(1, N):
        yy[i] = 2 * np.sin(xx[i - 1]) + 0.5 * yy[i - 1] + rng.normal(0, 0.3)
    out["pred_x"] = xx
    out["pred_y"] = yy
    # intervención: escalón de +5 en 2016-01 (índice 144) sobre AR(1) con control
    ctrl = 20 + np.cumsum(rng.normal(0, 0.3, N))
    out["control"] = ctrl
    out["tratada"] = 5 + 0.9 * ctrl + np.where(t >= 144, 5.0, 0.0) + rng.normal(0, 0.4, N)
    # factor común: 4 series = cargas * f + ruido
    f = np.cumsum(rng.normal(0, 1, N)) * 0.3
    for k, carga in enumerate([1.0, 0.8, -0.6, 1.2]):
        out[f"fac{k}"] = carga * f + rng.normal(0, 0.3, N)
    # positiva con tendencia (para log)
    out["positiva"] = np.exp(4 + 0.004 * t + 0.03 * np.cumsum(rng.normal(0, 0.3, N)) + 0.05 * np.sin(2 * np.pi * t / 12))
    fechas = pd.date_range(INICIO, periods=N, freq="ME")
    for nombre, v in out.items():
        pd.DataFrame({"fecha": fechas, "valor": v}).to_csv(carpeta / f"{nombre}.csv", index=False, encoding="utf-8-sig")
    return out
