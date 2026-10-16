# Bibliografía por categoría — La Cueva del Economista

Bibliografía maestra **organizada por las categorías del equipo de agentes**: cada categoría
es el sector de la biblioteca al que se ancla un especialista. Prioriza la **completitud**
(mejor que sobre a que falte) y combina el canon clásico con la frontera (2024-2026).

**Leyenda:** 📘 libro · 📄 paper · 🧰 software/manual · 🆓 acceso abierto · 🔒 pago/biblioteca
· `[C]` clásico · `[M]` moderno (2010-2023) · `[F]` frontera (2024-2026)
· **★** = texto más completo/de referencia de la categoría (el "ancla").

> Estado de carga: marcá con ✅ lo que ya está en `corpus/`. Lo 🔒 conseguilo por biblioteca
> UNC / editorial; lo 🆓 casi todo está en arXiv, otexts, o los repos de los autores.
> Esta lista **complementa y reemplaza** a `BIBLIOGRAFIA.md` (la vieja queda como respaldo).

---

## 00 · Datos y medición  → 🧰 Curador de datos
*Calidad, procedencia, reproducibilidad, revisiones (vintages), metadatos.*

- ★ `[M]` **Croushore, D. & Stark, T. (2001).** *A real-time data set for macroeconomists.*
  *J. Econometrics* 105(1). 🆓 — fundacional sobre **vintages y revisiones**: por qué importa
  *cuándo* bajaste el dato. Base del Real-Time Data Set de la Fed de Filadelfia.
- `[M]` **Croushore, D. (2011).** *Frontiers of real-time data analysis.* *J. Economic Literature* 49(1). 🆓 — survey de datos en tiempo real y su efecto en pronóstico/política.
- `[M]` **Wilkinson, M. et al. (2016).** *The FAIR Guiding Principles for scientific data management.* *Scientific Data*. 🆓 — el estándar **FAIR** (Findable, Accessible, Interoperable, Reusable).
- 🧰 **SDMX (Statistical Data and Metadata eXchange)** — sdmx.org. 🆓 — el estándar de metadatos que usan BCRA, INDEC, FMI, Eurostat. Referencia para diseñar la ficha de series.
- 🧰 **AEA Data and Code Availability Policy** — aeaweb.org/journals/data. 🆓 — qué exige hoy la profesión para que un resultado sea **reproducible** (datos + código + método).
- `[M]` **Gentzkow, M. & Shapiro, J. (2014).** *Code and Data for the Social Sciences: A Practitioner's Guide.* 🆓 — guía práctica de organización de datos/código en investigación económica.
- `[C]` **Morgenstern, O. (1963).** *On the Accuracy of Economic Observations.* Princeton UP. 🔒 — clásico sobre **error de medición** en datos económicos.
- 🇦🇷 **Nota país:** documentar el período de **intervención del INDEC (2007-2015)** como bandera de veracidad para IPC/PBI. Ver informes de la cátedra y prensa técnica de la época.

---

## 01 · Fundamentos  → 📚 base compartida (varios especialistas)
*Estacionariedad, procesos estocásticos, el marco general de series de tiempo.*

- ★ `[C]` **Hamilton, J. (1994).** *Time Series Analysis.* Princeton UP. 🔒 — la referencia técnica "biblia".
- ★ `[C]` **Enders, W. (2014).** *Applied Econometric Time Series*, 4ª ed. Wiley. 🔒 ✅ — el más aplicado y didáctico.
- `[C]` **Brockwell, P. & Davis, R. (2016).** *Introduction to Time Series and Forecasting*, 3ª ed. Springer. 🔒 — base estadística rigurosa.
- `[C]` **Shumway, R. & Stoffer, D. (2017).** *Time Series Analysis and Its Applications* (con R), 4ª ed. Springer. 🆓 (versión EZ en la web del autor) — muy usado, incluye state space.
- `[C]` **Kirchgässner, Wolters & Hassler (2013).** *Introduction to Modern Time Series Analysis.* Springer. 🔒 — accesible, orientado a economía.

