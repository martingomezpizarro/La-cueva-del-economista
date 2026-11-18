"""mesa_desde_mockup.py — convierte el mockup «La Cueva» en la página real de la plataforma.

El mockup (artifact «La Cueva», bajado como la-cueva.html) trae TODA la interfaz pensada:
Inicio personalizable, Mesa de investigación (catálogo, lienzo de gráficos con capas y
transformaciones, fichas, herramientas por verbo, registro de resultados, ecuaciones libres,
código Python, linaje y paquete reproducible, los 9 proyectos de la 1.0), Proyecto, Documento
y la bandeja. Este script la pasa a `web/cueva/index.html` sin reescribirla:

- Saca el bloque de datos embebido (`const CAT = …`, ~5 MB, con precios de la Terminal que no
  se pueden publicar) y lo reemplaza por `/api/v1/mesa/catalogo.js`, que arma el servidor con
  las series vivas (data/series + la Terminal, si está en la compu).
- Colores y tipografía: los del sistema común (`/web/estilo/tokens.css`, paleta de la Terminal)
  y el tema de `/web/estilo/tema.js`.
- Navegación: Línea de tiempo → `/tiempo`; Terminal → `/terminal/` (la Terminal real, no la
  ficha simplificada del mockup); en `/mesa` arranca en Investigación.
- Saca lo que era solo del mockup: el chip «Mockup» y el botón «⬇ HTML».

Uso (con el la-cueva.html del artifact a mano; NO se versiona porque trae datos privados):
    python scripts/mesa_desde_mockup.py --desde "<ruta>/la-cueva.html"
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "web" / "cueva" / "index.html"


def reemplazar(texto: str, viejo: str, nuevo: str, cuenta: int = 1) -> str:
    """Reemplazo que FALLA si el mockup cambió y el pedazo ya no está (no se rompe en silencio)."""
    n = texto.count(viejo)
    if n != cuenta:
        raise SystemExit(f"Esperaba {cuenta} aparición(es) y hay {n}: {viejo[:90]!r}")
    return texto.replace(viejo, nuevo)


def convertir(html: str) -> str:
    # 1. datos embebidos → catálogo vivo del servidor
    html, n = re.subn(
        r"<script>\s*/\* Generado por scripts/armar_datos_mesa\.py[^\n]*\n\s*const CAT = .*?;\s*\n</script>",
        '<script src="/api/v1/mesa/catalogo.js"></script>',
        html,
        count=1,
        flags=re.S,
    )
    if n != 1:
        raise SystemExit("No encontré el bloque de datos `const CAT = …` del mockup.")
    html, n = re.subn(r"<script>window\.__marcadoCueva = [^<]*</script>\n?", "", html, count=1)
    html, n2 = re.subn(
        r"<script>\s*/\* ⬇ HTML: descarga el código fuente.*?</script>\n?", "", html, count=1, flags=re.S
    )
    if n != 1 or n2 != 1:
        raise SystemExit("No encontré los scripts de descarga del mockup.")

    # 2. colores y tema del sistema común (paleta de la Terminal)
    html, n = re.subn(r":root\{\n  --ground:.*?color-scheme:dark\}\n", "", html, count=1, flags=re.S)
    if n != 1:
        raise SystemExit("No encontré el bloque de colores del mockup.")
    html = reemplazar(
        html,
        "<style>",
        '<link rel="stylesheet" href="/web/estilo/tokens.css">\n<script src="/web/estilo/tema.js"></script>\n<style>',
    )
    html = reemplazar(
        html,
        '$("#tema").addEventListener("click", () => { const r = document.documentElement; const oscuro = '
        'r.dataset.theme ? r.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches; '
        'r.dataset.theme = oscuro ? "light" : "dark"; render(); renderTablero(); });',
        '$("#tema").addEventListener("click", () => { window.CuevaTema.alternar(); render(); renderTablero(); });',
    )

    # 3. navegación de la plataforma
    html = reemplazar(
        html,
        '<a class="np" href="https://cuevadeleconomista.martingomezpizarro.com.ar/" target="_blank" '
        'rel="noopener" title="Se abre en una pestaña aparte">Línea de tiempo ↗</a>',
        '<a class="np" href="/tiempo" target="_blank" rel="noopener" title="Se abre en una pestaña aparte">'
        "Línea de tiempo ↗</a>",
    )
    html = reemplazar(
        html,
        '<a href="https://cuevadeleconomista.martingomezpizarro.com.ar/" target="_blank" rel="noopener">'
        "Línea de tiempo ↗",
        '<a href="/tiempo" target="_blank" rel="noopener">Línea de tiempo ↗',
    )
    html = reemplazar(
        html,
        '<a class="np" href="#mercados" data-v="mercados">Terminal</a>',
        '<a class="np" href="/terminal/">Terminal</a>',
    )
    html = reemplazar(html, '<a href="#mercados">Terminal<small>', '<a href="/terminal/">Terminal<small>')
    html = reemplazar(
        html,
        '    const h = (location.hash || "").slice(1) || "inicio";\n    if (!VISTAS.includes(h)) return;',
        '    const h = (location.hash || "").slice(1) || "inicio";\n'
        '    if (h === "mercados") { location.href = "/terminal/"; return; }\n'
        "    if (!VISTAS.includes(h)) return;",
    )
    html = reemplazar(
        html,
        'if (!location.hash || (location.hash === "#mesa" && !visto)) history.replaceState(null, "", "#inicio");',
        'if (!location.hash) history.replaceState(null, "", location.pathname.startsWith("/mesa") ? "#mesa" : "#inicio");\n'
        '  else if (location.hash === "#mesa" && !visto && !location.pathname.startsWith("/mesa")) '
        'history.replaceState(null, "", "#inicio");',
    )
    html = reemplazar(
        html,
        '  function abrirEnTerminal(id) {\n    location.hash = "#mercados";',
        "  function abrirEnTerminal(id) {\n"
        '    location.href = "/terminal/activo/" + encodeURIComponent(corto(id)); return;\n'
        '    location.hash = "#mercados";',
    )

    # 4. pie institucional, como el resto de las pantallas
    html = reemplazar(
        html,
        '<link rel="stylesheet" href="/web/estilo/tokens.css">',
        '<link rel="stylesheet" href="/web/estilo/tokens.css">\n'
        '<link rel="stylesheet" href="/web/estilo/pie.css">',
    )
    html = reemplazar(html, "\n</main>\n", '\n</main>\n<footer data-cueva-pie="barra"></footer>\n')
    html = html.rstrip()
    if not html.endswith("</html>"):
        raise SystemExit("El mockup no termina en </html>.")
    html = html[: -len("</html>")].rstrip()
    html += (
        '\n<script src="/web/cueva/metodos_servidor.js"></script>\n<script src="/web/cueva/terminal_a_pedido.js"></script>\n<script src="/web/estilo/sitio.js"></script>\n<script src="/web/estilo/pie.js"></script>\n'
        "</body>\n</html>\n"
        if not html.endswith("</body>")
        else ""
    )
    if html.endswith("</body>"):
        html = (
            html[: -len("</body>")]
            + '<script src="/web/cueva/metodos_servidor.js"></script>\n<script src="/web/cueva/terminal_a_pedido.js"></script>\n<script src="/web/estilo/sitio.js"></script>\n'
            '<script src="/web/estilo/pie.js"></script>\n</body>\n</html>\n'
        )

    # 5. robustez: el ejemplo inicial usa series de la Terminal (KO, PEP, SPY, VIX…); si en esta
    #    compu no están (Terminal sin datos), la Mesa arranca igual sin esas piezas.
    html = reemplazar(
        html,
        "function nuevoPanel(modo, fichas = [], extra = {}) {\n",
        "function nuevoPanel(modo, fichas = [], extra = {}) {\n  fichas = (fichas || []).filter(Boolean);\n",
    )
    html = reemplazar(html, "(function inicio() {\n", "(function inicio() { try {\n")
    html = reemplazar(
        html,
        "  st.deshacer = []; st.rehacer = [];\n  render();\n  ruta();\n})();\n",
        "  st.deshacer = []; st.rehacer = [];\n  render();\n  ruta();\n"
        '} catch (e) {\n  console.warn("Mesa: el ejemplo inicial quedó incompleto (faltan series de la Terminal '
        'en esta compu):", e);\n  try { renderHerr(); st.deshacer = []; st.rehacer = []; render(); ruta(); } catch (_) {}\n'
        "} })();\n",
    )

    # 6. filas «terminal» del catálogo: se traen a pedido (web/cueva/terminal_a_pedido.js)
    html = reemplazar(
        html,
        '${est === "datos" ? `draggable="true" data-arr-cat="${k}" data-cs-mesa="${k}" role="button" tabindex="0"` : ""}',
        '${est === "datos" ? `draggable="true" data-arr-cat="${k}" data-cs-mesa="${k}" role="button" tabindex="0"` '
        ': est === "terminal" ? `data-cs-term="${k}" role="button" tabindex="0"` : ""}',
    )
    html = reemplazar(
        html,
        '"Está en la Terminal; falta traerla a la Mesa"',
        '"Está en la Terminal: tocala para traerla a la Mesa"',
    )

    # 7. lo que era solo del mockup
    html = reemplazar(html, '    <span class="chip warn">Mockup</span>\n', "")
    html, n = re.subn(r'    <button class="btn sm" id="b-html"[^\n]*</button>\n', "", html, count=1)
    if n != 1:
        raise SystemExit("No encontré el botón ⬇ HTML.")
    return html


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--desde", type=Path, required=True, help="la-cueva.html bajado del artifact")
    ap.add_argument("--salida", type=Path, default=SALIDA)
    args = ap.parse_args()
    html = convertir(args.desde.read_text(encoding="utf-8"))
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(html, encoding="utf-8")
    print(f"{args.salida}: {len(html) / 1024:.0f} KB (sin datos embebidos)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
