# Unificación: La Cueva + Terminal de Análisis de Activos

> **Para quien retoma la unificación (persona o Claude).** Este documento reúne lo decidido y
> dónde está cada cosa. Leelo antes de tocar código. Después leé `CLAUDE.md` (estado del repo y
> reglas) y `docs/PLATAFORMA.md` (mapa de la plataforma). Escrito el 2026-11-15 con lo decidido
> por Martín el 2026-11-13.

---

## 1. Qué se decidió (2026-11-13)

1. **Se unifican los dos proyectos.** La Cueva del Economista pasa a llamarse **La Cueva**: ya no
   es solo de economía, es el lugar para cualquier análisis (series macro, activos, modelos).
   La Terminal de Análisis de Activos deja de ser una app aparte y pasa a ser **una pestaña de
   La Cueva**. Sus activos tienen que poder usarse en la Mesa de investigación, igual que una
   serie del INDEC o del BCRA.
2. **Estructura de pestañas:**

   | Pestaña | Qué es | Cómo se abre |
   |---|---|---|
   | **Inicio** | Página de entrada personalizable (§2) | Al entrar a la plataforma |
   | **Línea de tiempo** | Historia económica argentina desde 1880 | **En una pestaña aparte del navegador** |
   | **Mesa de trabajo** | Agrupa tres secciones: **Investigación** (la ex «Mesa de investigación»), **Proyecto** y **Documento** | Desde el Inicio o la barra superior |
   | **Terminal** | Análisis de activos (lo que hoy es el repo de la Terminal) | Desde el Inicio o la barra superior |

3. **La bandeja de series está en TODAS las pestañas y secciones.** Es lo que permite llevar lo
   que uno ve en cualquier lado (un precio de la Terminal, un evento de la Línea de tiempo, una
   serie de un módulo del Inicio, una capa transformada de un gráfico) a la Mesa de trabajo. Es
   un requisito, no un detalle de diseño.
4. **La Línea de tiempo quedó pendiente de adaptar** a este esquema (abre aparte, pero tiene
   que compartir la bandeja; ver §5.5).

## 1 bis. Decidido el 2026-11-15

