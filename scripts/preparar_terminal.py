"""preparar_terminal.py — deja lista la pestaña Terminal antes de levantar La Cueva.

Lo corre «La Cueva del Economista.bat». Hace lo mismo que Terminal.bat, pero para la
Terminal montada dentro de La Cueva:

1. Trae la última versión del repo de la Terminal (git pull --ff-only).
2. Instala sus paquetes de Python en el entorno de La Cueva si faltan.
3. Reconstruye su interfaz si cambió algo en web/src (necesita Node.js).
4. Si ya hay base de datos, trae en segundo plano los cierres que falten.

Si la Terminal no está en esta compu, avisa y termina sin error: La Cueva abre igual.
Nunca falla por la Terminal: cada paso avisa y sigue.
"""

from __future__ import annotations

import importlib
import shutil
import subprocess
import sys

from cueva import config

PAQUETES = ("duckdb", "yfinance", "dotenv", "pandas", "yaml", "fastapi")


def paso(texto: str) -> None:
    print(f"  · {texto}")


def git_pull(carpeta) -> None:
    if not shutil.which("git"):
        paso("git no está instalado: sigo con la versión de la Terminal que hay.")
        return
    r = subprocess.run(["git", "-C", str(carpeta.parent), "pull", "--ff-only", "--quiet"], check=False)
    if r.returncode != 0:
        paso("No pude traer la última versión de la Terminal (sin internet o con cambios locales). Sigo.")


def paquetes(carpeta) -> None:
    faltan = []
    for nombre in PAQUETES:
        try:
            importlib.import_module(nombre)
        except ImportError:
            faltan.append(nombre)
    if not faltan:
        return
    paso(f"Instalando paquetes de la Terminal ({', '.join(faltan)})…")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-q", "-r", str(carpeta / "requirements.txt")], check=False
    )


def interfaz(carpeta) -> None:
    web = carpeta / "web"
    indice = web / "dist" / "index.html"
    if indice.exists():
        ultima = indice.stat().st_mtime
        fuentes = [web / "package.json", *(p for p in (web / "src").rglob("*") if p.is_file())]
        if not any(p.stat().st_mtime > ultima for p in fuentes):
            return
    npm = shutil.which("npm")
    if not npm:
        paso("Falta Node.js para construir la interfaz de la Terminal (https://nodejs.org).")
        return
    paso("Construyendo la interfaz de la Terminal…")
    subprocess.run([npm, "install", "--no-audit", "--no-fund"], cwd=web, check=False)
    subprocess.run([npm, "run", "build"], cwd=web, check=False)


def precios(carpeta) -> None:
    if str(carpeta) not in sys.path:
        sys.path.insert(0, str(carpeta))
    try:
        from terminal import puente

        if puente.traer_precios() is None:
            paso(
                "La Terminal todavía no tiene datos: la primera carga es con «Terminal - actualizar datos.bat»."
            )
        else:
            paso("Trayendo los precios que falten en segundo plano (el avance se ve arriba en la Terminal).")
    except Exception as e:  # la Terminal nunca impide abrir La Cueva
        paso(f"No pude lanzar la actualización de precios: {e}")


def main() -> int:
    carpeta = config.carpeta_terminal()
    if carpeta is None:
        print("Terminal: no está en esta compu (la pestaña va a avisarlo). La Cueva abre igual.")
        return 0
    print(f"Terminal: {carpeta}")
    for etapa in (git_pull, paquetes, interfaz, precios):
        try:
            etapa(carpeta)
        except Exception as e:
            paso(f"{etapa.__name__}: {e} (sigo)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