---

## 02 · Univariados  → 📚 base compartida
*ARIMA, memoria larga, modelos de espacio de estados univariados.*

- ★ `[C]` **Box, Jenkins, Reinsel & Ljung (2015).** *Time Series Analysis: Forecasting and Control*, 5ª ed. Wiley. 🔒 — el origen de ARIMA.
- `[C]` **Harvey, A. (1989).** *Forecasting, Structural Time Series Models and the Kalman Filter.* Cambridge UP. 🔒 — modelos estructurales y Kalman (clave para tus interpolaciones).
- `[C]` **Durbin, J. & Koopman, S. (2012).** *Time Series Analysis by State Space Methods*, 2ª ed. Oxford UP. 🔒 — la referencia de espacio de estados.
- `[C]` **Beran, J. (1994).** *Statistics for Long-Memory Processes.* Chapman & Hall. 🔒 — memoria larga / ARFIMA.

---

## 03 · Transformaciones y frecuencia  → 🔧 Especialista en transformaciones
*Estacionarizar, deflactar, desestacionalizar, cambiar de frecuencia (Kalman vs alternativas).*

- ★ `[M]` **Hyndman, R. & Athanasopoulos, G. (2021).** *Forecasting: Principles and Practice (FPP3)*, 3ª ed. 🆓 **otexts.com/fpp3** ✅ — transformaciones, estacionariedad y descomposición, gratis y moderno.
- `[C]` **Box, G. & Cox, D. (1964).** *An analysis of transformations.* *JRSS-B*. 🔒 — transformaciones de potencia (estabilizar varianza).
- `[C]` **Cleveland et al. (1990).** *STL: A Seasonal-Trend decomposition procedure based on Loess.* 🆓 — desestacionalización STL.
- 🧰 **X-13ARIMA-SEATS** (US Census Bureau). 🆓 — el estándar de **ajuste estacional** oficial.
- **Cambio de frecuencia / interpolación temporal (clave para tu proyecto):**
  - ★ `[C]` **Chow, G. & Lin, A. (1971).** *Best linear unbiased interpolation, distribution, and extrapolation of time series by related series.* *REStat*. 🔒 — el método clásico de **desagregación temporal** con indicador.
  - `[C]` **Denton, F. (1971).** *Adjustment of monthly or quarterly series to annual totals.* *JASA*. 🔒 — benchmarking Denton.
  - `[C]` **Fernández, R. (1981)** y **Litterman, R. (1983).** variantes de Chow-Lin. 🔒
  - `[M]` **Sax, C. & Steiner, P. (2013).** *Temporal disaggregation of time series* (paquete `tempdisagg`, R). 🆓 — implementación práctica de todo lo anterior.
  - `[C]` **Harvey & state space** (ver 02): el **filtro de Kalman** como marco general de interpolación/suavizado (lo que usaste).

---

## 04 · Multivariados y cointegración  → 📊 Especialista en multivariados
*VAR, SVAR, VECM, ARDL, causalidad, relaciones de largo plazo.*

