"""Arma docs/mockup/mesa-investigacion.html: la plantilla + los datos reales del TF inyectados
(un solo archivo, se puede abrir con doble clic o publicar como artifact).

    python scripts/mockup_mesa_investigacion_datos.py <panel_mensual.csv> <diccionario_variables.csv>
    python scripts/armar_mockup_mesa_investigacion.py
"""

from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1] / "docs" / "mockup"
plantilla = (RAIZ / "mesa-investigacion.plantilla.html").read_text(encoding="utf-8")
datos = (RAIZ / "mesa_investigacion_datos.js").read_text(encoding="utf-8")
salida = RAIZ / "mesa-investigacion.html"
salida.write_text(plantilla.replace("/*__DATOS__*/", datos), encoding="utf-8")
print(f"{salida} ({salida.stat().st_size / 1024:.0f} KB)")
