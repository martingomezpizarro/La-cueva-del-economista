# Estado de la bibliografía — qué tenemos y qué falta

Actualizado al 2026-06-20. Leyenda: ✅ tenemos (en `rag/Bibliografia` o `corpus/`) ·
❌ falta (conseguir vos) · 🔗 abierto pendiente (bajar con click) · ★ ancla de la categoría.

> Para indexar lo que ya tenemos: mover/copiar a la carpeta de su categoría en `corpus/` y correr
> `python rag/ingest.py knowledge-base/corpus`. (Hoy los PDFs están en `rag/Bibliografia`.)

---

## ✅ YA TENEMOS (17 textos + lo previo)

| Texto | Categoría | Nota |
|---|---|---|
| Enders (2014), *Applied Econometric TS* | 01_fundamentos ★ | ya cargado |
| Brockwell & Davis (2016), *Intro to TS & Forecasting* | 01_fundamentos | |
| Kirchgässner, Wolters & Hassler (2013) | 01_fundamentos | |
| Harvey & Peters (1990), *Estimation… Structural TS* | 02_univariados | paper (no el libro Harvey 1989) |
| Jalles (2009), *Structural TS Models & Kalman Filter: a review* | 02_univariados | era `ssrn-1496864` |
| Chow & Lin (1971) | 03_transformaciones ★ | desagregación temporal |
| FPP3 (capítulos) | 03 / 07 / 10 | ya cargado |
| Johansen (2011), *Fractionally cointegrated VAR* | 04_multivariados | |
| Lütkepohl & Strohsal (2009), *Time-varying shock transmission SVAR* | 04_multivariados | |
| Breitung & Pesaran (2005), *Unit roots & cointegration in panels* | 04_multivariados | |
| Tsay (2010), *Analysis of Financial Time Series* | 05_volatilidad ★ | |
| Yukai Yang (2012), *Modelling nonlinear Vector TS* | 06_quiebres_nolineal | |
| Angrist & Pischke (2008), *Mostly Harmless Econometrics* | 08_causal | |
| Athey & Imbens (2017), *State of Applied Econometrics* | 08_causal ★ | |
| **Sala-i-Martin (1997), *Two Million Regressions*** | 09_robustez ★ | **bajado hoy → `corpus/09_robustez/`** |
| **Simonsohn et al., *Specification Curve*** | 09_robustez | **bajado hoy → `corpus/09_robustez/`** |
| Chan & Tobias (2020), *Bayesian Econometric Methods* | 11_bayesianas | paper (no el libro completo) |
| West & Harrison (1997), *Bayesian Forecasting & Dynamic Models* | 11_bayesianas ★ | |
| Marcellino & Pfarrhofer (2024), *Bayesian nonparametric* | 11_bayesianas | frontera |
| código Python (repo riesgo país) | 10_codigo_python | ya cargado |

**Cobertura:** fuerte en fundamentos, volatilidad, bayesianas, causal y robustez. Suficiente para
empezar a probar.

---

## 🔗 Abiertos pendientes (bajar con click cuando quieras — links verificados)
*No los traje al RAG (o eran muy grandes para extraer como archivo, o son libros online).*

- FAIR Principles (Nature, abierto): `nature.com/articles/sdata201618`
- Mullainathan & Spiess (2017), JEP: `aeaweb.org/articles?id=10.1257/jep.31.2.87`
- N-BEATS: `arxiv.org/abs/1905.10437`
- Survey DL/Foundation Models (2024): `arxiv.org/abs/2401.13912`
- FPP3 completo (online, sin PDF único): `otexts.com/fpp3`
- Cunningham — The Mixtape (online): `mixtape.scunning.com`
- Huntington-Klein — The Effect (online): `theeffectbook.net`
- Hansen (2007), model averaging: `ssc.wisc.edu/~bhansen/papers/`
- Croushore & Stark — Real-Time Data (Philly Fed): `philadelphiafed.org/surveys-and-data/real-time-data-research`

---

## ❌ Faltan — conseguir vos (sin versión abierta / Google Books no se baja)

