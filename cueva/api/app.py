"""app — Servidor de la Mesa de Trabajo (FastAPI).

Endpoints (todos bajo /api/v1):
    GET    /                                      → UI (web/index.html)
    GET    /api/v1/diag                           → estado de config (datos, RAG, API key, explorador)
    GET    /api/v1/series                         → catálogo de series (filtro, origen, limite, refrescar)
    GET    /api/v1/herramientas                   → herramientas econométricas disponibles
    POST   /api/v1/herramienta                    → ejecuta una herramienta {nombre, args, proyecto_id?}

    GET    /api/v1/proyectos                      → lista las investigaciones guardadas
    POST   /api/v1/proyectos                      → crea una investigación nueva
    GET    /api/v1/proyectos/{id}                 → carga una investigación
    PATCH  /api/v1/proyectos/{id}                 → actualiza campos del proyecto
    DELETE /api/v1/proyectos/{id}                 → elimina (borrado suave → _papelera/)
    POST   /api/v1/proyectos/{id}/notas           → agrega una nota libre
    PUT    /api/v1/proyectos/{id}/informe/{sec}   → actualiza una sección del informe
    POST   /api/v1/proyectos/{id}/informe/{sec}/toggle → oculta/muestra una sección
    POST   /api/v1/proyectos/{id}/agente/{aid}    → pregunta puntual a un agente (sin correr la mesa)
    POST   /api/v1/proyectos/{id}/investigar      → corre la mesa completa y STREAMEA los mensajes (SSE)

Errores: envelope uniforme {"error": {"codigo", "mensaje"}} con el status HTTP correcto.

Correr:
    pip install -e .
    uvicorn cueva.api.app:app --reload --port 8800
"""

from __future__ import annotations

import atexit
import json
import logging
import subprocess
import sys
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Path, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse

from cueva import config
from cueva.agentes.agentes import AGENTES
from cueva.agentes.orquestador import Orquestador
from cueva.agentes.pizarra import SECCIONES_INFORME
from cueva.datos import series as S
from cueva.econometria import herramientas as H
from cueva.sesiones import PidInvalido, ProyectoNoEncontrado, RepositorioProyectos

from .esquemas import (
    PID_PATTERN,
    HerramientaEjecutar,
    InformeTexto,
    NotaCrear,
    PreguntaAgente,
    ProyectoCrear,
    ProyectoPatch,
)

log = logging.getLogger("cueva.api")

WEB = config.ROOT / "web"

# ── Explorador (visualizador.html del Trabajo Final, proyecto hermano) ─────
VIZ_PORT = 8765
VIZ_URL = f"http://localhost:{VIZ_PORT}/"
_viz_proc: subprocess.Popen | None = None


