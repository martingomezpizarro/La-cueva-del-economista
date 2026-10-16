# Módulo Mesa de Trabajo

> El **módulo 2** de la plataforma: donde se hace un trabajo econométrico de punta a punta.
>
> - **Parte I — Qué es** (§1-6): comportamiento de cada pantalla, decidido sobre el mockup.
> - **Parte II — Estado y construcción** (§7-9): qué existe hoy en el repo y qué falta.
> - **Registro de decisiones** (§10).
>
> Contexto general: `docs/PLATAFORMA.md`. Referencia visual: `docs/mockup/cueva-mockup.html`,
> pestaña «Mesa de Trabajo». Se construye **después** de la Línea de Tiempo (`PLATAFORMA.md` §7);
> este documento fija lo decidido para no perderlo mientras tanto.

---

# Parte I — Qué es

## 1. Estructura

```
Mesa de Trabajo
├── Explorar          jugar con las series: comparar, deflactar, reescalar. Solo visual + estadísticos.
│
├── Análisis
│   ├── Tests             investigar el comportamiento de las series
│   ├── Transformaciones  transformar o construir series a partir de otras, con receta
│   └── Modelado          el Estudio: regresiones, modelos, cointegración… como pasos guardados
│
└── Laboratorio       pregunta, objetivos, hipótesis con evidencia, informe, bibliografía
```

El orden de las pestañas es el orden de un trabajo: mirar → probar → construir → modelar →
escribir. Nada obliga a seguirlo, pero la navegación lo sugiere.

**Qué distingue cada zona**:

| Zona | ¿Guarda algo en el proyecto? | ¿Corre en el servidor? |
|---|---|---|
| Explorar | no (salvo series elegidas) — es un espacio para mirar | no: transformaciones de visualización |
| Tests | sí: cada batería es un paso del Estudio | sí |
| Transformaciones | sí: cada serie derivada con su receta | sí |
| Modelado | sí: cada paso con argumentos y resultado completo | sí |
| Laboratorio | sí: pregunta, hipótesis, secciones, citas | la redacción asistida sí |

---

## 2. Explorar

Estructura tomada del **visualizador del Trabajo Final** (`visualizador_template.html`), que ya
probó ser cómoda. Decidido el 2026-08-29.

### 2.1 Barra principal

De izquierda a derecha:

| Control | Opciones | Alcance |
|---|---|---|
| **Selector de serie** | buscador por nombre o categoría sobre el catálogo completo | — |
| **Modo** | `Individual` · `Comparar` | gráfico |
| **Tipo de gráfico** | 📈 línea · ⛰ área · 🕯 velas | gráfico |
| **Frecuencia** | `D` · `S` · `M` · `T` · `A` | gráfico |
| **Δ Transformar ▾** | `log` · `Δ diferenciar` | por serie |
| **÷ Deflactar ▾** | PBI ARS · PBI constante · PBI USD · MEP · CER · IPC USA · **otra serie del catálogo…** | por serie |
| **⚙ Ajustes ▾** | abre las filas de media móvil, variación y ejes (§2.2) | gráfico |
| **✕ Limpiar** | vuelve al estado inicial | — |

- **Deflactar por cualquier serie del catálogo** es un requisito, no un extra: la lista corta son
  atajos.
- **Velas** exige una frecuencia más gruesa que la nativa (agregación OHLC: apertura, máximo,
  mínimo, cierre del período).

### 2.2 Ajustes (todas las opciones)

**Fila 1 — media móvil y variación**

| Control | Qué hace |
|---|---|
| Media móvil (obs.) | ventana en observaciones; `0` = desactivada. En Comparar se aplica a **todas** las series, cada una con su color, línea punteada |
| Variación | `Niveles` · `i.a.` · `i.t.` · `i.m.` · `i.s.` |
| ▥ Barras | muestra la variación como barras |

Los rezagos de la variación **dependen de la frecuencia**: i.a. = 252 obs. en diaria, 52 en
semanal, 12 en mensual, 4 en trimestral, 1 en anual.

**Fila 2 — ejes**

