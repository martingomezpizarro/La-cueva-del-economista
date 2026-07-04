# Skills de los especialistas

Cada archivo es el **"skill" de un agente**: su identidad, cómo razona, qué herramientas empuña,
a qué sector de la biblioteca se ancla y qué debe advertir. Es la instrucción de sistema que lo
hace preciso.

> **Ubicación provisional.** Los dejo acá para tenerlos ordenados junto a la bibliografía. Cuando
> armemos los agentes en LangGraph, estos skills se cablean como el `system prompt` de cada nodo
> (se pueden mover donde prefieras — vos tenés la última palabra sobre la estructura).

## Formato (frontmatter)
- `agente`: id corto (para el grafo).
- `modelo`: tier sugerido — `Claude` (criterio fino), `medio`, `barato` (rutinario). Cuida créditos.
- `ancla_biblioteca`: la carpeta `corpus/NN_…` y la ficha que fundamentan a este especialista.
- `herramientas`: las funciones determinísticas que puede ejecutar (no gastan tokens).

## Reglas comunes a todos los agentes
1. Fundamentar lo que se afirma en los pasajes recuperados de La Cueva-LM; citar fuente.
   Si la bibliografía no alcanza, decirlo — **no inventar**.
2. Hablar en español, claro y al punto.
3. Distinguir lo que la bibliografía afirma de las inferencias propias.
4. La computación es de las **herramientas** (sale $0); el agente aporta el **criterio**.
5. Si necesita a otro especialista, hace handoff al Líder o directo al colega.

## Roster
`lider` · `curador_datos` · `transformaciones` · `controles_causal` · `multivariados` ·
`volatilidad` · `pronostico_ml` · `robustez` · `critico` · `interprete`
