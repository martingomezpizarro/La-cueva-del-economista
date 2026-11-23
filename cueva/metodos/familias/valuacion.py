"""Valuación de empresas: los bloques del DCF, uno por paso (docs/VALUACION.md).

Se construyen de a uno con Martín, siguiendo la guía de NVDA: cada bloque calcula y muestra la
cuenta a la vista, con la procedencia de cada dato, pero NO saca conclusiones (las preguntas
«Para chequear» de la guía las responde quien investiga).

Paso 1 · `flujo_caja_libre`: el flujo de caja libre histórico de la firma (FCFF) por los dos
caminos —desde el estado de resultados y desde el estado de flujo de efectivo— con una fila de
control que muestra cuánto difieren, y las versiones con y sin compensación en acciones (SBC) y
con la I+D como gasto o como inversión.

Los balances salen de la Terminal (`terminal.puente.balances`). Para los tests existe la empresa
de prueba «__prueba__», con números inventados que cierran por construcción.
"""

from __future__ import annotations

import pandas as pd

from cueva.metodos.contrato import ErrorMetodo, Param, Resultado
from cueva.metodos.registro import metodo

F = "valuacion"

VARIABLES = [
    "ingresos", "resultado_operativo", "impuesto_ganancias", "resultado_antes_impuestos",
    "depreciacion", "capex", "flujo_operativo", "compensacion_acciones", "intereses",
    "investigacion_desarrollo", "cuentas_por_cobrar", "inventario", "cuentas_por_pagar",
]
SALDOS = {"cuentas_por_cobrar", "inventario", "cuentas_por_pagar"}
EMPRESA_PRUEBA = "__prueba__"

P_ACTIVO = Param("activo", "texto", "Empresa (ticker de la Terminal)", defecto="NVDA", requerido=True,
                 ayuda="El ticker tal como está en la Terminal (NVDA, MSFT, RIO…). Los balances salen de la SEC.")
P_PERIODO = Param("periodo", "opcion", "Período", defecto="ejercicios", opciones=["ejercicios", "12 meses móviles"],
                  ayuda="Ejercicios: un dato por año fiscal (el de NVDA cierra a fines de enero). 12 meses móviles: "
                        "en cada cierre de trimestre, la suma de los últimos 4 trimestres; se mueve cada trimestre.")
P_SBC = Param("restar_sbc", "bool", "Contar la compensación en acciones (SBC) como costo", defecto=True,
              ayuda="La SBC ya está restada dentro del resultado operativo (es un gasto), así que el FCFF desde el "
                    "EBIT la trata como costo. El flujo operativo la suma de vuelta porque no sale caja. Contarla "
                    "como costo es la práctica de Damodaran (se paga diluyendo o recomprando acciones); muchos "
                    "analistas la suman de vuelta. Se muestran las dos versiones; esta elige la principal.")
P_ID = Param("id_inversion", "bool", "Tratar la I+D como inversión", defecto=False,
             ayuda="Contablemente la I+D es un gasto. Tratada como inversión (Damodaran), se suma al resultado "
                   "operativo, se amortiza en varios años y cuenta como reinversión. El FCFF del año casi no cambia; "
                   "cambian el NOPAT, la reinversión y el capital invertido (paso 2).")
P_VIDA = Param("vida_id", "entero", "Años en que se amortiza la I+D", defecto=5, minimo=2, maximo=10,
               ayuda="Sólo si la I+D se trata como inversión. Damodaran usa 3 a 5 años para tecnología.")
P_ANIOS = Param("columnas", "entero", "Columnas de la tabla", defecto=10, minimo=3, maximo=30,
                ayuda="Cuántos períodos (los más recientes) se muestran en la tabla renglón por renglón.")


