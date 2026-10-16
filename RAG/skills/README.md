# Skills de los especialistas

Cada archivo es el **"skill" de un agente**: su identidad, cómo razona, qué herramientas empuña,
a qué sector de la biblioteca se ancla y qué debe advertir. Es la instrucción de sistema que lo
hace preciso.

**Estos archivos son la FUENTE DE VERDAD de cada agente** (cargador: `cueva/agentes/skills.py`).
Editar el markdown cambia la identidad, el tier de modelo, el sesgo de búsqueda RAG y la lista
blanca de herramientas SIN tocar Python.

## Formato (frontmatter)
- `agente`: id corto (el que usan pipelines y handoffs).
- `rol`: etiqueta legible con emoji.
- `modelo`: tier sugerido — `Claude` (criterio fino), `medio`, `barato` (rutinario). Cuida créditos.
- `ancla_biblioteca`: la carpeta `corpus/NN_…` y la ficha que fundamentan a este especialista.
- `sesgo_rag`: términos que enriquecen su búsqueda bibliográfica.
- `herramientas`: lista blanca para function calling. **Cada nombre DEBE existir en el REGISTRO
  de `cueva/econometria/herramientas.py`** (lo vigila un test: un skill que promete herramientas
  inexistentes hace que el agente alucine evidencia). Lo que el agente sabe hacer pero la
  plataforma no ejecuta va en el cuerpo como "asesorás sin ejecutar", nunca en esta lista.
- `prioriza_usuario`: `si` para anteponer la biblioteca subida por el usuario (Bibliógrafo).

## Reglas comunes a todos los agentes
1. Fundamentar lo que se afirma en los pasajes recuperados de La Cueva-LM; citar fuente.
   Si la bibliografía no alcanza, decirlo — **no inventar**.
2. Hablar en español, claro y al punto.
3. Distinguir lo que la bibliografía afirma de las inferencias propias.
4. La computación es de las **herramientas** (sale $0); el agente aporta el **criterio**.
   Evidencia que ninguna herramienta produjo NO se reporta como resultado.
5. Si necesita a otro especialista, hace handoff (línea `HANDOFF: <id> :: <pregunta>`).

## Roster
`lider` · `curador_datos` · `transformaciones` · `controles_causal` · `multivariados` ·
`volatilidad` · `pronostico_ml` · `robustez` · `critico` · `interprete` · `metodologo` ·
`bibliografo`
