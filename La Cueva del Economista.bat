@echo off
rem La Cueva del Economista: abre toda la plataforma en el navegador.
rem   Inicio, Linea de tiempo, Mesa de trabajo y la Terminal (si esta en esta compu).
rem La Terminal tambien se puede seguir abriendo sola con Terminal.bat, pero no las dos a la vez:
rem comparten la misma base de datos.
chcp 65001 >nul
cd /d "%~dp0"

echo === La Cueva del Economista ===
where git >nul 2>nul && (
    git pull --ff-only --quiet || echo No pude traer la ultima version de GitHub ^(sin internet o con cambios locales^). Sigo.
)

if not exist ".venv\Scripts\python.exe" (
    echo Creando el entorno de Python ^(solo la primera vez^)...
    python -m venv .venv || goto :error
    .venv\Scripts\python -m pip install -q -e ".[dev]" || goto :error
)

.venv\Scripts\python scripts\preparar_terminal.py

powershell -NoProfile -Command "if (Get-NetTCPConnection -LocalPort 8800 -State Listen -ErrorAction SilentlyContinue) { exit 1 }"
if errorlevel 1 (
    echo El puerto 8800 ya esta ocupado: La Cueva ya esta abierta. Abro el navegador.
    start "" http://localhost:8800/
    exit /b 0
)

echo Abriendo http://localhost:8800/  ^(Ctrl+C para cerrar^)
start "" cmd /c "timeout /t 4 >nul & start http://localhost:8800/"
.venv\Scripts\python -m uvicorn cueva.api.app:app --host 127.0.0.1 --port 8800 --log-level warning
exit /b 0

:error
echo No se pudo preparar el entorno de Python. Revisa que Python 3.12 este instalado.
pause
exit /b 1
