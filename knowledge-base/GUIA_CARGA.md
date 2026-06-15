# Guía para cargar conocimiento en La Cueva-LM

Esta guía es para vos (no hace falta programar). El objetivo: alimentar el "cerebro" de la
plataforma con buena bibliografía, buen código y buenas fichas, para que los agentes-profesores
respondan con rigor.

---

## 🧱 Lo básico: cómo se carga algo (3 pasos)

1. **Poné el archivo** en la carpeta del tema que corresponda, dentro de `knowledge-base/corpus/`.
   Sirven: PDFs (`.pdf`), código Python (`.py`), notebooks (`.ipynb`), texto/markdown (`.md`, `.txt`).
2. **Reindexá** con un solo comando (ingiere TODO lo que haya en el corpus):
   ```bash
   . .venv/bin/activate
   python rag/ingest.py knowledge-base/corpus
   ```
3. **Probá** una pregunta:
   ```bash
   python rag/ask.py "tu pregunta en español"
   ```

Las carpetas de tema están en `corpus/` (`01_fundamentos`, `02_univariados`, … `10_codigo_python`).
Poné cada cosa donde mejor encaje; no es crítico que sea perfecto.

---

## 📚 Qué bibliografía cargar (prioridad)

**Núcleo de series de tiempo (lo más importante):**
- ✅ Enders — *Applied Econometric Time Series* (ya cargado)
- Hamilton — *Time Series Analysis* (la "biblia", más técnico)
- Lütkepohl — *New Introduction to Multiple Time Series Analysis* (VAR/VECM a fondo)
- Box, Jenkins & Reinsel — *Time Series Analysis: Forecasting and Control* (ARIMA)

**Cointegración y modelos:**
- Pesaran, Shin & Smith (2001) — bounds test ARDL (paper clave)
- Johansen — cointegración (paper/capítulos)

**Argentina / riesgo país (tu diferencial):**
- Papers de determinantes del riesgo país emergente (push/pull factors)
- Metodologías INDEC/BCRA (balanza de pagos, deuda) — ya tenés algunas

**ML/DL para series (si vas a esa pata):**
- Papers de LSTM/GRU/Transformers para forecasting financiero

> 💡 Podés seguir usando **NotebookLM de Google** para estudiar y depurar estos PDFs antes de
> cargarlos acá. Es tu herramienta personal de curaduría; La Cueva-LM es el motor de la plataforma.

---

## 🐍 Qué CÓDIGO cargar (para que la IA programe bien)

Esto es clave: que el agente **escriba código econométrico correcto, con las librerías apropiadas
y los tests adecuados**. Cargá ejemplos de código que ya funcionan:

- ✅ Tu `src/models.py` y `src/utils.py` de la tesis (ya cargados) — wrappers de OLS/VAR/VECM/ARDL/GARCH.
- Notebooks tuyos que corren bien (`.ipynb`).
- **Documentación de librerías** convertida a texto: statsmodels (VAR, VECM, ARDL), `arch` (GARCH),
  `pmdarima`. Tip: guardá las páginas clave de la doc como `.md` en `corpus/10_codigo_python/`.
- Ejemplos oficiales de statsmodels (cointegración, IRF, tests de raíz unitaria).

Así, cuando alguien pida "estimá un VECM", el agente se apoya en código real y bien hecho — no improvisa.

---

## 📝 Cómo escribir una FICHA (el ingrediente secreto)

Las fichas son resúmenes de 1 página por método con **supuestos, errores típicos y cuándo usar**.
Son lo que permite al agente advertir errores teóricos (ej. "Granger ≠ causalidad").

1. Copiá `fichas/_plantilla_ficha.md` con un nombre nuevo (ej. `fichas/vecm.md`).
2. Completá los campos. Lo más valioso: la sección **⚠️ Errores típicos**.
3. Reindexá. ¡Las fichas también se cargan al motor!

Mirá `fichas/granger_causalidad.md` como ejemplo terminado.

> Estas fichas las escribís vos mientras estudiás (incluso preguntándole a NotebookLM "¿cuáles son
> los errores típicos al usar X?"). Cada ficha que sumás hace al profesor-agente más sabio.

---

## ✅ Checklist para empezar esta semana
- [ ] Sumar 1-2 libros núcleo (Hamilton y/o Lütkepohl) a `corpus/01_fundamentos` o `04_multivariados`.
- [ ] Guardar 2-3 páginas clave de la doc de statsmodels como `.md` en `corpus/10_codigo_python`.
- [ ] Escribir 2 fichas nuevas (ej. `vecm.md`, `ardl.md`) con sus errores típicos.
- [ ] Reindexar y probar 3 preguntas en español (teoría y código).
