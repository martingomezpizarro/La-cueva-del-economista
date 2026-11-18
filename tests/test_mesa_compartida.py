"""Bandeja, tablero y documento compartidos (cueva/api/mesa_compartida.py)."""

from __future__ import annotations


def _proyecto(cliente) -> str:
    return cliente.post("/api/v1/proyectos", json={"titulo": "McEwen Mining"}).json()["id"]


def test_bandeja_agrega_lista_y_quita(cliente):
    r = cliente.post(
        "/api/v1/bandeja",
        json={
            "tipo": "serie",
            "ref": "MUX",
            "etiqueta": "MUX · precio en USD",
            "procedencia": {"fuente": "Terminal", "serie": "MUX:precio"},
            "autor": "claude",
        },
    )
    assert r.status_code == 200
    item = r.json()
    assert item["autor"] == "claude" and item["tipo"] == "serie"

    items = cliente.get("/api/v1/bandeja").json()["items"]
    assert [i["id"] for i in items] == [item["id"]]

    assert cliente.delete(f"/api/v1/bandeja/{item['id']}").json() == {"ok": True}
    assert cliente.get("/api/v1/bandeja").json()["items"] == []
    assert cliente.delete(f"/api/v1/bandeja/{item['id']}").status_code == 404


def test_bandeja_rechaza_tipo_desconocido(cliente):
    r = cliente.post("/api/v1/bandeja", json={"tipo": "cualquiera", "ref": "X"})
    assert r.status_code == 422


def test_bandeja_se_conserva_en_disco(cliente):
    cliente.post("/api/v1/bandeja", json={"tipo": "serie", "ref": "GGAL"})
    from cueva.sesiones.bandeja import Bandeja

    assert [i["ref"] for i in Bandeja().listar()] == ["GGAL"]


def test_fijar_figura_e_insertarla_en_el_documento(cliente):
    pid = _proyecto(cliente)
    fig = cliente.post(
        f"/api/v1/proyectos/{pid}/figuras",
        json={
            "titulo": "Sankey Q3 2026",
            "tipo": "sankey",
            "datos": {"nodos": ["Ingresos", "Costo"], "flujos": [[0, 1, 10]]},
            "receta": {"op": "sankey", "de": "MUX", "p": {"periodo": "2026Q3"}},
            "procedencia": {"fuente": "SEC EDGAR 10-Q"},
            "origen": "terminal",
            "autor": "claude",
        },
    ).json()
    assert cliente.get(f"/api/v1/proyectos/{pid}/tablero").json()["figuras"][0]["id"] == fig["id"]

    texto = cliente.post(
        f"/api/v1/proyectos/{pid}/documento/bloques",
        json={
            "seccion": "resultados",
            "tipo": "texto",
            "texto": "Los ingresos crecieron.",
            "autor": "claude",
        },
    ).json()
    figura = cliente.post(
        f"/api/v1/proyectos/{pid}/documento/bloques",
        json={"seccion": "resultados", "tipo": "figura", "figura_id": fig["id"], "posicion": 0},
    ).json()

    doc = cliente.get(f"/api/v1/proyectos/{pid}/documento").json()
    res = next(s for s in doc["secciones"] if s["id"] == "resultados")
    assert [b["id"] for b in res["bloques"]] == [figura["id"], texto["id"]]
    assert res["bloques"][0]["figura"]["receta"]["op"] == "sankey"


def test_editar_mover_y_quitar_bloques(cliente):
    pid = _proyecto(cliente)
    url = f"/api/v1/proyectos/{pid}/documento/bloques"
    b = cliente.post(url, json={"seccion": "introduccion", "tipo": "texto", "texto": "borrador"}).json()

    cambiado = cliente.patch(
        f"{url}/{b['id']}", json={"texto": "versión final", "seccion": "desarrollo"}
    ).json()
    assert cambiado["id"] == b["id"] and cambiado["seccion"] == "desarrollo"
    assert cambiado["texto"] == "versión final"

    assert cliente.delete(f"{url}/{b['id']}").json() == {"ok": True}
    assert cliente.delete(f"{url}/{b['id']}").status_code == 404


def test_figura_inexistente_o_seccion_mala(cliente):
    pid = _proyecto(cliente)
    url = f"/api/v1/proyectos/{pid}/documento/bloques"
    assert (
        cliente.post(
            url, json={"seccion": "resultados", "tipo": "figura", "figura_id": "abcdef12"}
        ).status_code
        == 422
    )
    assert cliente.post(url, json={"seccion": "inventada", "tipo": "texto"}).status_code == 422


def test_quitar_figura_la_saca_del_documento(cliente):
    pid = _proyecto(cliente)
    fig = cliente.post(f"/api/v1/proyectos/{pid}/figuras", json={"titulo": "Precio", "tipo": "lineas"}).json()
    cliente.post(
        f"/api/v1/proyectos/{pid}/documento/bloques",
        json={"seccion": "desarrollo", "tipo": "figura", "figura_id": fig["id"]},
    )
    assert cliente.delete(f"/api/v1/proyectos/{pid}/figuras/{fig['id']}").json() == {"ok": True}
    doc = cliente.get(f"/api/v1/proyectos/{pid}/documento").json()
    assert all(not s["bloques"] for s in doc["secciones"])


def test_novedades(cliente):
    cliente.post("/api/v1/bandeja", json={"tipo": "serie", "ref": "VIX"})
    nov = cliente.get("/api/v1/novedades", params={"desde": 0}).json()
    assert [i["ref"] for i in nov["bandeja"]] == ["VIX"]
    assert cliente.get("/api/v1/novedades", params={"desde": 9e12}).json()["bandeja"] == []


def test_figuras_y_documento_sobreviven_a_guardar(tmp_path):
    from cueva.agentes.modelos import Proyecto
    from cueva.agentes.pizarra import Pizarra

    piz = Pizarra(Proyecto(titulo="t"))
    f = piz.fijar_figura("Precio", "lineas")
    piz.insertar_bloque("resultados", "figura", figura_id=f["id"])
    piz.guardar(tmp_path / "p.json")
    import json

    otra = Pizarra.desde_dict(json.loads((tmp_path / "p.json").read_text(encoding="utf-8")))
    assert otra.figuras[0]["id"] == f["id"] and otra.documento[0]["figura_id"] == f["id"]
