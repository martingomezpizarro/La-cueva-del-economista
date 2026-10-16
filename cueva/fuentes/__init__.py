"""fuentes — adaptadores de los organismos que publican las series.

QUÉ HACE: habla con las APIs y portales de datos (BCRA, INDEC, …), normaliza lo que
devuelven a `(fecha, valor)` y expone el registro de organismos (`registro.json`) con
su URL, su licencia y si el dato puede o no republicarse.

QUÉ NO HACE: no transforma series (eso es `econometria`), no las cachea en el catálogo
(eso lo hacen los scripts de `scripts/`) y no decide qué series existen (eso es
`cueva/datos/catalogo.json`).

Es la ÚNICA capa de datos que toca la red: `cueva/datos/` y `cueva/econometria/`
siguen siendo puras y leen de disco.
"""

from cueva.fuentes.registro import Organismo, organismo, registro

__all__ = ["Organismo", "organismo", "registro"]
