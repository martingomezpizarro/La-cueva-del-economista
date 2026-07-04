"""
grafo.py — PRUEBA MÍNIMA para encender LangGraph Studio.

⚠️ Esto NO es la arquitectura del proyecto. Es un "hola mundo" de un solo nodo para que
   Studio tenga algo que dibujar y puedas ver el flujo correr en vivo. No llama a ningún
   modelo de IA, así que no gasta tokens. Lo reemplazamos cuando diseñemos la estructura real.

Un grafo de LangGraph tiene tres ingredientes:
  - un ESTADO: la "ficha" de datos que viaja por el flujo (acá: pregunta y respuesta),
  - NODOS: funciones que reciben el estado y devuelven cambios (acá: 'encuadrar'),
  - ARISTAS: las flechas que dicen en qué orden corren los nodos (START → encuadrar → END).
"""
from typing import TypedDict

from langgraph.graph import StateGraph, START, END


# ── 1. El estado: qué datos viajan por el flujo ──────────────────────────
class Estado(TypedDict):
    pregunta: str
    respuesta: str


# ── 2. Un nodo: por ahora solo "acusa recibo" (sin IA, sin costo) ─────────
def encuadrar(estado: Estado) -> dict:
    return {"respuesta": f"Recibí tu pregunta: «{estado['pregunta']}». "
                         f"(nodo de prueba, sin llamar a ningún modelo)"}

# 👉 Acá, más adelante, en vez de este nodo de juguete van a vivir los agentes reales
#    (Metodólogo, Crítico, etc.), cada uno como un nodo que puede consultar la bibliografía
#    y, si hace falta, llamar a un modelo. Eso lo armamos juntos en el diseño.


# ── 3. Armar el grafo y conectarlo ───────────────────────────────────────
_g = StateGraph(Estado)
_g.add_node("encuadrar", encuadrar)
_g.add_edge(START, "encuadrar")
_g.add_edge("encuadrar", END)

grafo = _g.compile()   # <- 'langgraph.json' apunta a este objeto


# ── correr a mano (sin Studio), para probar: python _studio_demo/grafo.py ─
if __name__ == "__main__":
    print(grafo.invoke({"pregunta": "¿Funciona LangGraph?"}))
