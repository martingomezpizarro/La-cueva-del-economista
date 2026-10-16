# Bibliografía maestra — Econometría de series de tiempo

Lista curada para alimentar La Cueva-LM. Cubre desde el canon clásico hasta la frontera
(2024-2026). Foco: **series de tiempo** (modelos, tratamiento, transformaciones, controles,
errores, análisis de resultados, series bayesianas, deep learning). Riesgo país se trata aparte.

**Leyenda:** 📘 libro · 📄 paper · 🆓 acceso abierto (descargable) · 🔒 pago/biblioteca
· `[C]` clásico/fundacional · `[M]` moderno (2015-2023) · `[F]` frontera (2024-2026)

> Para descargar lo abierto: los `[F]`/`[M]` de deep learning casi todos están en **arXiv**
> (buscá el título). Los libros 🔒 conviene conseguirlos por biblioteca/editorial.
> Mapa de carpetas sugerido en `corpus/`: ver final del documento.

---

## 1. Manuales de referencia (el canon) — 📘
- `[C]` **Enders, W. (2014).** *Applied Econometric Time Series*, 4ª ed. Wiley. 🔒 — ✅ ya cargado. El más aplicado y didáctico.
- `[C]` **Hamilton, J. (1994).** *Time Series Analysis*. Princeton UP. 🔒 — la referencia técnica "biblia".
- `[C]` **Lütkepohl, H. (2005).** *New Introduction to Multiple Time Series Analysis*. Springer. 🔒 — VAR/VECM a fondo.
- `[C]` **Box, Jenkins, Reinsel & Ljung (2015).** *Time Series Analysis: Forecasting and Control*, 5ª ed. 🔒 — origen de ARIMA.
- `[C]` **Brockwell & Davis (2016).** *Introduction to Time Series and Forecasting*, 3ª ed. Springer. 🔒 — base estadística rigurosa.
- `[C]` **Tsay, R. (2010).** *Analysis of Financial Time Series*, 3ª ed. Wiley. 🔒 — series financieras, GARCH, alta frecuencia.
- `[C]` **Shumway & Stoffer (2017).** *Time Series Analysis and Its Applications* (con R). Springer. 🔒 — muy usado, incluye state space.
- `[C]` **Kirchgässner, Wolters & Hassler (2013).** *Introduction to Modern Time Series Analysis*. Springer. 🔒 — accesible, orientado a economía.
- `[M]` **Hyndman & Athanasopoulos (2021).** *Forecasting: Principles and Practice (FPP3)*. 🆓 **otexts.com/fpp3** — pronóstico moderno, gratis online. **Muy recomendado.**

---

## 2. Fundamentos: estacionariedad, raíces unitarias, transformaciones — 📄
- `[C]` **Dickey & Fuller (1979).** Distribution of estimators for autoregressive time series with a unit root. *JASA*.
- `[C]` **Said & Dickey (1984).** Test ADF (augmented Dickey-Fuller). *Biometrika*.
- `[C]` **Phillips & Perron (1988).** Testing for a unit root. *Biometrika*.
- `[C]` **Kwiatkowski, Phillips, Schmidt & Shin — KPSS (1992).** Test con H0 de estacionariedad. *J. Econometrics*.
- `[C]` **Elliott, Rothenberg & Stock (1996).** DF-GLS, tests de raíz unitaria más potentes. *Econometrica*.
- `[C]` **Box & Cox (1964).** Transformaciones de potencia (estabilizar varianza). *JRSS-B*.
- `[C]` **Perron (1989).** Raíz unitaria con quiebre estructural (crash + cambio de tendencia). *Econometrica*.

---

## 3. Modelos univariados (ARIMA, memoria larga, state space) — 📄📘
- `[C]` **Granger & Joyeux (1980); Hosking (1981).** ARFIMA / memoria larga (integración fraccional).
- `[C]` **Harvey (1989).** *Forecasting, Structural Time Series Models and the Kalman Filter*. 🔒 — modelos de estado/inobservables.
- `[C]` **Durbin & Koopman (2012).** *Time Series Analysis by State Space Methods*, 2ª ed. 🔒 — state space + filtro de Kalman (clave para tu trabajo Kalman).
- `[M]` **Hyndman, Koehler, Ord & Snyder (2008).** *Forecasting with Exponential Smoothing: The State Space Approach*. 🔒 — marco ETS.

---

## 4. Volatilidad (familia ARCH/GARCH, volatilidad estocástica) — 📄
- `[C]` **Engle (1982).** ARCH (Nobel 2003). *Econometrica*.
- `[C]` **Bollerslev (1986).** GARCH. *J. Econometrics*.
- `[C]` **Nelson (1991).** EGARCH (volatilidad asimétrica). *Econometrica*.
- `[C]` **Glosten, Jagannathan & Runkle (1993).** GJR-GARCH (efecto apalancamiento). *J. Finance*.
- `[C]` **Engle (2002).** DCC-GARCH (correlaciones condicionales dinámicas, multivariado). *JBES*.
- `[C]` **Kim, Shephard & Chib (1998).** Volatilidad estocástica (SV) por MCMC. *REStud*.