| Control | Qué hace |
|---|---|
| Desde · Hasta | rango de fechas |
| Base 100 | fecha de normalización |
| Y mín · Y máx | límites manuales del eje |
| ↺ Auto | vuelve a ejes automáticos |

### 2.3 Orden de las transformaciones

Las transformaciones **no conmutan**. Orden aplicado y documentado:

```
deflactar  →  variación  →  log  →  diferenciar
```

(Decisión abierta §9.3: si queda fijo o se vuelve configurable.)

### 2.4 Gráfico

- **Estadísticos arriba** del gráfico, sobre el rango visible: `Último` (resaltado) · `Máx` · `Mín`
  · `Media` · `Obs.` · `Faltantes`. Asimetría y desvío **no** van acá (van en §2.5).
- **Navegación**: rueda = zoom · arrastrar = desplazar · doble clic = todo.
- **Rango rápido**: `1M · 3M · 6M · YTD · 1A · 5A · Todo`. El zoom manual desmarca el botón activo.
- **Tarjetita del mouse**: nombre, fecha, valor y unidad de cada serie.
- **Series con unidades distintas en Comparar** → base 100 automática con aviso sobre el gráfico.

### 2.5 Debajo del gráfico — modo Individual

**Distribución y estadísticos** sobre el rango visible: `Desvío` · `Asimetría` · `Curtosis exc.` ·
`p25` · `Mediana` · `p75`, más un histograma.

### 2.6 Debajo del gráfico — modo Comparar

En este orden:

1. **Spread A − B** — solo con **exactamente 2 series visibles**. Alinea por fecha, resta, y
   rellena hacia cero en verde (positivo) y rojo (negativo). Muestra el último valor. Si las
   unidades difieren, avisa que el spread es indicativo (en base 100 sí es interpretable).
2. **Cuadro comparativo serie a serie** — estadísticos por serie en columnas.
3. **Matriz de correlación de Pearson** — sobre las series **transformadas y alineadas por fecha**
   (no sobre niveles crudos: evita la regresión espuria de Granger-Newbold). Celdas coloreadas
   azul/rojo. Exportable a CSV.
4. **Matriz de dispersión** — n × n, histogramas en la diagonal, `r` en cada celda. Exportable a PNG.

> Pendiente de decisión (charlado el 2026-08-29): cuando hay 3 series visibles el spread
> desaparece sin aviso. Opción: mostrar "Spread disponible con 2 series — apagá una".

### 2.7 Sidebar de series

Panel izquierdo **ocultable**, ancho (~312 px), con las series elegidas. El ocultador es una
**pestaña angosta pegada al borde, a media altura**, con flecha que gira — igual que el
visualizador del TF (decidido el 2026-08-29).

Cada serie es una tarjeta, **editable en el lugar**:

| Parte | Contenido |
|---|---|
| Encabezado | punto de color (clic = mostrar/ocultar en el gráfico) · nombre · id · unidad · **rol** (`dep` / `expl`, clic para cambiar) |
| Por serie | `Transformar`: `log` · `Δ dif.` — `Deflactar`: selector |
| Del gráfico · compartido | frecuencia · variación · media móvil · tipo de gráfico · rango (solo lectura: se cambian arriba) |
| **Ficha** (colapsada por defecto) | organismo · cobertura · frecuencia nativa · unidad · método · ajuste estacional · revisiones · descarga · licencia · nota · estado `verificada` / `sin verificar` |
| Pie | ＋ Agregar serie |

- Las series aparecen **en los dos modos**. En Individual, la activa se resalta; en Comparar, se
  grafican todas las visibles.
- La **Ficha** sale del bloque `proc` del catálogo (`docs/DATOS.md`). Ejemplo de nota que tiene
  que poder mostrarse: *"Huecos en 2002Q1-Q2 por el feriado bancario. NO interpolar: es justo donde
  ocurre el quiebre."*

---

## 3. Análisis

### 3.1 Tests

Baterías sobre las series del proyecto. Pestañas:

| Batería | Contenido | Herramienta del servidor |
|---|---|---|
| **Raíz unitaria** | tabla por serie × transformación: ADF (p) · KPSS (p) · PP (p) · orden de integración · veredicto (`No estacionaria` / `Estacionaria` / `Ambiguo`) | `estacionariedad` |
| **Quiebres** | Bai-Perron (máx. 5): fecha · estadístico · **evento coincidente** de la Línea de Tiempo | ❌ falta |
| **Correlograma** | ACF/PACF + Ljung-Box | ⏳ Ljung-Box está en `diagnosticos` |
| **Heterocedasticidad** | ARCH-LM | `arch_lm` |

- Botones `Configurar` (rezagos por AIC, determinísticos) y `Correr batería`.
- Debajo de cada batería, **la lectura del copiloto**: qué implica el conjunto de resultados para
  el paso siguiente (ej. "tres I(1) y una I(0) desaconseja un VAR en niveles").
- La columna **evento coincidente** es el puente con la Línea de Tiempo (`MODULO_LINEA_DE_TIEMPO`
  §6.2): los quiebres se cruzan con `data/historia/eventos.csv`.

### 3.2 Transformaciones

Construir series nuevas a partir de las del catálogo.

| Parte | Contenido |
|---|---|
| **Constructor** | expresión (ej. `log(tcn_oficial × ipc_eeuu ÷ ipc_arg)`) con validación en vivo · **cadena aplicada** (ej. alinear a trimestral → interpolar huecos ≤ 2 → base 100 = 2004Q1 → log) |
| **Previsualización** | gráfico + `Obs.` · `Desde` · `Huecos` · `Outliers` |
| **Series construidas** | tabla: serie · receta · obs. · frecuencia · **usada en** (qué pasos del Estudio la usan) |
| Acciones | `Importar CSV` · `＋ Nueva serie` |

**Regla**: cada serie derivada guarda su **receta** — quién la construyó, de qué series y con qué
transformaciones. Es lo que la hace reproducible y lo que el informe cita en el anexo.

> ⚠ Seguridad: la expresión **no se evalúa con `eval`**. Se parsea a un árbol con una gramática
> cerrada (series, números, `+ − × ÷`, `log`, `exp`, `dif`, `rezago`) y se ejecuta sobre pandas.

### 3.3 Modelado — el Estudio

Lista de **pasos declarativos**: herramienta + series + transformación + parámetros. Cada paso se
ejecuta **en el servidor** y queda guardado con su resultado completo, así el copiloto y el
informe lo citan por id.

Cada tarjeta de paso:

| Parte | Contenido |
|---|---|
| Encabezado | número · nombre (ej. `VECM — Johansen`) · argumentos en una línea (`dep: embi_arg · indeps: tcr, res_pbi · rezagos: 2`) · estado (`ok` / `2 alertas`) · menú ⋯ |
| Resumen | métricas clave (rango de cointegración, traza vs crítico, α, vida media, AIC) |
| Tablas | coeficientes con EE, t, p · diagnósticos con **semáforo** |
| Veredicto | comentario del agente que corresponde (Crítico, Metodólogo) + **acción sugerida** (ej. `Agregar paso GARCH`) |

Acciones del Estudio: `＋ Agregar paso` · `Duplicar estudio` · `Exportar a LaTeX`.

Ejemplos de veredicto que el diseño tiene que soportar:
- *Crítico*: "el resultado primario queda al borde del 10 % — reportarlo como tal, no como significativo".
- *Metodólogo*: "bidireccional entre TCR y EMBI+ es precedencia temporal, no causalidad económica".

---

## 4. Laboratorio

Todo lo que define el trabajo y su informe.

