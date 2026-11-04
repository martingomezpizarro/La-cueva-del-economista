"""Tests del catálogo de métodos (cueva/metodos).

Tres capas de guardarraíl:
1. CONTRATO: todo método registrado está bien declarado, tiene un caso de prueba en ARGS y
   corre devolviendo bloques válidos y JSON serializable. Sumar un método sin sumarlo a ARGS
   rompe `test_todo_metodo_tiene_caso`.
2. CONCLUSIONES: sobre series sintéticas de propiedades CONOCIDAS (tests/sinteticas_metodos.py)
   cada método importante llega a la conclusión correcta (y rechaza la incorrecta).
3. PROTOCOLO: la validación fuera de muestra no filtra el futuro y las redes en numpy tienen
   el gradiente bien.
"""

from __future__ import annotations

import json

import numpy as np
import pytest

from cueva.datos import series as S
from cueva.metodos import catalogo, ejecutar
from cueva.metodos import registro as MR
from cueva.metodos.contrato import FAMILIAS, TIPOS_PARAM
from tests import sinteticas_metodos as SM

TIPOS_BLOQUE = {
    "metricas",
    "tabla",
    "lineas",
    "bandas",
    "barras",
    "mapa_calor",
    "dispersion",
    "texto",
    "veredicto",
}


@pytest.fixture()
def banco(tmp_path, monkeypatch):
    tf = tmp_path / "trabajo"
    datos = tf / "data" / "Variables Finales"
    datos.mkdir(parents=True)
    SM.generar(datos)
    monkeypatch.setenv("CUEVA_TRABAJO_FINAL", str(tf))
    monkeypatch.setenv("CUEVA_MATRIZ_ARG", str(tmp_path / "sin_matriz"))
    (tmp_path / "sin_matriz").mkdir()
    S.refrescar()
    yield datos
    S.refrescar()


# Diseño común para los modelos predictivos (objetivo no lineal conocido)
ML = dict(
    dep="pred_y", indeps=["pred_x"], transf="nivel", transf_x="nivel", rezagos_y=2, rezagos_x=2, n_test=30
)
RED = dict(dep="pred_y", indeps=["pred_x"], transf="nivel", ventana=4, semillas=1, n_test=20)

