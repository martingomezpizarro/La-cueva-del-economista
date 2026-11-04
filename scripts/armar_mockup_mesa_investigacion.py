"""Arma docs/mockup/mesa-investigacion.html: la plantilla + los datos reales del TF inyectados
(un solo archivo, se puede abrir con doble clic o publicar como artifact).

    python scripts/mockup_mesa_investigacion_datos.py <panel_mensual.csv> <diccionario_variables.csv>
    python scripts/armar_mockup_mesa_investigacion.py
"""

from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1] / "docs" / "mockup"
plantilla = (RAIZ / "mesa-investigacion.plantilla.html").read_text(encoding="utf-8")
datos = (RAIZ / "mesa_investigacion_datos.js").read_text(encoding="utf-8")
# el componente de tablas vivas es el MISMO que usa la plataforma (sin los export de módulo)
tabla_viva = (RAIZ.parents[1] / "web" / "mesa" / "tabla_viva.js").read_text(encoding="utf-8")
tabla_viva = tabla_viva.replace("export function ", "function ").replace("export const ", "const ")
salida = RAIZ / "mesa-investigacion.html"
salida.write_text(
    plantilla.replace("/*__DATOS__*/", datos).replace("/*__TABLA_VIVA__*/", tabla_viva), encoding="utf-8"
)
print(f"{salida} ({salida.stat().st_size / 1024:.0f} KB)")
