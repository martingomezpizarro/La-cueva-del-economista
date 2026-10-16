# Auditoría de organización y plan de reorganización — agosto 2026

> **Qué es este documento.** Una revisión del repo contra los objetivos declarados de la
> plataforma (dos módulos: Línea de Tiempo y Mesa de Trabajo; cuatro fuentes en el backend:
> datos históricos, bibliografía, stack econométrico, agentes). No propone reescribir lo que
> funciona: identifica los **cinco desajustes estructurales** entre lo que la plataforma quiere
> ser y lo que el código modela hoy, y ordena el trabajo para cerrarlos.
>
> Complementa —no reemplaza— a `docs/PROPUESTA_ARQUITECTURA.md`, cuyo roadmap (fases 0-3) ya
> se ejecutó. Aquello ordenó el **código**; esto ordena el **dominio**.

Fecha: 2026-08-23 · Estado verificado: 91 tests en verde, `ruff check` limpio.

---

## 0. Lo que está sólido y no hay que tocar

Antes de la crítica, el inventario de lo que ya es una buena base:

| Activo | Evidencia |
|---|---|
| **Capas respetadas** | `cueva/econometria/` y `cueva/datos/` no importan `llm`, `agentes` ni `api` (verificado por grep). La dirección de dependencias declarada se cumple de verdad. |
| **Red de seguridad real** | 91 tests offline + CI sin claves ni corpus. Series sintéticas con semilla fija: los tests econométricos verifican propiedades conocidas, no capturan outputs. |
| **Un solo camino a los LLM** | `cueva/llm/gateway.py` con backoff y contador de tokens. Nada más habla con los SDKs. |
| **Agentes como dato** | `knowledge-base/skills/*.md` define los 12 agentes; `pipelines.py` define el guion. Editar markdown cambia el comportamiento. |
| **Taxonomía con fuente única** | `cueva/datos/catalogo.json` (9 familias, 465 series hoja) alimenta a la vez `series.py` y el árbol del explorador. |
| **Tool-use acotado** | Lista blanca por skill ∩ registro, tope por turno, argumentos saneados, cada ejecución publicada como evidencia. |

Todo lo que sigue asume que esto se conserva.

---

## 1. Los cinco desajustes

### D1 — La plataforma tiene dos productos y el repo modela uno

El objetivo 2 (**línea de tiempo económica y social de Argentina desde 1880**) no tiene
ninguna base en el repo: no existen entidades de evento, presidencia, ministro ni autoridad
monetaria, y no hay un solo archivo de datos históricos anterior a 1970.

Medición sobre las 122 fuentes reales (`data/Variables Finales`):

| Década en que arranca la serie | Archivos |
|---|---|
| 1970 | 1 |
| 1990 | 17 |
| 2000 | **84** |
| 2010 | 3 |

La serie más antigua del catálogo empieza en **1970** y el **84 % arranca en 2000**. Entre 1880
y 1970 la cobertura es **cero**. Lo único parecido a historia son cuatro dummies
(`dummy_gob`, `dummy_elec`, `dummy_cepo`, `dummy_covid`) y `defaults_history.csv`.

> **Consecuencia**: el módulo Línea de Tiempo no es "una pantalla que falta". Es un **dataset
> que falta**, y su construcción (fuentes históricas + cronología curada) es un frente de
> trabajo propio, independiente del código.

### D2 — Los datos no pertenecen al proyecto, y no tienen procedencia

