"""herramientas — Herramientas econométricas ejecutables por los agentes (modo HÍBRIDO).

Lo ESTÁNDAR se ejecuta de verdad sobre las series reales (estacionariedad, Granger, OLS, VAR,
VECM, GARCH, descriptivos). Lo no estándar no está acá: el agente lo detecta, lo asesora y, si
hace falta, pide confirmación al usuario.

Cada herramienta devuelve un dict uniforme (el CONTRATO de esta capa):
    {"ok": bool, "herramienta": str, "args": {...}, "resumen": "<texto para el agente>", ...}
El campo "resumen" es lo que el agente lee para razonar; el resto es evidencia estructurada.

Depende de statsmodels y arch. Si no están instalados, devuelve ok=False con instrucción de
instalación (no rompe la plataforma).
"""

from __future__ import annotations

import logging
from typing import Any

from cueva.datos import series as S

log = logging.getLogger("cueva.econometria")


def _necesita(modulo: str) -> dict:
    return {"ok": False, "resumen": f"Falta el paquete '{modulo}'. Instalá: pip install {modulo}"}


# ──────────────────────────────────────────────────────────────────────────
# Descriptivos
# ──────────────────────────────────────────────────────────────────────────
def describir(sid: str, freq: str = "mensual") -> dict:
    try:
        s = S.cargar(sid, freq=freq)
    except Exception as e:
        return {"ok": False, "herramienta": "describir", "resumen": f"No pude cargar {sid}: {e}"}
    pct_var = float(s.pct_change().std()) if len(s) > 2 else float("nan")
    resumen = (
        f"Serie '{sid}' ({freq}): n={len(s)}, rango {s.index.min().date()}→{s.index.max().date()}. "
        f"media={s.mean():.3g}, sd={s.std():.3g}, min={s.min():.3g}, max={s.max():.3g}. "
        f"tendencia {'creciente' if s.iloc[-1] > s.iloc[0] else 'decreciente'}."
    )
    return {
        "ok": True,
        "herramienta": "describir",
        "args": {"sid": sid, "freq": freq},
        "resumen": resumen,
        "stats": {
            "n": len(s),
            "media": float(s.mean()),
            "sd": float(s.std()),
            "min": float(s.min()),
            "max": float(s.max()),
            "vol_relativa": pct_var,
        },
    }


# ──────────────────────────────────────────────────────────────────────────
# Estacionariedad (ADF + KPSS)
# ──────────────────────────────────────────────────────────────────────────
def estacionariedad(sid: str, freq: str = "mensual", dif: int = 0) -> dict:
    try:
        from statsmodels.tsa.stattools import adfuller, kpss
    except Exception:
        return {**_necesita("statsmodels"), "herramienta": "estacionariedad"}
    try:
        s = S.cargar(sid, freq=freq)
    except Exception as e:
        return {"ok": False, "herramienta": "estacionariedad", "resumen": f"No pude cargar {sid}: {e}"}
    for _ in range(dif):
        s = s.diff().dropna()
    s = s.dropna()
    if len(s) < 12:
        return {
            "ok": False,
            "herramienta": "estacionariedad",
            "resumen": f"Pocos datos en {sid} (n={len(s)}).",
        }
    adf_stat, adf_p = adfuller(s, autolag="AIC")[:2]
    try:
        kpss_p = float(kpss(s, regression="c", nlags="auto")[1])
    except Exception:
        kpss_p = float("nan")
    # bool() explícito: statsmodels devuelve numpy.bool_, y `np.False_ is False` da False,
    # lo que hacía inalcanzable la conclusión "NO estacionaria" (bug heredado del código original)
    adf_estac = bool(adf_p < 0.05)
    kpss_estac = bool(kpss_p > 0.05) if kpss_p == kpss_p else None
    if adf_estac and kpss_estac:
        concl = "estacionaria"
    elif (not adf_estac) and (kpss_estac is False):
        concl = "NO estacionaria (probable raíz unitaria → I(1) o más)"
    else:
        concl = "resultados mixtos (revisar tendencia/quiebre)"
    resumen = (
        f"{sid}{' (dif ' + str(dif) + ')' if dif else ''}: ADF p={adf_p:.3f} "
        f"({'rechaza' if adf_estac else 'no rechaza'} raíz unitaria), "
        f"KPSS p={kpss_p:.3f}. Conclusión: {concl}."
    )
    return {
        "ok": True,
        "herramienta": "estacionariedad",
        "args": {"sid": sid, "freq": freq, "dif": dif},
        "resumen": resumen,
        "adf_p": float(adf_p),
        "kpss_p": float(kpss_p),
        "conclusion": concl,
    }