ARGS: dict[str, dict] = {
    # exploratorio
    "estadisticos": dict(sid="ar1"),
    "acf_pacf": dict(sid="ar1"),
    "correlacion_cruzada": dict(sid_x="pred_x", sid_y="pred_y", transf="nivel"),
    "periodograma": dict(sid="estacional", transf="nivel"),
    "perfil_estacional": dict(sid="estacional", transf="nivel"),
    "ventanas_moviles": dict(sids=["ar1", "paseo"], transf="dif"),
    "dispersion": dict(sid_x="coint_x", sid_y="coint_y", transf="dif"),
    "matriz_correlacion": dict(sids=["fac0", "fac1", "fac2"], transf="dif"),
    # pruebas
    "raiz_unitaria": dict(sid="paseo"),
    "quiebres_estructurales": dict(sid="quiebre"),
    "cambio_de_punto": dict(sid="quiebre", transf="nivel", costo="l2"),
    "prueba_chow": dict(dep="quiebre", fecha="2012-01", transf="nivel"),
    "cusum": dict(dep="quiebre", transf="nivel"),
    "normalidad": dict(sid="garch_ret", transf="nivel"),
    "no_linealidad_bds": dict(sid="garch_ret", transf="nivel"),
    "memoria_larga": dict(sid="ar1", transf="nivel"),
    "heterocedasticidad": dict(dep="coint_y", indeps=["coint_x"], transf="nivel"),
    # filtros
    "filtro_hp": dict(sid="positiva"),
    "filtro_hamilton": dict(sid="positiva"),
    "filtro_bandas": dict(sid="positiva"),
    "descomposicion_stl": dict(sid="positiva"),
    "beveridge_nelson": dict(sid="positiva"),
    "componentes_no_observados": dict(sid="positiva", ciclo=False),
    # univariados
    "benchmarks": dict(sid="estacional", transf="nivel"),
    "sarima": dict(sid="ar1", transf="nivel", automatico=False, p=1, d=0, q=0, horizonte=3),
    "suavizado_exponencial": dict(sid="estacional", transf="nivel", automatico=False, estacional="aditiva"),
    "theta": dict(sid="positiva", transf="nivel"),
    # volatilidad
    "garch_familia": dict(sid="garch_ret", transf="nivel", modelos=["GARCH", "GJR"]),
    "valor_en_riesgo": dict(sid="garch_ret", transf="nivel"),
    # regresión
    "mco": dict(dep="coint_y", indeps=["coint_x"], transf="dif", rezagos_x=1),
    "regresion_cuantilica": dict(dep="coint_y", indeps=["coint_x"], transf="dif"),
    "regresion_robusta": dict(dep="coint_y", indeps=["coint_x"], transf="dif"),
    "regresion_movil": dict(dep="coint_y", indeps=["coint_x"], transf="dif"),
    "variables_instrumentales": dict(
        dep="coint_y", endogenas=["coint_x"], instrumentos=["fac0"], transf="dif"
    ),
    "rezagos_distribuidos": dict(dep="pred_y", sid_x="pred_x", transf="nivel"),
    # multivariados
    "var_completo": dict(sids=["pred_x", "pred_y"], transf="nivel"),
    "proyecciones_locales": dict(dep="pred_y", impulso="pred_x", transf="nivel", horizonte=6),
    "toda_yamamoto": dict(sid_x="coint_x", sid_y="coint_y", transf="nivel"),
    "bvar_minnesota": dict(sids=["coint_x", "coint_y"], transf="nivel"),
    # cointegración
    "engle_granger": dict(dep="coint_y", indeps=["coint_x"], transf="nivel"),
    "ardl_limites": dict(dep="coint_y", indeps=["coint_x"], transf="nivel"),
    "johansen_vecm": dict(sids=["coint_y", "coint_x", "paseo"], transf="nivel"),
    "mco_dinamicos": dict(dep="coint_y", indeps=["coint_x"], transf="nivel"),
    # regímenes
    "markov_switching": dict(sid="markov", transf="nivel"),
    "umbral_setar": dict(sid="ar1", transf="nivel", bootstrap=49),
    "transicion_suave": dict(sid="ar1", transf="nivel"),
    # estado
    "tvp_kalman": dict(dep="coint_y", indeps=["coint_x"], transf="dif"),
    "factor_dinamico": dict(sids=["fac0", "fac1", "fac2", "fac3"], transf="dif"),
    "desagregacion_temporal": dict(sid_baja="positiva", freq_baja="trimestral", indicadores=["positiva"]),
    # causal
    "serie_interrumpida": dict(sid="tratada", transf="nivel", fecha="2016-01"),
    "impacto_causal": dict(
        sid="tratada", controles=["control"], transf="nivel", fecha="2016-01", bootstrap=100
    ),
    "control_sintetico": dict(
        sid="tratada", donantes=["control", "coint_x", "fac0"], transf="nivel", fecha="2016-01"
    ),
    "diferencias_en_diferencias": dict(sid="tratada", control="control", transf="nivel", fecha="2016-01"),
    "estudio_eventos": dict(sid="quiebre", transf="nivel", fechas="2008-01, 2012-01, 2016-01"),
    # ml
    **{
        f"ml_{m}": dict(ML)
        for m in ["ridge", "lasso", "elastic_net", "knn", "svr", "arbol", "hist_gbm", "xgboost", "lightgbm"]
    },
    "ml_random_forest": dict(ML, arboles=60),
    "ml_extra_trees": dict(ML, arboles=60),
    "ml_gbm": dict(ML, arboles=80),
    "ml_proceso_gaussiano": dict(ML),
    "ml_mlp": dict(ML, capas="16"),
    "ml_shap": dict(ML, arboles=80),
    "probabilidad_evento": dict(dep="positiva", indeps=["pred_x"], umbral=0.02, horizonte=3),
    "seleccion_variables": dict(
        dep="pred_y", candidatas=["pred_x", "ar1", "paseo"], transf="nivel", submuestras=20
    ),
    # redes
    "red_lstm": dict(RED, ocultas=6, epocas=40),
    "red_gru": dict(RED, ocultas=6, epocas=40),
    "red_reservorio": dict(RED, unidades=60),
    # no supervisado
    "componentes_principales": dict(sids=["fac0", "fac1", "fac2", "fac3"], transf="dif"),
    "clusters_series": dict(sids=["fac0", "fac1", "fac2", "ar1", "paseo"], transf="dif"),
    "clusters_periodos": dict(sids=["markov", "garch_ret"], transf="nivel", grupos=2),
    "anomalias": dict(sid="garch_ret", transf="nivel"),
    # evaluación
    "torneo_modelos": dict(ML, modelos=["ar_lineal", "ridge", "knn"]),
    "curva_especificaciones": dict(
        dep="coint_y",
        interes="coint_x",
        controles=["ar1"],
        transformaciones=["dif"],
        rezagos=["0", "1"],
        muestras=["completa"],
    ),
    # finanzas
    "metricas_rendimiento": dict(sids=["mercado", "accion_a"]),
    "montecarlo_cartera": dict(sids=["mercado", "accion_a"], simulaciones=500, horizonte=10),
    "montecarlo_umbral": dict(
        sid="mercado", nivel_objetivo=1.0, horizonte=20, simulaciones=500, metodo="gbm"
    ),
    "frontera_eficiente": dict(
        sids=["mercado", "accion_a", "accion_b"], freq="semanal", ventana=52, rebalanceo=8
    ),
    "cruce_medias": dict(sid="mercado", rapida=10, lenta=50),
    "momentum_regimen": dict(sids=["mercado"], formacion=60, salto=5, ventana_regimen=21),
    "pares_trading": dict(sid_a="par_a", sid_b="par_b"),
    "regimenes_volatilidad": dict(sid="mercado", regimenes=2),
    "estacionalidad_calendario": dict(sid="intradia", mapa="hora_x_dia", medida="volatilidad"),
    "neutralidad_factores": dict(sid="accion_a", factores=["mercado"]),
    # fase M1: activos, eventos y robustez
    "burbuja_gsadf": dict(sid="burbuja", simulaciones=49),
    "sobreajuste_backtest": dict(sid="mercado", bloques=6, bootstrap=100),
    "apuesta_binaria": dict(probabilidad=0.62, precio=0.5, apuestas=50),
    "triple_barrera": dict(sid="mercado", horizonte=10, modelo="logit"),
    "eventos_mercado": dict(sid="accion_a", mercado="mercado", fechas="2019-03-01, 2020-03-02, 2021-06-01"),
    "contagio_diebold_yilmaz": dict(sids=["mercado", "accion_a", "accion_b"], freq="mensual"),
    "dcc_garch": dict(sids=["mercado", "accion_a"]),
    "colas_extremas": dict(sid="mercado"),
    "curva_nelson_siegel": dict(sids=["fac0", "fac1", "fac2", "fac3"], plazos="0.25, 1, 5, 10"),
    "intervalos_conformales": dict(ML, modelo="svr"),
}


