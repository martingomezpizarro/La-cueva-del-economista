---
# Copiar a fichas/<id-del-evento>.md. Lo que ya está en eventos.csv (título, fechas,
# categoría, nivel) NO se repite acá.
id: <id-del-evento>

# Series troncales que la ficha activa al abrirse (máx. 4). Ids de series.json.
series: []

# Cada número importante vive UNA vez, acá, con su fuente. En el relato se escribe
# {{c:nombre}} y la UI lo renderiza como número clickeable.
cifras:
  - id: <nombre-corto>
    v: "<valor tal como se muestra>"
    et: "<etiqueta: qué es>"
    serie: null            # id de series.json, o null si la cifra no tiene serie
    anio: <aaaa>
    fuente: "<obra, cuadro y página, o norma>"

fuentes_primarias:
  - tipo: ley              # ley | decreto | comunicacion | discurso | memoria
    ref: "<identificación>"
    url: ""                # vacío si no está digitalizada

medios:
  # Sin credito + licencia + url_origen, la imagen no se usa. Placeholder antes que problema legal.
  []

relacionados: []
redactor: ""
revisado: <aaaa-mm-dd>
verificado: false
---

## Contexto

Uno a tres párrafos. Las citas bibliográficas van con clave Pandoc: [@clave, p. 47].

## Cronología

- **<aaaa-mm-dd>** — …

## Qué mirar

Qué debería moverse en las series troncales y por qué.

## Citas

> "Texto textual."
> — [@clave, p. 47]