# ── insumos ──────────────────────────────────────────────────────────────
def _prueba(frecuencia: str) -> dict:
    """Empresa inventada: 8 ejercicios que crecen 20 % por año, con todo cerrando por construcción."""
    fechas = pd.date_range("2018-01-31", periods=8, freq="12ME") if frecuencia == "A" else \
        pd.date_range("2018-03-31", periods=32, freq="QE")
    n = len(fechas)
    base = [100 * 1.2 ** (i / (1 if frecuencia == "A" else 4)) for i in range(n)]
    esc = 1 if frecuencia == "A" else 0.25
    d = {}
    for v, f in (("ingresos", 1.0), ("resultado_operativo", 0.30), ("resultado_antes_impuestos", 0.29),
                 ("impuesto_ganancias", 0.29 * 0.15), ("depreciacion", 0.04), ("capex", 0.06),
                 ("compensacion_acciones", 0.03), ("intereses", 0.01), ("investigacion_desarrollo", 0.12)):
        d[v] = [b * f * esc for b in base]
    d["cuentas_por_cobrar"] = [b * 0.15 for b in base]
    d["inventario"] = [b * 0.10 for b in base]
    d["cuentas_por_pagar"] = [b * 0.08 for b in base]
    # flujo operativo = resultado neto + D&A + SBC − ΔCT (indirecto)
    ct = [d["cuentas_por_cobrar"][i] + d["inventario"][i] - d["cuentas_por_pagar"][i] for i in range(n)]
    d["flujo_operativo"] = [(d["resultado_antes_impuestos"][i] - d["impuesto_ganancias"][i]) + d["depreciacion"][i]
                            + d["compensacion_acciones"][i] - (ct[i] - ct[i - 1] if i else 0) for i in range(n)]
    return {v: {"frecuencia": frecuencia, "puntos": [{"fecha": str(f.date()), "valor": x * 1e6, "origen": "empresa de prueba",
                                                    "url": None} for f, x in zip(fechas, vals, strict=True)]}
            for v, vals in d.items()}


def balances(activo: str, frecuencia: str) -> dict:
    if activo == EMPRESA_PRUEBA:
        return _prueba(frecuencia)
    try:
        from terminal import puente
    except ImportError as e:
        raise ErrorMetodo("La Terminal no está instalada en esta compu: los balances salen de ahí.") from e
    if not puente.disponible():
        raise ErrorMetodo("La Terminal no tiene base de datos todavía (corré «Terminal - actualizar datos»).")
    datos = puente.balances(activo, VARIABLES, frecuencia, "USD")
    if not datos or not datos.get("ingresos", {}).get("puntos"):
        raise ErrorMetodo(f"«{activo}» no tiene balances de la SEC en la Terminal.")
    return datos


def _serie(d: dict, v: str) -> pd.Series:
    ps = d.get(v, {}).get("puntos", [])
    if not ps:
        return pd.Series(dtype=float)
    s = pd.Series({pd.Timestamp(p["fecha"]): p["valor"] for p in ps}).sort_index()
    return s[~s.index.duplicated(keep="last")]


def _doce_meses(s: pd.Series) -> pd.Series:
    """Suma de 4 trimestres consecutivos (si falta uno en el medio, no hay dato)."""
    out = {}
    idx = list(s.index)
    for i in range(3, len(idx)):
        if (idx[i] - idx[i - 3]).days <= 300:
            out[idx[i]] = s.iloc[i - 3:i + 1].sum()
    return pd.Series(out, dtype=float)


def _hace_un_anio(s: pd.Series, fechas) -> pd.Series:
    """El valor de `s` un año antes de cada fecha (±35 días)."""
    out = {}
    for f in fechas:
        c = s[(s.index >= f - pd.Timedelta(days=400)) & (s.index <= f - pd.Timedelta(days=330))]
        if len(c):
            out[f] = c.iloc[-1]
    return pd.Series(out, dtype=float)


def _id_amortizada(rd: pd.Series, vida: int, anual: bool) -> pd.Series:
    """Amortización lineal de la I+D de los `vida` años anteriores (Damodaran)."""
    pasos = vida if anual else vida * 4
    peso = 1 / vida if anual else 1 / (vida * 4)
    out = {}
    vals = rd.values
    for i, f in enumerate(rd.index):
        previos = vals[max(0, i - pasos):i]
        if len(previos) == pasos:
            out[f] = previos.sum() * peso * (1 if anual else 4)
    s = pd.Series(out, dtype=float)
    return s if anual else s / 4      # en trimestral queda la amortización del trimestre