# ──────────────────────────────────────────────────────────────────────────
# 1. Contrato
# ──────────────────────────────────────────────────────────────────────────
def test_catalogo_bien_declarado():
    cat = catalogo()
    assert len(cat) >= 80
    ids = [m["id"] for m in cat]
    assert len(ids) == len(set(ids))
    for m in cat:
        assert m["familia"] in FAMILIAS, m["id"]
        assert m["pregunta"].strip(), m["id"]
        assert m["trampas"] or m["supuestos"] or m["cuando"], f"{m['id']} no dice nada de su uso"
        for p in m["params"]:
            assert p["tipo"] in TIPOS_PARAM
        json.dumps(MR.obtener(m["id"]).esquema())


def test_todo_metodo_tiene_caso():
    faltan = set(MR.registro()) - set(ARGS)
    assert not faltan, f"Métodos sin caso de prueba en ARGS: {sorted(faltan)}"


@pytest.mark.parametrize("mid", sorted(ARGS))
def test_metodo_corre_y_cumple_contrato(banco, mid):
    m = MR.obtener(mid)
    if MR.faltantes(m):
        pytest.skip(f"faltan dependencias: {MR.faltantes(m)}")
    r = ejecutar(mid, ARGS[mid])
    assert r["ok"], r["resumen"]
    assert r["resumen"]
    assert r["bloques"], "un método tiene que mostrar algo"
    for b in r["bloques"]:
        assert b["tipo"] in TIPOS_BLOQUE
    json.dumps(r, allow_nan=False)  # NaN/inf ya saneados