# ──────────────────────────────────────────────────────────────────────────
# Causalidad de Granger
# ──────────────────────────────────────────────────────────────────────────
def granger(sid_x: str, sid_y: str, freq: str = "mensual", max_lags: int = 6) -> dict:
    try:
        from statsmodels.tsa.stattools import grangercausalitytests
    except Exception:
        return {**_necesita("statsmodels"), "herramienta": "granger"}
    df = S.panel([sid_y, sid_x], freq=freq)
    if df.shape[1] < 2 or len(df.dropna()) < max_lags + 10:
        return {
            "ok": False,
            "herramienta": "granger",
            "resumen": "Datos insuficientes o no se alinearon las series.",
        }
    d = df.dropna()
    # statsmodels: testea si la 2da columna causa-Granger a la 1ra → orden [y, x]
    try:
        res = grangercausalitytests(d[[sid_y, sid_x]].diff().dropna(), maxlag=max_lags, verbose=False)
    except Exception as e:
        return {"ok": False, "herramienta": "granger", "resumen": f"Falló el test: {e}"}
    # int() nativo: statsmodels devuelve claves numpy.int64 y json.dumps no las acepta
    # (rompía la persistencia de la pizarra la primera vez que la mesa corrió granger)
    pvals = {int(lag): float(r[0]["ssr_ftest"][1]) for lag, r in res.items()}
    mejor = min(pvals, key=pvals.get)
    p = pvals[mejor]
    concl = (
        f"{sid_x} causa-Granger a {sid_y}"
        if p < 0.05
        else f"no hay evidencia de que {sid_x} cause-Granger a {sid_y}"
    )
    return {
        "ok": True,
        "herramienta": "granger",
        "args": {"sid_x": sid_x, "sid_y": sid_y, "freq": freq, "max_lags": max_lags},
        "resumen": f"Granger (en diferencias) {sid_x}→{sid_y}: p-mín={p:.3f} (lag {mejor}). {concl}. "
        f"Recordá: precedencia predictiva, NO causalidad estructural.",
        "p_por_lag": pvals,
        "lag_optimo": mejor,
    }


# ──────────────────────────────────────────────────────────────────────────
# OLS (con errores HAC)
# ──────────────────────────────────────────────────────────────────────────
def ols(dep: str, indeps: list[str], freq: str = "mensual") -> dict:
    try:
        import statsmodels.api as sm
    except Exception:
        return {**_necesita("statsmodels"), "herramienta": "ols"}
    df = S.panel([dep] + list(indeps), freq=freq).dropna()
    if len(df) < len(indeps) + 8:
        return {"ok": False, "herramienta": "ols", "resumen": "Datos insuficientes para OLS."}
    y = df[dep]
    X = sm.add_constant(df[list(indeps)])
    m = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": int(len(y) ** 0.25)})
    coefs = {k: round(float(v), 4) for k, v in m.params.items()}
    pvals = {k: round(float(v), 4) for k, v in m.pvalues.items()}
    signif = [k for k, v in pvals.items() if v < 0.05 and k != "const"]
    return {
        "ok": True,
        "herramienta": "ols",
        "args": {"dep": dep, "indeps": list(indeps), "freq": freq},
        "resumen": (
            f"OLS (HAC) de {dep} ~ {', '.join(indeps)}: R²={m.rsquared:.3f}, "
            f"R²aj={m.rsquared_adj:.3f}, DW={sm.stats.stattools.durbin_watson(m.resid):.2f}. "
            f"Significativas (5%): {', '.join(signif) or 'ninguna'}. "
            f"⚠️ si las series son I(1) sin cointegrar, el R² puede ser espurio."
        ),
        "r2": float(m.rsquared),
        "r2_adj": float(m.rsquared_adj),
        "coeficientes": coefs,
        "pvalores": pvals,
    }