def _lanzar_visualizador() -> None:
    """Arranca en segundo plano el server.py del visualizador del Trabajo Final,
    para poder embeberlo como pestaña de navegación libre. Best-effort: si falla, la
    plataforma sigue sin explorador."""
    global _viz_proc
    try:
        tf = config.carpeta_trabajo_final()
        if not tf:
            return
        server_py = tf / "notebooks" / "server.py"
        if not server_py.exists():
            return
        _viz_proc = subprocess.Popen(
            [sys.executable, str(server_py), "--port", str(VIZ_PORT), "--no-open"],
            cwd=str(server_py.parent),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        atexit.register(_viz_proc.terminate)
    except Exception as e:  # pragma: no cover
        log.warning("no pude lanzar el visualizador: %s", e)


# ── Repositorio de sesiones (inyectable; los tests lo reemplazan) ───────────
_repo: RepositorioProyectos | None = None


def get_repo() -> RepositorioProyectos:
    global _repo
    if _repo is None:
        _repo = RepositorioProyectos()
    return _repo


def crear_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        _lanzar_visualizador()
        yield
        if _viz_proc is not None and _viz_proc.poll() is None:
            _viz_proc.terminate()

    app = FastAPI(title="La Cueva del Economista — Mesa de Trabajo", lifespan=lifespan)

    # ── errores uniformes ──────────────────────────────────────────────────
    @app.exception_handler(HTTPException)
    async def _http_exc(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"codigo": f"http_{exc.status_code}", "mensaje": str(exc.detail)}},
        )

    @app.exception_handler(ProyectoNoEncontrado)
    async def _no_encontrado(request: Request, exc: ProyectoNoEncontrado):
        return JSONResponse(
            status_code=404,
            content={
                "error": {
                    "codigo": "proyecto_no_encontrado",
                    "mensaje": f"Investigación desconocida: {exc.args[0]}",
                }
            },
        )

    @app.exception_handler(PidInvalido)
    async def _pid_invalido(request: Request, exc: PidInvalido):
        return JSONResponse(
            status_code=422,
            content={"error": {"codigo": "pid_invalido", "mensaje": str(exc)}},
        )

    @app.exception_handler(Exception)
    async def _generico(request: Request, exc: Exception):
        rid = uuid.uuid4().hex[:8]
        log.exception("error no manejado rid=%s en %s", rid, request.url.path)
        return JSONResponse(
            status_code=500,
            content={"error": {"codigo": "error_interno", "mensaje": f"Error interno (referencia {rid})."}},
        )

    # ── UI ─────────────────────────────────────────────────────────────────
    @app.get("/", response_class=HTMLResponse)
    def home():
        idx = WEB / "index.html"
        if not idx.exists():
            return HTMLResponse("<h1>Falta web/index.html</h1>", status_code=500)
        return HTMLResponse(idx.read_text(encoding="utf-8"))

    # ── diagnóstico / series / herramientas ────────────────────────────────
    @app.get("/api/v1/diag")
    def diag():
        d = config.diagnostico()
        try:
            d["n_series"] = len(S.catalogo())
        except Exception as e:
            d["n_series"] = 0
            d["series_error"] = str(e)
        d["visualizador_url"] = VIZ_URL
        d["visualizador_disponible"] = _viz_proc is not None and _viz_proc.poll() is None
        return JSONResponse(d)

    @app.get("/api/v1/series")
    def listar_series(
        filtro: str = Query(default="", max_length=100),
        origen: str = Query(default="", max_length=40),
        limite: int = Query(default=300, ge=0, le=2000),
        refrescar: bool = False,
    ):
        if refrescar:
            S.refrescar()
        return JSONResponse(S.listar(filtro=filtro, origen=origen, limite=limite))

    @app.get("/api/v1/herramientas")
    def listar_herramientas():
        return JSONResponse(H.catalogo_herramientas())

    @app.post("/api/v1/herramienta")
    def ejecutar_herramienta(body: HerramientaEjecutar, repo: RepositorioProyectos = Depends(get_repo)):
        resultado = H.ejecutar(body.nombre, **body.args)
        if body.proyecto_id:
            try:
                with repo.abrir(body.proyecto_id) as piz:
                    piz.registrar_estudio(body.nombre, body.args, resultado.get("resumen", ""))
            except ProyectoNoEncontrado:
                pass
        return JSONResponse(resultado)

    # ── proyectos (investigaciones guardadas) ──────────────────────────────
    PID = Path(pattern=PID_PATTERN)

    @app.get("/api/v1/proyectos")
    def api_listar_proyectos(repo: RepositorioProyectos = Depends(get_repo)):
        return JSONResponse(repo.listar())

    @app.post("/api/v1/proyectos")
    def api_crear_proyecto(body: ProyectoCrear, repo: RepositorioProyectos = Depends(get_repo)):
        piz = repo.crear(titulo=body.titulo)
        return JSONResponse(piz.to_dict())

    @app.get("/api/v1/proyectos/{pid}")
    def api_obtener_proyecto(pid: str = PID, repo: RepositorioProyectos = Depends(get_repo)):
        return JSONResponse(repo.obtener(pid).to_dict())

    @app.patch("/api/v1/proyectos/{pid}")
    def api_actualizar_proyecto(
        body: ProyectoPatch, pid: str = PID, repo: RepositorioProyectos = Depends(get_repo)
    ):
        with repo.abrir(pid) as piz:
            for campo, valor in body.model_dump(exclude_unset=True).items():
                setattr(piz.proyecto, campo, valor)
        return JSONResponse(repo.obtener(pid).to_dict())

    @app.delete("/api/v1/proyectos/{pid}")
    def api_eliminar_proyecto(pid: str = PID, repo: RepositorioProyectos = Depends(get_repo)):
        repo.eliminar(pid)
        return JSONResponse({"ok": True})

    @app.post("/api/v1/proyectos/{pid}/notas")
    def api_agregar_nota(body: NotaCrear, pid: str = PID, repo: RepositorioProyectos = Depends(get_repo)):
        with repo.abrir(pid) as piz:
            nota = piz.agregar_nota(body.texto.strip())
        return JSONResponse(nota)

    @app.put("/api/v1/proyectos/{pid}/informe/{seccion}")
    def api_actualizar_informe(
        body: InformeTexto,
        pid: str = PID,
        seccion: str = Path(max_length=40),
        repo: RepositorioProyectos = Depends(get_repo),
    ):
        if seccion not in SECCIONES_INFORME:
            raise HTTPException(422, f"Sección de informe desconocida: {seccion}")
        with repo.abrir(pid) as piz:
            piz.actualizar_informe(seccion, body.texto)
        return JSONResponse({"ok": True})

    @app.post("/api/v1/proyectos/{pid}/informe/{seccion}/toggle")
    def api_toggle_seccion(
        pid: str = PID,
        seccion: str = Path(max_length=40),
        repo: RepositorioProyectos = Depends(get_repo),
    ):
        if seccion not in SECCIONES_INFORME:
            raise HTTPException(422, f"Sección de informe desconocida: {seccion}")
        with repo.abrir(pid) as piz:
            oculta = piz.toggle_seccion(seccion)
        return JSONResponse({"oculta": oculta})

    @app.post("/api/v1/proyectos/{pid}/agente/{agente_id}")
    def api_hablar_con_agente(
        body: PreguntaAgente,
        pid: str = PID,
        agente_id: str = Path(max_length=30),
        repo: RepositorioProyectos = Depends(get_repo),
    ):
        if agente_id not in AGENTES:
            raise HTTPException(404, f"Agente desconocido: {agente_id}")
        piz = repo.obtener(pid)
        pregunta = body.pregunta.strip()
        piz.agregar_chat(agente_id, "usuario", pregunta)
        respuesta = AGENTES[agente_id].responder_directo(piz, pregunta)
        turno = piz.agregar_chat(agente_id, agente_id, respuesta)
        repo.guardar(piz)
        return JSONResponse(turno)

    @app.post("/api/v1/proyectos/{pid}/investigar")
    def api_investigar(pid: str = PID, repo: RepositorioProyectos = Depends(get_repo)):
        piz = repo.obtener(pid)
        if getattr(piz, "_mesa_corriendo", False):
            raise HTTPException(409, "Ya hay una mesa corriendo sobre esta investigación.")
        orq = Orquestador(piz.proyecto, piz=piz)

        def stream():
            piz._mesa_corriendo = True
            try:
                for msg in orq.correr():
                    repo.guardar(piz)
                    yield "data: " + json.dumps(msg.to_dict(), ensure_ascii=False) + "\n\n"
                repo.guardar(piz)
                yield (
                    "data: " + json.dumps({"fin": True, "uso_llm": piz.uso_llm}, ensure_ascii=False) + "\n\n"
                )
            finally:
                piz._mesa_corriendo = False

        return StreamingResponse(stream(), media_type="text/event-stream")

    return app


app = crear_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("cueva.api.app:app", host="127.0.0.1", port=8800, reload=False)
