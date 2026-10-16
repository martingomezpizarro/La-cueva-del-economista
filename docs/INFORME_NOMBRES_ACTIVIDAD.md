# Informe · Nombres, jerarquía y cobertura en Actividad y Cuentas Nacionales

Diagnóstico pedido el 2026-08-29, después de crear `data/series/1.Actividad y Cuentas Nacionales/`.
**No se aplicó nada.** El único archivo nuevo es la tabla de equivalencias
`docs/nombres_cuentas_nacionales.csv` (540 filas), que no toca datos ni catálogo.

Actualizado el mismo día con la corrección de Martín sobre los cuadros del INDEC (punto 4).

---

## Resumen

| # | Hallazgo | Alcance | Gravedad |
|---|---|---|---|
| 1 | La carpeta nueva resuelve 506 de 574 entradas | 68 entradas sin archivo | media |
| 2 | El ingestor **lee el nombre original del INDEC y lo descarta** | 68 ramas × 5 medidas | **alta** |
| 3 | El catálogo es **plano**: ningún subgrupo tiene jerarquía | 522 series de la familia | **alta** |
| 4 | «VAB por rama» se quedó **sin sus 17 cabeceras**: se catalogaron en «PBI por sector», que es otro cuadro | 17 series × 2 medidas | **alta** |
| 5 | 140 etiquetas ambiguas en el catálogo entero (eran 82 en agosto) | 610 series | alta |
| 6 | `ingestar_cuentas_nacionales.py` quedó **roto** por el renombre de carpetas | el script no corre | media |
| 7 | 56 columnas con datos sin catalogar: son los **huecos** que dejó repartir mal los dos cuadros | 4 archivos | media |
| 8 | El **PBI trimestral** apunta a archivos que no están, teniendo el dato en la carpeta | 2 entradas | media |
| 9 | El INDEC repite «Nacional» e «Importado» dentro del cuadro de FBKF | 4 series | media |

---

## 1 · Qué resuelve la carpeta nueva

`data/series/1.Actividad y Cuentas Nacionales/` tiene 20 CSV. La familia *Actividad y Cuentas
Nacionales* del catálogo declara 574 entradas (522 series; algunas con más de una frecuencia):

- **506 entradas (88 %) resuelven** contra esos 20 archivos. Los 20 están referenciados: no sobra ninguno.
- **68 entradas no**, porque su CSV no está en la carpeta. Siguen dependiendo del repo del Trabajo
  Final, que desde esta máquina no se ve.

| Qué falta | Entradas | Archivo esperado | Se puede reponer |
|---|---|---|---|
| EMAE por sector (16 series × M/Q/A) | 48 | `emae_sectorial_{mensual,trimestral,anual}.csv` | **Sí**: los tres crudos están en `..._Fuentes/` |
| Kalman mensual de Oferta y Demanda | 10 | `od_*_kalman.csv` | No: los produce `kalman_filter.py` del Trabajo Final |
| PBI nivel (4 series × M + Q/A) | 8 | `pbi_*.csv` | Parcial: los trimestrales salen de `cn_oferta_demanda_*`; los mensuales son Kalman |
| Índice Líder UTDT | 2 | `utdt_il.csv` | Sí, pero es otra fuente (UTDT, no INDEC) |

Nota: los tres crudos del EMAE sectorial que están en `..._Fuentes/` **ya vienen con el nombre
completo en el encabezado** (`agricultura_ganaderia_caza_silvicultura`, …). Es el precedente de lo
que hay que hacer en el resto.

---

## 2 · El nombre original se lee y se tira

Este es el problema de fondo que planteaste, y tiene una causa concreta y barata de arreglar.

En `scripts/ingestar_cuentas_nacionales.py`, la función `_conceptos()` recorre la **columna 0** del
`.xls` —donde el INDEC escribe el nombre completo del concepto— pero devuelve solo los **índices de
fila**. Después `_trimestral()` hace `zip(cols, valores)` contra una lista fija de códigos cortos
(`RAMA_COLS`). El texto del INDEC nunca llega al CSV: se usa para contar filas y se descarta.

Por eso pasa lo que viste:

| Columna del CSV | Nombre en `catalogo_series` | Nombre del INDEC (perdido) |
|---|---|---|
| `agro_serv` | Servicios agrícolas y pecuarios | Servicios agrícolas y pecuarios, **excepto los veterinarios** |
| `ee_agua` | **Agua** | Captación, depuración y distribución de agua |
| `min_petroleo_gas` | Petróleo, gas y carbón | Extracción de carbón y lignito; extracción de turba. Extracción de petróleo crudo y gas natural; actividades de servicios relacionadas con la extracción de petróleo y gas, **excepto las actividades de prospección** |
| `ind_muebles` | Muebles y colchones | Fabricación de muebles y colchones; **industrias manufactureras n.c.p.** |
| `inmo_resto` | Inmobiliarias y empresariales — resto | **Resto** |
| `otr_culturales` | Servicios culturales y deportivos | Servicios culturales y deportivos. **Otras actividades** |

Las palabras en negrita son las que definen el alcance de la serie. Sin ellas, `ind_muebles` parece
"muebles" cuando en realidad incluye toda la industria n.c.p.

**La reconstrucción es exacta y ya está hecha.** `docs/nombres_cuentas_nacionales.csv` cubre los
cuatro cuadros (VAB/VBP por rama, PBI por categoría, Oferta y Demanda, FBKF) × los 13 CSV que salen
de ellos: **540 filas**, una por par (archivo, columna), con `nombre_indec` textual, `ruta_indec`,
`nivel`, `padre_columna`, `llamada_al_pie`, y el `id_catalogo` / `label_actual` / `subgrupo_actual`
que tiene hoy. 484 filas están catalogadas y **56 no** — son las del punto 7.

### Sobre poner el nombre largo como encabezado del CSV

No conviene, y vale la pena decir por qué: varios nombres del INDEC **contienen comas y punto y
coma** (`Fabricación de prendas de vestir; terminación y teñido de pieles`). Como encabezado de CSV
habría que citarlos siempre, y además `valCol` del catálogo es el contrato con el visualizador: si
cambia el encabezado, hay que reescribir 574 entradas.

Lo que sí resuelve el problema sin romper nada: **el código corto sigue siendo la llave, y el
nombre largo vive en el catálogo**, en un campo nuevo. Así el CSV queda estable y la plataforma
muestra e indexa el nombre completo.

---

## 3 · El catálogo es plano

Medí la profundidad de los 16 subgrupos de la familia: **todos dan 1**. Ninguna serie de Actividad
usa `children`. Los 68 conceptos del cuadro del INDEC —que en el original son tres niveles: VAB
total → letra → rama— quedan como 68 hermanos en una lista.

De ahí sale tu ejemplo. Hoy la fila del Sheets dice:

```
Actividad y Cuentas Nacionales | VAB por rama | Agua | vab_c_ee_agua
```

y debería poder decir:

```
Actividad y Cuentas Nacionales › VAB por rama ›
  Valor agregado bruto a precios básicos › Electricidad, gas y agua ›
  Captación, depuración y distribución de agua
```

**La buena noticia: la jerarquía no hay que inventarla, ya está codificada en los prefijos.** Las 68
columnas se reparten en 1 total + 16 letras + 51 ramas, y el prefijo dice el padre sin ambigüedad
(`agro_*`→`agro`, `ind_*`→`industria`, `ee_*`→`elect_gas_agua`, `min_*`, `hot_*`, `tr_*`, `fin_*`,
`inmo_*`, `ense_*`, `salud_*`, `otr_*`). La columna `ruta_completa` del CSV nuevo ya está armada con
esa regla.

---

## 4 · «VAB por rama» se quedó sin sus cabeceras

**Corrección respecto de la primera versión de este informe.** `cn_vab_rama_*` y
`cn_pbi_categoria_*` **no son el mismo cuadro** y no hay que elegir uno:

| | `cn_vab_rama_*` | `cn_pbi_categoria_*` |
|---|---|---|
| Columnas | **68** | **21** |
| Qué hace | **desagrega**: VAB total › 16 letras › 51 ramas | **agrega**: VAB + IVA + derechos + impuestos netos = PBI |
| Nombre del INDEC | `Agricultura, ganadería, caza y silvicultura` | `A - Agricultura, ganadería, caza y silvicultura` |
| Para qué sirve | estructura productiva por rama | el puente de VAB a PBI a precios de mercado |

Que la letra coincida con diferencia 0,0000 no es una duplicación por error: es **la verificación
de que el agregado cierra**. El mismo nivel de agregación publicado en dos cuadros con propósitos
distintos, y los dos hacen falta.