**Libros (biblioteca UNC / editorial / acceso institucional):**
- ★ Hamilton (1994), *Time Series Analysis* — 01_fundamentos
- ★ Lütkepohl (2005), *New Introduction to Multiple TS Analysis* — 04_multivariados
- Johansen (1995), *Likelihood-Based Inference in Cointegrated VAR* — 04_multivariados
- ★ Box, Jenkins, Reinsel & Ljung (2015) — 02_univariados
- Durbin & Koopman (2012), *State Space Methods* — 02_univariados
- Harvey (1989), *Structural TS Models & Kalman Filter* (libro) — 02_univariados
- Francq & Zakoïan (2019), *GARCH Models* — 05_volatilidad
- Maddala & Kim (1998), *Unit Roots, Cointegration & Structural Change* — 06/07
- Teräsvirta, Tjøstheim & Granger (2010), *Modelling Nonlinear Economic TS* — 06_quiebres
- Imbens & Rubin (2015), *Causal Inference…* — 08_causal

**Papers tras paywall (buscar working paper si querés):**
- Leamer (1983), *Let's take the con out of econometrics* — 09_robustez
- Steel (2020), *Model averaging…* (JEL) — 09_robustez

> Nota: los 8 de **Google Books** (Durbin-Koopman, Harvey 1989, Box-Jenkins, Lütkepohl 2005,
> Johansen 1995, Francq-Zakoïan, Maddala-Kim, Teräsvirta) **no se pueden descargar de ahí** (son
> vistas previas). Vía legal: biblioteca/compra/acceso institucional.

---

## 🤖 Automatización de los abiertos (2026-09-13)

Los de acceso abierto ya no se bajan a mano: están en `fuentes_abiertas.tsv` y se traen con

```bash
python scripts/bajar_abiertos.py          # baja lo que falte a su carpeta de corpus/
python scripts/bajar_abiertos.py --listar # ver el plan sin descargar
```

Usa solo biblioteca estándar (no necesita el venv) y valida que lo bajado sea un PDF real, no una
página de error. Para sumar una fuente: una línea nueva en el TSV (`carpeta⇥archivo⇥url`).

**Importante:** correlo desde tu terminal de Windows. Ni el contenedor de Claude ni la VM del
puente tienen salida a arxiv.org, nature.com ni webs de autor — la política de egress las bloquea.

### Cargado en el manifiesto (7)
N-BEATS · Survey arquitecturas TS 2024 · FAIR Principles · Mullainathan & Spiess (2017) ·
**Leamer (2010), _Tantalus on the Road to Asymptopia_** (JEP, abierto — reemplaza al Leamer 1983
que estaba tras paywall) · **Nobel lecture de Granger (2003)** sobre cointegración ·
**Nobel lecture de Engle (2003)** sobre ARCH. Las dos Nobel lectures son abiertas, citables y
cubren el hilo conductor de `04_multivariados` y `05_volatilidad` en primera persona del autor.

### Sobre Academia.edu — no cambia la lista de ❌
Academia.edu es un repositorio de **papers y working papers subidos por sus propios autores**, no
de manuales. Los PDFs de Hamilton (1994), Lütkepohl (2005), Box-Jenkins, Durbin-Koopman, etc. que
aparecen ahí son subidas no autorizadas de libros comerciales: la vía sigue siendo biblioteca UNC,
editorial o compra, igual que decía la nota de Google Books.

Donde Academia.edu **sí** rinde es en la capa aplicada: determinantes del riesgo país emergente,
EMBI, y aplicaciones de VAR/cointegración a Argentina y LatAm — justo el `🆓 Argentina / riesgo
país` de `GUIA_CARGA.md`. Esa búsqueda queda pendiente.

### Sustitutos abiertos aún por verificar
- Koop & Korobilis (2010), monografía bayesiana → working paper RCEA en RePEc (`rim/rimwps/47_09`).
- Lütkepohl (2005) → sus working papers y capítulos de survey sobre SVAR (EUI / FU Berlin) cubren
  buena parte del libro y son de descarga libre.
- Johansen (1995) → discussion papers de la Univ. de Copenhague; material de cátedra de Juselius
  sobre el CVAR.