**No pertenecen**: `cueva/config.py:84-95` busca la carpeta del Trabajo Final probando cinco
rutas candidatas (`CUEVA_TRABAJO_FINAL` → `cueva.local.toml` → tres rutas relativas). Los CSV
se leen **in situ** desde `…\ECONOMICS\TRABAJO FINAL\Trabajo\data\`, nunca se copian. Si esa
carpeta se mueve o se renombra, el catálogo queda vacío y `payload()` devuelve `{}`.
La carpeta origen, además, es un espacio de trabajo personal: contiene `_archivo/scratch/`,
`node_modules/`, backups de corridas y 500 archivos `.dat` de bases de bonos.

**No tienen procedencia**: `SerieInfo` (`cueva/datos/series.py:36-53`) y los items del catálogo
tienen `id, label, unit, freq, file, dateCol, valCol`. No tienen —en ningún lado— **organismo
emisor, URL de origen, fecha de descarga, método de cálculo, base del índice, ajuste
estacional, política de revisiones, vigencia ni licencia**. El campo `origen` es la constante
literal `"Trabajo Final"`.

> **Consecuencia**: el caso de uso estrella —producir un trabajo académico citable— es
> imposible hoy. Un informe no puede decir de dónde salió una serie, y el copiloto no sabe qué
> mide lo que está analizando.

**Bug verificado de paso**: `series.py:188` lee `pd.read_csv(path, nrows=400)` y de ese
encabezado calcula `n`, `desde` y `hasta` (`:230`, `:243-244`). Para toda serie de más de 400
filas —todas las diarias— **el catálogo reporta cobertura temporal y tamaño falsos**, aunque
`cargar()` sí lea el archivo completo.

### D3 — El modelo de datos no soporta un "proyecto de investigación"

El módulo Laboratorio que describís (hipótesis, objetivos, resultados, informe) necesita
relaciones que el modelo actual no tiene:

- `Proyecto.objetivos` e `hipotesis` son `list[str]` (`cueva/agentes/modelos.py:36-37`): sin
  id, sin estado, sin evidencia asociada. No se puede expresar "H2 quedó parcialmente
  respaldada por el paso 5".
- `Pizarra.informe` es un `dict[str,str]` con **6 secciones cerradas y hardcodeadas**
  (`pizarra.py:26-33`, validadas en `api/app.py:365`): no se crean, renombran ni reordenan.
- **Nada referencia a nada**: `Hallazgo` no apunta a una hipótesis ni a una sección; un
  `estudio` no apunta a un hallazgo; `Mensaje.herramientas` guarda **copias** de resultados en
  vez de referenciar `estudios[].id`.
- No existe entidad de referencia bibliográfica: las citas son `list[str]` de texto libre.

> **Consecuencia**: el informe no puede rastrear de qué evidencia sale cada afirmación, que es
> justamente lo que diferencia a esta plataforma de un Word con gráficos al lado.

### D4 — Los agentes están ciegos a lo que el usuario hace

El prompt de un agente (`agentes.py:104-211`) recibe: proyecto, fase, últimos 8 mensajes,
hallazgos, evidencia **de la fase actual**, y pasajes del RAG. Lo que **no** recibe:

| No ve | Dónde está | Por qué importa |
|---|---|---|
| `piz.estudios` | `pizarra.py` | Los pasos que el usuario corrió en el banco de trabajo son invisibles para la mesa. |
| `piz.informe`, `piz.notas` | `pizarra.py` | El único método que los inyecta es `orquestador.revisar()` (`:164-176`) — **y no está expuesto en ninguna ruta de la API**. |
| El catálogo de series | `datos/series.py` | Ve los `id` de las series elegidas, no qué miden, en qué unidad ni con qué cobertura. |

Además, el plan es estático: las 6 fases y qué herramienta corre en cada una están cableadas
en `orquestador._correr_herramientas` (`:120-153`) con cortes mágicos (`series[:6]`,
`series[:4]`, `if len(series)>=2 → var`).

> **Consecuencia**: hoy hay una *mesa que conversa*, no un *copiloto que acompaña*. La
> diferencia es exactamente este bloque de contexto.

### D5 — El frontend son dos aplicaciones pegadas por un iframe

`web/index.html` (shell, 1016 líneas) carga `web/explorador.html` (SPA, 7080 líneas) dentro de
un `<iframe>`. Se comunican por tres mensajes `postMessage` con `targetOrigin:'*'` y sin
verificar `ev.origin`.

- **Dos identidades visuales conviviendo**: el shell es gris-carbón (`#0d1117`, acento
  `#4fa8da`); la SPA es azul marino (`#0A1628`, acento `#5BA4E6`). El usuario ve la costura.