El problema real es otro: **el catálogo repartió mal el nivel-letra entre los dos cuadros**, y lo
hizo distinto según la medida.

| Subgrupo | Archivo | Debería tener | Tiene | Falta |
|---|---|---|---|---|
| VAB por rama (constante) | `cn_vab_rama_constante.csv` | 68 | **51** | total + 16 letras |
| VAB por rama (corriente) | `cn_vab_rama_corriente.csv` | 68 | **51** | total + 16 letras |
| VAB por rama — IVF | `cn_vab_rama_ivf.csv` | 68 | 68 | — |
| VAB por rama — IPI | `cn_vab_rama_ipi.csv` | 68 | **63** | total, agro, industria, construcción, comercio |
| PBI por sector — IPI | `cn_pbi_categoria_ipi.csv` | 20 | **8** | 12 letras |

Es decir: para los **niveles**, las 51 ramas se catalogaron desde `cn_vab_rama_*` y sus 16 letras
desde `cn_pbi_categoria_*` — así que «VAB por rama» tiene 102 series de rama colgando del aire,
y su cabecera vive en otro subgrupo, con otro nombre («A — Agro»). Para el **IVF** salió completo.
Para el **IPI** salió partido al revés: 4 letras desde `pbi_categoria` y 12 desde `vab_rama`.

No es un criterio: es el residuo de tres corridas distintas. Cada cuadro tiene que tener su juego
completo de columnas, sacadas de su propio archivo.

---

## 5 · Colisiones de nombres: el informe de agosto nunca se aplicó

En el catálogo completo hoy hay **140 etiquetas usadas por más de una serie, que afectan a 610 de
1034**. El informe del 2026-08-27 (`docs/INFORME_DUPLICADOS_Y_NOMBRES.md`) las había medido en 82
etiquetas / 281 series y dejó `scripts/normalizar_nombres_series.py` listo. **Nunca se corrió con
`--aplicar`**, y las +419 series de cuentas nacionales que se sumaron el 29 empeoraron el número.

Dentro de la familia Actividad, el patrón nuevo es este:

| Etiqueta | Veces | Series |
|---|---|---|
| Intermediación financiera | 6 | `emae_finanzas`, `vab_c_fin_intermediacion`, `vab_n_…`, `vab_q_…`, `vbp_c_…`, `vbp_n_…` |
| Alimentos y bebidas | 6 | `uci_alimentos` + las 5 de VAB/VBP |
| Agua | 5 | `vab_c_ee_agua`, `vab_n_…`, `vab_q_…`, `vbp_c_…`, `vbp_n_…` |
| A — Agro | 5 | `sec_c_agro`, `sec_n_agro`, `vab_q_agro`, `vbp_c_agro`, `vbp_n_agro` |

Y hay un caso peor que la repetición: dentro de **«VAB por rama» conviven «J — Interm. Financiera»
(la letra J, agregado) y «Intermediación financiera» (`fin_intermediacion`, una de sus tres
sub-ramas)**. Son dos series distintas, una contiene a la otra, y sus nombres se confunden.

**Encabezados de CSV repetidos entre archivos**: ninguno se repite *dentro* de un archivo (eso está
bien), pero `agro`, `pesca`, `mineria`, `industria`, … aparecen en **9 archivos distintos**. Y
`total` significa "VAB a precios básicos" en `cn_vab_rama_*` y "Valor bruto de producción" en
`cn_vbp_rama_*`. Mientras se pida siempre por el par (archivo, columna) no hay riesgo; si en algún
momento la plataforma permite pedir solo por nombre de columna, sí lo hay.

---

## 6 · El ingestor quedó roto por el renombre

**`scripts/ingestar_cuentas_nacionales.py` no corre.** Quedó apuntando a las carpetas viejas:

```python
CRUDO  = RAIZ / "data" / "series" / "Actividad y Cuentas Nacionales"   # ya no existe
SALIDA = RAIZ / "data" / "series" / "indec"                             # ya no existe
```

Hoy son `…_Fuentes/` y `1.Actividad y Cuentas Nacionales/`. Si se regenera la ingesta sin corregir
esto, falla en la primera línea.

---

## 7 · 56 columnas con datos que el catálogo no usa

Recorrí los 20 CSV cruzando cada encabezado contra los `valCol` del catálogo. Ninguna es un dato
perdido, y ninguna sobra: son **exactamente los huecos** del cuadro del punto 4.

