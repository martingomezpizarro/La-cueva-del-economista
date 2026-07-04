# 🛠️ Setup en una computadora nueva

> Instrucciones para una IA asistente (o para una persona) que tiene que dejar este
> proyecto funcionando desde cero tras clonar el repo. Seguilas en orden.

El repo **no** incluye el entorno virtual (`.venv/`), el índice generado (`rag/_indice/`)
ni los PDFs/EPUBs del corpus: todo eso es pesado y se reconstruye localmente. Acá está cómo.

---

## 0. Requisitos previos

- **Python 3.12** (el proyecto se desarrolló con 3.12.3). Verificá: `python3 --version`.
- **git** y acceso al repo privado `tomasgomezpizarro/cueva-del-economista`
  (el usuario `martingomezpizarro` es colaborador).
- Sistema operativo Linux/macOS (los comandos asumen `bash`). En Windows usar WSL o adaptar
  la activación del venv a `.venv\Scripts\activate`.

---

## 1. Clonar el repo (si no está ya)

```bash
git clone https://github.com/tomasgomezpizarro/cueva-del-economista
cd cueva-del-economista
```

---

## 2. Crear el entorno virtual e instalar dependencias

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r rag/requirements.txt
```

Esto instala las dependencias del prototipo del motor de conocimiento:

| Paquete        | Para qué |
|----------------|----------|
| `pymupdf`      | extraer texto de PDFs |
| `scikit-learn` | recuperación TF-IDF |
| `numpy`        | cálculo numérico |
| `anthropic`    | redacción fundamentada con Claude (opcional, ver paso 4) |

> Si más adelante el proyecto suma dependencias (statsmodels, etc.), van en
> `rag/requirements.txt`. Reinstalá con el mismo comando de arriba.

---

## 3. Recolocar el corpus y reconstruir el índice

El contenido de `knowledge-base/corpus/` (PDFs, papers, EPUBs) **no viaja en el repo**.
Las carpetas de tema sí existen (`01_fundamentos`, `02_univariados`, … `10_codigo_python`),
pero hay que volver a poner los archivos pesados dentro.

1. Copiá los PDFs/`.py`/`.ipynb`/`.md` a la carpeta de tema que corresponda dentro de
   `knowledge-base/corpus/` (ver `knowledge-base/GUIA_CARGA.md` para la guía completa).
2. Reconstruí el índice (ingiere TODO el corpus):

```bash
. .venv/bin/activate
python rag/ingest.py knowledge-base/corpus
```

Esto regenera `rag/_indice/` (embeddings, fragmentos, TF-IDF, metadatos).

---

## 4. (Opcional) Clave de LLM para respuestas redactadas

Sin clave, el sistema **igual recupera** los pasajes citados. Con clave, el LLM redacta una
respuesta fundamentada a partir de esos pasajes. Dos opciones (el Metodólogo usa la primera
que encuentre):

```bash
# Opción GRATIS (recomendada): Gemini. Key en https://aistudio.google.com/apikey
export GEMINI_API_KEY="tu_clave_aca"        # Windows: set GEMINI_API_KEY=...

# Opción paga: Claude
export ANTHROPIC_API_KEY="tu_clave_aca"
```

> No comitear la clave. El `.gitignore` ya ignora `.env` y `*.key`; si preferís un archivo,
> usá `.env` (no se versiona).

---

## 5. Verificar que funciona

```bash
. .venv/bin/activate
python rag/ask.py "¿Para qué sirve el test de Dickey-Fuller aumentado?"
python rag/ask.py "¿Cómo estimo un VECM en Python con statsmodels?"
```

Si devuelve pasajes citados (y, con `ANTHROPIC_API_KEY`, una respuesta redactada), está OK.

---

## Resumen ultra-corto

```bash
git clone https://github.com/tomasgomezpizarro/cueva-del-economista
cd cueva-del-economista
python3 -m venv .venv && . .venv/bin/activate
pip install --upgrade pip && pip install -r rag/requirements.txt
# (poner los PDFs en knowledge-base/corpus/…)
python rag/ingest.py knowledge-base/corpus
python rag/ask.py "tu pregunta en español"
```