| Bloque | Contenido |
|---|---|
| **Estado del informe** | secciones escritas (4 de 7) · citas verificadas · citas sin respaldo |
| **Pregunta de investigación** | texto editable + metadatos: frecuencia · series · series derivadas · ventana |
| **Hipótesis y evidencia** | `H1…Hn`, cada una con estado **`respaldada` · `parcial` · `pendiente` · `rechazada`** y **evidencia** enlazada: pasos del Estudio (`paso 5 · VECM r=1`), resultados (`α = −0,31`), obras (`📖 Enders, cap. 6`) y lo que falta (`falta prueba de robustez`) |
| **Documento** | secciones: 1 Introducción · 2 Marco teórico y antecedentes · 3 Datos · 4 Metodología · 5 Resultados · 6 Conclusiones · 7 Anexo (recetas, fuentes y salidas completas). Las no escritas muestran `Redactar con la evidencia de los pasos N–M` |
| **Bibliografía citada** (rail) | cada obra con estado: ✓ verificada contra el corpus (y cuántas veces se cita) · **!** cita sin fuente en el corpus |
| Acciones | `Vista previa` · `Exportar .docx` · `Pedir revisión al Crítico` |

**Regla**: *nada entra al informe sin fuente localizable*. El Bibliógrafo marca las citas que no
puede verificar.

> **Faltan en el mockup** (pedidos en la definición original del Laboratorio): **título** del
> trabajo, **objetivos** (general y específicos) y un lugar para **resultados** sueltos que todavía
> no están en una sección. Se agregan en la próxima iteración del mockup.

---

## 5. Copiloto

Transversal a toda la plataforma; especificado en `docs/PLATAFORMA.md` §4.2: botón flotante **IA**
movible → tarjeta de ~1/4 de pantalla → listado de agentes → chat.

Lo específico de la Mesa:

- **Qué ve el agente** (`ContextoDelCopiloto`, pendiente): las series elegidas con su ficha, los
  pasos del Estudio con su veredicto, las series derivadas con su receta, las hipótesis con su
  estado, las secciones escritas y los pasajes del RAG. Hoy no ve estudios ni informe.
- **Lecturas en el lugar**: además del chat, los agentes comentan **dentro** de las pantallas
  (lectura de la batería de tests, veredicto de un paso). Esos comentarios son mensajes del mismo
  agente, no un sistema aparte.
- **Sugerencias contextuales** en el composer según la pantalla y el agente.

---

## 6. Proyecto y Vista Rápida

- **Vista Rápida**: espacio efímero único, nada se persiste. Explorar funciona completo; el
  copiloto y lo que guarda en el proyecto quedan gateados.
- **Proyecto**: con nombre; persiste series, estudio, derivadas, hipótesis e informe.
- `💾 Promover a proyecto` se lleva todo lo acumulado en la Vista Rápida.
- El topbar muestra el proyecto activo.

---

# Parte II — Estado y construcción

## 7. Qué existe hoy

| Pantalla | En el repo | Brecha con este documento |
|---|---|---|
| Cascarón (topbar, tema) | ✅ `web/index.html` usa `web/estilo/tokens.css` y la topbar del mockup (2026-09-17) | — |
| Explorar | ✅ `web/explorador.html` (SPA nativa, estructura del visualizador del TF), datos en vivo por `GET /api/v1/explorador/datos` | sidebar editable con ficha `proc`; spread/cuadro/correlación/dispersión con el diseño de §2.6; ocultador tipo pestaña; **el iframe sigue con su tema oscuro propio: no sigue al de la plataforma** |
| Tests | ⏳ las herramientas existen (`estacionariedad`, `arch_lm`, `diagnosticos`) y se corren desde el Estudio | pantalla de baterías; Bai-Perron; correlograma; cruce con eventos |
| Transformaciones | ⏳ `transf` como parámetro de toda herramienta | constructor de expresiones con receta; tabla de series construidas |
| Modelado | ✅ pestaña «⚗️ Estudio»: pasos persistidos con id y resultado, 11 herramientas | acciones sugeridas desde el veredicto; duplicar; exportar a LaTeX |
| Laboratorio | ⏳ informe de 6 secciones fijas; hipótesis/objetivos como `list[str]` | entidades `Hipotesis`/`Objetivo`/`Seccion`/`Cita` con relaciones y estados (`AUDITORIA` D3) |
| Copiloto | ✅ FAB de agentes, chat 1:1 y mesa | listado desde skills, tarjeta movible; **contexto completo** (`AUDITORIA` D4) |

## 8. Orden de construcción