# ──────────────────────────────────────────────────────────────────────────
# VAR
# ──────────────────────────────────────────────────────────────────────────
def var(sids: list[str], freq: str = "mensual", max_lags: int = 8) -> dict:
    try:
        from statsmodels.tsa.api import VAR
    except Exception:
        return {**_necesita("statsmodels"), "herramienta": "var"}
    df = S.panel(list(sids), freq=freq).dropna()
    if df.shape[1] < 2 or len(df) < max_lags + 12:
        return {"ok": False, "herramienta": "var", "resumen": "Datos insuficientes para VAR (mín. 2 series)."}
    d = df.diff().dropna()  # VAR en diferencias por defecto (evita espuria si I(1))
    modelo = VAR(d)
    sel = modelo.select_order(max_lags)
    p = int(sel.aic) if sel.aic else 1
    res = modelo.fit(max(p, 1))
    return {
        "ok": True,
        "herramienta": "var",
        "args": {"sids": list(sids), "freq": freq},
        "resumen": (
            f"VAR en diferencias sobre {', '.join(sids)}: lag óptimo (AIC)={p}, "
            f"n={res.nobs}. Estable={'sí' if res.is_stable() else 'no'}. "
            f"Para relaciones de largo plazo entre I(1), considerar VECM."
        ),
        "lag_aic": p,
        "estable": bool(res.is_stable()),
    }


# ──────────────────────────────────────────────────────────────────────────
# VECM (Johansen)
# ──────────────────────────────────────────────────────────────────────────
def vecm(sids: list[str], freq: str = "mensual", det_order: int = 0, k_ar_diff: int = 2) -> dict:
    try:
        from statsmodels.tsa.vector_ar.vecm import VECM, coint_johansen
    except Exception:
        return {**_necesita("statsmodels"), "herramienta": "vecm"}
    df = S.panel(list(sids), freq=freq).dropna()
    if df.shape[1] < 2 or len(df) < 30:
        return {"ok": False, "herramienta": "vecm", "resumen": "Datos insuficientes para Johansen/VECM."}
    joh = coint_johansen(df, det_order, k_ar_diff)
    traza = joh.lr1
    cv95 = joh.cvt[:, 1]
    rango = int(sum(traza[i] > cv95[i] for i in range(len(traza))))
    if rango == 0:
        resumen = (
            f"Johansen sobre {', '.join(sids)}: rango de cointegración = 0 → NO cointegran. "
            f"Un VECM no corresponde; modelar en diferencias (VAR)."
        )
        return {
            "ok": True,
            "herramienta": "vecm",
            "args": {"sids": list(sids), "freq": freq},
            "resumen": resumen,
            "rango_cointegracion": 0,
        }
    VECM(df, k_ar_diff=k_ar_diff, coint_rank=rango, deterministic="ci").fit()
    return {
        "ok": True,
        "herramienta": "vecm",
        "args": {"sids": list(sids), "freq": freq},
        "resumen": (
            f"Johansen: rango de cointegración = {rango} → hay relación de largo plazo. "
            f"VECM estimado con rango {rango}. Interpretá el vector de cointegración "
            f"como el equilibrio de largo plazo y los α como velocidad de ajuste."
        ),
        "rango_cointegracion": rango,
    }


