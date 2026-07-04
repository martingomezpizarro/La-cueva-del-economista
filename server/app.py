"""
app.py — Servidor de la Mesa de Trabajo (FastAPI).

Endpoints:
    GET    /                                   → UI (server/static/index.html)
    GET    /api/diag                           → estado de config (datos, RAG, API key, explorador)
    GET    /api/series                         → catálogo de series (filtro, origen, limite)
    GET    /api/herramientas                   → herramientas econométricas disponibles
    POST   /api/herramienta                    → ejecuta una herramienta {nombre, args, proyecto_id?}

    GET    /api/proyectos                      → lista las investigaciones guardadas
    POST   /api/proyectos                      → crea una investigación nueva
    GET    /api/proyectos/{id}                 → carga una investigación
    PATCH  /api/proyectos/{id}                 → actualiza campos del proyecto (título, pregunta, series...)
    DELETE /api/proyectos/{id}                 → elimina una investigación
    POST   /api/proyectos/{id}/notas           → agrega una nota libre
    PUT    /api/proyectos/{id}/informe/{sec}   → actualiza una sección del informe
    POST   /api/proyectos/{id}/informe/{sec}/toggle → oculta/muestra una sección del informe
    POST   /api/proyectos/{id}/agente/{aid}    → le hace una pregunta puntual a un agente (sin correr la mesa)
    POST   /api/proyectos/{id}/investigar      → corre la mesa completa y STREAMEA los mensajes (SSE)

Correr:
    pip install -r requirements.txt
    uvicorn server.app:app --reload --port 8800
    # abrir http://localhost:8800
"""
from __future__ import annotations

import atexit
import json
import subprocess
import sys
from pathlib import Path

# permitir importar config / mesa / econ desde la raíz del repo
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse

import config
from econ import series as S, herramientas as H
from mesa.agentes import AGENTES
from mesa.modelos import Proyecto
from mesa.orquestador import Orquestador
from mesa.pizarra import Pizarra, cargar_proyecto, eliminar_proyecto, listar_proyectos

app = FastAPI(title="La Cueva del Economista — Mesa de Trabajo")

STATIC = Path(__file__).resolve().parent / "static"

# ── Explorador (visualizador.html del Trabajo Final) ───────────────────────
VIZ_PORT = 8765
VIZ_URL = f"http://localhost:{VIZ_PORT}/"
_viz_proc: subprocess.Popen | None = None


def _lanzar_visualizador() -> None:
    """Arranca en segundo plano el server.py del visualizador del Trabajo Final,
    para poder embeberlo como pestaña de navegación libre (ver docs/ARQUITECTURA.md)."""
    global _viz_proc
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


@app.on_event("startup")
def _startup() -> None:
    _lanzar_visualizador()


@app.get("/", response_class=HTMLResponse)
def home():
    idx = STATIC / "index.html"
    if not idx.exists():
        return HTMLResponse("<h1>Falta server/static/index.html</h1>", status_code=500)
    return HTMLResponse(idx.read_text(encoding="utf-8"))


@app.get("/api/diag")
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


@app.get("/api/series")
def listar_series(filtro: str = "", origen: str = "", limite: int = 300):
    return JSONResponse(S.listar(filtro=filtro, origen=origen, limite=limite))


@app.get("/api/herramientas")
def listar_herramientas():
    return JSONResponse(H.catalogo_herramientas())


@app.post("/api/herramienta")
async def ejecutar_herramienta(req: Request):
    body = await req.json()
    nombre = body.get("nombre", "")
    args = body.get("args", {}) or {}
    resultado = H.ejecutar(nombre, **args)

    proyecto_id = body.get("proyecto_id")
    if proyecto_id:
        try:
            piz = cargar_proyecto(proyecto_id)
            piz.registrar_estudio(nombre, args, resultado.get("resumen", ""))
            piz.guardar_auto()
        except FileNotFoundError:
            pass

    return JSONResponse(resultado)


