# Presentación de datos y procedencia — módulo Línea de Tiempo

> Qué ve el usuario cuando mira un número de la línea de tiempo, y de dónde sale ese número.
> Complementa `docs/MODULO_LINEA_DE_TIEMPO.md` (el módulo) y `docs/DATOS.md` §3 (el bloque `proc`
> del catálogo de la Mesa). Escrito el 2026-09-13 junto con la primera carga de `data/historia/`.

---

## 1. El principio

La Cueva es una plataforma académica pública. Su producto no es el número: es **el número con su
cadena de custodia**. Un dato sin procedencia declarada no es citable ni replicable, y entonces no
sirve para una tesis, que es el caso de uso que ordena todo lo demás.

De ahí una regla que se aplica sin excepción y que conviene poder decir en una línea:

> **Todo número visible en pantalla tiene que poder contestar tres preguntas con un solo clic:
> de dónde salió, qué unidad tiene y qué tan confiable es.**

Y su recíproca, que es la que cuesta sostener:

> **Si no puede contestarlas, no se muestra.** Sin fuente no hay evento; sin licencia no hay foto;
> sin serie, la cifra lo dice.

---

## 2. Los cuatro tipos de dato del módulo

No todos los números de la pantalla son la misma clase de cosa. Mezclarlos es el error que hace
que una plataforma parezca prolija y sea incitable.

| Tipo | Dónde vive | Granularidad | Quién lo produce |
|---|---|---|---|
| **Serie troncal** | `series.json` + `series/<id>.csv` | un valor por año | un script, desde crudos |
| **Cifra de ficha** | frontmatter de `fichas/<id>.md` | un valor puntual | transcripción a mano |
| **Parámetro institucional** | `eventos.csv` (resumen/nota) y fichas | un valor por norma | lectura de la norma |
| **Fecha** | `eventos.csv`, `presidencias.csv` | un día, mes o año | bibliografía o norma |

Las series se grafican; las cifras se citan; los parámetros se comparan; las fechas se ubican.
**Una cifra de ficha nunca se dibuja como serie** aunque tenga varios años: si hay que graficarla,
primero pasa por `series.json` con su empalme declarado.

> **Decisión 2026-09-13.** Las series de Gómez (2018) —Fondo de Conversión 1900-1928, redescuentos
> 1908-1934, cuenta Tesorería y financiamiento del BNA al Estado 1900-1934— entran como **cifras de
> ficha**, no como series troncales. Cubren 35 años sobre 145 y no son ninguna de las diez del
> catálogo cerrado. Los crudos transcriptos quedan en `data/historia/_crudo/gomez-2018/` para que
> cada cifra sea reproducible. Revisar si en algún momento se abre una categoría de *series de
> época*, visibles sólo con el zoom dentro de su ventana (implica reabrir la decisión §13.1).

---

## 3. Cómo se muestra la procedencia, por tipo

### 3.1 Serie troncal — la procedencia es *por año*, no por serie

Una serie larga argentina **nunca sale de una sola fuente**: es un empalme. El formato lo hace
visible en vez de esconderlo. Cada fila del CSV declara de qué tramo sale:

```
anio,valor,tramo
1880,100.0,ferreres
…
1993,412.7,indec
```

**En pantalla:**

- La **tarjetita del mouse** dice, por cada serie activa: nombre, valor, unidad y **la fuente de ese
  año** — no la de la serie. Si el usuario pasa de 1942 a 1943 y cambia de "Ferreres" a "BCRA", lo
  ve en el momento.
- Los **cambios de tramo** se marcan sobre la curva con un tick discreto en el eje. No se
  interrumpe la línea: la serie es continua por construcción, pero el lector tiene que poder ver
  dónde se pegó.
- Lo que la serie **no cubre** se pinta como banda gris "sin cobertura", **calculada desde los
  datos reales**, nunca declarada a mano. Hoy la cobertura honesta es el dato más incómodo del
  proyecto y precisamente por eso se muestra.
- El panel de la serie (o su tooltip extendido) muestra el campo **`empalme`**: retropolación por
  tasas, coeficiente de enlace en el año de superposición, o ninguno. **Sin descripción del
  empalme, no hay serie.**

**Campos obligatorios** en `series.json`, además de los evidentes:

- `tipo`: `nivel` | `tasa`. Decide qué transformación es válida: poner en base 100 algo que ya es
  un porcentaje no significa nada, y la UI avisa.
