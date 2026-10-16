"""Tests de la cronología argentina.

La tabla de presidencias es un dato como cualquier otro: si tiene un hueco, una fecha
mal escrita o dos presidentes el mismo día, cualquier cruce contra una serie de tiempo
devuelve algo falso sin avisar. Estos tests son el control.
"""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
PRESIDENCIAS = RAIZ / "data" / "historia" / "presidencias.csv"

TIPOS = {"constitucional", "de_facto", "provisional", "interino", "junta_militar"}
INICIO = date(1880, 10, 12)


@pytest.fixture(scope="module")
def periodos() -> list[dict]:
    if not PRESIDENCIAS.exists():
        pytest.skip("falta data/historia/presidencias.csv (correr scripts/construir_presidencias.py)")
    return list(csv.DictReader(PRESIDENCIAS.open(encoding="utf-8")))


def _fecha(texto: str) -> date | None:
    return date.fromisoformat(texto) if texto else None


def test_arranca_en_1880_y_llega_hasta_hoy(periodos):
    assert _fecha(periodos[0]["desde"]) == INICIO
    assert periodos[-1]["hasta"] == "", "el último período debe quedar abierto"


def test_las_fechas_son_validas_y_cada_periodo_avanza(periodos):
    for p in periodos:
        desde, hasta = _fecha(p["desde"]), _fecha(p["hasta"])
        assert desde is not None, f"{p['nombre']} sin fecha de inicio"
        if hasta is not None:
            assert hasta > desde, f"{p['nombre']}: termina antes de empezar"


def test_la_linea_de_tiempo_no_tiene_huecos(periodos):
    """Una fecha cualquiera entre 1880 y hoy tiene que resolver a alguien.

    Las juntas militares están en la tabla justamente para cerrar los cinco huecos
    que dejaban los traspasos de 1955, 1966, 1970, 1971 y 1976.
    """
    huecos = [
        f"{a['nombre']} termina {a['hasta']} y {b['nombre']} empieza {b['desde']}"
        for a, b in zip(periodos, periodos[1:], strict=False)
        if _fecha(a["hasta"]) and _fecha(b["desde"]) > _fecha(a["hasta"])
    ]
    assert not huecos, f"días sin nadie a cargo: {huecos}"


def test_no_hay_dos_a_la_vez(periodos):
    solapes = [
        f"{a['nombre']} hasta {a['hasta']} pisa a {b['nombre']} desde {b['desde']}"
        for a, b in zip(periodos, periodos[1:], strict=False)
        if _fecha(a["hasta"]) and _fecha(b["desde"]) < _fecha(a["hasta"])
    ]
    assert not solapes, f"períodos superpuestos: {solapes}"


def test_los_tipos_son_del_vocabulario(periodos):
    malos = {p["tipo"] for p in periodos} - TIPOS
    assert not malos, f"tipos fuera del vocabulario: {malos}"


def test_toda_fila_declara_fuente_y_estado_de_verificacion(periodos):
    """Igual que las series: sin fuente declarada, un dato no es citable."""
    for p in periodos:
        assert p["fuente"], f"{p['nombre']} sin fuente"
        assert p["verificado"] in {"sí", "no"}, f"{p['nombre']}: verificado='{p['verificado']}'"


def test_estan_los_que_los_listados_automaticos_suelen_perder(periodos):
    """Los interinos de diciembre de 2001 y los breves de 1943, 1981 y 1982.

    No es un capricho: la semana del default de 2001 pasó por Puerta, Rodríguez Saá y
    Camaño, y sin ellos cualquier serie diaria de ese diciembre queda sin gobierno.
    """
    nombres = " · ".join(p["nombre"] for p in periodos)
    for quien in ("Ramón Puerta", "Eduardo Camaño", "Arturo Rawson",
                  "Carlos Alberto Lacoste", "Alfredo Óscar Saint-Jean", "Javier Milei"):
        assert quien in nombres, f"falta {quien}"


def test_quien_gobernaba_resuelve_fechas_conocidas(periodos):
    def gobernaba(cuando: date) -> str:
        for p in periodos:
            desde, hasta = _fecha(p["desde"]), _fecha(p["hasta"])
            if desde <= cuando and (hasta is None or cuando < hasta):
                return p["nombre"]
        return ""

    # El día que Rodríguez Saá anuncia el default de la deuda soberana.
    assert gobernaba(date(2001, 12, 24)) == "Adolfo Rodríguez Saá"
    # El golpe que derroca a Yrigoyen.
    assert gobernaba(date(1930, 9, 7)) == "José Félix Uriburu"
    # Plena convertibilidad.
    assert gobernaba(date(1995, 1, 2)) == "Carlos Saúl Menem"