def test_errores_de_usuario_no_rompen(banco):
    r = ejecutar("raiz_unitaria", {"sid": "no_existe"})
    assert r["ok"] is False and "no_existe" in r["resumen"]
    r = ejecutar("quiebres_estructurales", {"sid": "quiebre", "max_quiebres": 99})
    assert r["ok"] is False and "≤" in r["resumen"]
    r = ejecutar("prueba_chow", {"dep": "quiebre"})
    assert r["ok"] is False and "Falta" in r["resumen"]
    assert ejecutar("metodo_inexistente", {})["ok"] is False


# ──────────────────────────────────────────────────────────────────────────
# 2. Conclusiones sobre propiedades conocidas
# ──────────────────────────────────────────────────────────────────────────
def test_raiz_unitaria_distingue_i1_de_i0(banco):
    assert ejecutar("raiz_unitaria", {"sid": "paseo"})["datos"]["orden"] == 1
    assert ejecutar("raiz_unitaria", {"sid": "ar1"})["datos"]["orden"] == 0


def test_bai_perron_encuentra_el_quiebre_de_2012(banco):
    r = ejecutar("quiebres_estructurales", {"sid": "quiebre"})
    assert r["metricas"]["Quiebres elegidos"] == 1
    assert r["datos"]["quiebres"][0][:7] in ("2011-12", "2012-01", "2012-02")


def test_cointegracion_detecta_el_par_verdadero_y_rechaza_el_falso(banco):
    assert (
        ejecutar("engle_granger", {"dep": "coint_y", "indeps": ["coint_x"], "transf": "nivel"})["datos"]["p"]
        < 0.01
    )
    assert (
        ejecutar("engle_granger", {"dep": "paseo", "indeps": ["coint_x"], "transf": "nivel"})["datos"]["p"]
        > 0.1
    )
    assert ejecutar("johansen_vecm", ARGS["johansen_vecm"])["datos"]["rango"] == 1


def test_dols_recupera_la_elasticidad(banco):
    r = ejecutar("mco_dinamicos", ARGS["mco_dinamicos"])
    assert abs(r["metricas"]["β coint_x"] - 0.8) < 0.03


def test_markov_recupera_las_medias_de_los_regimenes(banco):
    r = ejecutar("markov_switching", ARGS["markov_switching"])
    medias = sorted(f[1] for f in next(b for b in r["bloques"] if b["tipo"] == "tabla")["filas"])
    assert abs(medias[0] - 0) < 0.4 and abs(medias[1] - 3) < 0.4


def test_impacto_causal_y_sintetico_estiman_el_escalon(banco):
    r = ejecutar("impacto_causal", ARGS["impacto_causal"])
    assert 4 < r["metricas"]["Efecto promedio por período"] < 6.5
    r = ejecutar("control_sintetico", ARGS["control_sintetico"])
    assert 4 < r["metricas"]["Efecto promedio posterior"] < 6.5


def test_did_rechaza_un_control_sin_tendencias_paralelas(banco):
    ok = ejecutar("diferencias_en_diferencias", ARGS["diferencias_en_diferencias"])
    malo = ejecutar("diferencias_en_diferencias", dict(ARGS["diferencias_en_diferencias"], control="paseo"))
    assert ok["semaforo"] != "rojo"
    assert malo["semaforo"] == "rojo"


def test_desagregacion_respeta_los_totales(banco):
    r = ejecutar("desagregacion_temporal", ARGS["desagregacion_temporal"])
    assert r["metricas"]["Error máx. al re-agregar"] < 1e-8


def test_ml_no_lineal_le_gana_al_lineal_en_el_torneo(banco):
    r = ejecutar("torneo_modelos", dict(ML, modelos=["ar_lineal", "svr", "knn"]))
    ranking = [f[0] for f in r["datos"]["ranking"]]
    assert ranking.index("SVR") < ranking.index("AR lineal (MCO)")
    assert ranking[-1] in ("Paseo aleatorio", "Media histórica")