- ★ `[C]` **Lütkepohl, H. (2005).** *New Introduction to Multiple Time Series Analysis.* Springer. 🔒 — VAR/VECM a fondo, la referencia.
- `[C]` **Johansen, S. (1995).** *Likelihood-Based Inference in Cointegrated Vector Autoregressive Models.* Oxford UP. 🔒 — cointegración por máxima verosimilitud (el test que usás).
- `[C]` **Engle, R. & Granger, C. (1987).** *Co-integration and error correction.* *Econometrica*. 🔒 — el paper fundacional de cointegración.
- `[C]` **Sims, C. (1980).** *Macroeconomics and reality.* *Econometrica*. 🔒 — nace el VAR.
- `[C]` **Pesaran, Shin & Smith (2001).** *Bounds testing approaches to the analysis of level relationships.* *J. Applied Econometrics*. 🆓 — **ARDL / bounds test** (cointegración con variables de distinto orden).
- `[C]` **Blanchard, O. & Quah, D. (1989).** *The dynamic effects of aggregate demand and supply disturbances.* 🔒 — identificación SVAR por restricciones de largo plazo.
- `[C]` **Toda, H. & Yamamoto, T. (1995).** *Statistical inference in vector autoregressions with possibly integrated processes.* 🔒 — Granger robusto a integración.
- `[M]` **Kilian, L. & Lütkepohl, H. (2017).** *Structural Vector Autoregressive Analysis.* Cambridge UP. 🔒 — SVAR moderno, la referencia actual.

---

## 05 · Volatilidad  → 📈 Especialista en volatilidad
*ARCH/GARCH y familia, volatilidad estocástica, series financieras.*

- ★ `[C]` **Tsay, R. (2010).** *Analysis of Financial Time Series*, 3ª ed. Wiley. 🔒 — series financieras y GARCH, la referencia aplicada.
- `[C]` **Engle, R. (1982).** *Autoregressive conditional heteroskedasticity…* *Econometrica*. 🔒 — el ARCH original (Nobel).
- `[C]` **Bollerslev, T. (1986).** *Generalized ARCH.* *J. Econometrics*. 🔒 — el GARCH.
- `[C]` **Nelson, D. (1991).** *Conditional heteroskedasticity in asset returns* (EGARCH). 🔒 — asimetría.
- `[C]` **Glosten, Jagannathan & Runkle (1993).** GJR-GARCH. 🔒 — efecto apalancamiento.
- `[M]` **Francq, C. & Zakoïan, J.-M. (2019).** *GARCH Models*, 2ª ed. Wiley. 🔒 — tratamiento teórico completo y moderno.

---

## 06 · Quiebres, no linealidad y regímenes  → 🔎 Crítico + 📊 Multivariados
*Cambios estructurales, modelos de umbral, cambio de régimen.*

- ★ `[C]` **Hamilton, J. (1989).** *A new approach to the economic analysis of nonstationary time series…* (Markov-switching). 🔒
- `[C]` **Bai, J. & Perron, P. (1998, 2003).** *Estimating and testing linear models with multiple structural changes.* 🆓 — detección de **múltiples quiebres**.
- `[C]` **Perron, P. (1989).** *The great crash, the oil price shock, and the unit root hypothesis.* *Econometrica*. 🔒 — raíz unitaria con quiebre.
- `[C]` **Tong, H. (1990).** *Non-linear Time Series: A Dynamical System Approach.* Oxford UP. 🔒
- `[M]` **Teräsvirta, Tjøstheim & Granger (2010).** *Modelling Nonlinear Economic Time Series.* Oxford UP. 🔒

---

## 07 · Raíces unitarias y estacionariedad (tests)  → 🔧 + 🔎
*La batería de tests que decide el orden de integración.*

- `[C]` **Dickey, D. & Fuller, W. (1979).** 🔒 · **Said & Dickey (1984)** ADF. 🔒
- `[C]` **Phillips, P. & Perron, P. (1988).** 🔒 · **KPSS (1992)** (H0 = estacionaria). 🆓
- `[C]` **Elliott, Rothenberg & Stock (1996).** DF-GLS (más potente). 🔒
- `[C]` **Zivot, A. & Andrews, D. (1992).** raíz unitaria con quiebre endógeno. 🔒
- `[M]` **Maddala, G. & Kim, I.-M. (1998).** *Unit Roots, Cointegration, and Structural Change.* Cambridge UP. 🔒 — ★ texto que une raíces unitarias + cointegración + quiebres.

---

## 08 · Inferencia causal y controles  → 🧪 Especialista en controles/causal  *(HUECO a llenar)*
*Control sintético, diferencias-en-diferencias, IV, RDD, contrafácticos.*