| Archivo | Columnas sin usar | Qué falta catalogar |
|---|---|---|
| `cn_vab_rama_constante.csv` | 17 | total + las 16 letras del VAB a precios constantes |
| `cn_vab_rama_corriente.csv` | 17 | ídem, a precios corrientes |
| `cn_vab_rama_ipi.csv` | 5 | total, agro, industria, construcción, comercio |
| `cn_pbi_categoria_ipi.csv` | 12 | las 12 letras que faltan del IPI por categoría |
| 5 archivos | `pbi` | ver el punto siguiente |

Las 88 observaciones están completas en las 56. Catalogarlas suma **51 series** a la familia
(las 5 columnas `pbi` son la misma serie vista desde distintos cuadros).

---

## 8 · El PBI trimestral está en la carpeta y el catálogo no lo ve

De las 68 entradas huérfanas del punto 1, dos se cierran ahora mismo:

| Serie | Fuente declarada hoy | Existe | Dónde está el dato |
|---|---|---|---|
| `pbi_constante` [Q] | `pbi_constante_2004.csv` | **no** | `cn_oferta_demanda_constante.csv`, columna `pbi`, 88 obs |
| `pbi_nominal` [Q] | `pbi_corriente.csv` | **no** | `cn_oferta_demanda_corriente.csv`, columna `pbi`, 88 obs |

El repunteo del 29 (`repuntar_duplicados_cuentas_nacionales.py`) movió 85 fuentes a los `cn_*.csv`
nuevos, pero no estas dos: el archivo viejo no estaba en la carpeta, así que no había contra qué
comparar `valCol`. Quedaron colgadas del Trabajo Final por omisión, no por decisión.

Es la serie principal del catálogo. Vale la pena arreglarlo antes que nada.

---

## 9 · El INDEC también repite nombres, y ahí la jerarquía es obligatoria

En el cuadro de FBKF el propio INDEC escribe:

```
Formación bruta de capital fijo
  Construcciones
    Otras construcciones (3)
  Maquinaria y equipo
    Nacional          ← 
    Importado         ← 
  Equipo de transporte
    Nacional          ← el mismo nombre
    Importado         ← el mismo nombre
  Otros activos fijos (4)
```

«Nacional» e «Importado» aparecen dos veces y **solo el padre las distingue**. Copiar el nombre
del INDEC al pie de la letra, sin la jerarquía, produce cuatro series con dos nombres. Es el
argumento más fuerte a favor de anidar: no es cosmética, sin el padre el dato es irrecuperable.

Dos detalles más del origen, para tenerlos presentes al cargar los nombres:

- El cuadro de **PBI por categoría trae la letra dentro del nombre** (`A - Agricultura, ganadería,
  caza y silvicultura`), y el de **VAB por rama no** (`Agricultura, ganadería, caza y
  silvicultura`). Es la marca de que son dos cuadros distintos; conviene respetarla.
- Varios nombres traen **llamadas al pie**: `Consumo privado (5)`, `Variación de existencias (3)`,
  `Otros activos fijos (4)`. El `(n)` sale del `label` y el texto de la nota debería ir a
  `proc.notas`, que es donde vive lo que aclara el alcance de la serie.

---

## Propuesta (decidida el 2026-08-29)

**El nombre de la serie es literalmente el del cuadro del INDEC, y la jerarquía va en el catálogo
como un nivel más después del subgrupo.** No se desambigua con sufijos: se desambigua con el padre.

### Estructura

El catálogo ya sabe anidar — el balance de pagos y los vencimientos de deuda usan `children` hasta
5 niveles. Se usa lo mismo acá:

```
Familia   Actividad y Cuentas Nacionales
 Subgrupo   VAB por rama
  item        Valor agregado bruto a precios básicos        vab_c_total
   children     Agricultura, ganadería, caza y silvicultura  vab_c_agro
    children      Cultivos agrícolas                         vab_c_agro_cultivos
    children      Cría de animales                           vab_c_agro_animales
    children      Servicios agrícolas y pecuarios, excepto los veterinarios   vab_c_agro_serv
   children     Electricidad, gas y agua                     vab_c_elect_gas_agua
    children      Captación, depuración y distribución de agua   vab_c_ee_agua
```

