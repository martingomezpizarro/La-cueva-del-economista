"""metodos — El catálogo de métodos de análisis de La Cueva (econometría, ML, redes).

Capas:
    contrato    → cómo se declara un método y cómo arma su resultado (bloques tipados)
    registro    → catálogo vivo + validación de argumentos + ejecución segura
    insumos     → series del catálogo, transformaciones, matriz de diseño para ML, eventos
    validacion  → evaluación fuera de muestra honesta (origen móvil, Diebold-Mariano)
    redes_np    → redes neuronales chicas en numpy puro (sin torch)
    familias/   → los métodos, uno por función, agrupados por familia

Uso:
    from cueva.metodos import catalogo, ejecutar
    ejecutar("raiz_unitaria", {"sid": "emae_original", "transf": "log"})

Qué NO hace: no persiste (eso es `cueva/sesiones`), no sale a la red (eso es `cueva/fuentes`).
"""

# OJO: no reexportar la función `registro` acá: taparía al submódulo `cueva.metodos.registro`
# (`from cueva.metodos import registro` devolvería la función y no el módulo).
from cueva.metodos.registro import catalogo, declaraciones, ejecutar, obtener

__all__ = ["catalogo", "declaraciones", "ejecutar", "obtener"]