# ── paso 1 ───────────────────────────────────────────────────────────────
@metodo(
    "flujo_caja_libre",
    "Flujo de caja libre de la firma (FCFF) histórico",
    F,
    "¿Cuánta caja libre genera el negocio para todos los que lo financian, y cómo llegó a eso?",
    [P_ACTIVO, P_PERIODO, P_SBC, P_ID, P_VIDA, P_ANIOS],
    clase="traer",
    cuando="Paso 1 del DCF: antes de proyectar, ver qué flujo genera hoy el negocio, de qué está hecho y si los "
           "dos caminos de cálculo cierran.",
    supuestos=[
        "Impuestos operativos = resultado operativo × tasa efectiva (impuesto / resultado antes de impuestos) del "
        "mismo período: lo que pagaría la empresa sin deuda.",
        "Capital de trabajo operativo = cuentas por cobrar + inventario − cuentas por pagar (sin caja ni deuda).",
        "Camino 2: FCFF = flujo operativo − capex + intereses × (1 − t) − SBC. Los dos caminos difieren por "
        "partidas que el camino 1 no ve (otros activos y pasivos operativos, impuestos diferidos, otros "
        "resultados que no son caja).",
    ],
    trampas=[
        "Usar el flujo libre «simple» (flujo operativo − capex) como si fuera de la firma: ya pagó intereses.",
        "Restar la SBC dos veces: el EBIT ya la tiene restada; sólo el flujo operativo la suma de vuelta.",
        "Tomar un año excepcional (cripto 2018 y 2022, la IA desde 2023) como representativo.",
        "Una tasa efectiva negativa o muy baja por créditos fiscales de un año: no se proyecta tal cual.",
    ],
    referencias=["Damodaran, Investment Valuation, cap. 10 y 12",
                 "Koller, Goedhart y Wessels (McKinsey), Valuation, cap. 9"],
    etiquetas=["dcf", "fcff", "free cash flow", "flujo libre", "valuación", "sbc", "capital de trabajo"],
    nivel="basico",
)
def flujo_caja_libre(activo, periodo="ejercicios", restar_sbc=True, id_inversion=False, vida_id=5, columnas=10):
    activo = (activo or "").strip()
    if not activo:
        raise ErrorMetodo("Falta la empresa (ticker de la Terminal).")
    anual = periodo == "ejercicios"
    d = balances(activo, "A" if anual else "T")
    if not anual and any(d.get(v, {}).get("frecuencia") == "A" for v in ("ingresos", "flujo_operativo")):
        raise ErrorMetodo(f"{activo} sólo presenta balances anuales: elegí «ejercicios».")
    S = {v: _serie(d, v) for v in VARIABLES}
    flujo = lambda v: S[v] if anual else _doce_meses(S[v])  # noqa: E731
    ebit, impuesto, rai = flujo("resultado_operativo"), flujo("impuesto_ganancias"), flujo("resultado_antes_impuestos")
    da, capex, fo = flujo("depreciacion"), flujo("capex"), flujo("flujo_operativo")
    sbc, intereses, rd, ventas = flujo("compensacion_acciones"), flujo("intereses"), flujo("investigacion_desarrollo"), flujo("ingresos")
    ct = (S["cuentas_por_cobrar"].add(S["inventario"], fill_value=0) - S["cuentas_por_pagar"]).dropna()
    fechas = ebit.index.intersection(da.index).intersection(capex.index).intersection(rai.index)
    if len(fechas) < 2:
        raise ErrorMetodo(f"Hay menos de 2 períodos con resultado operativo, D&A y capex para {activo}.")
    t = (impuesto / rai).where(rai > 0)
    ct_antes = _hace_un_anio(ct, fechas)
    dct = (ct.reindex(fechas) - ct_antes).dropna()
    nopat = ebit * (1 - t)
    reinversion = capex - da + dct
    fcff1 = nopat + da - capex - dct
    simple = fo - capex
    # El EBIT ya restó la SBC como gasto: el camino 1 la trata como costo. El flujo operativo, en
    # cambio, la suma de vuelta (no sale caja): para comparar, al camino 2 se le resta.
    sbc_r = sbc.reindex(simple.index).fillna(0)
    fcff2 = simple + intereses.reindex(simple.index).fillna(0) * (1 - t) - sbc_r
    control = fcff1 - fcff2
    fcff1_mas_sbc = fcff1 + sbc.reindex(fcff1.index).fillna(0)
    amort = pd.Series(dtype=float)
    if id_inversion and len(S["investigacion_desarrollo"]):
        base_rd = S["investigacion_desarrollo"]
        amort_base = _id_amortizada(base_rd, vida_id, anual)
        amort = amort_base if anual else _doce_meses(amort_base)
        extra = (rd - amort).dropna()
        nopat = nopat + extra.reindex(nopat.index)
        reinversion = reinversion + extra.reindex(reinversion.index)
    principal = fcff1 if restar_sbc else fcff1_mas_sbc
    nombre_p = "FCFF" if restar_sbc else "FCFF sin contar la SBC"

    # ── tabla renglón por renglón ──
    cols = [f for f in fechas if f in fcff1.dropna().index][-columnas:]
    if not cols:
        raise ErrorMetodo(f"No hay ningún período con todos los datos del FCFF para {activo}.")
    M = 1e6
    meses = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
    etiq = [(f"FE {f.year}" if anual else f"{meses[f.month - 1]}-{f.strftime('%y')}") for f in cols]
    fila = lambda nombre, s, esc=M, dec=0: [nombre] + [  # noqa: E731
        (round(s[f] / esc, dec) if f in s.index and pd.notna(s[f]) else None) for f in cols]
    pct = lambda nombre, s: [nombre] + [(round(100 * s[f], 1) if f in s.index and pd.notna(s[f]) else None) for f in cols]  # noqa: E731
    filas = [
        ["Camino 1 · desde el estado de resultados"] + [""] * len(cols),
        fila("Resultado operativo (EBIT)", ebit),
        pct("Tasa efectiva (%)", t),
        fila("− Impuestos sobre el EBIT", -(ebit * t)),
        fila("= NOPAT", ebit * (1 - t)),
    ]
    if id_inversion and len(amort):
        filas.append(fila("+ I+D del período − su amortización", (rd - amort)))
        filas.append(fila("= NOPAT con I+D como inversión", nopat))
    filas += [
        fila("+ Depreciaciones y amortizaciones", da),
        fila("− Capex", -capex),
        fila("− Aumento del capital de trabajo", -dct),
        fila("= FCFF (la SBC queda como costo: ya está restada dentro del EBIT)", fcff1),
        fila("+ Compensación en acciones (SBC), si no se la cuenta como costo", sbc),
        fila("= FCFF sin contar la SBC (como el flujo operativo)", fcff1_mas_sbc),
        ["Camino 2 · desde el estado de flujo de efectivo"] + [""] * len(cols),
        fila("Flujo operativo (ya trae la SBC sumada de vuelta)", fo),
        fila("− Capex", -capex),
        fila("= Flujo libre simple", simple),
        fila("+ Intereses × (1 − t)", intereses * (1 - t)),
        fila("− Compensación en acciones (SBC)", -sbc),
        fila("= FCFF (camino 2, comparable con el 1)", fcff2),
        ["Control"] + [""] * len(cols),
        fila("Diferencia camino 1 − camino 2", control),
        pct("Diferencia como % del FCFF", control / fcff1.abs()),
    ]
    r = Resultado()
    unidad = "millones de USD" + (", ejercicios" if anual else ", 12 meses móviles a cada cierre")
    r.tabla(f"{activo} · flujo de caja libre renglón por renglón ({unidad})", ["Renglón"] + etiq, filas,
            nota="Fuente: balances de la SEC vía la Terminal (cada dato con su presentación en la Ficha). La fila de "
                 "control no se fuerza a cero: si los caminos difieren, la diferencia está en partidas que el camino "
                 "1 no ve (otros activos y pasivos operativos, impuestos diferidos, resultados que no son caja).")

    ult = cols[-1]
    v = principal.get(ult)
    r.metrica(f"{nombre_p} último período", None if v is None or pd.isna(v) else round(v / M),
              f"{etiq[-1]}, millones de USD")
    r.metrica("FCFF / ventas último período", (fcff1 / ventas).get(ult), "margen de flujo libre", "pct")
    r.metrica("SBC / FCFF último período", (sbc / fcff1).get(ult), "cuánto del flujo se come la SBC", "pct")
    r.metrica("Tasa efectiva último período", t.get(ult), "impuesto / resultado antes de impuestos", "pct")

    # ── gráficos del paso ──
    hist = fcff1.dropna().index
    r.lineas(f"{activo} · FCFF por los dos caminos, sin contar la SBC y flujo libre simple (millones de USD)", hist,
             {"FCFF (camino 1)": fcff1.reindex(hist) / M, "FCFF (camino 2)": fcff2.reindex(hist) / M,
              "FCFF sin contar la SBC": fcff1_mas_sbc.reindex(hist) / M, "Flujo libre simple": simple.reindex(hist) / M},
             estilos={"FCFF (camino 2)": {"guion": "dash"}, "Flujo libre simple": {"guion": "dot"}}, eje_y="M USD")
    dv = (ventas.reindex(dct.index) - _hace_un_anio(ventas, dct.index)).dropna()
    if len(dv) >= 2:
        r.lineas(f"{activo} · ¿el capital de trabajo absorbe caja cuando crecen las ventas? (cambio en 12 meses)",
                 dv.index, {"Aumento de las ventas": dv / M, "Aumento del capital de trabajo": dct.reindex(dv.index) / M},
                 eje_y="M USD")
    tt = t.dropna()
    if len(tt) >= 2:
        r.lineas(f"{activo} · tasa impositiva efectiva", tt.index, {"Tasa efectiva (%)": 100 * tt}, eje_y="%")

    # ── series de salida (para el paso 2) ──
    for nombre, s, desc in (("FCFF", fcff1, "Flujo de caja libre de la firma, camino 1"),
                            ("FCFF sin contar la SBC", fcff1_mas_sbc, "FCFF sumando de vuelta la compensación en acciones"),
                            ("NOPAT", nopat, "Resultado operativo después de impuestos" + (" (I+D como inversión)" if id_inversion else "")),
                            ("Reinversión", reinversion, "Capex − D&A + aumento del capital de trabajo" + (" + I+D neta" if id_inversion else "")),
                            ("Tasa efectiva", t, "Impuesto / resultado antes de impuestos")):
        s = s.dropna()
        if len(s):
            r.serie(f"{activo} · {nombre}", s.index, s.values / (M if nombre != "Tasa efectiva" else 1), desc)

    validos = fcff1.dropna().index
    huecos = [str(f.date()) for f in ebit.index if f > validos.min() and f not in validos]
    if huecos:
        r.advertir(f"Faltan datos para el FCFF en {len(huecos)} período(s) (por ejemplo {huecos[0]}): la empresa no "
                   "informó alguna línea con la etiqueta estándar ese año.")
    if (t.dropna() < 0).any():
        r.advertir("Hay períodos con tasa efectiva negativa (créditos o beneficios fiscales): el NOPAT de esos "
                   "períodos queda por encima del resultado operativo.")
    def mm(x):
        return "s/d" if x is None or pd.isna(x) else f"{round(x / M):,}".replace(",", ".")
    r.resumen = (f"{activo}: FCFF por dos caminos en {len(cols)} períodos ({unidad}). Último ({etiq[-1]}): "
                 f"{nombre_p} = {mm(principal.get(ult))} M USD; diferencia entre caminos {mm(control.get(ult))} M USD.")
    r.datos = {"activo": activo, "periodo": periodo, "ultimo": str(ult.date())}
    return r
