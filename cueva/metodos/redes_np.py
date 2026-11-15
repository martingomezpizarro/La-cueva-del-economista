"""redes_np — Redes neuronales recurrentes chicas en numpy puro (sin torch).

Por qué numpy: las series macro y financieras de la plataforma tienen cientos o pocos miles de
observaciones. Para ese tamaño una LSTM de 8-32 unidades entrena en segundos en CPU, y no
justifica 2-3 GB de dependencias. Cuando haga falta algo grande (N-BEATS, TFT, modelos
fundacionales) va por el extra opcional `[deep]` y la cola de trabajos.

Contenido:
    RecurrenteNP   LSTM o GRU de una capa + salida lineal, entrenada con BPTT y Adam,
                   parada temprana sobre un tramo de validación TEMPORAL (el último 15 %).
    ReservorioNP   Echo State Network: reservorio aleatorio fijo + lectura ridge. Muy rápida
                   y sorprendentemente buena con pocos datos.

Las dos exponen fit(X, y) / predict(X) con X de forma (n, L, d): n ventanas de L pasos y d
variables. Están verificadas con chequeo de gradiente numérico en los tests.
"""

from __future__ import annotations

import numpy as np


def _sig(x):
    return 1 / (1 + np.exp(-np.clip(x, -30, 30)))


class RecurrenteNP:
    def __init__(
        self,
        celda: str = "lstm",
        ocultas: int = 16,
        epocas: int = 300,
        tasa: float = 0.01,
        l2: float = 1e-4,
        lote: int = 32,
        paciencia: int = 30,
        semilla: int = 0,
        validacion: float = 0.15,
    ):
        if celda not in ("lstm", "gru"):
            raise ValueError("celda: 'lstm' o 'gru'")
        self.celda, self.H, self.epocas, self.tasa = celda, ocultas, epocas, tasa
        self.l2, self.lote, self.paciencia, self.semilla, self.validacion = (
            l2,
            lote,
            paciencia,
            semilla,
            validacion,
        )
        self.historia: list[tuple[float, float]] = []

    # ── parámetros ──
    def _init(self, d):
        rng = np.random.default_rng(self.semilla)
        H = self.H
        ng = 4 if self.celda == "lstm" else 3
        esc = 1 / np.sqrt(H + d)
        self.p = {
            "W": rng.normal(0, esc, (ng * H, H + d)),
            "b": np.zeros(ng * H),
            "V": rng.normal(0, 1 / np.sqrt(H), (1, H)),
            "c": np.zeros(1),
        }
        if self.celda == "lstm":
            self.p["b"][H : 2 * H] = 1.0  # sesgo de olvido en 1 (Jozefowicz et al. 2015)

    # ── hacia adelante ──
    def _adelante(self, X, p=None):
        p = p or self.p
        B, L, _ = X.shape
        H = self.H
        h = np.zeros((B, H))
        c = np.zeros((B, H))
        cache = []
        for t in range(L):
            hx = np.concatenate([h, X[:, t, :]], axis=1)
            if self.celda == "lstm":
                z = hx @ p["W"].T + p["b"]
                i, f, o, g = (
                    _sig(z[:, :H]),
                    _sig(z[:, H : 2 * H]),
                    _sig(z[:, 2 * H : 3 * H]),
                    np.tanh(z[:, 3 * H :]),
                )
                c_new = f * c + i * g
                tc = np.tanh(c_new)
                h_new = o * tc
                cache.append((hx, i, f, o, g, c, c_new, tc))
                h, c = h_new, c_new
            else:
                Wz, Wr, Wh = p["W"][:H], p["W"][H : 2 * H], p["W"][2 * H :]
                bz, br, bh = p["b"][:H], p["b"][H : 2 * H], p["b"][2 * H :]
                zg = _sig(hx @ Wz.T + bz)
                rg = _sig(hx @ Wr.T + br)
                rhx = np.concatenate([rg * h, X[:, t, :]], axis=1)
                hh = np.tanh(rhx @ Wh.T + bh)
                h_new = (1 - zg) * h + zg * hh
                cache.append((hx, zg, rg, rhx, hh, h))
                h = h_new
        yhat = h @ p["V"].T + p["c"]
        return yhat[:, 0], h, cache

    def _gradientes(self, X, y, p=None):
        p = p or self.p
        B, L, d = X.shape
        H = self.H
        yhat, hL, cache = self._adelante(X, p)
        e = yhat - y
        perdida = float(np.mean(e**2)) + self.l2 * float(np.sum(p["W"] ** 2) + np.sum(p["V"] ** 2))
        g = {k: np.zeros_like(v) for k, v in p.items()}
        dy = (2 / B) * e[:, None]
        g["V"] = dy.T @ hL + 2 * self.l2 * p["V"]
        g["c"] = dy.sum(0)
        dh = dy @ p["V"]
        if self.celda == "lstm":
            dc = np.zeros((B, H))
            for t in range(L - 1, -1, -1):
                hx, i, f, o, gg, c_prev, c_new, tc = cache[t]
                do = dh * tc
                dc = dc + dh * o * (1 - tc**2)
                di, df, dg = dc * gg, dc * c_prev, dc * i
                dz = np.concatenate(
                    [di * i * (1 - i), df * f * (1 - f), do * o * (1 - o), dg * (1 - gg**2)], axis=1
                )
                g["W"] += dz.T @ hx
                g["b"] += dz.sum(0)
                dhx = dz @ p["W"]
                dh = dhx[:, :H]
                dc = dc * f
        else:
            Wz, Wr, Wh = p["W"][:H], p["W"][H : 2 * H], p["W"][2 * H :]
            for t in range(L - 1, -1, -1):
                hx, zg, rg, rhx, hh, h_prev = cache[t]
                dhh = dh * zg
                dzg = dh * (hh - h_prev)
                dh_prev = dh * (1 - zg)
                da_h = dhh * (1 - hh**2)
                g["W"][2 * H :] += da_h.T @ rhx
                g["b"][2 * H :] += da_h.sum(0)
                drhx = da_h @ Wh
                drh = drhx[:, :H]
                drg = drh * h_prev
                dh_prev += drh * rg
                da_z = dzg * zg * (1 - zg)
                da_r = drg * rg * (1 - rg)
                g["W"][:H] += da_z.T @ hx
                g["b"][:H] += da_z.sum(0)
                g["W"][H : 2 * H] += da_r.T @ hx
                g["b"][H : 2 * H] += da_r.sum(0)
                dhx = da_z @ Wz + da_r @ Wr
                dh = dh_prev + dhx[:, :H]
        g["W"] += 2 * self.l2 * p["W"]
        return perdida, g

    # ── entrenamiento ──
    def fit(self, X, y):
        X = np.asarray(X, float)
        y = np.asarray(y, float)
        n = len(X)
        self._init(X.shape[2])
        nv = max(4, int(n * self.validacion)) if n > 40 else 0
        Xt, yt = X[: n - nv], y[: n - nv]
        Xv, yv = X[n - nv :], y[n - nv :]
        m = {k: np.zeros_like(v) for k, v in self.p.items()}
        v2 = {k: np.zeros_like(v) for k, v in self.p.items()}
        b1, b2, eps = 0.9, 0.999, 1e-8
        rng = np.random.default_rng(self.semilla + 1)
        mejor, mejor_p, sin_mejora, paso = np.inf, None, 0, 0
        for _ in range(self.epocas):
            orden = rng.permutation(len(Xt))
            for ini in range(0, len(Xt), self.lote):
                idx = orden[ini : ini + self.lote]
                _, g = self._gradientes(Xt[idx], yt[idx])
                norma = np.sqrt(sum(float(np.sum(v**2)) for v in g.values()))
                if norma > 5:
                    g = {k: v * 5 / norma for k, v in g.items()}
                paso += 1
                for k in self.p:
                    m[k] = b1 * m[k] + (1 - b1) * g[k]
                    v2[k] = b2 * v2[k] + (1 - b2) * g[k] ** 2
                    self.p[k] -= self.tasa * (m[k] / (1 - b1**paso)) / (np.sqrt(v2[k] / (1 - b2**paso)) + eps)
            ent = float(np.mean((self._adelante(Xt)[0] - yt) ** 2))
            val = float(np.mean((self._adelante(Xv)[0] - yv) ** 2)) if nv else ent
            self.historia.append((ent, val))
            if val < mejor - 1e-7:
                mejor, mejor_p, sin_mejora = val, {k: v.copy() for k, v in self.p.items()}, 0
            else:
                sin_mejora += 1
                if sin_mejora >= self.paciencia:
                    break
        if mejor_p is not None:
            self.p = mejor_p
        return self

    def predict(self, X):
        return self._adelante(np.asarray(X, float))[0]


