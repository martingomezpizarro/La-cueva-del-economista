"""La Mesa de investigación: la página (web/cueva/index.html) y su catálogo vivo.

`GET /api/v1/mesa/catalogo.js` devuelve `const CAT = {…};` con el formato que espera la
página (ver cueva/datos/catalogo_mesa.py): las series de data/series y, si la Terminal está
montada, las suyas por ticker. Se arma una vez y se guarda en memoria hasta que cambia algún
archivo de series o la base de la Terminal.
"""

from __future__ import annotations

import json
import logging
import threading

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

from cueva.api import terminal as pestana_terminal
from cueva.datos import catalogo_mesa
from cueva.datos import series as S

log = logging.getLogger(__name__)

_lock = threading.Lock()
_cache: dict = {"firma": None, "js": None}


def _series_terminal() -> tuple[list[dict], object]:
    """Fichas de la Terminal (con datos solo las precargadas) y una firma para el caché."""
    if not pestana_terminal.ESTADO.get("disponible"):
        return [], None
    try:
        from terminal import config as tconfig
        from terminal import puente

        firma = tconfig.RUTA_DB.stat().st_mtime if tconfig.RUTA_DB.exists() else None
        return puente.series_mesa(catalogo_mesa.TERMINAL_PRECARGADAS), firma
    except Exception as e:  # la Terminal nunca impide abrir la Mesa
        log.warning("mesa: no se pudieron leer las series de la Terminal: %s", e)
        return [], None


def catalogo_js() -> str:
    with _lock:
        firma_cueva = S._firma()
        # la firma de la Terminal se mira sin leer sus series (solo la fecha de la base)
        try:
            from terminal import config as tconfig

            firma_term = (
                tconfig.RUTA_DB.stat().st_mtime if pestana_terminal.ESTADO.get("disponible") else None
            )
        except Exception:
            firma_term = None
        firma = (firma_cueva, firma_term)
        if _cache["firma"] != firma or _cache["js"] is None:
            terminal, _ = _series_terminal()
            cat = catalogo_mesa.armar(terminal)
            _cache.update(
                firma=firma,
                js="const CAT = " + json.dumps(cat, ensure_ascii=False, separators=(",", ":")) + ";\n",
            )
            log.info(
                "mesa: catálogo armado (%d series, %d en el árbol)", len(cat["series"]), len(cat["arbol"])
            )
        return _cache["js"]


class SerieMesa(BaseModel):
    nombre: str = Field(max_length=120)
    fechas: list[str] = Field(max_length=60000)
    valores: list[float | None] = Field(max_length=60000)


class MetodoMesa(BaseModel):
    """Correr un método del catálogo sobre fichas de la Mesa (con sus datos)."""

    metodo: str = Field(pattern=r"^[a-z0-9_]{1,60}$")
    args: dict = Field(default_factory=dict)
    series: dict[str, SerieMesa] = Field(default_factory=dict, max_length=24)


def _sustituir(v, ids: dict[str, str]):
    """Cambia «@clave» por el id registrado de esa ficha (en strings y listas)."""
    if isinstance(v, str) and v.startswith("@"):
        if v[1:] not in ids:
            raise HTTPException(422, f"La ficha {v} no vino en «series».")
        return ids[v[1:]]
    if isinstance(v, list):
        return [_sustituir(x, ids) for x in v]
    return v


def correr_metodo(body: MetodoMesa) -> dict:
    from cueva.econometria import herramientas as H
    from cueva.metodos import insumos
    from cueva.metodos.contrato import ErrorMetodo, limpiar

    try:
        ids = {k: insumos.registrar_datos(s.nombre, s.fechas, s.valores) for k, s in body.series.items()}
    except ErrorMetodo as e:
        raise HTTPException(422, str(e)) from e
    args = {k: _sustituir(v, ids) for k, v in body.args.items()}
    res = limpiar(H.ejecutar(body.metodo, **args))
    # en los textos, el id interno de cada ficha («m:…») se cambia por su nombre
    texto = json.dumps(res, ensure_ascii=False)
    for clave, sid in ids.items():
        texto = texto.replace(sid, body.series[clave].nombre)
    return json.loads(texto)