- ★ `[M]` **Cunningham, S. (2021).** *Causal Inference: The Mixtape.* Yale UP. 🆓 **mixtape.scunning.com** — el más completo y didáctico; cubre DiD, control sintético, IV, RDD. (Nueva ed. *The Remix*, 2026.)
- ★ `[M]` **Huntington-Klein, N. (2022).** *The Effect: An Introduction to Research Design and Causality.* 🆓 **theeffectbook.net** — excelente para diseño de investigación.
- `[C]` **Angrist, J. & Pischke, J.-S. (2009).** *Mostly Harmless Econometrics.* Princeton UP. 🔒 — el clásico moderno; y *Mastering 'Metrics* (2015), más accesible.
- `[M]` **Imbens, G. & Rubin, D. (2015).** *Causal Inference for Statistics, Social, and Biomedical Sciences.* Cambridge UP. 🔒 — el tratado de referencia (potential outcomes).
- `[M]` **Morgan, S. & Winship, C. (2014).** *Counterfactuals and Causal Inference*, 2ª ed. 🔒
- **Control sintético (lo que te interesa puntualmente):**
  - `[C]` **Abadie, A. & Gardeazabal, J. (2003)** y **Abadie, Diamond & Hainmueller (2010, 2015).** 🆓 — fundacionales del **synthetic control**.
  - `[F]` **Abadie, A. (2021).** *Using synthetic controls: feasibility, data requirements, and methodological aspects.* *JEL*. 🆓 — survey moderno.
- **DiD reciente (la "revolución" 2021+):**
  - `[F]` **Callaway, B. & Sant'Anna, P. (2021).** *Difference-in-differences with multiple time periods.* 🆓
  - `[F]` **Goodman-Bacon, A. (2021).** *Difference-in-differences with variation in treatment timing.* 🆓
  - `[F]` **de Chaisemartin & D'Haultfœuille (2020).** estimadores robustos a efectos heterogéneos. 🆓

---

## 09 · Robustez y selección de modelos  → 🔬 Especialista en robustez/minería  *(HUECO a llenar)*
*Correr miles de especificaciones y separar lo robusto del ruido — tu cazador de patrones.*

- ★ `[C]` **Leamer, E. (1983).** *Let's take the con out of econometrics.* *AER*. 🆓 — el manifiesto del análisis de sensibilidad; y **Leamer (1985)** *Sensitivity analyses would help.*
- ★ `[C]` **Sala-i-Martin, X. (1997).** *I just ran two million regressions.* *AER*. 🆓 — el antecedente directo de tu idea de los 120.000 modelos (EBA con promedio).
- `[C]` **Granger, C. & Uhlig, H. (1990).** *Reasonable extreme-bounds analysis.* *J. Econometrics*. 🔒 — refinamiento del EBA.
- `[M]` **Young, C. & Holsteen, K. (2017).** *Model uncertainty and robustness: a computational framework.* *Sociological Methods & Research*. 🆓 — marco computacional de multiverso.
- `[M]` **Simonsohn, Simmons & Nelson (2020).** *Specification curve analysis.* *Nature Human Behaviour*. 🆓 — la **curva de especificación** (estándar actual).
- **Promediado de modelos (model averaging):**
  - `[C]` **Raftery, Madigan & Hoeting (1997).** *Bayesian Model Averaging.* *JASA*. 🆓
  - `[M]` **Hansen, B. (2007).** *Least squares model averaging.* *Econometrica*. 🆓
  - `[M]` **Steel, M. (2020).** *Model averaging and its use in economics.* *JEL*. 🆓 — ★ survey de referencia.
- **Selección con muchas variables (ML):**
  - `[M]` **Belloni, Chernozhukov & Hansen (2014).** *High-dimensional methods and inference… (LASSO).* *JEP*. 🆓

---

