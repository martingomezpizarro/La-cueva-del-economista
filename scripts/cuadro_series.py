"""cuadro_series.py — arma el cuadro navegable de todas las series del catálogo.

Corre la auditoría (`scripts/auditar_series.py`) y con eso genera una página que se
puede buscar, filtrar y ordenar: qué serie es, de qué archivo sale, desde cuándo hasta
cuándo, cada cuánto, quién la publica, qué mide y en qué unidad está medida.

Salidas:
    docs/cuadro_series.html   página completa, se abre con doble clic
    docs/inventario_series.csv  y  docs/INVENTARIO_SERIES.md   (los escribe la auditoría)

Uso:
    python scripts/cuadro_series.py
    python scripts/cuadro_series.py --cuerpo /tmp/cuadro.html   # sin <html>/<head>/<body>
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from auditar_series import CATALOGO, RAIZ, auditar, escribir  # type: ignore

SALIDA = RAIZ / "docs" / "cuadro_series.html"

# Cómo se lee cada estado en el cuadro: qué pasa y de qué gravedad es.
SEMAFORO = {
    "ok": ("bien", "Verificable"),
    "pendiente de descarga": ("espera", "Falta bajarla"),
    "vacía o columna equivocada": ("alerta", "Sin datos"),
    "ARCHIVO NO ENCONTRADO": ("mal", "Archivo ausente"),
    "sin archivo (nodo agrupador o dummy)": ("neutro", "Agrupador"),
}


def _estado(texto: str) -> tuple[str, str]:
    for clave, (nivel, etiqueta) in SEMAFORO.items():
        if texto.startswith(clave):
            return nivel, etiqueta
    return "neutro", texto


def _datos(filas: list[dict]) -> list[dict]:
    compactas = []
    for f in filas:
        nivel, etiqueta = _estado(f["estado"])
        compactas.append({
            "serie": f["serie"],
            "id": f["id"],
            "fam": f["familia"],
            "sub": f["subgrupo"],
            "base": f["base"],
            "ini": f["origen"],
            "fin": f["final"],
            "frec": f["frecuencia"],
            "fuente": f["fuente"],
            "desc": f["descripcion"],
            "mag": f["magnitud"],
            "esc": f["escala"],
            "mon": f["moneda"],
            "uni": f["unidad_texto"],
            "baseidx": f["base_indice"],
            "prec": f["precios"],
            "obs": f["n_obs"],
            "conf": f["confianza"],
            "niv": nivel,
            "est": etiqueta,
            "cf": f["col_fecha"],
            "cv": f["col_valor"],
            "ext": f["id_externo"],
        })
    return compactas


def _resumen(datos: list[dict]) -> dict:
    ids = {d["id"] for d in datos}
    con_fecha = [d for d in datos if d["ini"]]
    return {
        "series": len(ids),
        "entradas": len(datos),
        "verificables": sum(1 for d in datos if d["niv"] == "bien"),
        "pendientes": sum(1 for d in datos if d["niv"] == "espera"),
        "problemas": sum(1 for d in datos if d["niv"] in {"alerta", "mal"}),
        "sin_desc": sum(1 for d in datos if not d["desc"]),
        "mas_antigua": min((d["ini"] for d in con_fecha), default=""),
        "fuentes": len({d["fuente"] for d in datos if d["fuente"]}),
    }


def construir(datos: list[dict], resumen: dict, cuerpo_solo: bool = False) -> str:
    payload = json.dumps(datos, ensure_ascii=False, separators=(",", ":"))
    cabeza = "" if cuerpo_solo else (
        "<!doctype html>\n<html lang=\"es\">\n<head>\n<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
    )
    cierre_cabeza = "" if cuerpo_solo else "</head>\n<body>\n"
    pie = "" if cuerpo_solo else "\n</body>\n</html>\n"

    return f"""{cabeza}<title>Catálogo de Series</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Serif:wght@500;600&display=swap">