- Bruce Hansen, _Econometrics_: **ya no es gratis** (lo publicó Princeton en 2022). Su web solo
  ofrece datos y código, no el libro.

---

## ✅ Cosecha del 2026-09-13 — el corpus pasó de 15 a 41 PDFs

**Casi todo estaba en `Desktop\MARTIN\ECONOMICS`.** No hacía falta buscarlo afuera.

### ⭐ Enders resuelto
`ECONOMETRIA/Libros/Enders Walter (2015) LIBRO E.pdf` → `01_fundamentos/`. Era el pendiente
explícito de `CLAUDE.md` ("Enders NO está en el corpus") y de la fase 4 del roadmap. 498 páginas,
texto extraíble. Tachar de los pendientes.

### Curso de Econometría III de la UNC (Giuliodori & Rodriguez, 2025) — 9 PDFs
Es el material más alineado que hay: en español, exacto, y con la misma secuencia con la que
estudiaste. Renombrados **por contenido**, no por fecha de clase (el retrieval usa el nombre):
ACF/PACF y ARMA · predicción ARMA/SARMA · ARCH-GARCH · VAR con retardos distribuidos y MCO vs. SUR ·
cointegración de Johansen · test de Engle-Granger · función impulso-respuesta · random walk ·
cuadro resumen de procesos estocásticos. Se omitió "clases 6 y 7 de octubre" (58 p) porque es
subconjunto del de 13 de octubre (71 p) — duplicar contenido degrada el retrieval.

### Otros libros y papers de tu carpeta
- `01_fundamentos`: Creel, *Econometrics* (licencia abierta) · Moneta Pizarro (2021), *Econometría*
  (UNC, español) · Teoría Asintótica y Métodos de Estimación (Estadística III)
- `02_univariados`: Estadística 2 — S12 Series de tiempo (65 p)
- `03_transformaciones`: **Hylleberg et al. (1990)** — el paper HEGY de integración estacional
- `08_causal`: **Abadie & Gardeazabal (2003)** — el paper fundacional del control sintético ·
  Harasztosi & Lindner (2019)
- `09_robustez`: **Ciccone & Jarociński (2010)** — model averaging aplicado a determinantes del
  crecimiento, hermana directa de Sala-i-Martin · Barro (1996)
- **`13_riesgo_pais_aplicado` (carpeta nueva)** — el "diferencial" que pide `GUIA_CARGA.md`:
  Escudé (2008) ARGEM DSGE Argentina · BCRA (2020) péndulo de regímenes monetarios en AL ·
  Kórab, Fidrmuc & Dibooglu (2023) y Marthinsen & Gordon (2020) sobre dolarización ·
  Vera (2013) inflación estructural · Carrera, Ibarlucía & Sardi (2012) flujos de capitales y
  commodities (bajado de Academia.edu; el original está en EconStor)

### ⚠️ Antes de indexar
`03_transformaciones/Chow & Lin (1971).pdf` **está escaneado sin OCR** — 15 páginas y 0 texto
extraíble. Hoy ocupa lugar en el índice sin aportar nada. Pasarle OCR o sacarlo.
Los otros 40 tienen texto OK.

### Academia.edu: funciona pero a los tirones
El botón que sirve es **"Download PDF"** dentro de la página del paper — el link "Download" de los
resultados de búsqueda no hace nada. De 4 intentos bajó 1. Además la búsqueda devuelve el mismo
paper 5 veces subido por distintos usuarios: hay que elegir una copia o el RAG se llena de
duplicados. Pendiente: Oreiro & Adler (Uruguay), Barraez (2015) y Alonso García (contagio).

### 🔎 Hallazgo para la línea de datos, no para el RAG
`HISTORIA ECONÓMICA/.../Gómez, M. (2018) Avatares de un sistema monetario. La Primera Caja de
Conversión argentina... (1890-1935)` **y su base de datos** (`Downloads/files.zip` →
`Gomez_2018_Avatares_base_de_datos.xlsx` + guía). `docs/FUENTES_SERIES_LARGAS.md` busca
justamente la Caja de Conversión 1901-1935 y la daba por "transcripción manual". Acá hay una
serie ya reconstruida y documentada. No va al corpus econométrico: va a la capa de datos.