- **~5.960 líneas de JS en un solo bloque global** con ~250 funciones sin namespace; el módulo
  de animaciones *monkey-patchea* `window.switchTab` y `window.toggleSidebar`.
- **`parseCSV` está definida dos veces en el mismo archivo** (`explorador.html:2333` y `:5809`):
  la segunda pisa a la primera al cargar.
- **Econometría duplicada**: ADF, Phillips-Perron y OLS están implementados en JS
  (`explorador.html:5060-5243`) *y* existen como herramientas de servidor. Dos motores que
  pueden dar números distintos para el mismo test.
- `web/vendor/` (4,4 MB) **no está en `.gitignore`** y aparece como untracked.

---

## 2. Organización objetivo

### 2.1 Las cuatro fuentes, hechas carpetas

Tu descripción del backend se mapea casi uno a uno; lo que falta es **abrir `datos/` en dos** y
**darle un hogar a la historia**:

```
cueva/
├── datos/                    ← FUENTE 1: datos históricos
│   ├── catalogo/
│   │   ├── taxonomia.json        (ex catalogo.json: 9 familias)
│   │   └── fichas/<id>.json      ← NUEVO: procedencia por serie (D2)
│   ├── fuentes/                  ← NUEVO: un adaptador por organismo
│   │   ├── indec.py  bcra.py  mecon.py  worldbank.py  fred.py
│   │   └── manifiesto.json       (qué se bajó, cuándo, con qué hash)
│   ├── historia/                 ← NUEVO: FUENTE 1.2 (D1)
│   │   ├── cronologia.json       (eventos: fecha, tipo, descripción, fuentes)
│   │   ├── gobiernos.json        (presidencias, ministros de Economía, BCRA)
│   │   └── series_largas/        (1880→ : Ferreres, Orlando, MOxLAD, Maddison)
│   └── series.py                 (carga y panel — se mantiene)
│
├── conocimiento/             ← FUENTE 2: bibliografía
│   └── (ingesta, recuperar, fichas, biblioteca — se mantiene)
│       colecciones: corpus_econometrico | corpus_economico | usuario
│
├── econometria/              ← FUENTE 3: stack
│   ├── transformaciones.py       (partir herramientas.py, 916 líneas)
│   ├── pruebas.py                (estacionariedad, granger, arch_lm, diagnosticos)
│   ├── modelos.py                (ols, var, vecm, garch, arima)
│   ├── kalman.py
│   └── registro.py               (registro + esquemas DERIVADOS, no paralelos)
│
├── agentes/                  ← FUENTE 4
│   ├── contexto.py               ← NUEVO: arma lo que el agente ve (D4)
│   └── (skills, pipelines, orquestador, pizarra — se mantiene)
│
├── investigacion/            ← NUEVO: el dominio del Laboratorio (D3)
│   ├── modelos.py                (Hipotesis, Objetivo, Estudio, Seccion, Cita)
│   └── servicios.py              (casos de uso hoy embebidos en app.py)
│
└── api/
    └── routers/                  (partir app.py: 20 endpoints en una factory)
        explorador.py · catalogo.py · proyectos.py · mesa.py · historia.py
```

**Regla que ordena todo esto**: `datos/` deja de apuntar a una carpeta externa. Se define un
**dataset propio** (versionado o empaquetado aparte según tamaño) con series canónicas +
manifiesto; el Trabajo Final pasa a ser *una fuente de ingesta más*, no el sistema de archivos
de la plataforma.

### 2.2 Los tres contratos que faltan

Casi todos los problemas de arriba se cierran con tres tipos nuevos.

**1. `FichaDeSerie`** — el contrato de procedencia (cierra D2):

```python
@dataclass
class FichaDeSerie:
    id: str; etiqueta: str; unidad: str
    organismo: str                 # INDEC · BCRA · MECON · World Bank · Ferreres
    url_fuente: str
    metodo: str                    # cómo se construye (deflactación, empalme, base)
    cobertura: tuple[str, str]     # calculada sobre el archivo COMPLETO, no nrows=400
    frecuencia: str
    ajuste_estacional: bool
    revisiones: str                # "definitiva" | "provisoria" | "empalmada"
    descargada: str                # fecha ISO
    licencia: str
    notas: str
```