def test_probabilidad_de_evento_mejora_a_la_frecuencia_historica(banco):
    r = ejecutar("probabilidad_evento", ARGS["probabilidad_evento"])
    assert r["datos"]["bss"] > 0 and r["datos"]["auc"] > 0.6
    assert 0 <= r["datos"]["p_hoy"] <= 1


def test_pares_y_neutralidad(banco):
    bueno = ejecutar("pares_trading", ARGS["pares_trading"])
    malo = ejecutar("pares_trading", dict(sid_a="mercado", sid_b="neutral"))
    assert bueno["metricas"]["Cointegración en formación (p)"] < 0.05
    assert malo["semaforo"] == "rojo"
    r = ejecutar("neutralidad_factores", dict(sid="neutral", factores=["mercado"]))
    assert r["semaforo"] == "verde"
    r = ejecutar("neutralidad_factores", ARGS["neutralidad_factores"])
    assert r["semaforo"] == "amarillo"


def test_estacionalidad_intradia_ve_la_apertura_y_el_cierre(banco):
    r = ejecutar("estacionalidad_calendario", ARGS["estacionalidad_calendario"])
    assert r["metricas"]["Kruskal-Wallis por columna (p)"] < 0.01


def test_gsadf_detecta_la_burbuja_y_no_el_paseo(banco):
    si = ejecutar("burbuja_gsadf", dict(sid="burbuja", simulaciones=99))
    no = ejecutar("burbuja_gsadf", dict(sid="paseo", transf="nivel", simulaciones=99))
    assert si["metricas"]["GSADF"] > si["metricas"]["Crítico 95 %"]
    assert si["metricas"]["Episodios"] >= 1
    assert no["metricas"]["GSADF"] < no["metricas"]["Crítico 95 %"]


def test_apuesta_binaria_signo_del_valor_esperado():
    buena = ejecutar("apuesta_binaria", dict(probabilidad=0.7, precio=0.5, incertidumbre=0.02))
    mala = ejecutar("apuesta_binaria", dict(probabilidad=0.505, precio=0.5, comision=0.02))
    assert buena["metricas"]["Valor esperado por contrato"] > 0 and buena["semaforo"] == "verde"
    assert mala["semaforo"] == "rojo"
    # p < precio ⇒ conviene el NO
    assert (
        ejecutar("apuesta_binaria", dict(probabilidad=0.2, precio=0.5))["metricas"]["Lado conveniente"]
        == "NO"
    )


def test_sobreajuste_y_conjunto_de_confianza(banco):
    r = ejecutar("sobreajuste_backtest", ARGS["sobreajuste_backtest"])
    assert 0 <= r["datos"]["pbo"] <= 1 and 0 <= r["datos"]["dsr"] <= 1
    t = ejecutar("torneo_modelos", dict(ML, modelos=["ar_lineal", "svr", "knn"]))
    assert "Paseo aleatorio" not in t["datos"]["mcs"]  # el paseo queda fuera del conjunto


def test_conformal_cubre_cerca_de_lo_nominal(banco):
    r = ejecutar("intervalos_conformales", dict(ML, modelo="svr", n_test=60, cobertura=0.9))
    assert 75 <= r["metricas"]["Cobertura observada %"] <= 100


# ──────────────────────────────────────────────────────────────────────────
# 3. Protocolo
# ──────────────────────────────────────────────────────────────────────────
def test_origen_movil_no_mira_el_futuro():
    import pandas as pd

    from cueva.metodos.validacion import origen_movil

    n, h = 80, 3
    X = pd.DataFrame(
        {"a": np.arange(n, dtype=float)}, index=pd.date_range("2000-01-31", periods=n, freq="ME")
    )
    y = pd.Series(np.arange(n, dtype=float) + h, index=X.index)
    vistos = []

    class Espia:
        def fit(self, Xa, ya):
            vistos.append(len(Xa))
            self.ult = Xa[-1, 0]
            return self

        def predict(self, Xp):
            # en el origen i sólo pudo ver filas t ≤ i − h (objetivo ya realizado)
            assert self.ult <= Xp[0, 0] - h
            return np.array([0.0])

    origen_movil(X, y, Espia, h, 10, X["a"])
    assert vistos and max(vistos) <= n - h


