@echo off
REM ════════════════════════════════════════════════════════════════════
REM   La Cueva del Economista — arranca TODO con un doble-click:
REM   1) levanta el servidor (langgraph dev) en su propia ventana
REM   2) abre Studio en el navegador, en la URL fija
REM
REM   Dejá abierta la ventana negra del servidor mientras uses Studio.
REM   Si el navegador dice "Failed to fetch", desactiva la extension
REM   bloqueadora para smith.langchain.com  (plan B: agrega  --tunnel
REM   al final de la linea del 'start' del servidor).
REM ════════════════════════════════════════════════════════════════════

cd /d "%~dp0"

if not exist ".venv\Scripts\langgraph.exe" (
  echo No encuentro .venv\Scripts\langgraph.exe
  echo Activa el entorno e instala:  pip install "langgraph-cli[inmem]"
  pause
  exit /b 1
)

echo Encendiendo el servidor de La Cueva...
start "La Cueva - Servidor" ".venv\Scripts\langgraph.exe" dev --port 2024 --no-browser

echo Esperando a que arranque (unos segundos)...
timeout /t 10 /nobreak >nul

echo Abriendo Studio en el navegador...
start "" "https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024"

echo.
echo Listo. Si Studio dice "Failed to fetch", refresca la pagina o revisa la
echo extension bloqueadora. NO cierres la ventana negra del servidor.
timeout /t 6 /nobreak >nul