- `agregacion_anual`: `dic_dic` | `promedio` | `fin_periodo` | `suma`. **Obligatorio**, porque
  cambia el número: la inflación de 1989 dic-dic (4.923%) y promedio anual (3.079%) son dos datos
  distintos y las dos son "la inflación de 1989". La etiqueta del eje lo dice siempre.
- `confianza`: `alta` | `media` | `baja` | `verificada`. Igual que en el catálogo de la Mesa,
  `verificada` **la pone una persona**, nunca un script.

### 3.2 Cifra de ficha — el número vive una sola vez

En el frontmatter, con etiqueta, año, serie (o `null`) y fuente. En el relato se escribe
`{{c:nombre}}` y la UI lo renderiza como número clickeable.

**Por qué por nombre y no por posición:** reordenar la lista de cifras no rompe el relato. Y por
qué una sola vez: si el número aparece en la cronología y en el panel de evidencia, tiene que ser
literalmente el mismo dato, no dos strings que se pueden desincronizar.

**Al tocar una cifra:**

1. si declara `serie` y esa serie no está activa, se activa (liberando lugar si ya hay 4);
2. el gráfico hace zoom al año de la cifra;
3. se resalta el punto con año y valor;
4. el resaltado se apaga solo a los ~2,6 s.

Una cifra **sin** `serie` (por ejemplo "250 USD semanales", "Decreto 1570/2001") se muestra igual
pero marcada *sin serie*: **no finge un vínculo que no existe**. Esta es la parte del diseño que
más se tienta uno de saltear y la que más barata sale respetar.

En el panel de evidencia, cada cifra se lista con su `fuente` completa —obra, cuadro y página, o
número de norma— visible sin interacción. La fuente no es un tooltip: es parte del dato.

### 3.3 Evento — `refs` o `fuente`, siempre

Cada fila de `eventos.csv` lleva `refs` (claves de `referencias.bib`) o `fuente` (norma, decreto,
base de datos), o las dos. **Una fila sin ninguna no pasa el test.**

En la ficha y en el panel lateral se muestran distinto, porque son cosas distintas:

- **`fuente`** es la fuente primaria: se imprime tal cual, con su identificación completa
  (`Ley 3871 del 31/10/1899, arts. 1, 3, 4, 5 y 7 (Anales, complemento 1889-1919, p. 473)`).
  Si tiene URL al texto original, va enlazada.
- **`refs`** son obras: se formatean desde `referencias.bib` en el bloque bibliografía.

### 3.4 Bibliografía — y el marcador de "no verificable"

`RAG/referencias.bib` es el registro único de obras citables de toda la plataforma. En las fichas
las citas usan sintaxis Pandoc, `[@clave, p. 47]`, para que el día que una ficha pase a un informe
se exporte tal cual a LaTeX o Word.

El campo **`file`** de una entrada apunta al PDF dentro de `RAG/corpus/` si lo tenemos. Y de ahí
sale una distinción que el usuario tiene que ver:

| Entrada | Qué puede hacer el Bibliógrafo | Cómo se muestra |
|---|---|---|
| con `file` | verificar la cita contra el texto | cita normal |
| sin `file` | nada: la obra es citable pero no verificable | **"cita no verificable"** junto a la referencia |

No es un defecto a esconder: es información sobre el estado del propio proyecto. Al 2026-09-13,
8 de las 38 entradas tienen `file`.

### 3.5 Estado editorial — en el encabezado, siempre

Toda ficha muestra `verificada <fecha>` o `sin verificar` en el encabezado. Los eventos sin ficha
muestran "ficha pendiente de redacción" en vez de un vacío. Hoy **las tres fichas del tramo
1880-1935 son borradores sin verificar**, firmadas como tales, y eso se lee antes que el texto.

---

## 4. Unidades: la trampa concreta de este período

El tramo 1880-1935 mezcla cinco unidades y las fuentes no siempre lo aclaran en el mismo lugar:
pesos moneda nacional (m$n, "pesos papel"), pesos oro, libras esterlinas, dólares e índices con
bases distintas (1886=100, 1993=100, ene-1929=100).

Reglas:

1. **Toda cifra declara su unidad en el campo `v`**, no en el texto que la rodea: `"30 mill. $ oro"`,
   no `"30 millones"` con la unidad en la oración.
2. **Ninguna serie troncal es nominal en pesos.** Hubo cinco cambios de moneda desde 1880; las
   troncales son reales, índices o ratios. Ésta es la defensa estructural contra el problema.
3. **La paridad legal 1899-1929 es 2,27 m$n por peso oro** y es la única conversión que se aplica
   sin discusión, dentro de ese rango. Fuera de él hace falta el tipo de cambio observado, que
   para buena parte del período **no está publicado**: si no se tiene, no se convierte.
