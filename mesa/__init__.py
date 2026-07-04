"""
La Mesa de Trabajo — la red de agentes-profesores de La Cueva del Economista.

Submódulos:
    modelos       dataclasses de la sesión (Proyecto, Mensaje, Hallazgo)
    pizarra       el "blackboard" compartido que ven todos los agentes
    llm           wrapper de Claude con modo offline
    rag_cliente   consulta a La Cueva-LM (RAG sobre el corpus + bibliografía del usuario)
    agentes       los agentes y su clase base
    orquestador   conduce la conversación entre agentes
"""
