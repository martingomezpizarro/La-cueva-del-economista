# 🛠️ Setup en una computadora nueva

> Instrucciones para una IA asistente (o para una persona) que tiene que dejar este
> proyecto funcionando desde cero tras clonar el repo. Seguilas en orden.

El repo **no** incluye el entorno virtual (`.venv/`), el índice generado (`indice/`)
ni los PDFs/EPUBs del corpus: todo eso es pesado y se reconstruye localmente.

---

## 0. Requisitos previos

- **Python 3.12+** (el proyecto corre con 3.12/3.13). Verificá: `python --version`.
- **git** y acceso al repo privado `tomasgomezpizarro/cueva-del-economista`.
- Funciona en Windows, Linux y macOS (los comandos de venv difieren, se indican ambos).

---

## 1. Clonar e instalar

```bash
git clone https://github.com/tomasgomezpizarro/cueva-del-economista
cd cueva-del-economista

python -m venv .venv
. .venv/bin/activate            # Windows: .venv\Scripts\activate

pip install --upgrade pip
pip install -e ".[dev]"         # el paquete cueva + herramientas de desarrollo
```

Extras opcionales (ver `pyproject.toml`):

| Extra | Cuándo |
|---|---|
| `.[embeddings]` | para RE-INGESTAR el corpus con recuperación semántica multilingüe (baja torch ~2GB) |
| `.[claude]` | solo si se va a usar Anthropic como backend (de pago; el default es Gemini gratis) |
| `.[grafo]` | solo para el pipeline LangGraph legado (`grafo_cueva.py`, se retira en fase 2) |

---

## 2. Verificar que el código funciona (sin datos ni claves)

```bash
pytest          # 48 tests offline: deben pasar todos
ruff check .    # lint: sin errores
```

---

## 3. Recolocar el corpus y reconstruir el índice

El contenido de `knowledge-base/corpus/` (PDFs, papers, EPUBs) **no viaja en el repo**.
Las carpetas de tema sí existen (`01_fundamentos`, … `12_frontera_dl`); hay que volver a
poner los archivos pesados dentro (ver `knowledge-base/GUIA_CARGA.md`).

```bash
pip install -e ".[embeddings]"                      # una sola vez (torh ~2GB)
python scripts/ingestar.py knowledge-base/corpus    # regenera indice/
```

> Sin `[embeddings]` también funciona (`--no-embeddings` o dejar que caiga solo a TF-IDF),
> pero la recuperación español→inglés es peor.

---

## 4. (Opcional) Clave de LLM para respuestas redactadas

Sin clave, el sistema **igual corre de punta a punta** (modo offline: los agentes muestran
maquetas). Con clave, redactan respuestas fundamentadas reales.

```bash
# Opción GRATIS (default del proyecto): Gemini. Key en https://aistudio.google.com/apikey
# Guardala en un archivo .env en la raíz (NO se versiona):
echo 'GEMINI_API_KEY=tu_clave_aca' > .env

# Opción paga (requiere pip install -e ".[claude]"):
# ANTHROPIC_API_KEY=tu_clave_aca
```

---

## 5. Datos (series económicas)

`cueva/config.py` autodetecta las carpetas hermanas `Trabajo Final` y `ANÁLISIS MATRIZ ARG`.
Si están en otra ruta, indicalo por variable de entorno o `cueva.local.toml`:

```bash
python scripts/mesa_cli.py --diag     # muestra qué encontró (series, índice, backend LLM)
```

---

## 6. Levantar la plataforma

```bash
uvicorn cueva.api.app:app --port 8800     # abrir http://localhost:8800
```

O probar por terminal:

```bash
python scripts/preguntar.py "¿Para qué sirve el test de Dickey-Fuller aumentado?"
python scripts/metodologo.py "Quiero explicar el EMBI con reservas y TCR" -i
python scripts/mesa_cli.py --pregunta "..." --ids serie_a serie_b --dep serie_a
```

---

## 7. Hooks de commit (recomendado)

```bash
pre-commit install    # formato + lint + detector de secretos antes de cada commit
```

---

## Resumen ultra-corto

```bash
git clone https://github.com/tomasgomezpizarro/cueva-del-economista && cd cueva-del-economista
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]" && pytest
# (poner los PDFs en knowledge-base/corpus/… y correr scripts/ingestar.py)
# (clave GRATIS de Gemini en .env como GEMINI_API_KEY=…)
uvicorn cueva.api.app:app --port 8800
```
