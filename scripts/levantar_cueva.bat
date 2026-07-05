@echo off
REM Levanta la Mesa de Trabajo de La Cueva del Economista en http://localhost:8800
REM Uso: doble clic, o "scripts\levantar_cueva.bat" desde la raiz del repo.

cd /d "%~dp0\.."

if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] No encuentro .venv\Scripts\activate.bat
    echo Cree el entorno primero: python -m venv .venv ^&^& pip install -e ".[dev]"
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat

echo.
echo === Diagnostico (series, indice, backend LLM) ===
python scripts\mesa_cli.py --diag

echo.
echo === Levantando servidor en http://localhost:8800 ===
uvicorn cueva.api.app:app --port 8800

pause
