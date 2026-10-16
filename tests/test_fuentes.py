"""Tests del registro de organismos y de la procedencia declarada en el catálogo.

No tocan la red: verifican que el catálogo se pueda auditar y citar sin salir a
internet. El cliente del BCRA se prueba con respuestas simuladas.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cueva.fuentes import bcra as mod_bcra
from cueva.fuentes import unidades
from cueva.fuentes.registro import OrganismoDesconocido, organismo, registro

RAIZ = Path(__file__).resolve().parent.parent
CATALOGO = json.loads((RAIZ / "cueva" / "datos" / "catalogo.json").read_text(encoding="utf-8"))

CAMPOS_OBLIGATORIOS = {"nombre", "sigla", "sitio", "licencia", "redistribuible"}


def _descender(items):
    """El catálogo anida hasta 5 niveles vía `children`: hay que bajar hasta el fondo."""
    for item in items:
        yield item
        yield from _descender(item.get("children") or [])


def _items():
    for fam in CATALOGO["familias"]:
        for sub in fam.get("subs", []):
            yield from _descender(sub["items"])
        yield from _descender(fam.get("items", []))


def _procedencias():
    """Todo bloque proc del catálogo: el de la serie y el de cada fuente de datos."""
    for item in _items():
        if item.get("proc"):
            yield item["id"], item["proc"]
        for fd in item.get("sources", []):
            if fd.get("proc"):
                yield f"{item['id']}@{fd.get('freq')}", fd["proc"]


# ------------------------------------------------------------------ registro

def test_registro_tiene_los_campos_que_hacen_falta_para_citar():
    for clave, org in registro().items():
        faltantes = CAMPOS_OBLIGATORIOS - set(org.datos)
        assert not faltantes, f"a la fuente '{clave}' le faltan {faltantes}"
        assert org.cita()


def test_organismo_desconocido_avisa_con_las_claves_validas():
    with pytest.raises(OrganismoDesconocido) as exc:
        organismo("banco_imaginario")
    assert "bcra" in str(exc.value)


# ------------------------------------------------------------------ catálogo

def test_toda_serie_declara_procedencia():
    sin_proc = [item["id"] for item in _items() if not item.get("proc")]
    assert not sin_proc, f"series sin bloque proc: {sin_proc[:10]}"


def test_toda_procedencia_apunta_a_una_fuente_conocida():
    conocidas = set(registro())
    for sid, proc in _procedencias():
        assert proc.get("fuente") in conocidas, f"{sid} declara la fuente '{proc.get('fuente')}'"


def test_las_series_propias_declaran_como_se_construyen():
    """Elaboración propia sin insumos ni transformación es una serie irreplicable."""
    huerfanas = [
        sid for sid, proc in _procedencias()
        if proc.get("fuente") == "propia" and not (proc.get("insumos") or proc.get("transformacion"))
    ]
    assert not huerfanas, f"series propias sin receta: {huerfanas[:10]}"


def test_la_confianza_es_uno_de_los_valores_previstos():
    validos = {"alta", "media", "baja", "verificada"}
    for sid, proc in _procedencias():
        assert proc.get("confianza") in validos, f"{sid} tiene confianza '{proc.get('confianza')}'"


# --------------------------------------------------------------- cliente BCRA

def test_variable_se_arma_con_los_nombres_de_campo_reales_de_la_api():
    """La v4 usa periodicidad/unidadExpresion/primerFechaInformada, no frecuencia/unidad/fechaInicio."""
    v = mod_bcra.VariableBCRA.desde_json({
        "idVariable": 1606,
        "descripcion": "Base monetaria",
        "categoria": "Agregados monetarios y sus componentes",
        "tipoSerie": "Saldos",
        "periodicidad": "M",
        "unidadExpresion": "En miles de ARS",
        "moneda": "ML",
        "primerFechaInformada": "1940-06-30",
        "ultFechaInformada": "2026-06-30",
        "ultValorInformado": 45711975442.0,
    })
    assert (v.periodicidad, v.unidad, v.moneda) == ("M", "En miles de ARS", "ML")
    assert (v.desde, v.hasta) == ("1940-06-30", "2026-06-30")
    assert v.slug == "1606_base_monetaria"


def test_slug_es_estable_y_sin_acentos():
    assert mod_bcra._slug("Inflación mensual", 27) == "0027_inflacion_mensual"


def test_observaciones_aplana_la_respuesta_anidada_y_descarta_nulos():
    payload = {"results": [{"idVariable": 15, "detalle": [
        {"fecha": "2026-08-24", "valor": 100.5},
        {"fecha": "2026-08-25", "valor": None},
        {"fecha": "2026-08-26", "valor": 101},
    ]}]}
    assert list(mod_bcra._observaciones(payload)) == [
        ("2026-08-24", 100.5), ("2026-08-26", 101.0),
    ]


def test_observaciones_tolera_la_forma_plana():
    payload = {"results": [{"fecha": "2026-01-02", "valor": 7}]}
    assert list(mod_bcra._observaciones(payload)) == [("2026-01-02", 7.0)]


def test_serie_pagina_y_deduplica_el_borde(monkeypatch):
    """La API corta en LIMITE_PAGINA_SERIE: el cliente tiene que pedir la página siguiente."""
    monkeypatch.setattr(mod_bcra, "LIMITE_PAGINA_SERIE", 2)
    paginas = [
        {"results": [{"detalle": [
            {"fecha": "2026-01-01", "valor": 1}, {"fecha": "2026-01-02", "valor": 2}]}]},
        {"results": [{"detalle": [
            {"fecha": "2026-01-02", "valor": 2}, {"fecha": "2026-01-03", "valor": 3}]}]},
        {"results": []},
    ]
    llamadas: list[dict] = []

    def falso_pedir(self, ruta, **params):
        llamadas.append(params)
        return paginas[len(llamadas) - 1]

    monkeypatch.setattr(mod_bcra.ClienteBCRA, "_pedir", falso_pedir)
    cli = mod_bcra.ClienteBCRA()
    assert cli.serie(15, desde="2026-01-01", hasta="2026-01-31") == [
        ("2026-01-01", 1.0), ("2026-01-02", 2.0), ("2026-01-03", 3.0),
    ]
    assert [c["Offset"] for c in llamadas] == [0, 2, 4]


def test_variables_pagina_hasta_que_la_pagina_vuelve_corta(monkeypatch):
    """`count` es lo que queda desde el offset, no el total: cortar por página corta."""
    monkeypatch.setattr(mod_bcra, "LIMITE_PAGINA_INDICE", 2)

    def var(i):
        return {"idVariable": i, "descripcion": f"v{i}", "categoria": "X", "tipoSerie": "Saldos",
                "periodicidad": "M", "unidadExpresion": "u", "moneda": "ML",
                "primerFechaInformada": "1940-06-30", "ultFechaInformada": "2026-06-30"}

    paginas = [
        {"metadata": {"resultset": {"count": 3}}, "results": [var(1), var(2)]},
        {"metadata": {"resultset": {"count": 1}}, "results": [var(3)]},
    ]
    llamadas: list[dict] = []

    def falso_pedir(self, ruta, **params):
        llamadas.append(params)
        return paginas[len(llamadas) - 1]

    monkeypatch.setattr(mod_bcra.ClienteBCRA, "_pedir", falso_pedir)
    assert [v.id for v in mod_bcra.ClienteBCRA().variables()] == [1, 2, 3]
    assert [c["Offset"] for c in llamadas] == [0, 2]


def test_las_series_historicas_del_bcra_estan_en_el_catalogo():
    """El bloque que el BCRA publicó el 2026-08-21 tiene que estar y llegar a 1940."""
    por_id = {item["id"]: item for item in _items()}
    for sid in ("bm_hist", "m1_ml", "m2_ml", "m3_ml", "res_mensual"):
        assert sid in por_id, f"falta la serie histórica '{sid}'"
        proc = por_id[sid]["proc"]
        assert proc["fuente"] == "bcra"
        assert proc["cobertura"]["desde"].startswith("1940"), proc["cobertura"]


# ------------------------------------------------------------------ unidades

def test_toda_unidad_del_catalogo_esta_en_el_vocabulario():
    """Si el catálogo estrena una unidad, hay que darla de alta en unidades.json."""
    desconocidas = sorted({
        item.get("unit", "") for item in _items()
        if unidades.interpretar(item.get("unit", "")).magnitud == "desconocida"
    })
    assert not desconocidas, (
        f"unidades fuera del vocabulario: {desconocidas}. "
        "Agregalas a cueva/fuentes/unidades.json"
    )


def test_interpretar_descompone_magnitud_escala_y_moneda():
    u = unidades.interpretar("Miles de ARS")
    assert (u.magnitud, u.escala, u.moneda, u.factor) == ("moneda", "miles", "ARS", 1000)


def test_dos_escalas_distintas_de_la_misma_moneda_no_son_comparables():
    """La trampa del BCRA: el bloque histórico va en miles y el diario en millones."""
    historica = unidades.interpretar("Miles de ARS")
    diaria = unidades.interpretar("Mill. ARS")
    assert not historica.comparable_con(diaria)
    assert diaria.factor // historica.factor == 1000


def test_unidad_desconocida_no_rompe_salvo_que_se_pida():
    assert unidades.interpretar("qué es esto").magnitud == "desconocida"
    with pytest.raises(unidades.UnidadDesconocida):
        unidades.interpretar("qué es esto", estricto=True)
