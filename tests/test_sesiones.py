"""Tests del repositorio de sesiones: validación de IDs (B2), locks (B3), borrado suave."""

import threading

import pytest

from cueva.sesiones import PidInvalido, ProyectoNoEncontrado, RepositorioProyectos


def test_crear_y_obtener(repo):
    piz = repo.crear("Mi tesis")
    assert repo.obtener(piz.id) is piz  # misma instancia viva (caché por proceso)
    assert repo.listar()[0]["titulo"] == "Mi tesis"


def test_persistencia_real(repo, tmp_path):
    piz = repo.crear("Persistida")
    with repo.abrir(piz.id) as p:
        p.agregar_nota("hola")
    # un repositorio NUEVO (proceso fresco simulado) debe leerla del disco
    repo2 = RepositorioProyectos(ruta=repo.ruta)
    assert repo2.obtener(piz.id).notas[0]["texto"] == "hola"


def test_pid_invalido_no_toca_el_filesystem(repo):
    """B2: un id malicioso no debe llegar a construir rutas."""
    for malo in ("../../secreto", "..%2Fsecreto", "con espacios", "A" * 40, ""):
        with pytest.raises(PidInvalido):
            repo.obtener(malo)
        with pytest.raises(PidInvalido):
            repo.eliminar(malo)


def test_no_encontrado(repo):
    with pytest.raises(ProyectoNoEncontrado):
        repo.obtener("deadbeef")


def test_borrado_suave(repo):
    piz = repo.crear("Efímera")
    repo.eliminar(piz.id)
    with pytest.raises(ProyectoNoEncontrado):
        repo.obtener(piz.id)
    assert (repo.ruta / "_papelera" / f"{piz.id}.json").exists()
    assert repo.listar() == []  # la papelera no aparece en el listado


def test_escrituras_concurrentes_no_se_pisan(repo):
    """B3: N hilos agregando notas al MISMO proyecto → no se pierde ninguna."""
    piz = repo.crear("Concurrente")

    def agregar(i):
        with repo.abrir(piz.id) as p:
            p.agregar_nota(f"nota {i}")

    hilos = [threading.Thread(target=agregar, args=(i,)) for i in range(20)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()

    repo2 = RepositorioProyectos(ruta=repo.ruta)
    assert len(repo2.obtener(piz.id).notas) == 20


def test_migracion_esquema_v1(repo):
    """Los proyectos guardados con el esquema viejo (campo `herramienta`) se cargan bien."""
    import json

    viejo = {
        "id": "abc12345",
        "proyecto": {"id": "abc12345", "titulo": "Vieja"},
        "mensajes": [
            {
                "autor": "herramientas",
                "rol": "🧪",
                "contenido": "x",
                "fase": "control",
                "herramienta": {"herramienta": "vecm", "rango_cointegracion": 1},
            },
        ],
    }
    repo.ruta.mkdir(parents=True, exist_ok=True)
    (repo.ruta / "abc12345.json").write_text(json.dumps(viejo), encoding="utf-8")
    piz = repo.obtener("abc12345")
    assert piz.mensajes[0].herramientas == [{"herramienta": "vecm", "rango_cointegracion": 1}]
