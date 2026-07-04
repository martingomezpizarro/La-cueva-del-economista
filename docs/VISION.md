# Visión — La Cueva del Economista

## El problema
Hacer investigación econométrica de series de tiempo en Argentina es lento y solitario:
los datos están dispersos (INDEC, BCRA, FRED, etc.), las herramientas son fragmentadas, y
el rigor teórico depende de tener un profesor al lado que te diga "ahí estás interpretando
mal la causalidad de Granger" o "antes de ese VAR verificá cointegración".

## La solución
Una plataforma que combina tres patas:

1. **Datos unificados** — todas las series económicas argentinas, accesibles y graficables.
2. **Motor de análisis** — todo el análisis econométrico de series de tiempo (estacionariedad,
   ARIMA, VAR, VECM, ARDL, GARCH, cointegración, pronóstico, ML) desde la web.
3. **Agentes-profesores (IA)** — el diferencial. Asistentes incansables que reciben lo que el
   usuario hace y quiere hacer, consultan la base de conocimiento bibliográfica, y:
   - controlan que esté procediendo bien,
   - sugieren direcciones de investigación,
   - ayudan a interpretar y validar resultados,
   todo **fundamentado en bibliografía real, con citas** (no inventan).

## Caso de uso estrella
**Facilitar enormemente la realización de trabajos finales** (tesis de grado como la de
riesgo país argentino). El usuario carga su pregunta y su bibliografía; la plataforma lo
acompaña de punta a punta con rigor teórico.

## El motor de conocimiento: "La Cueva-LM"
El usuario quería usar NotebookLM por lo bien que responde fundamentado en los PDFs que se le
cargan. NotebookLM no tiene API (no se puede integrar a una plataforma), así que construimos
**nuestro propio equivalente** ("La Cueva-LM"): mismo comportamiento (cargás PDFs → respuestas
fundamentadas con citas) pero **integrable**, de modo que los agentes puedan consultarlo
automáticamente. Técnicamente es un sistema **RAG** (Retrieval-Augmented Generation) con Claude.

Además, el usuario puede subir **su propia bibliografía** y la misma maquinaria la incorpora al
contexto de su investigación.

## Decisiones tomadas
- Repo nuevo, reusando el código de datos/econometría del proyecto de riesgo país.
- IA = RAG propio + Claude (no NotebookLM como backend).
- Empezamos por el motor de conocimiento (esta pata da identidad a la plataforma).