# ──────────────────────────────────────────────────────────────────────────
# GARCH (volatilidad)
# ──────────────────────────────────────────────────────────────────────────
def garch(sid: str, freq: str = "mensual", p: int = 1, q: int = 1) -> dict:
    try:
        from arch import arch_model
    except Exception:
        return {**_necesita("arch"), "herramienta": "garch"}
    try:
        s = S.cargar(sid, freq=freq)
    except Exception as e:
        return {"ok": False, "herramienta": "garch", "resumen": f"No pude cargar {sid}: {e}"}
    ret = s.pct_change().dropna() * 100
    if len(ret) < 30:
        return {"ok": False, "herramienta": "garch", "resumen": "Pocos retornos para GARCH."}
    m = arch_model(ret, vol="GARCH", p=p, q=q, dist="t").fit(disp="off")
    par = {k: round(float(v), 4) for k, v in m.params.items()}
    persistencia = float(par.get("alpha[1]", 0) + par.get("beta[1]", 0))
    return {
        "ok": True,
        "herramienta": "garch",
        "args": {"sid": sid, "freq": freq, "p": p, "q": q},
        "resumen": (
            f"GARCH({p},{q}) sobre retornos de {sid}: persistencia α+β={persistencia:.3f} "
            f"({'alta — shocks de volatilidad duran' if persistencia > 0.9 else 'moderada'}). "
            f"AIC={m.aic:.1f}."
        ),
        "persistencia": persistencia,
        "parametros": par,
    }