def test_diebold_mariano_detecta_al_mejor():
    from cueva.metodos.validacion import diebold_mariano

    rng = np.random.default_rng(0)
    e_bueno, e_malo = rng.normal(0, 1, 200), rng.normal(0, 2, 200)
    stat, p = diebold_mariano(e_bueno, e_malo)
    assert stat < 0 and p < 0.01


@pytest.mark.parametrize("celda", ["lstm", "gru"])
def test_gradiente_de_las_redes_en_numpy(celda):
    from cueva.metodos.redes_np import RecurrenteNP

    rng = np.random.default_rng(0)
    m = RecurrenteNP(celda, ocultas=4, l2=1e-3)
    m._init(2)
    X, y = rng.normal(size=(5, 4, 2)), rng.normal(size=5)
    _, g = m._gradientes(X, y)
    for k in m.p:
        idx = tuple(rng.integers(0, s) for s in m.p[k].shape)
        v = m.p[k][idx]
        m.p[k][idx] = v + 1e-6
        lp, _ = m._gradientes(X, y)
        m.p[k][idx] = v - 1e-6
        lm, _ = m._gradientes(X, y)
        m.p[k][idx] = v
        num = (lp - lm) / 2e-6
        assert abs(num - g[k][idx]) <= 1e-5 * max(1, abs(num)), (k, num, g[k][idx])


# ──────────────────────────────────────────────────────────────────────────
# Integración: herramientas, agentes, API, mis series
# ──────────────────────────────────────────────────────────────────────────
def test_puente_con_herramientas_y_comodines(banco):
    from cueva.econometria import herramientas as H

    r = H.ejecutar("raiz_unitaria", sid="ar1")
    assert r["ok"] and r["metodo"] == "raiz_unitaria"
    decl = H.declaraciones_herramientas(["familia:pruebas", "describir"])
    nombres = {d["name"] for d in decl}
    assert {"raiz_unitaria", "quiebres_estructurales", "describir"} <= nombres
    assert all("parameters_json_schema" in d for d in decl)


def test_api_metodos_y_mis_series(banco):
    from fastapi.testclient import TestClient

    from cueva.api.app import crear_app

    c = TestClient(crear_app())
    d = c.get("/api/v1/metodos").json()
    assert len(d["metodos"]) >= 80 and d["familias"]
    assert c.get("/api/v1/metodos/raiz_unitaria").json()["id"] == "raiz_unitaria"
    assert c.get("/api/v1/metodos/nada").status_code == 404
    r = c.post("/api/v1/herramienta", json={"nombre": "filtro_hp", "args": {"sid": "positiva"}}).json()
    assert r["ok"] and r["series_salida"]
    # una salida guardada como serie entra al catálogo y sirve de insumo
    s = r["series_salida"][1]
    g = c.post(
        "/api/v1/mis-series/derivada",
        json={"nombre": "ciclo hp", "fechas": s["fechas"], "valores": s["valores"]},
    ).json()
    assert g["id"] == "mis_ciclo_hp"
    r2 = c.post("/api/v1/herramienta", json={"nombre": "acf_pacf", "args": {"sid": "mis_ciclo_hp"}}).json()
    assert r2["ok"], r2["resumen"]
    # subir un CSV propio con varias columnas (OHLC)
    csv = "fecha;cierre;volumen\n" + "\n".join(
        f"2024-01-{d:02d};{100 + d},5;{1000 + d}" for d in range(1, 29)
    )
    up = c.post("/api/v1/mis-series", files={"archivo": ("Mi Acción.csv", csv.encode(), "text/csv")})
    assert up.status_code == 200, up.text
    ids = {x["id"] for x in up.json()["series"]}
    assert {"mis_mi_accion__cierre", "mis_mi_accion__volumen"} <= ids
    assert (
        c.post("/api/v1/mis-series", files={"archivo": ("x.txt", b"hola", "text/plain")}).status_code == 422
    )
    assert c.delete("/api/v1/mis-series/mis_mi_accion.csv").json()["ok"]