| Tema | Decisión |
|---|---|
| Frontend (§5.1) | **Conviven.** La Cueva pone el cascarón común (barra, Inicio, bandeja, un solo `tokens.css`); la Terminal entra como pestaña con su React tal cual. |
| Estilo | **Manda el de la Terminal** (oscuro, financiero), reacomodado. El `tokens.css` común se arma a partir de su paleta, no de «pizarrón y tiza». |
| Backend (§5.2) | **Un solo servidor.** La Cueva instala la Terminal desde su repo privado (`pip install -e <repo>/terminal`) y la monta con `terminal.puente.montar(app)` en `/terminal/`. El código de la Terminal no entra a este repo público. Ya está hecho del lado de la Terminal (PR #27 de INVESTIGACI-N-ACTIVOS). |
| Series de mercado (§5.3) | **Se llaman como el activo: el ticker** (`GGAL`, `NVDA`), sin prefijo `mkt_`. `puente.listar_series()` y `puente.datos_serie(ticker, moneda)` leen el DuckDB local y traen la fuente para el linaje. |
| Almacén | Como dice la especificación 1.0: un solo almacén con el esquema point-in-time de la Terminal; los CSV de `data/series/` siguen siendo la fuente versionada de la macro y se cargan ahí. |
| Nombre | La pestaña se llama **Terminal** (no «Mercados»). |
| Rama de métodos (§5.6) | **Se une a `main`.** Probada el 15/11: sin conflictos; 303 tests pasan y fallan los mismos 9 que ya fallaban en `main`. |
| «Rápido» | Un proyecto armado desde la Mesa en **menos de 15 minutos** por alguien que sabe qué quiere hacer. |
| Factores para neutralidad | **Fama-French** (Ken French Data Library, diarios); ETFs como respaldo. |
| Cómputo del sitio público | Python (en el navegador, etapa 3), además del código que ya se puede escribir en la Mesa. |
| Datos | **No es el foco ahora.** Intradía y precios con licencia para el sitio público se buscan después de la unificación (puede haber presupuesto si el análisis lo justifica). |
| Macro y riesgos (Terminal) | Al rediseñarla entran el crédito (spreads, bonos y CDS cargados a mano, Merton) y lo que ayude a identificar coyunturas: la tesis de fondo es estimar la probabilidad de éxito según la coyuntura, clusterizando períodos. |

## 1 ter. Avance

**Paso 1 de la etapa 1 — estructura común (2026-11-18), HECHO:**
- `web/estilo/barra.js`: la barra común (Inicio · Línea de tiempo ↗ · Mesa de trabajo · Terminal)
  en todas las pantallas. Cada página deja `<nav class="modswitch" data-barra>` y la barra la
  completa; en el sitio publicado no hay Inicio, la Mesa es `/` y la Terminal aparece apagada.
- `cueva/api/terminal.py` + `config.carpeta_terminal()`: si el repo de la Terminal está en la
  compu (por defecto `PROGRAMACION/PORTFOLIO MANAGER/INVESTIGACIÓN ACTIVOS/terminal`, override
  `CUEVA_TERMINAL`), se monta en `/terminal/` con su `puente`; si no, `/terminal/` explica por qué
  (503). `GET /api/v1/terminal/estado`. Tests: `tests/test_terminal.py`.
- Dentro de La Cueva, la Terminal carga la misma barra (lo inyecta su servidor; PR #28 de la
  Terminal) y descuenta su alto con `--alto-cueva`.
- `tokens.css`: oscuro por defecto con la paleta de la Terminal; el claro («pizarrón y tiza»)
  queda como opción del botón de tema. Tipografía sans (Inter/Segoe UI) en vez de Fraunces/Plex.
- **«La Cueva del Economista.bat»** (raíz): trae lo último de GitHub, prepara la Terminal
  (`scripts/preparar_terminal.py`: pull, paquetes, interfaz, precios) y abre `localhost:8800`.
  No abrir a la vez con Terminal.bat: comparten la base DuckDB.

### Requisito de Martín (18/11): la Mesa tiene que quedar como en el mockup «La Cueva»

La Investigación del mockup estaba toda pensada y **no se recorta**. Hoy `/mesa` tiene Explorar y
Métodos; el backend de casi todo ya existe (102 métodos, recetas, código restringido, Mis series,
Mis resultados), pero la pantalla del mockup no está portada. Lista de control (✗ = falta en `/mesa`):

| Pieza del mockup | En `/mesa` | Backend |
|---|---|---|
| Catálogo a la izquierda (Familia › Grupo › Subgrupo › Serie, D/M/T/A, con datos / faltan), buscar y traer | parcial (drawer) | `/api/v1/series` |
| Series de la Terminal en el mismo catálogo (por ticker) | ✗ | `terminal.puente` |
| Lienzo de N gráficos con modos (tiempo, dispersión, distribución, 3D, árbol) y **capas** (tipo, eje, color, estilo, visible) | ✗ | — (frontend) |
| **Transformaciones como chips** en cada capa, que se sacan con ✕ | ✗ | `metodos/recetas.py` |
| Deshacer / rehacer | ✗ | — |
| **Fichas** seleccionables con alias y receta | ✗ (hay «series del trabajo») | Mis series |
| **Herramientas por verbo** a la derecha: arrastrar a ficha o gráfico, formulario de parámetros | parcial (pestaña Métodos aparte) | `/api/v1/metodos`, `/api/v1/herramienta` |
| Tests, transformaciones, modelos, ML, regímenes, clusters… los 102 métodos | ✓ como catálogo | ✓ |
| **Registro de resultados** (corridas, detalle, salidas → fichas, 📌 al proyecto) | ✗ | Mis resultados |
| Tablas vivas (filtrar, agrupar, graficar, guardar) | ✓ | ✓ |
| **Ecuaciones libres** (`objetivo ~ fórmula`, `nombre = fórmula`) | ✗ | falta |
| **Código Python** restringido → fichas con receta | ✗ en pantalla | `/api/v1/codigo/evaluar` |
| **Linaje** + **paquete reproducible** (CSV con huella, `receta.py`, `verificar.py`) | ✗ | falta |
| **Proyectos de la 1.0** (9, de un clic) | ✗ | métodos ✓ |
| **Proyecto** (tablero de figuras con su receta) | ✗ | proyectos ✓ |
| **Documento** (borrador con figuras numeradas y anexo de datos automático) | ✗ | falta |
| **Bandeja** (soltar desde cualquier lado; arrastrar a gráfico, ficha, herramienta o ecuación) | ✗ | paso 3 |

**Reparto de trabajo entre las dos cuentas de Claude (18/11), para no pisarse:**
- Cuenta de La Cueva (rama `claude/mesa-compartida-mcp`): el **servidor** de la bandeja, el tablero
  y el Documento (`cueva/sesiones/bandeja.py`, `cueva/api/mesa_compartida.py`) y el **MCP**.
- Cuenta de la Terminal: la **pantalla** de la Mesa en `/mesa`, portada del mockup «La Cueva» y
  conectada a esa API (no reimplementa el guardado de la bandeja ni del documento).
- **Hace falta el HTML del mockup «La Cueva» en el repo** (`docs/mockup/la-cueva.html`): hoy solo
  existe como artifact y es la referencia de la pantalla. Lo sube la cuenta que lo armó.

**Portada hecha (2026-11-18):** el mockup «La Cueva» (bajado como `la-cueva.html`, que NO se
versiona porque trae datos privados) se convierte con `scripts/mesa_desde_mockup.py` en
`web/cueva/index.html`, servido en `/` (Inicio) y `/mesa` (Investigación · Proyecto · Documento).
Todo lo de la tabla de arriba anda como en el mockup, en el navegador. Los datos ya no van
embebidos: `GET /api/v1/mesa/catalogo.js` los arma en vivo (`cueva/datos/catalogo_mesa.py`, mismo
formato `CAT` y mismos ids) con data/series + la Terminal (`terminal.puente.series_mesa`, con 68
series precargadas y el resto del universo como «terminal»). Colores de `tokens.css`. La portada
de lectura pasó a `/portada` y la Mesa anterior (Explorar · Métodos) a `/mesa/anterior`.
Para cambiar la pantalla: editar `web/cueva/index.html` (el mockup ya no es la fuente).

**Métodos del servidor en la Mesa (2026-11-18), HECHO:** `web/cueva/metodos_servidor.js` suma los
102 métodos de `GET /api/v1/metodos` a la caja de herramientas, cada uno bajo su verbo (reemplaza
las punteadas que ya existen). Formulario con sus parámetros; las fichas van con sus DATOS a
`POST /api/v1/mesa/metodo` (`cueva/api/mesa.py`), que las registra como series efímeras `m:<huella>`
(`cueva/datos/series.registrar_efimera`, las ven métodos nuevos y herramientas viejas) y devuelve
el resultado, que la Mesa pasa al registro (métricas, gráficos `RUNVIS.srv`, tablas, notas, series
de salida). Siguen punteadas: Mis series, deflactar, empalme y N-BEATS/TFT.

**Terminal a pedido (2026-11-18), HECHO:** `web/cueva/terminal_a_pedido.js` + `GET /api/v1/mesa/serie/{id}`:
las filas «terminal» del catálogo (todo el universo por ticker, la macro de FRED, los balances
`<TICKER>_<variable>_T`) se tocan y se traen; el buscador «Traer» también las encuentra. Quedan
como fichas comunes (gráficos, transformaciones, los 102 métodos).

**Bandeja Terminal → Mesa (18/11, hecho):** la bandeja es UNA, la del servidor (`/api/v1/bandeja`).
En la Terminal, la barra de La Cueva carga `web/estilo/bandeja.js`: botón «Bandeja · n» y, en la
ficha de un activo (`/terminal/activo/<T>`) o de una serie macro (`/terminal/macro/<id>`), «⇩ T a la
bandeja» + menú con el precio y cada variable de balances (`GET /api/v1/mesa/activo/{ticker}`). En la
Mesa, `web/cueva/bandeja_servidor.js` sincroniza `st.bandeja` con el servidor en los dos sentidos
(cada 4 s y al volver a la pestaña) y trae a pedido los datos de lo que llegó. Sin bandeja de ejemplo.

**Falta para cerrar la Mesa:** (3) tablero y documento contra la API de la otra cuenta (hoy en el navegador);
(4) partir el JS de la página en módulos.

Orden acordado: después del paso 1, **portar la Mesa del mockup a `/mesa` con datos reales**, y la
bandeja se construye junto con ella (paso 3), porque la Mesa es su destino principal.

**Siguen:** paso 2 (almacén único), paso 3 (bandeja en Terminal y Mesa), paso 4 (bandeja en la
Línea de tiempo); después Inicio con módulos.

## 2. El Inicio

Boceto original de Martín: una credencial arriba a la izquierda, el título y el saludo al
centro, el selector de pestañas debajo, módulos libres en el resto y una barra de precios abajo.

- **Fijo (nadie lo puede sacar ni mover):** el título («La Cueva» + «Bienvenido, …» + avatar),
  el selector de pestañas y la **credencial** (nombre, código de identificación, institución,
  rol; editable con un lápiz).
- **Libre:** cada usuario arma su Inicio con módulos que agrega, mueve, ensancha (1, 2 o 3
  columnas), configura y quita. Lo que Martín listó: **cuadros, gráficos, series, accesos
  rápidos, estadísticas (de sus proyectos), carruseles de precios** y escritura libre.
- Módulos que ya existen en el mockup: carrusel de precios, gráfico (rango 1A/5A/10A/Todo),
  serie (KPI con sparkline), cuadro, movimientos del día de la Terminal, accesos rápidos,
  «Mis proyectos» (corridas, figuras, fichas, palabras del documento) y nota.
- **Todo módulo usa las mismas series que Investigación** (Cueva + Terminal) y todo lo que
  muestra se puede arrastrar a la bandeja.
- **Pendiente de decidir:** qué módulos se habilitan en la v1 y cuáles quedan para después, y
  la infraestructura para que cada usuario tenga su Inicio (§5.4).

**Ojo:** la Terminal ya tiene su propia pantalla «Inicio» (`terminal/web/src/paginas/Inicio.tsx`:
listas con precio y variación, tarjetas de riesgo con semáforo por percentil). Esas piezas no
compiten con el Inicio de La Cueva: son **candidatas naturales a módulos** de ese Inicio.

## 3. Dónde está cada cosa

| Qué | Dónde | Notas |
|---|---|---|
| Código de La Cueva | este repo, `main` | FastAPI + JS en módulos ES sin build; tokens en `web/estilo/tokens.css` |
| Código de la Terminal | repo **privado** `martingomezpizarro/INVESTIGACI-N-ACTIVOS`, carpeta `terminal/` | FastAPI + DuckDB + React/Vite/TypeScript + lightweight-charts. Ver `terminal/README.md` |
| Datos de la Terminal | `terminal/datos/terminal.duckdb`, **solo en la compu de Martín** (gitignorado) | Se arma con `Terminal - actualizar datos.bat`; la primera vez tarda ~15 min y baja ~426 activos |
| **Mockup actual («La Cueva»)** | artifact en claude.ai: https://claude.ai/artifact/HYY2s3Va7JVq7NyUePi85c | **No está en ningún repo.** Tiene el Inicio, la navegación nueva, Investigación, Proyecto, Documento, Terminal y la bandeja, con datos reales embebidos (13 series de la Cueva + 68 de la Terminal). Martín lo comparte por email desde «Share» |
| Especificación de la 1.0 | Claude Doc: https://claude.ai/artifact/6ZUv9WJZcZ6UjypvwzUJcc | Criterios de aceptación (9 proyectos), Python completo, linaje reproducible, catálogos de gráficos y modelos. Los Claude Docs no se comparten fuera de la cuenta: Martín tiene que exportarlo (Markdown o PDF) |
| Catálogo de 102 métodos | rama **`claude/gifted-wright-8r5bj0`** (sin mergear) | 54 archivos, ~20 000 líneas: `web/mesa/metodos.js`, `tabla_viva.js`, código Python con lista blanca de AST, `tests/test_metodos.py`. Decidir si se mergea (§5.6) |
| Mockups anteriores | artifacts «Mesa interactiva», «Mesa de Trabajo — Cueva», «La Cueva del Economista» | Historia de diseño; el mockup actual los reemplaza |
| Corpus del RAG (PDFs) | solo en la compu de Martín | No se versiona (derechos de autor) |

## 4. Qué tiene hoy el mockup

- **Barra superior:** La Cueva · Inicio · Línea de tiempo ↗ · Mesa de trabajo (Investigación |
  Proyecto | Documento) · Terminal.
- **Inicio:** como en §2. En el mockup se guarda en `localStorage` (clave `cueva_inicio_v1`)
  como `{cred, w: [{id, t: tipo, a: ancho 1-3, c: config}]}`: ese es el modelo de datos
  propuesto para guardarlo por usuario.
- **Investigación:** catálogo en árbol (Familia › Grupo › Subgrupo › Serie), varios gráficos con
  capas mezclables, fichas con receta, herramientas por verbo, registro de corridas, ecuaciones
  libres con parámetros estimados, código Python restringido, linaje y **paquete reproducible**
  (zip con CSVs, `receta.py`, `verificar.py`). Los 9 proyectos de la 1.0 corren en el navegador.
- **Terminal:** ficha por activo con los datos del DuckDB.
- **Bandeja flotante:** en todas las vistas; se arrastra desde el Inicio, el catálogo, los
  gráficos y el registro.
- La Línea de tiempo abre el sitio publicado en otra pestaña (todavía no comparte la bandeja).

## 5. Decisiones abiertas para la unificación

1. **Un frontend o dos.** La Cueva es JS con módulos ES sin build; la Terminal es React +
   TypeScript con Vite. Opciones: (a) portar la Terminal a módulos ES, (b) pasar La Cueva a
   React, (c) convivir: un cascarón común (barra, bandeja, Inicio) y cada pestaña con su stack.
   Lo que no se negocia: **un solo `tokens.css`** y **una sola bandeja**.
2. **Un backend o dos.** Los dos son FastAPI. Lo natural es montar la API de la Terminal como
   router dentro de `cueva/api/` (o como app montada) y no tener dos servidores.
3. **Series de mercado dentro del catálogo.** Hoy `data/series/` es la única fuente de verdad
   de las series curadas (CSV con procedencia, `docs/DATOS.md`). Los precios de la Terminal se
   actualizan a diario desde Yahoo, Data912 y el BCRA: no entran bien como CSV fijos.
   Propuesta: dos tipos de serie con **el mismo esquema de ID** y la misma bandeja:
   **curadas** (CSV, como hoy) y **de mercado** (por ejemplo `mkt_GGAL.BA_close`), que se
   leen del DuckDB o se bajan a pedido y llevan su procedencia en el linaje.
4. **Inicio por usuario.** Plan: visitante = Inicio por defecto en su navegador; registrado =
   su lista de módulos en la cuenta. Depende de la autenticación, que sigue pendiente (pendientes de
   la fase 4 en `CLAUDE.md`).
5. **Bandeja compartida entre pestañas.** Como la Línea de tiempo abre aparte, la bandeja tiene
   que sincronizarse entre pestañas del navegador (`BroadcastChannel` o el evento `storage` de
   `localStorage`) y, para usuarios registrados, guardarse en la cuenta.
6. **Rama `claude/gifted-wright-8r5bj0`.** Tiene el catálogo de métodos y la tabla viva que el
   mockup ya usa. Revisarla y mergearla (o rescatar lo útil) antes de construir Investigación.
7. **Licencias de los datos de mercado.** Este repo es **público** y el sitio también. Antes
   de publicar precios de Yahoo o Data912, revisar si se pueden redistribuir (registro de
   fuentes en `cueva/fuentes/registro.json`). El repo de la Terminal es privado.
8. **Qué módulos del Inicio entran en la v1** (§2).

## 6. Orden sugerido

1. Leer este documento, `CLAUDE.md`, `docs/PLATAFORMA.md` y `terminal/README.md` del otro repo.
2. Abrir el mockup y recorrer las cuatro pestañas y la bandeja.
3. Resolver §5.1 a §5.3 con Martín (stack, backend y modelo de series de mercado): todo lo
   demás depende de eso.
4. Construir el cascarón común: barra superior, rutas, `tokens.css` y bandeja global.
5. Montar la Terminal como pestaña.
6. Construir el Inicio con 4 o 5 módulos.
7. Adaptar la Línea de tiempo (abrir aparte + bandeja sincronizada).
8. Mergear o rescatar la rama de métodos y seguir con Investigación.

## 7. Reglas de trabajo

- Español en código, docs y mensajes de commit. Convenciones y Definition of Done en `CLAUDE.md`.
- Martín dedica unas 2 horas por semana; la fecha deseada de lanzamiento es el 31/12/2026, y la
  auditoría del 27/10 (`auditorias/AUDITORIA_CIERRE_2026-10-27.md` en el proyecto de Claude)
  dice que con ese ritmo no alcanza para lanzar con cuentas de usuario.
- Antes de cambios grandes o destructivos, confirmar con Martín.