---

## 5. Modelos multivariados (VAR / SVAR) — 📄
- `[C]` **Sims (1980).** Macroeconomics and Reality — nacimiento del VAR (Nobel 2011). *Econometrica*.
- `[C]` **Blanchard & Quah (1989).** SVAR con restricciones de largo plazo. *AER*.
- `[C]` **Bernanke, Boivin & Eliasz (2005).** FAVAR (VAR aumentado con factores). *QJE*.
- `[C]` **Jordà (2005).** Local projections para funciones impulso-respuesta (alternativa al VAR). *AER*.

---

## 6. Cointegración y corrección de error — 📄
- `[C]` **Engle & Granger (1987).** Cointegración y ECM (Nobel 2003). *Econometrica*.
- `[C]` **Johansen (1988, 1991).** Test de cointegración por máxima verosimilitud / VECM. *Econometrica*.
- `[C]` **Pesaran, Shin & Smith (2001).** ARDL bounds test (cointegración con I(0)/I(1) mezclados). *J. Applied Econometrics*. **Clave para tu metodología.**
- `[C]` **Stock & Watson (1993).** DOLS (estimación de vectores de cointegración). *Econometrica*.

---

## 7. Quiebres estructurales, no linealidad, regímenes — 📄
- `[C]` **Hamilton (1989).** Markov-switching (cambios de régimen). *Econometrica*.
- `[C]` **Tong (1990).** *Non-linear Time Series* — modelos TAR/umbral. 🔒
- `[C]` **Bai & Perron (1998, 2003).** Detección de múltiples quiebres estructurales. *Econometrica / J. Applied Econometrics*.
- `[C]` **Teräsvirta (1994).** STAR (transición suave). *JASA*.

---

## 8. Pronóstico y evaluación — 📄📘
- `[C]` **Diebold & Mariano (1995).** Test de comparación de precisión predictiva. *JBES*.
- `[C]` **West (1996).** Inferencia sobre precisión predictiva. *Econometrica*.
- `[M]` **Makridakis, Spiliotis & Assimakopoulos (2018, 2020).** Competencias M4/M5: ML vs estadística. *Int. J. Forecasting / PLoS ONE*.
- `[M]` **Taylor & Letham (2018).** Prophet (Facebook). *The American Statistician*. 🆓

---

## 9. Series de tiempo BAYESIANAS — 📄📘
- `[C]` **West & Harrison (1997).** *Bayesian Forecasting and Dynamic Models*. Springer. 🔒 — DLMs, fundacional.
- `[C]` **Doan, Litterman & Sims (1984); Litterman (1986).** BVAR con prior de Minnesota. *Econometric Reviews / JBES*.
- `[C]` **Primiceri (2005).** TVP-VAR con volatilidad estocástica (parámetros que cambian en el tiempo). *REStud*.
- `[C]` **Cogley & Sargent (2005).** Inflación-persistencia con TVP-VAR-SV. *Review of Economic Dynamics*.
- `[M]` **Bańbura, Giannone & Reichlin (2010).** Large Bayesian VARs (BVAR de gran dimensión). *J. Applied Econometrics*.
- `[M]` **Scott & Varian (2014).** BSTS — Bayesian Structural Time Series (nowcasting con Google). *Int. J. Math. Modelling*.
- `[M]` **Koop & Korobilis (2010).** *Bayesian Multivariate Time Series Methods for Empirical Macroeconomics*. 🆓 (monografía, web del autor) — **excelente puerta de entrada.**
- `[M]` **Chan, Koop, Poirier & Tobias (2019).** *Bayesian Econometric Methods*, 2ª ed. (Cambridge). 🔒 — con ejercicios resueltos.
- `[F]` **Chan, J. (2022-2024).** Variational inference y tensor-VARs para BVAR grandes con SV. 🆓 arXiv (varios) — frontera computacional bayesiana.

---

## 10. Alta dimensión, factores, nowcasting, ML para macro — 📄
- `[C]` **Stock & Watson (2002).** Forecasting con factores dinámicos (DFM) en muchas series. *JASA/JBES*.
- `[C]` **Giannone, Reichlin & Small (2008).** Nowcasting del PBI en tiempo real. *J. Monetary Economics*.
- `[M]` **Medeiros, Vasconcelos, Veiga & Zilberman (2021).** Forecasting de inflación con Random Forest/ML (gana a benchmarks). *JBES*.
- `[M]` **Coulombe, Leroux, Stevanovic & Surprenant (2022).** ¿Sirve el ML para forecasting macro? *J. Applied Econometrics*.

---