# ──────────────────────────────────────────────────────────────────────────
# Proyectos (investigaciones guardadas)
# ──────────────────────────────────────────────────────────────────────────
def _piz_o_404(pid: str) -> Pizarra:
    try:
        return cargar_proyecto(pid)
    except FileNotFoundError:
        raise HTTPException(404, f"Investigación desconocida: {pid}")


CAMPOS_PROYECTO_EDITABLES = (
    "titulo", "pregunta", "objetivos", "hipotesis", "contexto",
    "series", "serie_dependiente", "frecuencia", "bibliografia_usuario",
)


@app.get("/api/proyectos")
def api_listar_proyectos():
    return JSONResponse(listar_proyectos())


@app.post("/api/proyectos")
async def api_crear_proyecto(req: Request):
    raw = await req.body()
    body = json.loads(raw) if raw else {}
    proyecto = Proyecto(titulo=body.get("titulo") or "Investigación sin título")
    piz = Pizarra(proyecto)
    piz.guardar_auto()
    return JSONResponse(piz.to_dict())


@app.get("/api/proyectos/{pid}")
def api_obtener_proyecto(pid: str):
    return JSONResponse(_piz_o_404(pid).to_dict())


@app.patch("/api/proyectos/{pid}")
async def api_actualizar_proyecto(pid: str, req: Request):
    piz = _piz_o_404(pid)
    body = await req.json()
    for campo in CAMPOS_PROYECTO_EDITABLES:
        if campo in body:
            setattr(piz.proyecto, campo, body[campo])
    piz.guardar_auto()
    return JSONResponse(piz.to_dict())


@app.delete("/api/proyectos/{pid}")
def api_eliminar_proyecto(pid: str):
    eliminar_proyecto(pid)
    return JSONResponse({"ok": True})


@app.post("/api/proyectos/{pid}/notas")
async def api_agregar_nota(pid: str, req: Request):
    piz = _piz_o_404(pid)
    body = await req.json()
    texto = (body.get("texto") or "").strip()
    if not texto:
        raise HTTPException(400, "Nota vacía")
    nota = piz.agregar_nota(texto)
    piz.guardar_auto()
    return JSONResponse(nota)


@app.put("/api/proyectos/{pid}/informe/{seccion}")
async def api_actualizar_informe(pid: str, seccion: str, req: Request):
    piz = _piz_o_404(pid)
    body = await req.json()
    try:
        piz.actualizar_informe(seccion, body.get("texto", ""))
    except KeyError as e:
        raise HTTPException(400, str(e))
    piz.guardar_auto()
    return JSONResponse({"ok": True})


@app.post("/api/proyectos/{pid}/informe/{seccion}/toggle")
def api_toggle_seccion(pid: str, seccion: str):
    piz = _piz_o_404(pid)
    oculta = piz.toggle_seccion(seccion)
    piz.guardar_auto()
    return JSONResponse({"oculta": oculta})


@app.post("/api/proyectos/{pid}/agente/{agente_id}")
async def api_hablar_con_agente(pid: str, agente_id: str, req: Request):
    if agente_id not in AGENTES:
        raise HTTPException(404, f"Agente desconocido: {agente_id}")
    piz = _piz_o_404(pid)
    body = await req.json()
    pregunta = (body.get("pregunta") or "").strip()
    if not pregunta:
        raise HTTPException(400, "Pregunta vacía")

    piz.agregar_chat(agente_id, "usuario", pregunta)
    respuesta = AGENTES[agente_id].responder_directo(piz, pregunta)
    turno = piz.agregar_chat(agente_id, agente_id, respuesta)
    piz.guardar_auto()
    return JSONResponse(turno)


@app.post("/api/proyectos/{pid}/investigar")
def api_investigar(pid: str):
    piz = _piz_o_404(pid)
    orq = Orquestador(piz.proyecto, piz=piz)

    def stream():
        for msg in orq.correr():
            piz.guardar_auto()
            yield "data: " + json.dumps(msg.to_dict(), ensure_ascii=False) + "\n\n"
        piz.guardar_auto()
        yield "data: " + json.dumps({"fin": True}, ensure_ascii=False) + "\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server.app:app", host="127.0.0.1", port=8800, reload=False)
