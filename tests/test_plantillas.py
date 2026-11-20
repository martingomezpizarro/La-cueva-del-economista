"""Proyectos predeterminados y estado de la Mesa por proyecto."""


def test_lista_de_plantillas(cliente):
    r = cliente.get("/api/v1/plantillas")
    assert r.status_code == 200
    ids = [p["id"] for p in r.json()]
    assert "valuacion_empresa" in ids
    val = next(p for p in r.json() if p["id"] == "valuacion_empresa")
    assert {m["id"] for m in val["metodos"]} >= {"dcf", "gordon", "dcf_inverso"}


def test_crear_desde_plantilla_arranca_vacio(cliente):
    r = cliente.post(
        "/api/v1/proyectos",
        json={
            "titulo": "Valuación NVDA",
            "plantilla": "valuacion_empresa",
            "metodos": ["dcf", "inexistente", "dcf_inverso"],
            "activo": "NVDA",
        },
    )
    assert r.status_code == 200
    d = r.json()
    assert d["plantilla"] == "valuacion_empresa"
    v = d["mesa"]["valuacion"]
    assert v["activo"] == "NVDA" and v["metodos"] == ["dcf", "dcf_inverso"]
    # los bloques arrancan sin datos: se cargan a mano desde la Ficha
    assert v["bloques"]["dcf"] == {"insumos": {}, "parametros": {}}
    lista = cliente.get("/api/v1/proyectos").json()
    assert any(p["id"] == d["id"] and p["plantilla"] == "valuacion_empresa" for p in lista)


def test_plantilla_desconocida(cliente):
    r = cliente.post("/api/v1/proyectos", json={"titulo": "x", "plantilla": "nada"})
    assert r.status_code == 404


def test_guardar_y_leer_estado_de_la_mesa(cliente):
    pid = cliente.post("/api/v1/proyectos", json={"titulo": "Prueba"}).json()["id"]
    assert cliente.get(f"/api/v1/proyectos/{pid}/mesa").json()["mesa"] == {}
    estado = {"pines": [{"id": "p1", "titulo": "Gráfico"}], "doc": [], "docTit": "Borrador"}
    assert cliente.put(f"/api/v1/proyectos/{pid}/mesa", json=estado).status_code == 200
    assert cliente.get(f"/api/v1/proyectos/{pid}/mesa").json()["mesa"] == estado
    assert cliente.put(f"/api/v1/proyectos/{pid}/mesa", json=[1, 2]).status_code == 422