class ReservorioNP:
    """Echo State Network (Jaeger 2001): reservorio recurrente aleatorio y fijo; sólo se entrena
    la lectura lineal (ridge) sobre el estado final de cada ventana."""

    def __init__(
        self,
        unidades: int = 200,
        radio: float = 0.9,
        fuga: float = 0.5,
        ridge: float = 1e-2,
        semilla: int = 0,
        densidad: float = 0.1,
    ):
        self.N, self.radio, self.fuga, self.ridge, self.semilla, self.densidad = (
            unidades,
            radio,
            fuga,
            ridge,
            semilla,
            densidad,
        )

    def _estados(self, X):
        B, L, _ = X.shape
        h = np.zeros((B, self.N))
        for t in range(L):
            pre = X[:, t, :] @ self.Win.T + h @ self.W.T
            h = (1 - self.fuga) * h + self.fuga * np.tanh(pre)
        return np.concatenate([h, X[:, -1, :], np.ones((B, 1))], axis=1)

    def fit(self, X, y):
        X = np.asarray(X, float)
        rng = np.random.default_rng(self.semilla)
        d = X.shape[2]
        W = rng.normal(0, 1, (self.N, self.N)) * (rng.random((self.N, self.N)) < self.densidad)
        rad = np.max(np.abs(np.linalg.eigvals(W))) or 1
        self.W = W * self.radio / rad
        self.Win = rng.uniform(-0.5, 0.5, (self.N, d))
        S = self._estados(X)
        self.beta = np.linalg.solve(S.T @ S + self.ridge * np.eye(S.shape[1]), S.T @ np.asarray(y, float))
        return self

    def predict(self, X):
        return self._estados(np.asarray(X, float)) @ self.beta


def ventanas(M: np.ndarray, L: int) -> np.ndarray:
    """(T, d) → (T−L+1, L, d): la ventana i termina en la fila i+L−1."""
    T = len(M)
    return np.stack([M[i : i + L] for i in range(T - L + 1)])