Así «Agua» deja de existir: la serie se llama *Captación, depuración y distribución de agua* y su
lugar en el árbol dice de qué es parte.

### Campos nuevos por serie

| Campo | Qué guarda | De dónde sale |
|---|---|---|
| `label` | **el nombre textual del INDEC**, sin recortar | columna 0 del `.xls` |
| `padre` | id del item que la contiene (`""` si es raíz) | prefijo de la columna |
| `nivel` | 1 total · 2 letra/categoría · 3 rama | derivado de `padre` |
| `proc.notas` | el texto de la llamada al pie, cuando el nombre trae `(n)` | pie del cuadro |

El `id` y el `valCol` **no se tocan**: son el contrato con los proyectos guardados y con el
visualizador. El código corto sigue siendo la llave del CSV; el nombre largo vive acá.

### En `catalogo_series` (el Sheets)

Dos columnas nuevas después de `Serie`, y dos al final del bloque técnico. `ID` no se toca.

| Columna | Ejemplo |
|---|---|
| `Categoría` | `Electricidad, gas y agua` |
| `Ruta` | `VAB por rama › Electricidad, gas y agua › Captación, depuración y distribución de agua` |
| `Archivo` | `cn_vab_rama_corriente.csv` |
| `Columna` | `ee_agua` |

`Archivo` + `Columna` es lo que engancha cada fila del Sheets con los CSV de
`1.Actividad y Cuentas Nacionales/`.

### Qué pasa con `normalizar_nombres_series.py`

Ese script cualificaba con sufijos (`Agua` → `VAB corriente — Agua`). Con esta decisión **no se
corre sobre la familia Actividad**: acá desambigua la jerarquía. Sí sigue haciendo falta para las
otras familias, donde el patrón es distinto (los 108 vencimientos de deuda con «Moneda Local» ×54
no tienen padre que los salve).

### Qué queda por decidir

Cómo se llama la serie cuando el mismo concepto aparece en las cinco medidas (constante,
corriente, IVF, IPI, VBP). Con el nombre literal, «Cultivos agrícolas» va a existir cinco veces con
el mismo `label`, distinguidas solo por el subgrupo. Dentro del árbol se entiende; en el buscador y
en la leyenda de un gráfico, no. Las dos salidas: que el subgrupo viaje pegado al nombre cuando la
etiqueta sale del árbol, o agregar un campo `medida` (constante / corriente / IVF / IPI) y que el
visualizador lo muestre aparte.

---

## Orden sugerido

1. **Arreglar las rutas del ingestor** (2 líneas). Sin eso no se puede regenerar nada.
2. **Guardar el nombre del INDEC en la ingesta**: que `_conceptos()` devuelva también el texto y
   que quede un `<archivo>_nombres.csv` al lado de cada CSV. Deja de perderse en cada corrida.
3. **Cargar `label`, `padre` y `nivel`** desde `docs/nombres_cuentas_nacionales.csv` y anidar
   los subgrupos por rama. Simulación primero.
4. **Catalogar las 56 columnas huérfanas** (punto 7): +51 series, cada cuadro con su juego completo.
5. **Repuntar `pbi_constante` y `pbi_nominal`** a `cn_oferta_demanda_*` (punto 8).
6. **Ingestar el EMAE sectorial** desde `..._Fuentes/` — cierra 48 de las 68 entradas huérfanas.
7. **Agregar las 4 columnas a la planilla** y reimportar el Sheets.

Los 7 son mecánicos y reversibles con git. El único punto abierto es el de «qué queda por decidir».

---

## Estado de la implementación (2026-08-29, tarde)

Corrección al modelo, según tu criterio: **VAB, VBP, IVF e IPI son categorías**; «Cultivos
agrícolas» es la **serie**; **constante y corriente son unidades de medida** de esa misma serie,
que se eligen después. No son cuatro subgrupos con la serie repetida adentro.

### Pasos 1 y 2 — hechos

`scripts/ingestar_cuentas_nacionales.py`:

- `CRUDO` y `SALIDA` apuntan a `…_Fuentes/` y `1.Actividad y Cuentas Nacionales/`. Vuelve a correr.
- `_conceptos()` ahora devuelve `(fila, texto)` en vez de solo la fila: **el nombre del INDEC deja
  de tirarse**. Se registra por (archivo, columna) y se escribe en `cn_nombres.csv`, al lado de los
  CSV. La llamada al pie —el `(3)` de «Variación de existencias (3)»— va en su propia columna.