# ═══════════════════════════════════════════════════════════════════════════
# Eventos, fichas y bibliografía — el resto del módulo Línea de Tiempo.
# Los datos se testean como código: si una ficha cita una obra que no está en
# referencias.bib, o un {{c:x}} apunta a una cifra que no existe, la suite lo dice.
# ═══════════════════════════════════════════════════════════════════════════

from cueva.datos import historia as H  # noqa: E402


def test_los_datos_de_historia_son_consistentes():
    """El chequeo completo de `validar()`: vocabulario, refs cruzadas, cifras, medios."""
    errores = H.validar()
    assert not errores, "errores en data/historia/:\n  - " + "\n  - ".join(errores)


def test_sin_fuente_no_hay_evento():
    for e in H.cargar_eventos():
        assert e.refs or e.fuente, f"{e.id} no declara ni refs ni fuente"


def test_los_ids_de_evento_son_slugs_unicos():
    ids = [e.id for e in H.cargar_eventos()]
    assert len(ids) == len(set(ids)), "hay ids repetidos en eventos.csv"
    for i in ids:
        assert H.ID_RE.match(i), f"id mal formado: {i}"


def test_el_gobierno_se_deriva_por_fecha_y_no_se_guarda():
    """§8.1: guardar el gobierno de cada evento lo desincronizaría al corregir un traspaso."""
    assert H.gobierno_en(date(1890, 8, 6)).nombre == "Carlos Pellegrini"
    assert H.gobierno_en(date(1935, 5, 31)).nombre == "Agustín Pedro Justo"
    assert not hasattr(H.cargar_eventos()[0], "gobierno")


def test_la_ficha_resuelve_sus_cifras_y_sus_citas():
    f = H.cargar_ficha("crisis-baring-1890")
    assert f is not None
    titulos = [s["titulo"] for s in f.secciones]
    assert "Contexto" in titulos and "Cronología" in titulos
    assert f.cifras, "la ficha no declara cifras"
    assert all(c["fuente"] for c in f.cifras), "hay una cifra sin fuente"
    cuerpo = "".join(s["html"] for s in f.secciones)
    assert 'class="cifra"' in cuerpo, "ninguna cifra quedó enlazada en el relato"
    assert "{{c:" not in cuerpo, "quedó un marcador de cifra sin resolver"
    assert any(b["clave"] == "dellapaolera-taylor-2003" for b in f.bibliografia)


def test_una_cifra_sin_serie_no_finge_un_vinculo():
    """Y una que declara una serie inexistente tampoco: la UI lo tiene que poder decir."""
    f = H.cargar_ficha("crisis-baring-1890")
    sin_serie = [c for c in f.cifras if not c["serie"]]
    assert sin_serie, "la ficha debería tener cifras sin serie"
    assert all(not c["serie_disponible"] for c in f.cifras), (
        "todavía no hay series troncales: ninguna cifra puede declararse disponible"
    )


def test_el_markdown_de_una_ficha_no_puede_inyectar_html():
    """El relato se renderiza en el servidor; el frontend no interpreta texto libre."""
    secciones = H.renderizar(
        "## Contexto\n\nHola <script>alert(1)</script> y <img src=x onerror=y>.\n",
        {}, set(),
    )
    cuerpo = "".join(s["html"] for s in secciones)
    assert "<script" not in cuerpo and "<img" not in cuerpo, "entró una etiqueta del autor"
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in cuerpo, "el texto tiene que sobrevivir, escapado"


def test_el_payload_trae_lo_que_la_pantalla_necesita():
    p = H.payload()
    assert p["rango"]["desde"] == 1880
    assert p["presidencias"] and p["eventos"] and p["vocabulario"]["categorias"]
    assert p["series"] == [], "todavía no hay series troncales (fase T3)"
    assert p["estado"]["eventos"] == len(H.cargar_eventos())
    # el gobierno viaja derivado, no guardado
    assert any(e["gobierno"] for e in p["eventos"])


def test_un_evento_inexistente_o_con_id_raro_no_toca_el_disco():
    for malo in ("no-existe-1999", "../../etc/passwd", "MAYUSCULAS"):
        with pytest.raises(H.EventoNoEncontrado):
            H.payload_evento(malo)