def serie_terminal(sid: str) -> dict | None:
    """Una serie de la Terminal con sus datos, para traerla a pedido a la Mesa
    (las que no vienen precargadas en el catálogo aparecen con estado «terminal»)."""
    if not pestana_terminal.ESTADO.get("disponible"):
        return None
    from terminal import puente

    ficha = next((f for f in puente.series_mesa([sid]) if f["id"] == sid), None)
    if ficha is None or not ficha.get("puntos"):
        return None
    sub = ficha.get("subgrupo") or ficha.get("grupo") or ""
    corto = ficha.get("corto") or ficha["nombre"]
    return {
        "id": sid,
        "nombre": f"{corto} · {sub}" if sub else corto,
        "corto": corto,
        "freq": ficha["freq"],
        "unidad": ficha.get("unidad") or "",
        "fuente": ficha["fuente"],
        "familia": ficha["familia"],
        "grupo": ficha["grupo"],
        "subgrupo": ficha.get("subgrupo") or "",
        "url": ficha.get("url"),
        "x": [f for f, _ in ficha["puntos"]],
        "y": [v for _, v in ficha["puntos"]],
    }


def series_de_activo(ticker: str) -> list[dict]:
    """Las series de la Terminal que pertenecen a un activo: su precio (id = ticker) y sus
    balances trimestrales (`<ticker>_<variable>_T`); o, si `ticker` es un id de FRED de la
    pestaña Macro (VIXCLS…), esa serie con el id que usa la Mesa (vix…). Sin datos: es el
    menú para mandar a la bandeja."""
    if not pestana_terminal.ESTADO.get("disponible"):
        return []
    from terminal import puente

    t = ticker.upper()
    salida = []
    for f in puente.series_mesa([]):
        sid = f["id"]
        if sid.upper() == t:
            etiqueta, grupo = "Precio diario", "Precio"
        elif (f.get("fuente") or "").upper().endswith("FRED " + t):
            etiqueta, grupo = f.get("nombre") or sid, f.get("grupo") or "Macro"
        elif sid.upper().startswith(t + "_") and sid.endswith("_T"):
            etiqueta, grupo = sid[len(t) + 1 : -2].replace("_", " "), f.get("grupo") or "Balances"
        else:
            continue
        salida.append(
            {
                "id": sid,
                "nombre": etiqueta
                if grupo != "Precio" and "FRED" in (f.get("fuente") or "")
                else f"{t} · {etiqueta}",
                "etiqueta": etiqueta,
                "grupo": grupo,
                "freq": f.get("freq") or "",
                "unidad": f.get("unidad") or "",
            }
        )
    salida.sort(key=lambda d: (d["id"].upper() != t, d["grupo"], d["etiqueta"]))
    return salida


def registrar(app: FastAPI) -> None:
    @app.get("/api/v1/mesa/activo/{ticker}")
    def mesa_activo(ticker: str):
        """Qué series de un activo de la Terminal se pueden mandar a la bandeja."""
        import re

        if not re.fullmatch(r"[A-Za-z0-9.\-^=]{1,30}", ticker):
            raise HTTPException(422, "Ticker inválido.")
        try:
            return JSONResponse({"ticker": ticker, "series": series_de_activo(ticker)})
        except Exception as e:
            log.warning("mesa: no se pudieron listar las series de %s: %s", ticker, e)
            raise HTTPException(503, f"No se pudo leer «{ticker}» de la Terminal.") from e

    @app.get("/api/v1/mesa/serie/{sid}")
    def mesa_serie(sid: str):
        """Trae a pedido una serie de la Terminal (ticker, vix, KO_ingresos_T…) con sus datos."""
        import re

        if not re.fullmatch(r"[A-Za-z0-9_.\-^=]{1,60}", sid):
            raise HTTPException(422, "Id de serie inválido.")
        try:
            datos = serie_terminal(sid)
        except Exception as e:  # la Terminal nunca tumba la Mesa
            log.warning("mesa: no se pudo traer %s de la Terminal: %s", sid, e)
            raise HTTPException(503, f"No se pudo leer «{sid}» de la Terminal.") from e
        if datos is None:
            raise HTTPException(404, f"«{sid}» no está en la Terminal de esta compu (o no tiene datos).")
        return JSONResponse(datos)

    @app.post("/api/v1/mesa/metodo")
    def mesa_metodo(body: MetodoMesa):
        return JSONResponse(correr_metodo(body))

    @app.get("/api/v1/mesa/catalogo.js", include_in_schema=False)
    def mesa_catalogo():
        return Response(
            catalogo_js(), media_type="application/javascript", headers={"Cache-Control": "no-cache"}
        )