# ──────────────────────────────────────────────────────────────────────────
# Diagnósticos de especificación (la batería del Crítico, sobre residuos OLS)
# ──────────────────────────────────────────────────────────────────────────
def diagnosticos(dep: str, indeps: list[str], freq: str = "mensual") -> dict:
    """Estima OLS de dep ~ indeps y corre la batería de diagnósticos sobre los residuos:
    Ljung-Box y Breusch-Godfrey (autocorrelación), ARCH-LM (heterocedasticidad condicional),
    Jarque-Bera (normalidad), RESET de Ramsey (especificación) y CUSUM (estabilidad).
    Devuelve un semáforo: verde (sin banderas), amarillo (1-2), rojo (3+)."""
    try:
        import statsmodels.api as sm
        from statsmodels.stats.diagnostic import (
            acorr_breusch_godfrey,
            acorr_ljungbox,
            breaks_cusumolsresid,
            het_arch,
            linear_reset,
        )
        from statsmodels.stats.stattools import durbin_watson, jarque_bera
    except Exception:
        return {**_necesita("statsmodels"), "herramienta": "diagnosticos"}
    df = S.panel([dep] + list(indeps), freq=freq).dropna()
    if df.shape[1] < 2 or len(df) < len(indeps) + 15:
        return {"ok": False, "herramienta": "diagnosticos", "resumen": "Datos insuficientes para diagnosticar."}
    y = df[dep]
    X = sm.add_constant(df[list(indeps)])
    m = sm.OLS(y, X).fit()  # los tests clásicos se definen sobre los residuos OLS (sin HAC)
    resid = m.resid
    nlags = max(1, min(12, len(resid) // 10))
    try:
        pvals = {
            "autocorrelación (Ljung-Box)": float(
                acorr_ljungbox(resid, lags=[nlags], return_df=True)["lb_pvalue"].iloc[0]
            ),
            "autocorrelación (Breusch-Godfrey)": float(acorr_breusch_godfrey(m, nlags=nlags)[1]),
            "heterocedasticidad (ARCH-LM)": float(het_arch(resid, nlags=nlags)[1]),
            "no normalidad (Jarque-Bera)": float(jarque_bera(resid)[1]),
            "especificación (RESET Ramsey)": float(linear_reset(m, power=2, use_f=True).pvalue),
            "inestabilidad (CUSUM-OLS)": float(breaks_cusumolsresid(resid, ddof=X.shape[1])[1]),
        }
    except Exception as e:
        return {"ok": False, "herramienta": "diagnosticos", "resumen": f"Falló la batería: {e}"}
    banderas = [nombre for nombre, p in pvals.items() if p < 0.05]
    semaforo = "verde" if not banderas else ("amarillo" if len(banderas) <= 2 else "rojo")
    detalle = " · ".join(f"{n}: p={p:.3f}" for n, p in pvals.items())
    return {
        "ok": True,
        "herramienta": "diagnosticos",
        "args": {"dep": dep, "indeps": list(indeps), "freq": freq},
        "resumen": (
            f"Diagnósticos sobre residuos de OLS {dep} ~ {', '.join(indeps)} "
            f"(DW={durbin_watson(resid):.2f}): {detalle}. "
            f"SEMÁFORO: {semaforo.upper()}"
            + (f" — banderas: {'; '.join(banderas)}." if banderas else " — sin banderas al 5%.")
        ),
        "pvalores": {n: round(p, 4) for n, p in pvals.items()},
        "banderas": banderas,
        "semaforo": semaforo,
    }


# ──────────────────────────────────────────────────────────────────────────
# ARCH-LM sobre retornos (¿se justifica modelar la varianza?)
# ──────────────────────────────────────────────────────────────────────────
def arch_lm(sid: str, freq: str = "mensual", lags: int = 12) -> dict:
    """Test ARCH-LM de Engle sobre los retornos de una serie: si hay efectos ARCH,
    un modelo de volatilidad condicional (GARCH) se justifica; si no, no."""
    try:
        from statsmodels.stats.diagnostic import het_arch
    except Exception:
        return {**_necesita("statsmodels"), "herramienta": "arch_lm"}
    try:
        s = S.cargar(sid, freq=freq)
    except Exception as e:
        return {"ok": False, "herramienta": "arch_lm", "resumen": f"No pude cargar {sid}: {e}"}
    ret = s.pct_change().dropna() * 100
    if len(ret) < 30:
        return {"ok": False, "herramienta": "arch_lm", "resumen": f"Pocos retornos en {sid} (n={len(ret)})."}
    ret = ret - ret.mean()
    nlags = max(1, min(int(lags), len(ret) // 10))
    stat, p = het_arch(ret, nlags=nlags)[:2]
    hay_arch = bool(p < 0.05)
    return {
        "ok": True,
        "herramienta": "arch_lm",
        "args": {"sid": sid, "freq": freq, "lags": nlags},
        "resumen": (
            f"ARCH-LM sobre retornos de {sid} ({nlags} rezagos): LM={float(stat):.2f}, p={float(p):.3f} → "
            + (
                "HAY efectos ARCH: modelar la varianza (GARCH) se justifica."
                if hay_arch
                else "sin evidencia de efectos ARCH: un GARCH no se justifica."
            )
        ),
        "p_valor": float(p),
        "hay_arch": hay_arch,
    }


# ──────────────────────────────────────────────────────────────────────────
# Registro de herramientas (lo que los agentes pueden ver y pedir)
# ──────────────────────────────────────────────────────────────────────────
REGISTRO: dict[str, dict[str, Any]] = {
    "describir": {"fn": describir, "params": ["sid"], "desc": "Estadísticos básicos y forma de una serie."},
    "estacionariedad": {
        "fn": estacionariedad,
        "params": ["sid", "dif?"],
        "desc": "Tests ADF + KPSS de raíz unitaria / estacionariedad.",
    },
    "granger": {
        "fn": granger,
        "params": ["sid_x", "sid_y"],
        "desc": "Causalidad de Granger (precedencia predictiva) X→Y.",
    },
    "ols": {"fn": ols, "params": ["dep", "indeps[]"], "desc": "Regresión OLS con errores HAC."},
    "var": {"fn": var, "params": ["sids[]"], "desc": "Vector Autorregresivo (en diferencias)."},
    "vecm": {"fn": vecm, "params": ["sids[]"], "desc": "Cointegración de Johansen + VECM (largo plazo)."},
    "garch": {"fn": garch, "params": ["sid"], "desc": "Volatilidad condicional GARCH sobre retornos."},
    "diagnosticos": {
        "fn": diagnosticos,
        "params": ["dep", "indeps[]"],
        "desc": "Batería de diagnósticos sobre residuos OLS: Ljung-Box, Breusch-Godfrey, "
        "ARCH-LM, Jarque-Bera, RESET, CUSUM. Devuelve semáforo verde/amarillo/rojo.",
    },
    "arch_lm": {
        "fn": arch_lm,
        "params": ["sid", "lags?"],
        "desc": "Test ARCH-LM de Engle sobre retornos: ¿se justifica un GARCH?",
    },
}


def catalogo_herramientas() -> list[dict]:
    return [{"nombre": k, "params": v["params"], "desc": v["desc"]} for k, v in REGISTRO.items()]


# ──────────────────────────────────────────────────────────────────────────
# Declaraciones para function calling (JSON Schema por herramienta)
# ──────────────────────────────────────────────────────────────────────────
_FREQ = {
    "type": "string",
    "enum": ["diaria", "mensual", "trimestral", "anual"],
    "description": "Frecuencia de remuestreo",
}
_SID = {"type": "string", "description": "ID de la serie (del catálogo de series)"}
_SIDS = {
    "type": "array",
    "items": {"type": "string"},
    "minItems": 2,
    "maxItems": 4,
    "description": "IDs de las series (del catálogo)",
}

ESQUEMAS: dict[str, dict] = {
    "describir": {"type": "object", "properties": {"sid": _SID, "freq": _FREQ}, "required": ["sid"]},
    "estacionariedad": {
        "type": "object",
        "properties": {
            "sid": _SID,
            "freq": _FREQ,
            "dif": {
                "type": "integer",
                "minimum": 0,
                "maximum": 2,
                "description": "Cantidad de diferencias a aplicar antes del test",
            },
        },
        "required": ["sid"],
    },
    "granger": {
        "type": "object",
        "properties": {
            "sid_x": _SID,
            "sid_y": _SID,
            "freq": _FREQ,
            "max_lags": {"type": "integer", "minimum": 1, "maximum": 12},
        },
        "required": ["sid_x", "sid_y"],
    },
    "ols": {
        "type": "object",
        "properties": {
            "dep": _SID,
            "indeps": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 1,
                "maxItems": 4,
                "description": "IDs de las series explicativas",
            },
            "freq": _FREQ,
        },
        "required": ["dep", "indeps"],
    },
    "var": {"type": "object", "properties": {"sids": _SIDS, "freq": _FREQ}, "required": ["sids"]},
    "vecm": {"type": "object", "properties": {"sids": _SIDS, "freq": _FREQ}, "required": ["sids"]},
    "garch": {"type": "object", "properties": {"sid": _SID, "freq": _FREQ}, "required": ["sid"]},
    "diagnosticos": {
        "type": "object",
        "properties": {
            "dep": _SID,
            "indeps": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 1,
                "maxItems": 4,
                "description": "IDs de las series explicativas",
            },
            "freq": _FREQ,
        },
        "required": ["dep", "indeps"],
    },
    "arch_lm": {
        "type": "object",
        "properties": {
            "sid": _SID,
            "freq": _FREQ,
            "lags": {"type": "integer", "minimum": 1, "maximum": 24, "description": "Rezagos del test"},
        },
        "required": ["sid"],
    },
}


def declaraciones_herramientas(nombres: list[str]) -> list[dict]:
    """Declaraciones function-calling SOLO de las herramientas pedidas que existen y son
    ejecutables (intersección con el REGISTRO = lista blanca efectiva). Lo que se descarta
    se LOGUEA: un skill que promete herramientas inexistentes es un bug de configuración,
    no algo que deba fallar en silencio."""
    out = []
    for n in nombres:
        if n in REGISTRO and n in ESQUEMAS:
            out.append(
                {
                    "name": n,
                    "description": REGISTRO[n]["desc"],
                    "parameters_json_schema": ESQUEMAS[n],
                }
            )
        else:
            log.warning("herramienta declarada pero inexistente en el REGISTRO: %s (se descarta)", n)
    return out


def ejecutar(nombre: str, **kwargs) -> dict:
    """Ejecuta una herramienta estándar por nombre. Si no existe → modo asesor (híbrido)."""
    if nombre not in REGISTRO:
        return {
            "ok": False,
            "herramienta": nombre,
            "no_estandar": True,
            "resumen": (
                f"'{nombre}' no es una herramienta estándar ejecutable. "
                f"El agente debe asesorar sobre cómo hacerlo y, si corresponde, "
                f"pedir confirmación al usuario antes de programarlo a medida."
            ),
        }
    try:
        return REGISTRO[nombre]["fn"](**kwargs)
    except TypeError as e:
        return {"ok": False, "herramienta": nombre, "resumen": f"Argumentos inválidos: {e}"}
    except Exception as e:
        return {"ok": False, "herramienta": nombre, "resumen": f"Error ejecutando {nombre}: {e}"}