<style>
{ESTILOS.read_text(encoding='utf-8')}
</style>
{cierre_cabeza}
<header class="barra">
  <div class="marca">
    <h1>Catálogo de Series</h1>
    <p class="bajada">La Cueva del Economista · cada serie con su archivo, su cobertura, su fuente y su unidad</p>
  </div>
  <dl class="metricas">
    <div><dt>Series</dt><dd>{resumen['series']}</dd></div>
    <div><dt>Entradas</dt><dd>{resumen['entradas']}<span class="sufijo">serie × frecuencia</span></dd></div>
    <div><dt>Verificables</dt><dd class="v-bien">{resumen['verificables']}</dd></div>
    <div><dt>Por bajar</dt><dd class="v-espera">{resumen['pendientes']}</dd></div>
    <div><dt>Con problema</dt><dd class="v-mal">{resumen['problemas']}</dd></div>
    <div><dt>Dato más viejo</dt><dd class="fecha">{resumen['mas_antigua'] or '—'}</dd></div>
  </dl>
</header>

<div class="controles">
  <div class="buscador">
    <input id="q" type="search" placeholder="Buscar por serie, id, archivo o descripción…" autocomplete="off" spellcheck="false">
  </div>
  <div class="filtros" id="filtros"></div>
  <div class="acciones">
    <span class="conteo" id="conteo"></span>
    <button type="button" id="copiar">Copiar filtrado</button>
    <button type="button" id="limpiar">Limpiar</button>
  </div>
</div>

<main class="tabla-zona">
  <table id="tabla">
    <thead>
      <tr>
        <th data-col="serie" class="orden">Serie</th>
        <th data-col="base" class="orden">Base</th>
        <th data-col="ini" class="orden num">Origen</th>
        <th data-col="fin" class="orden num">Final</th>
        <th data-col="frec" class="orden centro">Frec.</th>
        <th data-col="fuente" class="orden">Fuente</th>
        <th class="ancha">Descripción</th>
        <th data-col="mag" class="orden">Magnitud</th>
        <th data-col="esc" class="orden">Escala</th>
        <th data-col="mon" class="orden centro">Moneda</th>
      </tr>
    </thead>
    <tbody id="cuerpo"></tbody>
  </table>
  <p class="vacio" id="vacio" hidden>Ninguna serie coincide con eso.</p>
</main>

<footer class="pie">
  <p>Generado con <code>python scripts/cuadro_series.py</code> desde <code>cueva/datos/catalogo.json</code>. Click en una fila para ver la ficha completa.</p>
</footer>

<script>
const DATOS = {payload};
{GUION.read_text(encoding='utf-8')}
</script>{pie}"""


ESTILOS = RAIZ / "web" / "cuadro" / "cuadro.css"
GUION = RAIZ / "web" / "cuadro" / "cuadro.js"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cuerpo", default="",
                    help="Escribir además una versión sin <html>/<head>/<body>, para publicar.")
    args = ap.parse_args()

    if not CATALOGO.exists():
        raise SystemExit(f"No encuentro {CATALOGO}")

    filas = auditar()
    escribir(filas)  # deja el CSV y el markdown al día
    datos = _datos(filas)
    resumen = _resumen(datos)

    SALIDA.write_text(construir(datos, resumen), encoding="utf-8")
    print(f"{resumen['entradas']} entradas · {resumen['series']} series -> "
          f"{SALIDA.relative_to(RAIZ)}")
    print(f"   verificables {resumen['verificables']} · por bajar {resumen['pendientes']} "
          f"· con problema {resumen['problemas']} · sin descripción {resumen['sin_desc']}")

    if args.cuerpo:
        destino = Path(args.cuerpo)
        destino.write_text(construir(datos, resumen, cuerpo_solo=True), encoding="utf-8")
        print(f"   versión para publicar -> {destino}")


if __name__ == "__main__":
    main()