- **562 nombres de los 20 archivos.** Verificado: los 20 CSV salen **byte a byte idénticos** a los
  que ya estaban en la carpeta, así que el cambio no toca ningún dato.

Los nombres del UCI y de la serie desestacionalizada no salen de la columna 0 sino del encabezado
del cuadro (están transpuestos); los del EMAE no salen de un cuadro sino de la publicación de
datos.gob.ar. Los tres casos quedaron contemplados.

### Pasos 3 y 4 — simulados

`scripts/reestructurar_actividad.py` (simula siempre; `--aplicar` todavía corta a propósito).
`python scripts/reestructurar_actividad.py --ver "VAB por rama"` imprime el árbol.

**13 categorías · 109 conceptos · 556 series · 56 a crear · 0 choques de id.**

| Categoría | Conceptos | Series | Nuevas | Profundidad |
|---|---|---|---|---|
| VAB por rama | 68 | 136 | **34** | 3 |
| VBP por rama | 68 | 136 | 0 | 3 |
| IVF por rama | 68 | 68 | 0 | 3 |
| IPI por rama | 68 | 68 | **5** | 3 |
| PBI por categoría de tabulación | 21 | 42 | 2 | 3 |
| IPI por categoría de tabulación | 21 | 21 | **13** | 3 |
| Oferta y Demanda | 11 | 22 | 2 | 2 |
| Oferta y Demanda desestacionalizada | 6 | 6 | 0 | 1 |
| IPI de Oferta y Demanda | 11 | 11 | 0 | 2 |
| FBKF | 10 | 20 | 0 | 3 |
| IPI de FBKF | 10 | 10 | 0 | 3 |
| Utilización de la capacidad instalada | 13 | 13 | 0 | 2 |
| EMAE — Nivel General | 3 | 3 | 0 | 1 |

Así queda el árbol:

```
VAB por rama
  Valor agregado bruto a precios básicos      [constante: vab_c_total (nueva) · corriente: vab_n_total (nueva)]
    Agricultura, ganadería, caza y silvicultura   [vab_c_agro (nueva) · vab_n_agro (nueva)]
      Cultivos agrícolas                          [vab_c_agro_cultivos · vab_n_agro_cultivos]
      Cría de animales                            [vab_c_agro_animales · vab_n_agro_animales]
      Servicios agrícolas y pecuarios, excepto los veterinarios
      Caza, repoblación de animales de caza y servicios conexos
      Construcciones agropecuarias
      Silvicultura, extracción de madera y servicios conexos
    Electricidad, gas y agua                      [vab_c_elect_gas_agua (nueva) · …]
      Generación captación y distribución de energía eléctrica
      Fabricación de gas; distribución de combustibles gaseosos por tuberías
      Captación, depuración y distribución de agua
```

«Agua» dejó de existir. Detalle fila por fila en `docs/reestructura_actividad.csv`.

### Sobre los ids nuevos

Ninguno choca con los 1034 que ya hay. El script **aprende la convención de cada categoría** en vez
de imponer una: los viejos no son uniformes (`sec_c_indus` para `industria`, `sec_c_eega` para
`elect_gas_agua`), así que antes de inventar un id mira cómo se llamó esa misma columna en el resto
de la categoría. Por eso salen `sec_p_eega` y `sec_p_admp`, y no `sec_p_elect_gas_agua`.

### Lo que falta cerrar antes de `--aplicar`

1. **El modelo de unidades.** Hoy `sources` solo distingue frecuencia; constante y corriente son
   dos series con dos `id`. Merge no conviene: hay 4 proyectos guardados en `data/proyectos/` y el
   `id` es su contrato. Lo que propongo es **agrupar sin fusionar**: cada hoja lleva `serie`
   (clave común, `agro_cultivos`) y `unidad_medida`, el árbol muestra un nodo y el visualizador
   ofrece la unidad. No cambia `cargar()` ni rompe nada.
2. **`od_c_pbi` / `od_n_pbi`.** El script los propone como nuevos, pero es mejor **repuntar
   `pbi_constante` y `pbi_nominal`** (punto 8) a esas columnas en vez de crear ids paralelos.
3. **Los nombres de las categorías.** Puse «IPI por rama», «IPI por categoría de tabulación»,
   «IPI de Oferta y Demanda», «IPI de FBKF». Son cuatro IPI distintos y hay que poder nombrarlos
   sin confundirlos; si preferís otra forma, se cambia en una constante del script.