4. **Las reservas de la Caja de Conversión y las del BCRA no se empalman.** Son balances de
   instituciones distintas y en el medio hubo una revaluación del oro que por sí sola movió
   663,4 millones de m$n. Si alguna vez se grafican juntas, va con corte visible y nota.

---

## 5. Escalas: qué se puede comparar con qué

El problema es real: la inflación de 1989 (3.079%) contra la deuda de 2002 (166% del PBI). Ningún
modo único lo resuelve, así que hay tres y se declaran:

| Modo | Qué hace | Cuándo |
|---|---|---|
| **Índice 100** (default) | base 100 en el primer año visible, se re-ancla al hacer zoom | comparar trayectorias heterogéneas |
| **Log** | nivel real en escala logarítmica | series que crecen multiplicativamente |
| **Paneles** | un panel por serie, con su eje y su escala real | cuando normalizar mentiría |

Y el panel **Δ i.a.** es independiente de los tres, para ver nivel y variación a la vez. Dos
detalles que son de honestidad, no de estética:

- la variación de un **nivel** es un cambio porcentual; la de una **tasa**, una diferencia en
  **puntos porcentuales**. El panel las calcula distinto y lo dice en la etiqueta;
- el eje del panel Δ se recorta al percentil 94 × 2,4 para que la hiperinflación no aplaste el
  resto, y **el recorte se declara** en la etiqueta. Un eje recortado en silencio es un gráfico
  que miente.

Máximo **4 series simultáneas**. Más de cuatro curvas sobre 145 años es ilegible.

---

## 6. Medios: la regla que no se negocia

Las fotos de archivo argentino **no son libres por defecto**. Toda imagen lleva `credito`,
`licencia` y `url_origen`, y el test lo exige. Preferir Wikimedia Commons, el Archivo General de
la Nación y material con licencia declarada; Télam, Clarín y La Nación requieren permiso explícito.

Sin licencia clara: **placeholder**. Un marco vacío con su crédito es mejor que un problema legal.

---

## 7. Lo que los tests tienen que hacer cumplir

`tests/test_historia.py`, además de lo que ya chequea sobre presidencias:

| Archivo | Qué falla |
|---|---|
| todas las tablas | fecha inválida · `hasta < desde` · `verificado` fuera de `si`/`no` · fila sin fuente |
| `eventos.csv` | id duplicado o mal formado · categoría/subtipo/nivel fuera del vocabulario · **sin `refs` ni `fuente`** · clave de `refs` inexistente en `referencias.bib` · `ficha=si` sin archivo |
| `fichas/*.md` | ficha sin fila en `eventos.csv` · `{{c:x}}` que no existe en `cifras` · **cifra sin `fuente`** · `serie` que no está en `series.json` · `[@clave]` inexistente · medio sin `credito`/`licencia`/`url_origen` · `relacionados` inexistentes |
| `series.json` + `series/*.csv` | serie sin `tipo`, `agregacion_anual` o `empalme` · año repetido · `tramo` del CSV no declarado · tramos superpuestos sin empalme descrito |
| `medios/` | imagen que ninguna ficha usa · imagen > 500 KB |

El criterio de fondo: **los datos se testean como código**. Es lo mismo que ya rige para
`catalogo.json` con el bloque `proc`, aplicado a la historia.

---

## 8. Pendiente de decidir

1. **Series de época.** ¿Se abre una categoría de series cortas visibles sólo dentro de su ventana
   de zoom (Fondo de Conversión, redescuentos, cuenta Tesorería), o el catálogo cerrado de diez
   troncales se mantiene sin excepciones? Hoy: sin excepciones.
2. **Ruta de `referencias.bib`.** El documento del módulo dice `knowledge-base/referencias.bib`;
   el repo usa `RAG/`. El archivo se creó en `RAG/referencias.bib`. Unificar.
3. **`_crudo/` y git.** Las transcripciones a mano no son descargas reponibles: si se borran, se
   pierde trabajo. Decidir si salen de `_crudo/` o si se hace una excepción en el `.gitignore`.
4. **Capa de reglas institucionales vigentes.** Los parámetros del régimen (encajes, topes,
   respaldos mínimos, composición del directorio) forman una tabla natural —la hoja
   `27_BCRA_1935` de Gómez ya es una fila de ella—. Si la plataforma va a mostrar "qué reglas
   regían en tal año", conviene diseñarla ahora y no cuando haya veinte fichas escritas.