**2. `Estudio` + `Hipotesis` + `Seccion` con referencias** (cierra D3): que `Hipotesis` tenga
`id`, `estado` (`pendiente|respaldada|parcial|rechazada`) y `evidencia: list[str]` con ids de
estudios; que `Seccion` sea creable y ordenable; que `Cita` sea una entidad con `verificada:
bool` contra el corpus.

**3. `ContextoDelCopiloto`** (cierra D4): un objeto único que arma `agentes/contexto.py` y que
recibe *todo* agente, en cualquiera de los tres modos (1:1, supervisor, pipeline): fichas de
las series elegidas, estudios corridos con su veredicto, hipótesis con su estado, secciones
escritas, notas, y los pasajes del RAG. Hoy cada modo arma su propio contexto a mano y ninguno
está completo.

### 2.3 Frontend: una sola aplicación

El iframe fue la solución correcta para reusar el visualizador del Trabajo Final. Ya no lo es:
la SPA es nativa, así que la costura no compra nada y cuesta dos temas, dos escapadores de
HTML, dos motores econométricos y un canal `postMessage` frágil.

Camino recomendado, en este orden:

1. **Un solo sistema de tokens** (`web/estilo/tokens.css`) que ambos archivos importen. Barato,
   sin riesgo, elimina la costura visual de inmediato.
2. **Borrar la econometría en JS** y dejar que todo test pase por `POST /api/v1/herramienta`.
   Elimina la clase de bug "dos motores, dos números".
3. **Partir el JS en módulos ES** por pantalla (`explorar.js`, `analisis.js`, `estudio.js`,
   `tiempo.js`) con un único store de estado. Sin build: `<script type="module">` alcanza.
4. **Fusionar el shell y la SPA** cuando 1-3 estén hechos. Recién ahí el iframe sale sin dolor.

---

## 3. Deuda concreta verificada (para ir tachando)

Ordenada por daño, con archivo y línea.

| # | Problema | Ubicación |
|---|---|---|
| 1 | `n`, `desde`, `hasta` calculados sobre `nrows=400` → cobertura falsa en toda serie larga | `datos/series.py:188,230,243` |
| 2 | Sin procedencia de series (`origen` es una constante) | `datos/series.py:36-53` + `catalogo.json` |
| 3 | Hipótesis/objetivos como `list[str]`; informe de 6 secciones fijas; cero relaciones | `agentes/modelos.py:36-37`, `pizarra.py:26-33` |
| 4 | Los agentes no ven estudios ni informe; `revisar()` sí los ve pero no está en la API | `agentes/agentes.py:131-147`, `orquestador.py:164` |
| 5 | `_mesa_corriendo`: atributo fantasma sobre `Pizarra`, con race check-then-set | `api/app.py:411,419,430` |
| 6 | `except ProyectoNoEncontrado: pass` → el estudio se pierde y devuelve 200 | `api/app.py:293-296` |
| 7 | Persistencia sin escritura atómica: un corte a mitad corrompe el proyecto | `pizarra.py:226`, `sesiones/repositorio.py:91` |
| 8 | Job de subprocess (15 min, escribe CSV fuera del repo) dentro de un handler HTTP | `api/app.py:205-246` |
| 9 | `REGISTRO[...]["params"]` y `ESQUEMAS[...]` describen la misma firma dos veces | `econometria/herramientas.py:687` vs `:772` |
| 10 | Casos de uso ("promover Vista Rápida", patch por `setattr`) embebidos en handlers | `api/app.py:310-319,326-333` |
| 11 | Chats 1:1 sin contador de tokens ni transcript (la mesa sí los tiene) | `api/app.py:395` |
| 12 | `parseCSV` definida dos veces en el mismo archivo | `web/explorador.html:2333` y `:5809` |
| 13 | Econometría duplicada JS/Python (ADF, PP, OLS) | `web/explorador.html:5060-5243` |
| 14 | `postMessage` con `'*'` y sin verificar `ev.origin` | `web/index.html:408`, `explorador.html:6588` |
| 15 | `web/vendor/` (4,4 MB) sin ignorar en git | `.gitignore` |
| 16 | `kalman.py` (136 líneas) y `POST /explorador/kalman` sin tests | `econometria/kalman.py` |
| 17 | `AGENTES_IDS` hardcodea 12 ids que ya define `knowledge-base/skills/` | `agentes/modelos.py:117-130` |

