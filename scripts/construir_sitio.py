"""construir_sitio.py — arma la versión publicada (estática) de La Cueva para GitHub Pages.

La plataforma real es un servidor FastAPI. Esta versión congela lo que se puede leer sin
servidor y lo deja en una carpeta lista para subir:

    /                       Mesa de Trabajo (cascarón + explorador de series en iframe)
    /explorador/            el explorador de series (web/explorador.html)
    /tiempo/                la Línea de Tiempo
    /tiempo/<evento>/       permalink de cada evento (misma página, abre con la ficha puesta)
    /api/v1/historia.json   y  /api/v1/historia/eventos/<id>.json   (la historia, congelada)
    /api/v1/explorador/datos.json                                  (las series del explorador)
    /web/ · /vendor/        CSS, módulos ES y librerías, tal cual

Cada página lleva inyectado `web/estatico/estatico.js`, que traduce los `fetch` de la API a
esos JSON. Lo que en el servidor ejecuta Python (Estudio, Kalman, agentes) avisa que no está.

Las series del explorador NO están en el repo (viven en la carpeta del Trabajo Final de cada
máquina). Para publicarlas hay que exportarlas una vez en la máquina que las tiene:

    python scripts/construir_sitio.py --exportar-datos-explorador
        → data/publico/explorador_datos.json  (se versiona; el workflow de Pages lo usa)

Uso:
    python scripts/construir_sitio.py                      # arma _sitio/
    python scripts/construir_sitio.py --salida /tmp/sitio --dominio ""   # sin CNAME
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from cueva.datos import explorador_datos  # noqa: E402
from cueva.datos import historia as HIST  # noqa: E402

WEB = RAIZ / "web"
DOMINIO = "cuevadeleconomista.martingomezpizarro.com.ar"
DATOS_PUBLICOS = RAIZ / "data" / "publico" / "explorador_datos.json"
SALIDA = RAIZ / "_sitio"

INYECCION = '<script src="/web/estatico/estatico.js"></script>'
AVISO_SIN_DATOS = (
    '<p class="note aviso"><b>Todavía no se publicaron las series.</b> El explorador '
    "abre, pero sin datos: falta exportarlas con "
    "<code>scripts/construir_sitio.py --exportar-datos-explorador</code>.</p>"
)


def _json(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def _escribir(ruta: Path, texto: str) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(texto, encoding="utf-8")


def inyectar(html: str) -> str:
    """Mete estatico.js justo después del <meta charset>: antes que cualquier otro script."""
    nuevo, n = re.subn(r"(<meta charset=[^>]*>)", r"\1" + INYECCION, html, count=1, flags=re.I)
    if n != 1:
        raise ValueError("La página no tiene <meta charset>: no sé dónde inyectar estatico.js")
    return nuevo


def datos_explorador(origen: Path | None) -> dict:
    """Las series del explorador: archivo pedido > exportado en el repo > payload en vivo."""
    for ruta in (origen, DATOS_PUBLICOS):
        if ruta and ruta.exists():
            return json.loads(ruta.read_text(encoding="utf-8"))
    return explorador_datos.payload()


def construir(salida: Path, dominio: str = DOMINIO, origen_datos: Path | None = None) -> dict:
    """Arma el sitio en `salida` (la borra antes). Devuelve un resumen de lo que escribió."""
    if salida.exists():
        shutil.rmtree(salida)
    salida.mkdir(parents=True)

    # estáticos tal cual: el sistema de diseño, los módulos ES y las librerías
    for carpeta in ("estilo", "tiempo", "estatico"):
        shutil.copytree(WEB / carpeta, salida / "web" / carpeta)
    shutil.copytree(WEB / "vendor", salida / "vendor")
    medios = RAIZ / "data" / "historia" / "medios"
    if medios.exists():
        shutil.copytree(medios, salida / "historia-medios")

    # Línea de Tiempo: la página, un permalink por evento y la API congelada
    historia = HIST.payload()
    _escribir(salida / "api" / "v1" / "historia.json", _json(historia))
    pagina_tiempo = inyectar((WEB / "tiempo" / "index.html").read_text(encoding="utf-8"))
    _escribir(salida / "tiempo" / "index.html", pagina_tiempo)
    ids = [e["id"] for e in historia["eventos"]]
    for eid in ids:
        _escribir(
            salida / "api" / "v1" / "historia" / "eventos" / f"{eid}.json", _json(HIST.payload_evento(eid))
        )
        _escribir(salida / "tiempo" / eid / "index.html", pagina_tiempo)

    # Mesa de Trabajo: el cascarón en la raíz y el explorador con sus series
    datos = datos_explorador(origen_datos)
    _escribir(salida / "api" / "v1" / "explorador" / "datos.json", _json(datos))
    _escribir(
        salida / "explorador" / "index.html", inyectar((WEB / "explorador.html").read_text(encoding="utf-8"))
    )
    mesa = (WEB / "estatico" / "mesa.html").read_text(encoding="utf-8")
    mesa = mesa.replace("<!--__AVISO_SIN_DATOS__-->", "" if datos else AVISO_SIN_DATOS)
    _escribir(salida / "index.html", inyectar(mesa))
    _escribir(salida / "404.html", inyectar(mesa))

    # GitHub Pages: dominio propio y sin Jekyll (si no, ignora las carpetas con «_»)
    if dominio:
        _escribir(salida / "CNAME", dominio + "\n")
    _escribir(salida / ".nojekyll", "")

    return {"eventos": len(ids), "archivos_de_series": len(datos), "dominio": dominio or None}


def exportar_datos_explorador(destino: Path = DATOS_PUBLICOS) -> int:
    """Congela las series del explorador desde la carpeta de datos local (Trabajo Final)."""
    datos = explorador_datos.payload()
    if not datos:
        raise SystemExit(
            "No encontré series: esta máquina no tiene la carpeta del Trabajo Final "
            "(o CUEVA_TRABAJO_FINAL apunta mal). No exporto un archivo vacío."
        )
    _escribir(destino, _json(datos))
    return len(datos)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--salida", type=Path, default=SALIDA, help="carpeta del sitio (default: _sitio/)")
    ap.add_argument("--dominio", default=DOMINIO, help='dominio del CNAME ("" para no escribirlo)')
    ap.add_argument(
        "--datos-explorador", type=Path, help="JSON de series a publicar (default: data/publico/)"
    )
    ap.add_argument(
        "--exportar-datos-explorador",
        action="store_true",
        help="en vez de armar el sitio, congela las series locales en data/publico/explorador_datos.json",
    )
    args = ap.parse_args()

    if args.exportar_datos_explorador:
        n = exportar_datos_explorador()
        print(f"{n} archivos de series → {DATOS_PUBLICOS.relative_to(RAIZ)}")
        return

    r = construir(args.salida, args.dominio, args.datos_explorador)
    print(f"Sitio en {args.salida}: {r['eventos']} eventos, {r['archivos_de_series']} archivos de series.")
    if not r["archivos_de_series"]:
        print(
            "OJO: el explorador sale SIN series (falta --exportar-datos-explorador en la máquina con datos)."
        )


if __name__ == "__main__":
    main()