---

## APLICADO — 2026-08-29, noche

El modelo final, corregido por Martín: **cuatro niveles fijos**, y la unidad **fuera** de la
jerarquía.

```
Familia    Actividad y Cuentas Nacionales
Grupo      Valor Agregado Bruto por rama
Subgrupo   Electricidad, gas y agua
Serie      Captación, depuración y distribución de agua
Unidad     Mill. ARS 2004   ·   Mill. ARS
```

Las dos unidades son dos filas del catálogo, una arriba de la otra; en la plataforma se resuelven
con el botón «Precios: Constantes | Corrientes». No se fusionaron ni se anidaron: `vab_c_ee_agua`
y `vab_n_ee_agua` siguen siendo dos ids, y por eso los 4 proyectos guardados no se rompen.

### Qué se hizo

| | |
|---|---|
| `scripts/ingestar_cuentas_nacionales.py` | rutas arregladas; `_conceptos()` devuelve `(fila, texto)`; escribe `cn_nombres.csv` con 562 nombres. Los 20 CSV salen byte a byte idénticos. |
| `scripts/reestructurar_actividad.py` | **nuevo**. Arma Grupo › Subgrupo › Serie, cataloga las 56 columnas huérfanas y reescribe la familia. |
| `scripts/auditar_series.py` | emite `grupo` además de `subgrupo`; los bloques sin `grupo` usan `sub` para los dos, así el resto del catálogo sigue andando. |
| `scripts/catalogo_planilla.py` | columna **Grupo** entre Familia y Subgrupo; el orden pasa a Familia › Grupo › Subgrupo › Serie. |
| `cueva/datos/catalogo.json` | 1034 → **1090 series**. Copia previa en `_logs/catalogo_pre_reestructura_2026-08-29.json`. |

### Verificaciones

- **0 series perdidas.** `aplicar()` aborta si algún id del catálogo viejo no aparece en el nuevo;
  la primera corrida abortó justo por eso —se llevaba puestos los 22 ids de EMAE por sector, Nivel
  de Actividad e Índice Líder, que no salen de ningún cuadro de `cn_nombres.csv`—. Ahora esos tres
  subgrupos se reubican sin tocarlos.
- **0 choques de id.** Los 56 nuevos son ids libres, con la convención aprendida de su propio grupo
  (`sec_p_eega`, no `sec_p_elect_gas_agua`).
- **Las otras 8 familias quedaron byte a byte iguales.**
- `tests/test_fuentes.py` y `tests/test_datos.py`: **25 pasan**. Las series nuevas heredan la
  procedencia de una hermana del mismo archivo —misma fuente, misma URL, mismo script—, que es lo
  verificable; inventarles un `proc` propio sería declarar algo que nadie chequeó.
- Regenerados: `INVENTARIO_SERIES.md`, `catalogo_series.csv` (con el merge de cobertura),
  `catalogo_series.xlsx` y el árbol de `web/explorador.html`.

### De paso

`emae_tc` no tenía `proc` a nivel de serie, aunque sus dos hermanas (`emae`, `emae_desest`) sí.
Venía así de la corrida del 29 y hacía fallar `test_fuentes.py` desde antes de esta reestructura.
Se le copió el de su fuente mensual.

### Lo que queda

1. **Importar el Sheets.** El CSV está listo con la columna Grupo; el procedimiento (subir a Drive,
   «Reemplazar hoja actual», estirar las fórmulas de «Resumen», rehacer el filtro) no cambió.
2. **El visualizador todavía lee un solo nivel de `subs`.** Los bloques traen `grupo` y `subgrupo`
   como campos aparte y `sub` compuesto (`"Valor Agregado Bruto por rama › Electricidad, gas y
   agua"`), así que anda sin tocarlo. El botón de Precios y los cuatro niveles nativos son trabajo
   del explorador, no del catálogo.
3. **Las 66 entradas huérfanas que quedan**: el EMAE sectorial (48, reponible desde `..._Fuentes/`),
   los 10 Kalman mensuales, 6 del PBI y 2 del Índice Líder. `pbi_constante` y `pbi_nominal`
   trimestrales siguen apuntando a archivos que no están, teniendo el dato en
   `cn_oferta_demanda_*`.
