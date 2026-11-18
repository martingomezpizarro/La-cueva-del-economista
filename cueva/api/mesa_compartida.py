"""mesa_compartida — bandeja, tablero y documento por API.

Es la parte de la API que comparten la interfaz (Inicio, Terminal, Mesa, Línea de tiempo) y el
asistente que trabaja por MCP. Lo que agrega uno lo ve el otro: todo queda en el servidor.

- Bandeja: `GET|POST|DELETE /api/v1/bandeja`, `DELETE /api/v1/bandeja/{item}`
- Tablero del proyecto: `GET /api/v1/proyectos/{pid}/tablero`,
  `POST /api/v1/proyectos/{pid}/figuras`, `DELETE /api/v1/proyectos/{pid}/figuras/{fid}`
- Documento: `GET /api/v1/proyectos/{pid}/documento`,
  `POST /api/v1/proyectos/{pid}/documento/bloques`,
  `PATCH|DELETE /api/v1/proyectos/{pid}/documento/bloques/{bid}`
- Novedades (para refrescar la pantalla cuando escribe el otro): `GET /api/v1/novedades?desde=ts`

Qué NO hace: no calcula nada. Los números salen de la Terminal (`/terminal/api/...`) o de los
métodos de la Mesa (`/api/v1/herramienta`); acá solo se guardan y se ordenan.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field

from cueva.agentes.pizarra import SECCIONES_INFORME
from cueva.sesiones.bandeja import TIPOS, Bandeja, ItemDesconocido, get_bandeja
from cueva.sesiones.repositorio import RepositorioProyectos

PID_PATTERN = r"^[0-9a-f]{8,32}$"
CORTO = r"^[0-9a-f]{8,10}$"
Autor = Literal["usuario", "claude"]


class ItemBandejaCrear(BaseModel):
    tipo: Literal["serie", "figura", "resultado", "dataset"]
    ref: str = Field(min_length=1, max_length=200)
    etiqueta: str = Field(default="", max_length=200)
    receta: dict | None = None
    procedencia: dict | None = None
    datos: dict | None = None
    autor: Autor = "usuario"


class FiguraCrear(BaseModel):
    titulo: str = Field(min_length=1, max_length=200)
    tipo: str = Field(min_length=1, max_length=40)  # lineas, barras, tabla, sankey…
    datos: dict | None = None
    receta: dict | None = None
    procedencia: dict | None = None
    origen: Literal["terminal", "mesa", "inicio", "tiempo", "claude"] = "mesa"
    autor: Autor = "usuario"


class BloqueCrear(BaseModel):
    seccion: str = Field(max_length=40)
    tipo: Literal["texto", "figura"]
    texto: str = Field(default="", max_length=50_000)
    figura_id: str | None = Field(default=None, pattern=CORTO)
    posicion: int | None = Field(default=None, ge=0)
    autor: Autor = "usuario"


class BloqueCambiar(BaseModel):
    texto: str | None = Field(default=None, max_length=50_000)
    seccion: str | None = Field(default=None, max_length=40)
    posicion: int | None = Field(default=None, ge=0)


def crear_router(get_repo: Callable[[], RepositorioProyectos]) -> APIRouter:
    r = APIRouter(prefix="/api/v1", tags=["mesa compartida"])
    PID = Path(pattern=PID_PATTERN)

    # ── bandeja ───────────────────────────────────────────────────────────
    @r.get("/bandeja")
    def bandeja_listar(b: Bandeja = Depends(get_bandeja)):
        return {"items": b.listar(), "tipos": list(TIPOS)}

    @r.post("/bandeja")
    def bandeja_agregar(body: ItemBandejaCrear, b: Bandeja = Depends(get_bandeja)):
        return b.agregar(**body.model_dump())

    @r.delete("/bandeja/{item_id}")
    def bandeja_quitar(item_id: str = Path(pattern=CORTO), b: Bandeja = Depends(get_bandeja)):
        try:
            b.quitar(item_id)
        except ItemDesconocido:
            raise HTTPException(404, f"No está en la bandeja: {item_id}") from None
        return {"ok": True}

    @r.delete("/bandeja")
    def bandeja_vaciar(b: Bandeja = Depends(get_bandeja)):
        return {"ok": True, "quitados": b.vaciar()}

    # ── tablero ───────────────────────────────────────────────────────────
    @r.get("/proyectos/{pid}/tablero")
    def tablero(pid: str = PID, repo: RepositorioProyectos = Depends(get_repo)):
        piz = repo.obtener(pid)
        return {"proyecto": piz.proyecto.titulo, "figuras": piz.figuras}

    @r.post("/proyectos/{pid}/figuras")
    def fijar(body: FiguraCrear, pid: str = PID, repo: RepositorioProyectos = Depends(get_repo)):
        with repo.abrir(pid) as piz:
            return piz.fijar_figura(**body.model_dump())

    @r.delete("/proyectos/{pid}/figuras/{fid}")
    def desfijar(
        pid: str = PID,
        fid: str = Path(pattern=CORTO),
        repo: RepositorioProyectos = Depends(get_repo),
    ):
        with repo.abrir(pid) as piz:
            if not piz.quitar_figura(fid):
                raise HTTPException(404, f"Figura desconocida: {fid}")
        return {"ok": True}

    # ── documento ─────────────────────────────────────────────────────────
    @r.get("/proyectos/{pid}/documento")
    def documento(pid: str = PID, repo: RepositorioProyectos = Depends(get_repo)):
        """El documento entero, sección por sección: el texto del informe y los bloques
        insertados, con cada figura resuelta (datos + receta + procedencia para la leyenda)."""
        piz = repo.obtener(pid)
        figuras = {f["id"]: f for f in piz.figuras}
        secciones = []
        for s in SECCIONES_INFORME:
            bloques = []
            for b in piz.documento:
                if b["seccion"] != s:
                    continue
                bloques.append({**b, "figura": figuras.get(b["figura_id"]) if b["figura_id"] else None})
            secciones.append(
                {
                    "id": s,
                    "texto": piz.informe.get(s, ""),
                    "oculta": s in piz.secciones_ocultas,
                    "bloques": bloques,
                }
            )
        return {"proyecto": piz.proyecto.titulo, "secciones": secciones, "actualizado": piz.actualizado}

    @r.post("/proyectos/{pid}/documento/bloques")
    def insertar(body: BloqueCrear, pid: str = PID, repo: RepositorioProyectos = Depends(get_repo)):
        if body.seccion not in SECCIONES_INFORME:
            raise HTTPException(422, f"Sección desconocida: {body.seccion}. Opciones: {SECCIONES_INFORME}")
        with repo.abrir(pid) as piz:
            try:
                return piz.insertar_bloque(**body.model_dump())
            except (KeyError, ValueError) as e:
                raise HTTPException(422, str(e)) from None

    @r.patch("/proyectos/{pid}/documento/bloques/{bid}")
    def cambiar(
        body: BloqueCambiar,
        pid: str = PID,
        bid: str = Path(pattern=CORTO),
        repo: RepositorioProyectos = Depends(get_repo),
    ):
        if body.seccion is not None and body.seccion not in SECCIONES_INFORME:
            raise HTTPException(422, f"Sección desconocida: {body.seccion}")
        with repo.abrir(pid) as piz:
            try:
                bloque = None
                if body.texto is not None:
                    bloque = piz.editar_bloque(bid, body.texto)
                if body.seccion is not None or body.posicion is not None:
                    actual = next(b for b in piz.documento if b["id"] == bid)
                    bloque = piz.mover_bloque(bid, body.seccion or actual["seccion"], body.posicion)
            except StopIteration:
                raise HTTPException(404, f"Bloque desconocido: {bid}") from None
            except KeyError:
                raise HTTPException(404, f"Bloque desconocido: {bid}") from None
            except ValueError as e:
                raise HTTPException(422, str(e)) from None
        if bloque is None:
            raise HTTPException(422, "Nada que cambiar: mandá texto, sección o posición")
        return bloque

    @r.delete("/proyectos/{pid}/documento/bloques/{bid}")
    def quitar_bloque(
        pid: str = PID,
        bid: str = Path(pattern=CORTO),
        repo: RepositorioProyectos = Depends(get_repo),
    ):
        with repo.abrir(pid) as piz:
            if not piz.quitar_bloque(bid):
                raise HTTPException(404, f"Bloque desconocido: {bid}")
        return {"ok": True}

    # ── novedades ─────────────────────────────────────────────────────────
    @r.get("/novedades")
    def novedades(
        desde: float = Query(0, ge=0),
        repo: RepositorioProyectos = Depends(get_repo),
        b: Bandeja = Depends(get_bandeja),
    ):
        """Qué cambió desde `desde` (segundos epoch): ítems nuevos de la bandeja y proyectos
        tocados. La pantalla lo consulta cada pocos segundos para mostrar lo que agregó el otro."""
        return {
            "bandeja": [i for i in b.listar() if i.get("ts", 0) > desde],
            "proyectos": [p for p in repo.listar() if p.get("actualizado", 0) > desde],
        }

    return r