Sigue los caminos B y D de `docs/AUDITORIA_2026-08.md` §4, con dos piezas que llegan desde la
Línea de Tiempo:

1. **Tema unificado** — ✅ **el cascarón, hecho el 2026-09-17.** `web/index.html` carga
   `web/estilo/tokens.css`, tiene la topbar del mockup (marca · conmutador de módulos ·
   Vista Rápida/Proyecto · chips de estado · botón de tema) y sus colores propios pasaron a
   tokens. Los nombres viejos (`--bg`, `--panel`, `--txt`…) quedaron como **alias puente**
   hacia los tokens para no tocar el CSS que ya andaba; lo nuevo usa tokens directos.
   El tema es del usuario y se comparte entre módulos: `web/estilo/tema.js` (clave
   `cueva_tema` en localStorage), que usan las dos pantallas.
   ⏳ **Falta**: `web/explorador.html` (el iframe) sigue con su paleta oscura fija — se
   unifica en el punto 2. Y sigue pendiente borrar la econometría duplicada en JS.
2. **Explorar** — sidebar editable con ficha, paneles de Comparar, ocultador.
3. **Dominio de investigación** — `cueva/investigacion/`: `Hipotesis`, `Objetivo`, `Estudio`,
   `Seccion`, `Cita` (usa `knowledge-base/referencias.bib`, que crea la fase T2 de la Línea de Tiempo).
4. **`ContextoDelCopiloto`** — `cueva/agentes/contexto.py`, uno solo para los tres modos.
5. **Laboratorio** — hipótesis con evidencia, informe por secciones, bibliografía verificada.
6. **Tests y Transformaciones** como pantallas propias.

## 9. Decisiones abiertas

1. **¿Hasta dónde escribe el copiloto?** Secciones completas o párrafo por párrafo con aceptación.
   Cambia el modelo de `Seccion`.
2. **Spread con 3 series**: ¿desaparece o avisa? (§2.6)
3. **Orden de transformaciones**: ¿fijo (deflactar → variación → log → diferenciar) o configurable?
4. **Puente desde la Línea de Tiempo**: ¿"importar evento como dummy" en Transformaciones?

## 10. Registro de decisiones

| Fecha | Decisión |
|---|---|
| 2026-07-14 | Explorador nativo; Vista Rápida efímera + promover a proyecto con nombre |
| 2026-07-14 | Estudio = pasos declarativos que corren en el servidor y persisten con resultado |
| 2026-08-28 | Tres zonas: Explorar · Análisis (Tests, Transformaciones, Modelado) · Laboratorio |
| 2026-08-29 | Explorar copia la estructura del visualizador del TF: barra, frecuencia, transformar, deflactar (incluida cualquier serie), ajustes completos |
| 2026-08-29 | Estadísticos (Último, Máx, Mín, Media, Obs., Faltantes) arriba del gráfico; asimetría y desvío abajo |
| 2026-08-29 | Zoom, arrastre y tarjetita iguales a la Línea de Tiempo |
| 2026-08-29 | Sidebar ocultable con series elegidas, campos editables en el lugar y Ficha colapsada |
| 2026-08-29 | Media móvil aplica a todas las series en Comparar |
| 2026-08-29 | Comparar: spread A−B, cuadro comparativo, correlación de Pearson y matriz de dispersión |
| 2026-08-29 | Rango rápido 1M · 3M · 6M · YTD · 1A · 5A · Todo |
| 2026-08-29 | Ocultador del sidebar como pestaña en el borde (estilo visualizador TF) |
| 2026-08-29 | Copiloto como botón flotante movible con listado de agentes, no panel fijo |
| 2026-09-17 | La Mesa adopta `tokens.css` por **alias puente**, no reescribiendo su CSS: `--bg`, `--panel`, `--txt`… pasan a apuntar a los tokens |
| 2026-09-17 | El **tema es del usuario, no de la pantalla**: `web/estilo/tema.js` lo guarda y lo comparten los dos módulos |
| 2026-09-17 | La subnav de cinco vistas (§1) **no se construye todavía**: tres de esas pantallas no existen y poner pestañas vacías sería maqueta, no plataforma |