## 10 · Pronóstico, ML y deep learning  → 🔮 Especialista en pronóstico/ML
*De ARIMA a foundation models; evaluación y combinación de pronósticos.*

- ★ `[M]` **Hyndman & Athanasopoulos — FPP3 (2021).** 🆓 ✅ — el mejor punto de entrada al pronóstico moderno.
- `[C]` **Diebold, F. & Mariano, R. (1995).** *Comparing predictive accuracy.* 🔒 — el test estándar para comparar pronósticos.
- `[C]` **Bates, J. & Granger, C. (1969).** *The combination of forecasts.* 🔒 — combinar modelos.
- **ML para economistas:**
  - ★ `[M]` **Athey, S. & Imbens, G. (2019).** *Machine learning methods that economists should know about.* *Annual Review of Economics*. 🆓
  - `[M]` **Mullainathan, S. & Spiess, J. (2017).** *Machine learning: an applied econometric approach.* *JEP*. 🆓
- **Deep learning para series (frontera):**
  - `[M]` **Oreshkin et al. (2020).** *N-BEATS.* ICLR. 🆓 — quebró el M4, interpretable.
  - `[F]` **Survey (2024):** *A Survey of Deep Learning and Foundation Models for Time Series Forecasting.* arXiv:2401.13912. 🆓 — panorama completo (transformers, GNN, LLM, difusión).
  - `[F]` **Garza et al. (2023) — TimeGPT** y **Das et al. (2024) — TimesFM** (Google). 🆓 — **foundation models** de series (zero-shot).
  - `[C]` **Hyndman et al. (2002) — ETS / espacio de estados exponencial smoothing.** 🆓

---

## 11 · Bayesianas  → 📊/🔮 (transversal)
*Inferencia bayesiana en series: BVAR, TVP, volatilidad estocástica.*

- ★ `[M]` **Chan, Koop, Poirier & Tobias (2019).** *Bayesian Econometric Methods*, 2ª ed. Cambridge UP. 🔒 — ★ el más completo y aplicado.
- `[C]` **West, M. & Harrison, J. (1997).** *Bayesian Forecasting and Dynamic Models.* Springer. 🔒
- `[C]` **Primiceri, G. (2005).** *Time varying structural VARs and monetary policy.* *REStud*. 🆓 — TVP-VAR.
- `[M]` **Koop, G. & Korobilis, D. (2010).** *Bayesian multivariate time series methods for empirical macroeconomics.* 🆓 — survey práctico de BVAR.

---

## 12 · Interpretación económica y aplicaciones  → 📖 Intérprete + 👔 Líder
*Cómo se traduce la salida a economía; y el dominio de aplicación (riesgo país).*

- `[M]` **Stock, J. & Watson, M. (2020).** *Introduction to Econometrics*, 4ª ed. Pearson. 🔒 — interpretación econométrica estándar.
- **Dominio (riesgo país / EMBI, para tu caso):**
  - `[M]` **Comelli, F. (2012).** *Emerging market sovereign bond spreads: estimation and back-testing.* IMF WP. 🆓
  - `[M]` **Hilscher, J. & Nosbusch, Y. (2010).** *Determinants of sovereign risk.* *Review of Finance*. 🆓
  - `[C]` **Edwards, S. (1984).** *LDC foreign borrowing and default risk.* *AER*. 🔒
  - 📄 *(cargá acá los papers de tu tesis: push vs pull factors, EMBI, etc.)*

---

## Cómo se usa esta lista

1. Cada **especialista** se ancla a su categoría (su skill apunta a la carpeta `corpus/NN_…`).
2. Lo marcado **★** es el "ancla" mínima de cada categoría: si solo conseguís uno, que sea ese.
3. Los **huecos** declarados (08 causal, 09 robustez) son la prioridad de carga.
4. Al cargar un texto, ponelo en `corpus/NN_<categoria>/` y reindexá con `rag/ingest.py`.
