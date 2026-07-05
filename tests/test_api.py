"""Tests de contrato de la API (TestClient, repositorio temporal, modo offline)."""


def _crear(cliente, titulo="Test"):
    r = cliente.post("/api/v1/proyectos", json={"titulo": titulo})
    assert r.status_code == 200
    return r.json()


def test_diag(cliente):
    d = cliente.get("/api/v1/diag").json()
    assert "backend_llm" in d
    assert d["n_series"] == 5  # las sintéticas del fixture


def test_ciclo_de_vida_proyecto(cliente):
    piz = _crear(cliente, "Mi tesis")
    pid = piz["id"]

    # PATCH válido
    r = cliente.patch(f"/api/v1/proyectos/{pid}", json={"pregunta": "¿X explica Y?", "frecuencia": "mensual"})
    assert r.status_code == 200
    assert r.json()["proyecto"]["pregunta"] == "¿X explica Y?"

    # nota + informe
    assert cliente.post(f"/api/v1/proyectos/{pid}/notas", json={"texto": "primera nota"}).status_code == 200
    assert (
        cliente.put(f"/api/v1/proyectos/{pid}/informe/desarrollo", json={"texto": "borrador"}).status_code
        == 200
    )

    # GET refleja todo
    d = cliente.get(f"/api/v1/proyectos/{pid}").json()
    assert d["notas"][0]["texto"] == "primera nota"
    assert d["informe"]["desarrollo"] == "borrador"

    # DELETE suave + 404 posterior con envelope de error
    assert cliente.delete(f"/api/v1/proyectos/{pid}").json() == {"ok": True}
    r = cliente.get(f"/api/v1/proyectos/{pid}")
    assert r.status_code == 404
    assert r.json()["error"]["codigo"] == "proyecto_no_encontrado"


def test_validacion_de_entrada(cliente):
    pid = _crear(cliente)["id"]
    # frecuencia inexistente → 422
    assert cliente.patch(f"/api/v1/proyectos/{pid}", json={"frecuencia": "quincenal"}).status_code == 422
    # nota vacía → 422
    assert cliente.post(f"/api/v1/proyectos/{pid}/notas", json={"texto": ""}).status_code == 422
    # título gigante → 422
    assert cliente.post("/api/v1/proyectos", json={"titulo": "x" * 500}).status_code == 422
    # sección de informe desconocida → 422
    assert cliente.put(f"/api/v1/proyectos/{pid}/informe/hackear", json={"texto": "x"}).status_code == 422


def test_path_traversal_bloqueado(cliente):
    """B2: IDs maliciosos no llegan al filesystem."""
    for malo in ("..%2F..%2Fsecreto", "..%5C..%5Csecreto", "AAAA-BBBB"):
        r = cliente.get(f"/api/v1/proyectos/{malo}")
        assert r.status_code in (404, 422), f"{malo} devolvió {r.status_code}"


def test_herramientas(cliente):
    assert any(h["nombre"] == "vecm" for h in cliente.get("/api/v1/herramientas").json())

    # herramienta estándar sobre serie sintética
    r = cliente.post("/api/v1/herramienta", json={"nombre": "estacionariedad", "args": {"sid": "caminata"}})
    assert r.status_code == 200 and r.json()["ok"]

    # no estándar → modo asesor, no error
    r = cliente.post("/api/v1/herramienta", json={"nombre": "magia_negra", "args": {}})
    assert r.status_code == 200 and r.json().get("no_estandar")

    # nombre con formato inválido → 422 (ni siquiera se busca)
    assert cliente.post("/api/v1/herramienta", json={"nombre": "rm -rf /", "args": {}}).status_code == 422


def test_chat_con_agente_offline(cliente):
    pid = _crear(cliente)["id"]
    r = cliente.post(f"/api/v1/proyectos/{pid}/agente/metodologo", json={"pregunta": "¿por dónde empiezo?"})
    assert r.status_code == 200
    assert "MODO OFFLINE" in r.json()["texto"]
    # agente inexistente
    assert cliente.post(f"/api/v1/proyectos/{pid}/agente/nadie", json={"pregunta": "?"}).status_code == 404


def _leer_sse(respuesta):
    """Parsea un stream SSE tipado → [(evento, datos)]."""
    import json as J

    eventos, actual = [], "mensaje"
    for linea in respuesta.iter_lines():
        if linea.startswith("event: "):
            actual = linea[7:].strip()
        elif linea.startswith("data: "):
            eventos.append((actual, J.loads(linea[6:])))
    return eventos


def test_investigar_streamea_hasta_el_fin(cliente):
    """E2E: la mesa completa por SSE tipado en modo offline, terminando con el evento fin."""
    pid = _crear(cliente)["id"]
    cliente.patch(f"/api/v1/proyectos/{pid}", json={"pregunta": "¿?", "series": ["coint_x", "coint_y"]})

    with cliente.stream("POST", f"/api/v1/proyectos/{pid}/investigar") as r:
        assert r.status_code == 200
        eventos = _leer_sse(r)

    nombres = [n for n, _ in eventos]
    assert nombres[-1] == "fin"
    assert "uso_llm" in eventos[-1][1]
    assert any(n == "mensaje" and d.get("autor") == "herramientas" for n, d in eventos)


def test_investigar_pipeline_invalido(cliente):
    pid = _crear(cliente)["id"]
    r = cliente.post(f"/api/v1/proyectos/{pid}/investigar?pipeline=inventado")
    assert r.status_code == 422
