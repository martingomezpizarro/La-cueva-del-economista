"""kalman — interpolación/ajuste por filtro de Kalman (SARIMAX en espacio de estados).

Port nativo del endpoint /api/kalman que vivía en el server del visualizador del Trabajo
Final: recibe una serie objetivo (posiblemente trimestral con huecos) y exógenas opcionales,
ajusta un SARIMAX y devuelve la serie predicha en la frecuencia pedida.

Es una capa PURA: recibe un payload dict (fechas/valores ya serializados), devuelve un dict
con el contrato {"ok": bool, ...}. No conoce HTTP ni lee archivos.
"""

from __future__ import annotations

import logging

log = logging.getLogger("cueva.econometria")


def _parsear_orden(texto: str, default: tuple) -> tuple:
    try:
        return tuple(int(x) for x in str(texto).split(","))
    except (ValueError, AttributeError):
        return default


def ajustar_kalman(payload: dict) -> dict:
    """payload = {target: {dates, values}, exog: [{label, dates, values}], freq, is_flow,
    order: 'p,d,q', seasonal_order: 'P,D,Q,s'} → serie ajustada + diagnóstico."""
    try:
        import numpy as np
        import pandas as pd
        from statsmodels.tsa.statespace.sarimax import SARIMAX
    except Exception:
        return {"ok": False, "error": "Falta statsmodels. Instalá: pip install statsmodels"}

    target = payload.get("target", {})
    exog_lista = payload.get("exog", [])
    freq = payload.get("freq", "MS")
    es_flujo = bool(payload.get("is_flow", False))
    orden = _parsear_orden(payload.get("order", "4,1,4"), (4, 1, 4))
    orden_estacional = _parsear_orden(payload.get("seasonal_order", "1,0,1,12"), (1, 0, 1, 12))

    if not target.get("dates"):
        return {"ok": False, "error": "La serie objetivo no tiene fechas."}

    fechas_t = pd.to_datetime(target["dates"])
    ts = pd.Series(target["values"], index=fechas_t, name="target").dropna()

    exog_df = None
    if exog_lista:
        columnas = []
        for i, e in enumerate(exog_lista):
            fechas_e = pd.to_datetime(e.get("dates", []))
            serie_e = pd.Series(e.get("values", []), index=fechas_e, name=e.get("label", f"exog_{i}")).dropna()
            columnas.append(serie_e)
        if columnas:
            exog_df = pd.concat(columnas, axis=1).resample(freq).mean().ffill().bfill()

    # Mover el objetivo a la frecuencia destino. Caso típico: PBI trimestral → mensual,
    # anclando el dato al último mes del trimestre (y /3 si es un flujo).
    if freq == "MS":
        if exog_df is not None:
            target_df = pd.DataFrame(index=exog_df.index, columns=["target"])
        else:
            target_df = pd.DataFrame(
                index=pd.date_range(ts.index.min(), ts.index.max(), freq="MS"), columns=["target"]
            )
        for fecha_q in ts.index:
            mes_ancla = ((fecha_q.month - 1) // 3) * 3 + 3
            fecha_ancla = pd.Timestamp(year=fecha_q.year, month=mes_ancla, day=1)
            valor = ts.loc[fecha_q]
            if es_flujo:
                valor = valor / 3.0
            if fecha_ancla in target_df.index:
                target_df.loc[fecha_ancla, "target"] = valor
    else:
        target_df = ts.resample(freq).mean().to_frame(name="target")

    if exog_df is not None:
        indice_comun = target_df.index.intersection(exog_df.index)
        df_modelo = pd.concat([target_df.loc[indice_comun], exog_df.loc[indice_comun]], axis=1)
        exog_entrena = df_modelo[exog_df.columns].astype(float)
        y = df_modelo["target"].astype(float)
    else:
        df_modelo = target_df
        exog_entrena = None
        y = df_modelo["target"].astype(float)

    modelo = SARIMAX(
        y,
        exog=exog_entrena,
        order=orden,
        seasonal_order=orden_estacional,
        trend="c",
        enforce_stationarity=False,
        enforce_invertibility=False,
    )
    try:
        resultado = modelo.fit(disp=False, maxiter=500, method="powell")
        if np.isnan(float(getattr(resultado, "aic", np.nan))):
            raise ValueError("AIC es NaN")
    except Exception:
        arranque = np.zeros(modelo.k_params)
        arranque[-1] = 1.0  # varianza base
        try:
            resultado = modelo.fit(start_params=arranque, disp=False, maxiter=500, method="powell")
        except Exception as e:
            return {"ok": False, "error": f"No convergió el SARIMAX: {e}"}

    y_pred = resultado.predict()
    residuos = resultado.resid.dropna()
    try:
        import statsmodels.api as sm

        lb = sm.stats.acorr_ljungbox(residuos, lags=[max(1, min(12, len(residuos) // 5))], return_df=True)
        lb_pval = float(lb["lb_pvalue"].values[0])
    except Exception:
        lb_pval = None

    mascara = ~np.isnan(y.values)
    rmse = (
        float(np.sqrt(np.mean((y.values[mascara] - y_pred.values[mascara]) ** 2))) if mascara.sum() else None
    )

    return {
        "ok": True,
        "dates": [d.strftime("%Y-%m-%d") for d in df_modelo.index],
        "y_obs": [float(v) if not pd.isna(v) else None for v in y.values],
        "y_pred": [float(v) if not pd.isna(v) else None for v in y_pred.values],
        "residuals": [float(v) if not pd.isna(v) else None for v in residuos.values],
        "summary": str(resultado.summary()),
        "params": {str(k): float(v) for k, v in resultado.params.items()},
        "aic": float(resultado.aic),
        "bic": float(resultado.bic),
        "rmse": rmse,
        "ljung_box_pval": lb_pval,
    }