---

## 4. Plan sugerido (fase 4 revisada)

El orden está elegido para que **cada paso desbloquee al siguiente**, y para que el frente de
datos (lento, manual) corra en paralelo al de código.

### Camino A — Fundaciones de datos *(desbloquea todo lo demás)*

- **A1. Ficha de procedencia.** Definir `FichaDeSerie`, escribir las fichas de las ~50 series
  que realmente se usan, y arreglar el bug de `nrows=400`. Sin esto no hay informe citable.
- **A2. Dataset propio.** Ingesta desde el Trabajo Final hacia una carpeta canónica de la
  plataforma, con manifiesto y hash. El TF pasa a ser una fuente, no el filesystem.
- **A3. Adaptadores por organismo.** Un módulo por fuente (INDEC, BCRA, MECON, World Bank,
  FRED) para que actualizar series sea un comando, no un ritual manual.

### Camino B — El proyecto de investigación *(hace real al Laboratorio)*

- **B1.** Nuevos contratos: `Hipotesis`, `Objetivo`, `Estudio` con id, `Seccion` creable,
  `Cita` verificable. Migración de esquema v2 → v3 (ya hay precedente en `repositorio.py`).
- **B2.** `agentes/contexto.py`: un solo armador de contexto para los tres modos. Cierra D4 y
  convierte la mesa en copiloto.
- **B3.** Exponer `orquestador.revisar()` en la API (existe y funciona, nadie puede llamarlo).

### Camino C — Historia *(el segundo producto)*

- **C1.** `cronologia.json` + `gobiernos.json` curados y con fuentes. Ya hay una semilla de 52
  eventos y 41 presidencias lista para revisar.
- **C2.** Series largas 1880→: Ferreres, Orlando/Della Paolera, MOxLAD, Maddison. Es un
  trabajo de investigación con empalmes documentados, no una descarga.
- **C3.** Endpoint `GET /api/v1/historia` + pantalla de línea de tiempo.

### Camino D — Higiene *(en paralelo, barato)*

- Ignorar `web/vendor/`; escritura atómica en persistencia; `_mesa_corriendo` como estado real
  con lock; el `except: pass` del estudio; tokens CSS unificados; borrar la econometría JS.

### Después (no antes)

SQLite + job queue, auth, Docker y deploy —la fase 4 original de `PROPUESTA_ARQUITECTURA.md`—
tienen sentido cuando el dominio esté bien modelado. Escalar un modelo de datos que todavía no
representa lo que la plataforma hace es multiplicar el costo de cambiarlo.

---

## 5. Lo que este documento decide y lo que deja abierto

**Decide** (salvo objeción): que `datos/` deje de apuntar a una carpeta externa; que la
procedencia de series sea un contrato de primera clase; que el proyecto de investigación tenga
entidades relacionadas; que el copiloto reciba un contexto único y completo.

**Deja abierto** (decisiones tuyas, con impacto real):

1. **Alcance de la Línea de Tiempo.** ¿Es una vista de consulta (leer historia) o también
   alimenta la Mesa (arrastrar un evento y que se convierta en dummy)? La segunda es
   claramente más valiosa y bastante más cara.
2. **Dónde viven los datos.** ¿Dataset versionado en el repo (simple, tope práctico ~100 MB),
   repo de datos aparte, o descarga por manifiesto en el primer arranque?
3. **Qué tan lejos llega el copiloto en la escritura.** ¿Redacta secciones completas, o
   propone y el humano acepta párrafo por párrafo? Cambia el modelo de datos del informe.
