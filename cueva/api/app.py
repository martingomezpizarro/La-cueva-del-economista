"""app — Servidor de la Mesa de Trabajo (FastAPI).

Endpoints (todos bajo /api/v1):
    GET    /                                      → UI (web/index.html)
    GET    /explorador                            → explorador nativo (web/explorador.html)
    GET    /tiempo  ·  /tiempo/{evento_id}        → Línea de Tiempo (web/tiempo/index.html)
    GET    /api/v1/historia                       → todo lo del módulo en una respuesta
    GET    /api/v1/historia/eventos/{id}          → la ficha completa de un evento
    GET    /api/v1/diag                           → estado de config (datos, RAG, API key, explorador)
    GET    /api/v1/series                         → catálogo de series (filtro, origen, limite, refrescar)
    GET    /api/v1/explorador/datos               → datos columnares para el explorador (ex EMBEDDED)
    POST   /api/v1/explorador/kalman              → ajuste SARIMAX/Kalman (nativo)
    POST   /api/v1/explorador/analisis-basico     → corre el script legacy del TF (puente subprocess)
    GET    /api/v1/herramientas                   → herramientas econométricas disponibles
    POST   /api/v1/herramienta                    → ejecuta una herramienta {nombre, args, proyecto_id?}

    GET    /api/v1/proyectos                      → lista las investigaciones guardadas
    POST   /api/v1/proyectos                      → crea una investigación (acepta semilla de Vista Rápida)
    GET    /api/v1/proyectos/{id}                 → carga una investigación
    PATCH  /api/v1/proyectos/{id}                 → actualiza campos del proyecto
    DELETE /api/v1/proyectos/{id}                 → elimina (borrado suave → _papelera/)
    POST   /api/v1/proyectos/{id}/notas           → agrega una nota libre
    DELETE /api/v1/proyectos/{id}/estudios/{eid}  → quita un estudio del cuaderno
    PUT    /api/v1/proyectos/{id}/informe/{sec}   → actualiza una sección del informe
    POST   /api/v1/proyectos/{id}/informe/{sec}/toggle → oculta/muestra una sección
    POST   /api/v1/proyectos/{id}/agente/{aid}    → pregunta puntual a un agente (sin correr la mesa)
    POST   /api/v1/proyectos/{id}/investigar      → corre la mesa completa y STREAMEA los mensajes (SSE)

Estáticos: /web (CSS y módulos ES de la plataforma), /vendor (librerías JS del explorador),
/data (datos del Trabajo Final, solo lectura), /explorador-reporte (reporte del análisis legacy).

Errores: envelope uniforme {"error": {"codigo", "mensaje"}} con el status HTTP correcto.

Correr:
    pip install -e .
    uvicorn cueva.api.app:app --reload --port 8800
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
import threading
import uuid

from fastapi import Depends, FastAPI, HTTPException, Path, Query, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from cueva import config
from cueva.agentes.agentes import AGENTES
from cueva.agentes.orquestador import Orquestador
from cueva.agentes.pizarra import SECCIONES_INFORME
from cueva.datos import explorador_datos
from cueva.datos import historia as HIST
from cueva.datos import series as S
from cueva.econometria import herramientas as H
from cueva.econometria.kalman import ajustar_kalman
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

# El análisis básico legacy (script 02a del Trabajo Final) corre de a uno por vez
_analisis_basico_lock = threading.Lock()

# Mapeo query-string → flags CLI del script 02a (mismo contrato que el server viejo del TF)
_QS_A_CLI = {
    "freq": "--freq",
    "lag_ardl_dep": "--max-lag-ardl-dep",
    "lag_ardl_ind": "--max-lag-ardl-ind",
    "lag_var": "--max-lag-var",
    "lag_vecm": "--max-lag-vecm",
    "max_vars": "--max-vars",
    "modelos": "--modelos",
    "fecha_inicio": "--fecha-inicio",
    "fecha_fin": "--fecha-fin",
    "tiempo_max_min": "--tiempo-max-min",
    "max_corridas": "--max-corridas",
    "corridas_ardl": "--corridas-ardl",
    "corridas_var": "--corridas-var",
    "corridas_vecm": "--corridas-vecm",
    "granger_grafo_pmax": "--granger-grafo-pmax",
    "dummy_cap": "--dummy-cap",
}


# ── Repositorio de sesiones (inyectable; los tests lo reemplazan) ───────────
_repo: RepositorioProyectos | None = None


def get_repo() -> RepositorioProyectos:
    global _repo
    if _repo is None:
        _repo = RepositorioProyectos()
    return _repo


def crear_app() -> FastAPI:
    app = FastAPI(title="La Cueva del Economista — Mesa de Trabajo")

    # ── estáticos de la plataforma ─────────────────────────────────────────
    # /web sirve el sistema de diseño (web/estilo/) y los módulos ES de cada pantalla.
    # Los módulos nativos se cargan como archivos, no embebidos: sin build.
    app.mount("/web", StaticFiles(directory=str(WEB)), name="web")
    medios = config.ROOT / "data" / "historia" / "medios"
    if medios.exists():
        # imágenes de las fichas; cada una lleva crédito y licencia en su ficha (§6.7)
        app.mount("/historia-medios", StaticFiles(directory=str(medios)), name="historia-medios")
    if (WEB / "vendor").exists():
        app.mount("/vendor", StaticFiles(directory=str(WEB / "vendor")), name="vendor")
    tf = config.carpeta_trabajo_final()
    if tf and (tf / "data").exists():
        # solo lectura: los CSVs del Trabajo Final que el explorador carga on-demand
        app.mount("/data", StaticFiles(directory=str(tf / "data")), name="datos-tf")
    if tf and (tf / "outputs" / "analisis_basico").exists():
        app.mount(
            "/explorador-reporte",
            StaticFiles(directory=str(tf / "outputs" / "analisis_basico")),
            name="reporte-basico",
        )

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

    @app.exception_handler(HIST.EventoNoEncontrado)
    async def _evento_no_encontrado(request: Request, exc: HIST.EventoNoEncontrado):
        return JSONResponse(
            status_code=404,
            content={
                "error": {
                    "codigo": "evento_no_encontrado",
                    "mensaje": f"No hay un evento con id {exc.args[0]!r} en data/historia/eventos.csv.",
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

    @app.get("/explorador", response_class=HTMLResponse)
    def explorador():
        pagina = WEB / "explorador.html"
        if not pagina.exists():
            return HTMLResponse("<h1>Falta web/explorador.html</h1>", status_code=500)
        return HTMLResponse(pagina.read_text(encoding="utf-8"))

    # ── módulo 1: Línea de Tiempo ──────────────────────────────────────────
    @app.get("/tiempo", response_class=HTMLResponse)
    @app.get("/tiempo/{evento_id}", response_class=HTMLResponse)
    def tiempo(evento_id: str = ""):
        """La pantalla. Con evento_id es el permalink: la SPA abre con la ficha puesta."""
        pagina = WEB / "tiempo" / "index.html"
        if not pagina.exists():
            return HTMLResponse("<h1>Falta web/tiempo/index.html</h1>", status_code=500)
        return HTMLResponse(pagina.read_text(encoding="utf-8"))

    @app.get("/api/v1/historia")
    def api_historia():
        """Todo lo necesario al abrir /tiempo, en una sola respuesta (módulo §10.1)."""
        return JSONResponse(HIST.payload())

    @app.get("/api/v1/historia/eventos/{evento_id}")
    def api_historia_evento(evento_id: str = Path(pattern=r"^[a-z0-9-]{3,80}$")):
        """La ficha completa. El markdown viene renderizado a HTML saneado desde el servidor."""
        return JSONResponse(HIST.payload_evento(evento_id))

    # ── diagnóstico / series / herramientas ────────────────────────────────
    @app.get("/api/v1/diag")
    def diag():
        d = config.diagnostico()
        try:
            d["n_series"] = len(S.catalogo())
        except Exception as e:
            d["n_series"] = 0
            d["series_error"] = str(e)
        d["visualizador_url"] = "/explorador"
        d["visualizador_disponible"] = (WEB / "explorador.html").exists()
        return JSONResponse(d)

    # ── explorador nativo: datos, kalman y análisis básico legacy ──────────
    @app.get("/api/v1/explorador/datos")
    def api_datos_explorador(refrescar: bool = False):
        """Payload columnar {archivo: {col: [...]}} para la SPA (el viejo EMBEDDED, en vivo)."""
        if refrescar:
            explorador_datos.refrescar()
        return JSONResponse(explorador_datos.payload())

    @app.post("/api/v1/explorador/kalman")
    async def api_kalman(request: Request):
        try:
            payload = await request.json()
        except Exception as e:
            raise HTTPException(400, f"JSON inválido: {e}") from e
        return JSONResponse(ajustar_kalman(payload))

    @app.post("/api/v1/explorador/analisis-basico")
    async def api_analisis_basico(request: Request):
        """Puente al script legacy 02a_analisis_basico.py del Trabajo Final: recibe el CSV
        de variables (body) + configuración (query), lo corre por subprocess y el reporte
        queda servido en /explorador-reporte/. Se reemplazará por el banco de trabajo."""
        tf = config.carpeta_trabajo_final()
        script = tf / "notebooks" / "02a_analisis_basico.py" if tf else None
        if not script or not script.exists():
            raise HTTPException(503, "No encuentro el script del análisis básico (carpeta Trabajo Final).")
        cuerpo = (await request.body()).decode("utf-8", errors="replace")
        if not cuerpo.strip():
            raise HTTPException(422, "El body debe traer el CSV de variables.")
        if not _analisis_basico_lock.acquire(blocking=False):
            raise HTTPException(409, "Ya hay un análisis básico corriendo.")
        try:
            carpeta_csv = tf / "notebooks" / "Variables Regresivas"
            carpeta_csv.mkdir(parents=True, exist_ok=True)
            csv_path = carpeta_csv / "analisis_series_visualizador.csv"
            csv_path.write_text(cuerpo, encoding="utf-8")
            extra: list[str] = []
            for clave, flag in _QS_A_CLI.items():
                valor = request.query_params.get(clave, "").strip()
                if valor:
                    extra += [flag, valor]
            cmd = [
                sys.executable,
                str(script),
                "--invalidate",
                "panel,ctx,est,ardl,var,vecm,consolidado",
                "--csv",
                csv_path.name,
            ] + extra
            proc = subprocess.run(
                cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                cwd=str(tf), timeout=900,
            )
            log_tail = (proc.stdout + "\n" + proc.stderr).splitlines()[-30:]
            return JSONResponse({"ok": proc.returncode == 0, "log_tail": log_tail})
        except subprocess.TimeoutExpired:
            return JSONResponse({"ok": False, "log_tail": ["Timeout (15 min) excedido"]})
        finally:
            _analisis_basico_lock.release()

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

    # ── biblioteca del usuario (bibliografía propia subida) ────────────────
    @app.get("/api/v1/biblioteca")
    def api_listar_biblioteca():
        from cueva.conocimiento import biblioteca

        return JSONResponse(biblioteca.listar())

    @app.post("/api/v1/biblioteca")
    async def api_subir_biblioteca(archivo: UploadFile):
        """Sube un PDF/md/txt propio y lo indexa en la colección 'usuario' (con provenance).

        Nota: la indexación corre en el request (segundos para un paper; un libro con
        embeddings puede tardar ~1 min). En fase 4 pasa a la cola de trabajos."""
        from cueva.conocimiento import biblioteca

        contenido = await archivo.read()
        try:
            resultado = biblioteca.guardar_e_indexar(archivo.filename or "", contenido)
        except biblioteca.ArchivoInvalido as e:
            raise HTTPException(422, str(e)) from e
        return JSONResponse(resultado)

    @app.post("/api/v1/herramienta")
    def ejecutar_herramienta(body: HerramientaEjecutar, repo: RepositorioProyectos = Depends(get_repo)):
        resultado = H.ejecutar(body.nombre, **body.args)
        if body.proyecto_id:
            try:
                with repo.abrir(body.proyecto_id) as piz:
                    estudio = piz.registrar_estudio(
                        body.nombre, body.args, resultado.get("resumen", ""), resultado=resultado
                    )
                    resultado["estudio_id"] = estudio["id"]
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
        # semilla de la Vista Rápida (promover): series y estudios acumulados en el espacio efímero
        if body.series or body.estudios or body.serie_dependiente or body.frecuencia:
            with repo.abrir(piz.id) as p:
                if body.series:
                    p.proyecto.series = body.series
                if body.serie_dependiente:
                    p.proyecto.serie_dependiente = body.serie_dependiente
                if body.frecuencia:
                    p.proyecto.frecuencia = body.frecuencia
                for e in body.estudios:
                    p.registrar_estudio(e.herramienta, e.args, e.resumen, resultado=e.resultado)
        return JSONResponse(repo.obtener(piz.id).to_dict())

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

    @app.delete("/api/v1/proyectos/{pid}/estudios/{estudio_id}")
    def api_quitar_estudio(
        pid: str = PID,
        estudio_id: str = Path(max_length=16, pattern=r"^[0-9a-f]{8}$"),
        repo: RepositorioProyectos = Depends(get_repo),
    ):
        with repo.abrir(pid) as piz:
            hubo = piz.quitar_estudio(estudio_id)
        if not hubo:
            raise HTTPException(404, f"Estudio desconocido: {estudio_id}")
        return JSONResponse({"ok": True})

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
    def api_investigar(
        pid: str = PID,
        pipeline: str = Query(default="clasica", max_length=40),
        repo: RepositorioProyectos = Depends(get_repo),
    ):
        from cueva.agentes.pipelines import PIPELINES

        if pipeline not in PIPELINES:
            raise HTTPException(422, f"Pipeline desconocido: {pipeline} (hay: {', '.join(PIPELINES)})")
        piz = repo.obtener(pid)
        if getattr(piz, "_mesa_corriendo", False):
            raise HTTPException(409, "Ya hay una mesa corriendo sobre esta investigación.")
        orq = Orquestador(piz.proyecto, piz=piz, pipeline=pipeline)

        def _evento(nombre: str, datos: dict) -> str:
            return f"event: {nombre}\ndata: " + json.dumps(datos, ensure_ascii=False) + "\n\n"

        def stream():
            piz._mesa_corriendo = True
            try:
                for msg in orq.correr():
                    repo.guardar(piz)
                    yield _evento("mensaje", msg.to_dict())
                repo.guardar(piz)
                yield _evento("fin", {"fin": True, "uso_llm": piz.uso_llm})
            except Exception as e:  # el stream ya arrancó: no puede devolver 500, avisa por SSE
                log.exception("mesa falló en %s", pid)
                yield _evento("error", {"mensaje": str(e)})
            finally:
                piz._mesa_corriendo = False

        return StreamingResponse(stream(), media_type="text/event-stream")

    return app


app = crear_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("cueva.api.app:app", host="127.0.0.1", port=8800, reload=False)
