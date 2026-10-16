# `data/series/` — la fuente de verdad de los datos de La Cueva

**Todo dato que use el catálogo vive acá.** Si una serie apunta a un archivo que no está en esta
carpeta, esa serie no es reproducible fuera de esta máquina: no se cataloga todavía, se anota como
pendiente. (Decisión del 2026-08-29.)

## Organización

Una carpeta **por familia del catálogo**, numerada para que el orden en el disco sea el orden de la
plataforma, más una carpeta hermana con los crudos del organismo:

```
data/series/
    1.Actividad y Cuentas Nacionales/        # los CSV tidy que lee el catálogo
        cn_vab_rama_constante.csv            #   fecha + una columna por concepto
        cn_nombres.csv                       #   (archivo, columna) → nombre textual del INDEC
        emae_nivel_general.csv
        ...
    Actividad y Cuentas Nacionales_Fuentes/  # los .xls y .csv como los publica el organismo
        sh_oferta_demanda_por_sector_03_26.xls
        ...
    bcra/
```

Los CSV del catálogo son **anchos**: `fecha` + una columna por serie, con un código corto como
encabezado. El código corto es la llave (`valCol` del catálogo); el **nombre completo del
organismo** vive en `cn_nombres.csv` y de ahí sale el `label`. No se pone el nombre largo como
encabezado: varios llevan comas y punto y coma, y cambiar el encabezado obliga a reescribir el
catálogo entero.

Los archivos de una serie por CSV (`fecha,valor`) con `_index.csv` al lado siguen siendo el formato
de las descargas del BCRA.

## Se llena con los scripts, no a mano

```bash
python scripts/ingestar_cuentas_nacionales.py       # .xls del INDEC → CSV tidy + cn_nombres.csv
python scripts/actualizar_bcra.py --indice          # diccionario de variables + metodología
python scripts/actualizar_bcra.py --series --todas  # las series históricas
```

Cuándo un archivo puede vivir acá versionado y cuándo hay que dejar solo el script que lo repone:
`docs/DATOS.md` §3, y el detalle fuente por fuente en `cueva/fuentes/registro.json`
(campo `redistribuible`).

## El fallback al Trabajo Final

`cueva/datos/series.py` y `scripts/auditar_series.py` buscan **primero acá** y después en la
carpeta del Trabajo Final, para poder migrar series de a una sin romper el catálogo. Es
transitorio: hace que algo funcione en una máquina y falle en cualquier otra. Cuando no queden
series apuntando afuera, se saca.

Al 2026-08-29 la familia Actividad resuelve 562 de 630 entradas acá; las 68 restantes piden 22
archivos que todavía no están.
