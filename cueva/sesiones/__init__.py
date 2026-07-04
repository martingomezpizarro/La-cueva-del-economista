"""cueva.sesiones — persistencia de las investigaciones (patrón Repository).

Única puerta de entrada para cargar/guardar pizarras: esconde CÓMO se persiste
(hoy JSON por proyecto; mañana SQLite/Postgres) y serializa el acceso concurrente
con un lock por proyecto — dos requests sobre la misma investigación ya no se pisan.
"""

from .repositorio import PidInvalido, ProyectoNoEncontrado, RepositorioProyectos

__all__ = ["RepositorioProyectos", "ProyectoNoEncontrado", "PidInvalido"]
