"""La pestaña Terminal: monta la Terminal de Análisis de Activos dentro de La Cueva.

La Terminal vive en un repo privado aparte (`INVESTIGACI-N-ACTIVOS`). Si su carpeta está en
esta compu (`config.carpeta_terminal()`), se importa su `terminal.puente` y queda montada en
`/terminal/` con la barra común. Si no está, o le falta alguna dependencia, `/terminal/`
muestra por qué y cómo habilitarla: La Cueva sigue funcionando igual.

Este módulo NO lee la base de la Terminal ni sus datos: eso lo hace el puente.
"""

from __future__ import annotations

import html
import importlib
import logging
import sys

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from cueva import config

log = logging.getLogger(__name__)

ESTADO: dict = {"disponible": False, "motivo": "sin intentar", "carpeta": None}


def _importar_puente():
    """Devuelve el módulo `terminal.puente` o levanta la excepción que lo impide."""
    carpeta = config.carpeta_terminal()
    if carpeta and str(carpeta) not in sys.path:
        sys.path.insert(0, str(carpeta))  # la carpeta que contiene el paquete `terminal`
    ESTADO["carpeta"] = str(carpeta) if carpeta else None
    return importlib.import_module("terminal.puente")


def montar(app: FastAPI) -> dict:
    """Monta la Terminal si se puede; si no, deja una página que explica por qué."""
    try:
        puente = _importar_puente()
        puente.montar(app)
        ESTADO.update(disponible=True, motivo="montada en /terminal/", datos=puente.disponible())
    except ModuleNotFoundError as e:
        if e.name and e.name.split(".")[0] == "terminal":
            motivo = "La carpeta de la Terminal no está en esta compu."
        else:
            motivo = f"Falta instalar «{e.name}» (pip install -r <Terminal>/terminal/requirements.txt)."
        ESTADO.update(disponible=False, motivo=motivo)
        _pagina_no_disponible(app)
    except Exception as e:  # la Terminal no puede tumbar La Cueva
        log.exception("no se pudo montar la Terminal")
        ESTADO.update(disponible=False, motivo=f"Error al montar la Terminal: {e}")
        _pagina_no_disponible(app)
    log.info("Terminal: %s", ESTADO["motivo"])
    return ESTADO


def _pagina_no_disponible(app: FastAPI) -> None:
    @app.get("/terminal", response_class=HTMLResponse, include_in_schema=False)
    @app.get("/terminal/{resto:path}", response_class=HTMLResponse, include_in_schema=False)
    def terminal_no_disponible(resto: str = ""):
        return HTMLResponse(PAGINA.replace("{{motivo}}", html.escape(ESTADO["motivo"])), status_code=503)


PAGINA = """<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Terminal · La Cueva del Economista</title>
<link rel="stylesheet" href="/web/estilo/tokens.css">
<script src="/web/estilo/tema.js"></script>
<script src="/web/estilo/barra.js" defer></script>
</head><body>
<header class="topbar">
  <a class="brand" href="/" style="text-decoration:none;color:inherit">
    <div class="brand-name">La Cueva del <em>Economista</em></div></a>
  <nav class="modswitch" data-barra></nav>
</header>
<main style="max-width:640px;margin:48px auto;padding:0 20px">
  <h1 style="font-size:22px">La Terminal no está disponible</h1>
  <p>{{motivo}}</p>
  <p class="lbl" style="margin-top:24px">Cómo habilitarla</p>
  <ol>
    <li>Tener el repo de la Terminal en la compu (por defecto en
      <code>PROGRAMACION\\PORTFOLIO MANAGER\\INVESTIGACIÓN ACTIVOS</code>), o indicar su carpeta
      <code>terminal</code> en la variable <code>CUEVA_TERMINAL</code>.</li>
    <li>Abrir La Cueva con <code>La Cueva del Economista.bat</code>: instala lo que le falte.</li>
  </ol>
</main></body></html>"""
