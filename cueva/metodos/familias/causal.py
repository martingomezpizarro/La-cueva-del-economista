"""Inferencia causal y eventos: serie interrumpida, impacto causal con contrafactual, control
sintético, diferencias en diferencias y estudio de eventos de la Línea de Tiempo.

Regla de la familia: TODO método causal declara su supuesto de identificación en el
veredicto y corre una prueba placebo cuando se puede. Una estimación causal sin placebo es una
correlación con buena prensa.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from cueva.metodos.contrato import ErrorMetodo, Param, Resultado
from cueva.metodos.insumos import P_FREQ, P_SERIE, P_SERIES, P_TRANSF, eventos_en, fmt, panel, serie
from cueva.metodos.registro import metodo

F = "causal"
P_FECHA = Param("fecha", "fecha", "Fecha de la intervención", requerido=True, ayuda="Primer período tratado (ej. 2019-09)")


def _corte(indice, fecha) -> int:
    i = int(np.searchsorted(indice.values, np.datetime64(pd.Timestamp(fecha))))
    if i < 12 or i > len(indice) - 3:
        raise ErrorMetodo("La fecha deja muy pocos datos antes (mín. 12) o después (mín. 3) de la intervención.")
    return i


@metodo(
    "serie_interrumpida",
    "Serie de tiempo interrumpida (regresión segmentada)",
    F,
    "¿La intervención cambió el nivel o la tendencia de la serie?",
    params=[P_SERIE(), P_FREQ, P_TRANSF, P_FECHA, Param("estacionales", "bool", "Dummies estacionales", defecto=False)],
    cuando="Una política con fecha clara y sin grupo de control (cepo, ley, cambio de régimen).",
    supuestos=["Sin la intervención, la tendencia previa habría continuado.", "Nada más cambió en la misma fecha."],
    trampas=["Cualquier otro shock simultáneo se atribuye a la intervención.", "Con autocorrelación, los EE MCO subestiman: se usan Newey-West."],
    referencias=["Bernal, Cummins y Gasparrini (2017)", "Wagner et al. (2002)"],
    etiquetas=["its", "interrumpida", "segmentada", "intervención", "política", "cambio de nivel"],
    nivel="basico",
)
def serie_interrumpida(sid, freq, transf, fecha, estacionales):
    import statsmodels.api as sm

    s, et = serie(sid, freq, transf, minimo=24)
    c = _corte(s.index, fecha)
    n = len(s)
    t = np.arange(n, dtype=float)
    post = (t >= c).astype(float)
    X = pd.DataFrame({"tendencia": t, "escalón": post, "cambio de pendiente": post * (t - c)}, index=s.index)
    if estacionales and freq == "mensual":
        for mm in range(2, 13):
            X[f"m{mm}"] = (s.index.month == mm).astype(float)
    res = sm.OLS(s.values, sm.add_constant(X)).fit(cov_type="HAC", cov_kwds={"maxlags": 6})
    contraf = res.params["const"] + res.params["tendencia"] * t
    if estacionales and freq == "mensual":
        contraf = contraf + X[[c_ for c_ in X.columns if c_.startswith("m")]].values @ res.params[[c_ for c_ in X.columns if c_.startswith("m")]].values
    r = Resultado()
    r.tabla("Efectos", ["término", "coef", "EE", "p"], [[k, res.params[k], res.bse[k], res.pvalues[k]] for k in ("tendencia", "escalón", "cambio de pendiente")], resaltar_p="p")
    aj = np.asarray(res.fittedvalues)
    r.lineas(f"{et}: observado, ajustado y contrafactual", s.index, {"observado": s.values, "ajustado": aj, "contrafactual (sin intervención)": np.where(t >= c, contraf, np.nan)}, estilos={"contrafactual (sin intervención)": {"guion": "dash"}}, marcas=[{"x": str(s.index[c].date()), "texto": "intervención"}])
    efecto_final = aj[-1] - contraf[-1]
    r.metrica("Cambio de nivel", res.params["escalón"])
    r.metrica("Cambio de pendiente", res.params["cambio de pendiente"])
    r.metrica("Efecto al final de la muestra", efecto_final)
    # placebo: misma regresión con fecha falsa en la mitad del pre-período
    if c >= 24:
        cp = c // 2
        postp = (t[:c] >= cp).astype(float)
        Xp = sm.add_constant(np.column_stack([t[:c], postp, postp * (t[:c] - cp)]))
        rp = sm.OLS(s.values[:c], Xp).fit(cov_type="HAC", cov_kwds={"maxlags": 6})
        r.metrica("Placebo (fecha falsa) p escalón", rp.pvalues[2])
        if rp.pvalues[2] < 0.05:
            r.advertir(f"El placebo en {s.index[cp].date()} también da un escalón significativo: la serie tiene saltos que no son de la intervención.")
    sig = res.pvalues["escalón"] < 0.05 or res.pvalues["cambio de pendiente"] < 0.05
    r.veredicto(("Hay cambio significativo tras la intervención" if sig else "No hay cambio significativo tras la intervención") + ". Supuesto clave: sin la política, la tendencia previa habría seguido.", "verde" if sig else "amarillo")
    r.resumen = f"Serie interrumpida de {et} en {fecha}: escalón {fmt(res.params['escalón'])} (p={fmt(res.pvalues['escalón'])}), cambio de pendiente {fmt(res.params['cambio de pendiente'])} (p={fmt(res.pvalues['cambio de pendiente'])})."
    return r


@metodo(
    "impacto_causal",
    "Impacto causal con contrafactual sintético (estilo CausalImpact)",
    F,
    "¿Cuánto se apartó Y de lo que habría sido sin la intervención, usando series de control no afectadas?",
    params=[P_SERIE("sid", "Serie tratada (Y)"), P_SERIES("controles", "Controles (no afectados)", minimo=1, maximo=8), P_FREQ, P_TRANSF, P_FECHA, Param("bootstrap", "entero", "Réplicas para el intervalo", defecto=300, minimo=100, maximo=2000)],
    cuando="Shocks de política en un país/sector cuando hay series comparables que no recibieron el shock.",
    supuestos=["Los controles no fueron afectados por la intervención.", "La relación Y~controles del período previo se mantiene."],
    trampas=["Un control afectado por la política contamina el contrafactual (y sesga el efecto hacia cero)."],
    costo="segundos",
    referencias=["Brodersen et al. (2015)", "Abadie (2021)"],
    etiquetas=["causalimpact", "contrafactual", "intervención", "efecto acumulado", "bsts"],
)
def impacto_causal(sid, controles, freq, transf, fecha, bootstrap):
    df, et = panel([sid, *controles], freq, transf, minimo=24)
    c = _corte(df.index, fecha)
    y = df[sid].values
    X = np.column_stack([np.ones(len(df)), df[controles].values])
    Xp, yp = X[:c], y[:c]
    lam = 1e-3 * np.trace(Xp.T @ Xp) / Xp.shape[1]
    beta = np.linalg.solve(Xp.T @ Xp + lam * np.eye(X.shape[1]), Xp.T @ yp)
    pred = X @ beta
    e = yp - pred[:c]
    # intervalo por bootstrap de bloques de residuos (respeta la autocorrelación)
    rng = np.random.default_rng(0)
    L = max(3, int(round(len(e) ** (1 / 3))))
    npost = len(df) - c
    sims = np.empty((bootstrap, npost))
    for b in range(bootstrap):
        idx = np.concatenate([np.arange(st, st + L) for st in rng.integers(0, len(e) - L, size=npost // L + 1)])[:npost]
        ib = rng.integers(0, c, size=c)
        bb = np.linalg.solve(Xp[ib].T @ Xp[ib] + lam * np.eye(X.shape[1]), Xp[ib].T @ yp[ib])
        sims[b] = X[c:] @ bb + e[idx]
    lo, hi = np.percentile(sims, [2.5, 97.5], axis=0)
    efecto = y[c:] - pred[c:]
    acum = np.cumsum(efecto)
    acum_sims = np.cumsum(y[c:] - sims, axis=1)
    alo, ahi = np.percentile(acum_sims, [2.5, 97.5], axis=0)
    p = float(np.mean(np.sign(acum_sims[:, -1]) != np.sign(acum[-1])) * 2)
    r2 = 1 - np.sum(e**2) / np.sum((yp - yp.mean()) ** 2)
    r = Resultado()
    r.lineas(f"{et[sid]}: observado vs contrafactual", df.index, {"observado": y, "contrafactual": pred, "IC inf.": np.r_[np.full(c, np.nan), lo], "IC sup.": np.r_[np.full(c, np.nan), hi]}, estilos={"contrafactual": {"guion": "dash"}, "IC inf.": {"guion": "dot"}, "IC sup.": {"guion": "dot"}}, marcas=[{"x": str(df.index[c].date()), "texto": "intervención"}])
    r.lineas("Efecto acumulado", df.index[c:], {"acumulado": acum, "IC inf.": alo, "IC sup.": ahi}, estilos={"IC inf.": {"guion": "dot"}, "IC sup.": {"guion": "dot"}})
    r.metrica("R² en el período previo", r2)
    r.metrica("Efecto promedio por período", efecto.mean())
    r.metrica("Efecto acumulado", acum[-1])
    r.metrica("Efecto relativo %", efecto.mean() / np.mean(np.abs(pred[c:])) * 100 if np.mean(np.abs(pred[c:])) else None)
    r.metrica("p (bootstrap, bilateral)", min(1.0, p))
    r.tabla("Pesos de los controles", ["control", "β"], [[et[cn], beta[i + 1]] for i, cn in enumerate(controles)])
    if r2 < 0.5:
        r.advertir("Los controles explican poco del período previo (R² < 0,5): el contrafactual es débil.")
    sig = alo[-1] > 0 or ahi[-1] < 0
    r.veredicto(f"Efecto acumulado {fmt(acum[-1])} (IC {fmt(alo[-1])} a {fmt(ahi[-1])}): {'significativo' if sig else 'no significativo'}. Supuesto: los controles no fueron afectados.", "verde" if sig else "amarillo")
    r.serie(f"contraf_{sid}"[:40], df.index, pred, f"Contrafactual de {et[sid]} sin la intervención de {fecha}")
    r.resumen = f"Impacto causal en {et[sid]} desde {fecha}: efecto medio {fmt(efecto.mean())} por período, acumulado {fmt(acum[-1])} (IC 95 % {fmt(alo[-1])} a {fmt(ahi[-1])}); R² previo {fmt(r2)}."
    return r


@metodo(
    "control_sintetico",
    "Control sintético (Abadie)",
    F,
    "¿Qué habría pasado con la unidad tratada si no hubiera recibido el shock, armando una combinación de unidades parecidas?",
    params=[P_SERIE("sid", "Unidad tratada (Y)"), P_SERIES("donantes", "Unidades donantes (misma variable, otros países/provincias)", minimo=2, maximo=20), P_FREQ, P_TRANSF, P_FECHA, Param("ajustar_nivel", "bool", "Permitir diferencia de nivel (Doudchenko-Imbens)", defecto=True, ayuda="Resta la media previa de cada unidad: el sintético copia la dinámica, no el nivel")],
    cuando="Una provincia, sector o país tratado y varios comparables sin tratar (Abadie y Gardeazabal 2003).",
    supuestos=["Pesos no negativos que suman 1: el sintético es un promedio, no una extrapolación.", "Buen ajuste previo."],
    trampas=["Con mal ajuste previo, el 'efecto' es sólo diferencia de niveles."],
    costo="segundos",
    referencias=["Abadie, Diamond y Hainmueller (2010)", "Abadie (2021)"],
    etiquetas=["control sintético", "abadie", "donantes", "placebo", "contrafactual"],
    nivel="avanzado",
)
def control_sintetico(sid, donantes, freq, transf, fecha, ajustar_nivel):
    from scipy.optimize import minimize

    df, et = panel([sid, *donantes], freq, transf, minimo=20)
    c = _corte(df.index, fecha)

    def pesos(y, D):
        k = D.shape[1]
        obj = lambda w: np.sum((y - D @ w) ** 2)  # noqa: E731
        res = minimize(obj, np.full(k, 1 / k), method="SLSQP", bounds=[(0, 1)] * k, constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1}], options={"maxiter": 500})
        return res.x

    Y = df[sid].values.astype(float)
    D = df[donantes].values.astype(float)
    if ajustar_nivel:
        Y = Y - Y[:c].mean()
        D = D - D[:c].mean(0)
    w = pesos(Y[:c], D[:c])
    sint = D @ w
    rmspe_pre = np.sqrt(np.mean((Y[:c] - sint[:c]) ** 2))
    rmspe_post = np.sqrt(np.mean((Y[c:] - sint[c:]) ** 2))
    razon = rmspe_post / rmspe_pre if rmspe_pre > 0 else np.inf
    # placebos en el espacio: cada donante como si fuera el tratado
    razones = []
    for j in range(len(donantes)):
        otros = [k for k in range(len(donantes)) if k != j]
        wj = pesos(D[:c, j], D[:c, otros])
        sj = D[:, otros] @ wj
        pre = np.sqrt(np.mean((D[:c, j] - sj[:c]) ** 2))
        post = np.sqrt(np.mean((D[c:, j] - sj[c:]) ** 2))
        razones.append(post / pre if pre > 0 else np.inf)
    p = (1 + sum(rr >= razon for rr in razones)) / (1 + len(razones))
    r = Resultado()
    r.lineas(f"{et[sid]} vs sintético" + (" (en desvíos de la media previa)" if ajustar_nivel else ""), df.index, {et[sid]: Y, "sintético": sint}, estilos={"sintético": {"guion": "dash"}}, marcas=[{"x": str(df.index[c].date()), "texto": "intervención"}])
    r.lineas("Brecha (tratada − sintético)", df.index, {"brecha": Y - sint})
    r.tabla("Pesos del sintético", ["donante", "peso"], sorted([[et[d], float(wi)] for d, wi in zip(donantes, w, strict=True)], key=lambda x: -x[1]))
    r.metrica("RMSPE previo", rmspe_pre)
    if rmspe_pre > 0.5 * np.std(Y[:c]):
        r.advertir("Mal ajuste previo (RMSPE > medio desvío de la tratada): la tratada queda fuera del rango de los donantes. Activá «permitir diferencia de nivel» o sumá donantes.")
    r.metrica("RMSPE posterior / previo", razon)
    r.metrica("p de permutación (placebos)", p, "proporción de donantes con brecha relativa ≥ la del tratado")
    r.metrica("Efecto promedio posterior", float(np.mean(Y[c:] - sint[c:])))
    r.veredicto(f"Efecto promedio {fmt(float(np.mean(Y[c:] - sint[c:])))}; p de permutación {fmt(p)} con {len(donantes)} placebos.", "verde" if p <= 0.1 else "amarillo")
    r.resumen = f"Control sintético de {et[sid]} en {fecha}: efecto medio {fmt(float(np.mean(Y[c:] - sint[c:])))}, razón RMSPE {fmt(razon)}, p={fmt(p)}."
    return r


@metodo(
    "diferencias_en_diferencias",
    "Diferencias en diferencias (dos series) con prueba de tendencias paralelas",
    F,
    "¿Cuánto cambió la tratada respecto del control después de la intervención?",
    params=[P_SERIE("sid", "Serie tratada"), P_SERIE("control", "Serie de control"), P_FREQ, P_TRANSF, P_FECHA, Param("ventanas", "entero", "Adelantos/rezagos del estudio de eventos", defecto=6, minimo=2, maximo=24)],
    cuando="Hay un grupo que recibe la política y otro comparable que no (provincias, sectores, países).",
    supuestos=["Tendencias paralelas: sin la política, ambas se habrían movido igual (se mira en los adelantos)."],
    trampas=["Si los adelantos son significativos, las tendencias no eran paralelas y el DiD está sesgado."],
    referencias=["Angrist y Pischke (2009), cap. 5", "Roth et al. (2023)"],
    etiquetas=["did", "diferencias en diferencias", "tendencias paralelas", "estudio de eventos"],
)
def diferencias_en_diferencias(sid, control, freq, transf, fecha, ventanas):
    import statsmodels.api as sm

    df, et = panel([sid, control], freq, transf, minimo=24)
    c = _corte(df.index, fecha)
    d = (df[sid] - df[control]).values
    n = len(d)
    post = (np.arange(n) >= c).astype(float)
    res = sm.OLS(d, sm.add_constant(post)).fit(cov_type="HAC", cov_kwds={"maxlags": 6})
    # tendencias paralelas: con UNA unidad tratada no hay inferencia por período relativo; se testea
    # que la diferencia no tenga pendiente en el período previo y se grafica la trayectoria relativa
    pre = d[:c]
    tp = np.arange(c, dtype=float)
    rp = sm.OLS(pre, sm.add_constant(tp)).fit(cov_type="HAC", cov_kwds={"maxlags": 6})
    p_par = float(rp.pvalues[1])
    k = ventanas
    js = [j for j in range(-k, k + 1) if 0 <= c + j < n]
    base = d[c - 1]
    coef = [d[c + j] - base for j in js]
    sd_pre = float(np.std(np.diff(pre), ddof=1)) if c > 3 else 0.0
    ee = [sd_pre * np.sqrt(abs(j + 1)) for j in js]
    r = Resultado()
    r.lineas("Tratada y control", df.index, {et[sid]: df[sid].values, et[control]: df[control].values}, marcas=[{"x": str(df.index[c].date()), "texto": "intervención"}])
    r.lineas("Brecha relativa a t = −1 (banda: ±1,96 × desvío de los cambios previos × √distancia)", js, {"efecto": coef, "IC inf.": [b - 1.96 * e for b, e in zip(coef, ee, strict=True)], "IC sup.": [b + 1.96 * e for b, e in zip(coef, ee, strict=True)]}, estilos={"IC inf.": {"guion": "dot"}, "IC sup.": {"guion": "dot"}})
    r.metrica("Efecto DiD", res.params[1])
    r.metrica("EE (Newey-West)", res.bse[1])
    r.metrica("p", res.pvalues[1])
    r.metrica("Tendencias paralelas: p de la pendiente previa", p_par, "H0: la brecha no tenía tendencia antes (lo deseable es NO rechazar)")
    if p_par < 0.05:
        r.veredicto(f"La brecha ya tenía tendencia antes de {fecha} (p={fmt(p_par)}): las tendencias NO eran paralelas y el DiD está sesgado. Probá serie_interrumpida sobre la brecha o un control sintético.", "rojo")
    else:
        r.veredicto(f"Efecto DiD {fmt(res.params[1])} (p={fmt(res.pvalues[1])}); no se rechazan tendencias paralelas en el período previo.", "verde" if res.pvalues[1] < 0.05 else "amarillo")
    r.resumen = f"DiD {et[sid]} vs {et[control]} en {fecha}: efecto {fmt(res.params[1])} (p={fmt(res.pvalues[1])}); tendencias paralelas p={fmt(p_par)}."
    return r


@metodo(
    "estudio_eventos",
    "Estudio de eventos sobre la Línea de Tiempo",
    F,
    "¿Qué le pasa en promedio a Y en los períodos alrededor de un tipo de evento (devaluaciones, crisis, cepos)?",
    params=[
        P_SERIE(),
        P_FREQ,
        Param("transf", "opcion", "Transformación", defecto="dif_log", opciones=list(P_TRANSF.opciones)),
        Param("categoria", "opcion", "Tipo de evento", defecto="regimen_cambiario", opciones=["regimen_cambiario", "control_cambios", "crisis_bancaria", "crisis_cambiaria", "default", "reestructuracion_deuda", "shock_externo", "norma", "cambio_moneda", "monetario", "fiscal", "crisis", "politico", "internacional", "externo"], ayuda="Subtipo o categoría de data/historia/eventos.csv"),
        Param("fechas", "texto", "…o fechas propias", ayuda="Separadas por coma: 2002-01, 2014-01, 2018-04 (si se completa, manda sobre el tipo)"),
        Param("antes", "entero", "Períodos antes", defecto=6, minimo=1, maximo=36),
        Param("despues", "entero", "Períodos después", defecto=12, minimo=1, maximo=48),
        Param("acumulado", "bool", "Mostrar acumulado desde t = −1", defecto=True),
    ],
    cuando="Para responder con datos preguntas de la historia económica: el patrón típico alrededor de un tipo de episodio.",
    supuestos=["Los eventos son comparables entre sí; la respuesta media resume una regularidad."],
    trampas=["Pocos eventos ⇒ el promedio lo maneja uno solo: mirá las trayectorias individuales.", "Eventos superpuestos (ventanas que se pisan) mezclan efectos."],
    referencias=["MacKinlay (1997)", "Reinhart y Rogoff (2009)"],
    etiquetas=["estudio de eventos", "línea de tiempo", "devaluación", "crisis", "historia", "episodios"],
    nivel="basico",
)
def estudio_eventos(sid, freq, transf, categoria, fechas, antes, despues, acumulado):
    s, et = serie(sid, freq, transf, minimo=24)
    if fechas:
        lista = [{"fecha": f.strip(), "titulo": f.strip()} for f in fechas.split(",") if f.strip()]
    else:
        evs = eventos_en(s.index[0], s.index[-1])
        lista = [e for e in evs if categoria in (e["categoria"],)]
        try:
            from cueva.datos import historia

            sub = {e.id: e.subtipo for e in historia.cargar_eventos()}
            lista = [e for e in evs if e["categoria"] == categoria or sub.get(e["id"]) == categoria]
        except Exception:
            pass
    if not lista:
        raise ErrorMetodo(f"No hay eventos «{categoria}» dentro del rango de {et}. Probá con fechas propias.")
    filas, tray = [], {}
    rel = list(range(-antes, despues + 1))
    for e in lista:
        t0 = int(np.searchsorted(s.index.values, np.datetime64(pd.Timestamp(e["fecha"]))))
        if t0 - antes < 0 or t0 + despues >= len(s):
            filas.append([e["fecha"], e["titulo"], "fuera de rango"])
            continue
        v = s.values[t0 - antes : t0 + despues + 1].astype(float)
        if acumulado:
            v = np.cumsum(v) - np.cumsum(v)[antes - 1] if antes >= 1 else np.cumsum(v)
        tray[f"{e['fecha'][:7]} {e['titulo'][:30]}"] = v
        filas.append([e["fecha"], e["titulo"], "incluido"])
    if not tray:
        raise ErrorMetodo("Ningún evento tiene ventana completa dentro de la serie: achicá antes/después.")
    M = np.array(list(tray.values()))
    media = M.mean(0)
    ee = M.std(0, ddof=1) / np.sqrt(len(M)) if len(M) > 1 else np.zeros_like(media)
    r = Resultado()
    r.lineas(f"Respuesta {'acumulada ' if acumulado else ''}promedio de {et} alrededor de los eventos (n={len(M)})", rel, {"promedio": media, "IC inf.": media - 1.96 * ee, "IC sup.": media + 1.96 * ee}, estilos={"IC inf.": {"guion": "dot"}, "IC sup.": {"guion": "dot"}}, marcas=[{"x": 0, "texto": "evento"}])
    r.lineas("Trayectorias individuales", rel, tray)
    r.tabla("Eventos", ["fecha", "evento", "estado"], filas)
    r.metrica("Eventos incluidos", len(M))
    r.metrica(f"Promedio en t=+{despues}", media[-1])
    r.metrica("Promedio en t=0", media[antes])
    if len(M) < 4:
        r.advertir("Menos de 4 eventos: el promedio es frágil.")
    r.resumen = f"Estudio de eventos ({'fechas propias' if fechas else categoria}) sobre {et}: {len(M)} eventos; respuesta {'acumulada ' if acumulado else ''}promedio {fmt(media[antes])} en t=0 y {fmt(media[-1])} en t=+{despues}."
    return r