## 11. FRONTERA — Deep Learning y modelos fundacionales para series — 📄 (casi todo 🆓 en arXiv)
**Redes y arquitecturas:**
- `[M]` **Salinas, Flunkert & Gasthaus (2020).** DeepAR (forecasting probabilístico con RNN, Amazon). *Int. J. Forecasting*.
- `[M]` **Oreshkin et al. (2020).** N-BEATS. *ICLR*. — MLP puro que compite con todo.
- `[M]` **Challu et al. (2023).** N-HiTS. *AAAI*. — sucesor eficiente de N-BEATS.
- `[M]` **Lim et al. (2021).** Temporal Fusion Transformer (TFT). *Int. J. Forecasting*.
- `[M]` **Zhou et al. (2021).** Informer (AAAI best paper) — long-sequence forecasting.
- `[M]` **Wu et al. (2021).** Autoformer (NeurIPS); **Zhou et al. (2022)** FEDformer (ICML).
- `[M]` **Zeng et al. (2023).** *Are Transformers Effective for Time Series Forecasting?* (DLinear). *AAAI*. — **crítica clave: lineal simple gana a transformers complejos.**
- `[M]` **Nie et al. (2023).** PatchTST (patching). *ICLR*. — cambió el paradigma.
- `[F]` **Liu et al. (2024).** iTransformer. *ICLR 2024*. — invierte las dimensiones, SOTA multivariado.
- `[M]` **Wu et al. (2023).** TimesNet. *ICLR*. — modelado multi-periódico 2D.
- `[F]` **Gu & Dao (2024).** Mamba (state-space selectivo S6) — alternativa eficiente a transformers; muy activo en series 2024-25.

**Modelos fundacionales (zero-shot, "el GPT de las series") — lo más nuevo:**
- `[F]` **Ansari et al. (2024).** Chronos (Amazon) — tokeniza series como lenguaje. arXiv 2403.07815. **Chronos-2 (2025).**
- `[F]` **Das et al. (2024).** TimesFM (Google) — decoder-only, pre-entrenado en 100B puntos.
- `[F]` **Woo et al. (2024).** Moirai (Salesforce) — universal, multi-frecuencia. **Moirai-MoE (2024).**
- `[F]` **Goswami et al. (2024).** MOMENT — familia de modelos fundacionales open.
- `[F]` **Rasul et al. (2024).** Lag-Llama — fundacional probabilístico sobre arquitectura Llama.
- `[F]` **Shi et al. (2024).** Time-MoE — mixture-of-experts a escala billón de parámetros.
- `[F]` **Garza et al. (Nixtla).** TimeGPT — primer fundacional comercial.

**Surveys de la frontera (para visión de conjunto):**
- `[F]` **"Deep Learning for Time Series Forecasting: A Survey" (2025).** arXiv 2503.10198. 🆓
- `[F]` **"A Comprehensive Survey of Deep Learning for Time Series Forecasting: Architectural Diversity and Open Challenges" (2024).** arXiv 2411.05793. 🆓
- `[F]` **"Deep learning for time series forecasting: a survey of recent advances" (2025).** *Frontiers of Computer Science*.

---

## 12. Inferencia causal en series de tiempo — 📄
- `[C]` **Granger (1969).** Causalidad de Granger (precedencia predictiva). *Econometrica*.
- `[M]` **Brodersen et al. (2015).** CausalImpact (Google) — efecto causal con BSTS. *Annals of Applied Statistics*. 🆓
- `[C]` **Abadie, Diamond & Hainmueller (2010).** Synthetic control. *JASA*.

---

## 13. Software y código de referencia (para que la IA programe bien) — 🆓
- **statsmodels** (Python): ARIMA, VAR, VECM, Johansen, ARDL, tests. Cargar páginas clave de la doc como `.md`.
- **arch** (Python, K. Sheppard): GARCH y familia, tests de raíz unitaria.
- **Nixtla** — statsforecast / neuralforecast / mlforecast: forecasting estadístico, neuronal y fundacional moderno.
- **darts** (Unit8), **GluonTS** (Amazon), **sktime**: frameworks de forecasting con DL.
- **PyMC** / **Stan** / **NumPyro**: series bayesianas (BVAR, TVP, SV, DLMs).
- **Tu propio código** (`src/models.py`, `utils.py`, notebooks) — ✅ ya cargado.

---

## Mapa de carpetas sugerido en `corpus/`
```
01_fundamentos/      → secciones 1, 2
02_univariados/      → sección 3
03_volatilidad/      → sección 4
04_multivariados/    → secciones 5, 10
05_cointegracion/    → sección 6
06_quiebres_nolineal/→ sección 7
07_pronostico/       → sección 8, 12
10_codigo_python/    → sección 13
11_bayesianas/       → sección 9          (NUEVA)
12_frontera_dl/      → sección 11         (NUEVA)
```

## Cómo priorizar la carga (sugerencia)
1. **Núcleo ya:** Hyndman FPP3 (🆓), Koop & Korobilis (🆓), 3-4 surveys de frontera (🆓 arXiv).
2. **Libros:** Hamilton y Lütkepohl (los más consultados después de Enders).
3. **Papers fundacionales:** los `[C]` de cada método que vayas a usar.
4. **Frontera:** los modelos fundacionales (Chronos, TimesFM, Moirai) — todos abiertos en arXiv.
