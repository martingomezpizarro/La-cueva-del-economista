# Conectar datos — estado y paso a paso (2026-10-14)

## 0. El bloqueo de fondo: la plataforma todavía no lee `data/series/`

`cueva/datos/series.py` (`_carpeta_vars`) y `cueva/datos/explorador_datos.py` (`_carpeta_raw`)
resuelven los archivos **solo** contra la carpeta del Trabajo Final. Todo lo que se baja a
`data/series/` (BCRA, datos.gob.ar, Actividad) está en disco pero la plataforma no lo ve.

Arreglo propuesto (una función, dos llamadores):

1. `cueva/datos/rutas.py` con `ubicar(archivo) -> Path | None`: busca primero en
   `data/series/**` (índice por nombre de archivo, cacheado por mtime de la carpeta) y,
   solo si no está, en el Trabajo Final — con `logging.warning` cuando cae ahí.
2. `series.py` y `explorador_datos.py` usan `ubicar()` en vez de `carpeta / f["file"]`.
3. `_firma()` incluye el mtime de `data/series/` para invalidar el caché.
4. Test: un catálogo de prueba con un archivo en `data/series/x/` y otro solo en el TF.

## 1. Conectar `bajar_datos_gob.py` al MCP `datos_ar`

El script está en `scripts/bajar_datos_gob.py` y su configuración en
`cueva/fuentes/datos_gob.json` (6 archivos, 139 entradas del catálogo). Baja los CSV de
distribución de datos.gob.ar a `data/series/datos_gob/`, con encabezados idénticos a los
`dateCol`/`valCol` del catálogo, y deja `_index.csv` con URL, rango y columnas faltantes.

1. **Probarlo a mano** (terminal de Windows, en la carpeta del proyecto):
   ```
   .venv\Scripts\python scripts\bajar_datos_gob.py --listar
   .venv\Scripts\python scripts\bajar_datos_gob.py --simular
   .venv\Scripts\python scripts\bajar_datos_gob.py
   ```
2. **Ubicar el servidor del MCP**: en `%APPDATA%\Claude\claude_desktop_config.json`, la
   entrada `datos_ar` dice qué `.py` se ejecuta (`command` + `args`).
3. **Sumar el script a la lista blanca**: en ese `.py`, el diccionario que hoy tiene
   `actualizar_bcra.py`, `cobertura_bcra.py`, `bajar_crisis_rr.py` y `bajar_abiertos.py`
   (lo que devuelve la herramienta `cueva_scripts`). Agregar:
   ```python
   "bajar_datos_gob.py": "CSV del portal datos.gob.ar (INDEC/SSPM) que pide el catálogo",
   ```
4. **De paso, en el mismo servidor**: pasarle `PYTHONIOENCODING=utf-8` al subproceso
   (`env={**os.environ, "PYTHONIOENCODING": "utf-8"}`), así ningún script vuelve a caerse
   por la consola cp1252 de Windows.
5. **Reiniciar Claude Desktop** (Salir desde la bandeja, no solo cerrar la ventana).
6. **Verificar**: pedir `cueva_scripts` y que aparezca; después
   `cueva_correr("bajar_datos_gob.py", ["--listar"])`.
7. **Bajar**: `cueva_correr("bajar_datos_gob.py")`. Revisar en `_index.csv` la columna
   `faltan`: si el organismo renombró un encabezado, el script lo avisa y no inventa.

## 2. Lo que falta para los datasets, en orden de rendimiento

| # | Qué | Entradas | Cómo |
|---|---|---|---|
| 0 | Que la plataforma lea `data/series/` | todas | §0 |
| 1 | datos.gob.ar: saldo comercial, balance de pagos, IPC | 139 | §1 |
| 2 | Los que el TF armaba con scripts propios: `ti_mensual`, `deuda_externa_sectores`, `deuda_externa_plazo` | 17 | el MCP los encuentra (161.1, 82.2_ITI); sumar un modo «API de Series» al script |
| 3 | Finanzas: vencimientos 1 y 2 años, saldo de deuda, calendario | 191 | xlsx de Finanzas; portar `build_vencimientos_*.py` del TF a `scripts/` |
| 4 | Mecon: resultado fiscal | 24 | xlsx; portar el lector |
| 5 | BCRA fuera de la API: ITCRM y depósitos/préstamos USD | 19 | planillas (Series.xlsm ids 107, 108, 118-125); ITCRM largo: Bruegel desde 1960 |
| 6 | EMBI (BCRP), Yahoo (VIX, DXY, UST), OFR, Heritage, Banco Mundial, UTDT | ~55 | Yahoo puede salir del MCP `mercados`; el resto, un script por fuente |
| 7 | Estimaciones Kalman propias (PBI, OyD, BP, deuda, fiscal) | ~70 | regenerarlas con `cueva/econometria/kalman.py` desde los insumos, no copiarlas del TF |
| 8 | Dummies | 13 | generarlas desde `data/historia/presidencias.csv` y `eventos.csv` |
| 9 | Ratios nuevos: dolarización de depósitos y descalce | 2 | Transformaciones, cuando esté el punto 5 |

Auditoría serie por serie: `Claude outputs/series_faltantes_2026-10-14.csv`.
