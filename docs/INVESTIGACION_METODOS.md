# Investigación: todos los métodos de análisis, y cómo viven en La Cueva

> Sesión 2026-11-04. Pedido de Martín: *"desde la Cueva uno tiene las bases de datos y desde ahí
> mismo puede trabajar con análisis estadístico, econométrico e inferencia con redes neuronales,
> gradient boosting, árboles, random forest… probar todo, combinar todas las estrategias, hacerse
> un trabajo desde cero"*. Ampliado en la misma sesión: *"también lo quiero usar para mi proyecto
> de análisis de activos… identificar patrones, clusters, momentos, regímenes, que aumenten la
> esperanza de que sucedan determinados eventos (el aumento del riesgo país, o el resultado de una
> acción)"*.
>
> Este documento es el mapa. Lo que ya está construido está marcado ✅ con su id (se corre desde
> `/mesa` → **Métodos**, desde la API o desde los agentes). Lo que falta está clasificado por
> esfuerzo para decidir el orden.

**Estado al cierre de la sesión: 100 métodos en 16 familias, todos con test (125), todos en la pantalla.**

---

## 0. Cómo leer el mapa

### 0.1 Tres preguntas, tres familias de herramientas

Toda pregunta de un trabajo cae en una de tres clases. Confundirlas es el error más común (y el
más caro) de la econometría aplicada y del ML:

| Pregunta | Ejemplo | Herramientas | Cómo se valida |
|---|---|---|---|
| **Describir** — ¿cómo es / cómo se mueve? | ¿La inflación tiene raíz unitaria? ¿Cuándo cambió de régimen? | pruebas, filtros, regímenes, no supervisado | supuestos del test, robustez |
| **Predecir** — ¿qué va a pasar? | ¿Cuánto va a dar el EMAE el mes que viene? ¿P(riesgo país > 1000 en 3 meses)? | univariados, VAR, ML, redes, Monte Carlo | **fuera de muestra**, contra un benchmark ingenuo |
| **Explicar causalmente** — ¿qué pasa si…? | ¿El cepo subió la brecha? ¿Cuánto traspasa el tipo de cambio a precios? | IV, DiD, control sintético, proyecciones locales, eventos | supuesto de identificación + placebo |

Un modelo que predice bien no explica causas (un XGBoost puede usar la brecha como proxy de
todo), y un coeficiente causal bien identificado puede predecir mal. La plataforma separa las
dos validaciones: los métodos predictivos se juzgan **sólo** fuera de muestra; los causales
**declaran** su supuesto de identificación en el veredicto y corren un placebo cuando se puede.

### 0.2 Leyenda de estado

| Marca | Significa |
|---|---|
| ✅ `id` | Construido, testeado, en la pantalla `Métodos` y disponible para los agentes |
| 🟢 | Próximo: < 1 día, con librerías que ya están instaladas |
| 🟡 | Medio: 1-3 días o una dependencia liviana nueva |
| 🔴 | Pesado: necesita `torch`, GPU o la cola de trabajos (fase 4 del roadmap) |
| ⚪ | Fuera del alcance de series de tiempo o sin datos en la plataforma (se anota para no olvidarlo) |

---

## 1. Catálogo por familia

### 1.1 Exploración y descriptivos (🔎 `exploratorio`)

| Método | Para qué | Estado |
|---|---|---|
| Estadísticos, percentiles, extremos, histograma | primera mirada | ✅ `estadisticos` |
| ACF / PACF + Ljung-Box (Box-Jenkins) | memoria, órdenes AR/MA | ✅ `acf_pacf` |
| Correlación cruzada (adelantos/rezagos) | indicadores líderes | ✅ `correlacion_cruzada` |
| Periodograma de Welch | ciclos dominantes | ✅ `periodograma` |
| Perfil estacional + Kruskal-Wallis | ¿hay meses distintos? | ✅ `perfil_estacional` |
| Media/desvío/correlación móviles | inestabilidad | ✅ `ventanas_moviles` |
| Dispersión con Pearson/Spearman/Kendall y outliers | forma de la relación | ✅ `dispersion` |
| Matriz de correlación con significancia | mapa de candidatas | ✅ `matriz_correlacion` |
| Coherencia espectral entre dos series | ¿comparten ciclos a cierta frecuencia? | 🟢 |
| Wavelets (continua, coherencia wavelet) | ciclos que cambian en el tiempo | 🟡 `pywt` |
| Análisis espectral singular (SSA) | tendencia + oscilaciones sin modelo | 🟢 |
| Recurrence plots / exponente de Lyapunov | dinámica no lineal (exploratorio) | 🟡 |
| Información mutua / correlación de distancia | dependencia no lineal entre pares | 🟢 |

### 1.2 Pruebas sobre las series (🧪 `pruebas`)

| Método | Para qué | Estado |
|---|---|---|
| Batería de raíz unitaria: ADF, Phillips-Perron, DF-GLS (ERS), KPSS, Zivot-Andrews, con orden de integración por voto | ¿niveles, diferencias o cointegración? | ✅ `raiz_unitaria` |
| Bai-Perron (programación dinámica propia, BIC/LWZ) **cruzado con la Línea de Tiempo** | quiebres múltiples y su evento | ✅ `quiebres_estructurales` |
| PELT (media, varianza o distribución) | cambios de régimen de volatilidad | ✅ `cambio_de_punto` |
| Chow en fecha conocida | ¿cambió la relación con la reforma? | ✅ `prueba_chow` |
| CUSUM y CUSUM² | estabilidad de coeficientes | ✅ `cusum` |
| Normalidad (JB, Shapiro, D'Agostino, Anderson) + QQ | colas, elección de distribución | ✅ `normalidad` |
| BDS sobre residuos AR | ¿queda no linealidad? | ✅ `no_linealidad_bds` |
| Memoria larga (Hurst R/S, GPH) | integración fraccional | ✅ `memoria_larga` |
| Heterocedasticidad (BP, White, ARCH-LM) | errores robustos o modelar varianza | ✅ `heterocedasticidad` |
| Raíz unitaria estacional (HEGY, OCSB, Canova-Hansen) | ¿diferenciar estacionalmente? | 🟡 |
| Raíz unitaria con 2 quiebres (Lee-Strazicich, Clemente-Montañés-Reyes) | Argentina tiene más de un quiebre | 🟡 |
| Quandt-Andrews (sup-F) y Andrews-Ploberger | quiebre único de fecha desconocida en regresión | 🟢 |
| Linealidad de Teräsvirta / Tsay | elegir entre AR, SETAR y STAR | 🟢 (LM3 ya está en `transicion_suave`) |
| Raíz unitaria en panel (IPS, LLC, CIPS) | provincias/países | 🟡 (requiere datos de panel) |
| Prueba de burbuja (SADF/GSADF de Phillips-Shi-Yu) con fechado BSADF y críticos por wild bootstrap | explosividad: dólar, activos, brecha | ✅ `burbuja_gsadf` |

### 1.3 Filtros y descomposición (🪚 `filtros`)

Todos producen series derivadas que se pueden guardar y usar en otros métodos.

| Método | Estado |
|---|---|
| Hodrick-Prescott (λ por frecuencia, aviso de sesgo de punta) | ✅ `filtro_hp` |
| Filtro de Hamilton (2018) | ✅ `filtro_hamilton` |
| Baxter-King y Christiano-Fitzgerald | ✅ `filtro_bandas` |
| STL robusto (fuerza de estacionalidad y tendencia) | ✅ `descomposicion_stl` |
| Beveridge-Nelson | ✅ `beveridge_nelson` |
| Componentes no observados de Harvey (Kalman) | ✅ `componentes_no_observados` |
| MSTL (varias estacionalidades: diaria + semanal) | 🟢 — útil para datos intradía |
| X-13ARIMA-SEATS (el método del INDEC) | 🟡 binario de Census; statsmodels lo envuelve |
| HP de un lado (en tiempo real) | 🟢 |
| BN con prior de señal/ruido (Kamber-Morley-Wong) | 🟢 |

### 1.4 Modelos univariados y pronóstico (📈 `univariados`)

| Método | Estado |
|---|---|
| Benchmarks ingenuos (paseo, media, deriva, estacional) | ✅ `benchmarks` |
| SARIMA con selección automática y evaluación | ✅ `sarima` |
| ETS / Holt-Winters con selección por AIC | ✅ `suavizado_exponencial` |
| Theta | ✅ `theta` |
| ARFIMA (memoria larga) | 🟡 |
| TBATS / regresión armónica dinámica | 🟡 |
| Croston (demanda intermitente) | ⚪ |
| Prophet | 🟡 dependencia pesada; aporta poco sobre ETS en macro |

### 1.5 Volatilidad y riesgo (🌪 `volatilidad`)

| Método | Estado |
|---|---|
| GARCH, GJR, EGARCH, APARCH, FIGARCH con comparación BIC y distribución t/skew-t/GED | ✅ `garch_familia` |
| VaR/ES histórico, normal y Cornish-Fisher + Kupiec | ✅ `valor_en_riesgo` |
| GARCH-M (prima por riesgo) | 🟢 |
| DCC-GARCH (correlaciones dinámicas; ¿suben en las crisis?) | ✅ `dcc_garch` |
| Volatilidad estocástica (SV) | 🟡 |
| Volatilidad realizada y HAR-RV (Corsi) | 🟢 con datos intradía |
| Teoría de valores extremos (POT / GPD, Hill, niveles de retorno) | ✅ `colas_extremas` |
| Backtest de VaR de Christoffersen (independencia) | 🟢 |
| Cópulas (gaussiana, t, Clayton, Gumbel) | 🟡 — dependencia en las colas entre activos |

### 1.6 Regresión y estimación (📐 `regresion`)

| Método | Estado |
|---|---|
| MCO con HAC/HC3, rezagos tipo ARDL, dummies estacionales, diagnóstico completo y VIF | ✅ `mco` |
| Regresión cuantílica (growth-at-risk) | ✅ `regresion_cuantilica` |
| Robusta (Huber, Tukey) con pesos por fecha | ✅ `regresion_robusta` |
| MCO móvil con bandas | ✅ `regresion_movil` |
| Variables instrumentales (MC2E) + F primera etapa + Hausman + Sargan | ✅ `variables_instrumentales` |
| Rezagos distribuidos de Almon (traspaso) | ✅ `rezagos_distribuidos` |
| MCG / Cochrane-Orcutt / Prais-Winsten | 🟢 |
| Probit/logit para eventos (crisis, recesión) | ✅ vía `probabilidad_evento` (logit) |
| Regresión no lineal (MCNL) con forma elegida (logística, exponencial, Cobb-Douglas) | 🟢 |
| GAM (splines) | 🟡 `pygam` — no linealidad interpretable |
| GMM general | 🟡 |
| MIDAS (frecuencias mixtas) | 🟡 — mensual que predice trimestral |
| Regresión bayesiana / BMA (promedio de modelos) | 🟡 |

### 1.7 Sistemas multivariados (🕸 `multivariados`)

| Método | Estado |
|---|---|
| VAR con IRF (Cholesky / generalizada), FEVD, Granger por pares y estabilidad | ✅ `var_completo` |
| Proyecciones locales de Jordà | ✅ `proyecciones_locales` |
| Toda-Yamamoto (causalidad en niveles) | ✅ `toda_yamamoto` |
| BVAR con prior de Minnesota | ✅ `bvar_minnesota` |
| SVAR de largo plazo (Blanchard-Quah) | 🟢 |
| SVAR con restricciones de signo (Uhlig) | 🟡 — política monetaria sin Cholesky |
| Descomposición histórica de shocks | 🟢 |
| Proyecciones locales con estado (dependientes del régimen) | 🟢 — ¿la política funciona igual en recesión? |
| TVP-VAR con volatilidad estocástica (Primiceri) | 🔴 |
| FAVAR | 🟡 |
| VAR por umbral (TVAR) | 🟡 |
| Conectividad de Diebold-Yilmaz (derrames, transmisores netos, índice móvil) | ✅ `contagio_diebold_yilmaz` |

### 1.8 Cointegración y largo plazo (🔗 `cointegracion`)

| Método | Estado |
|---|---|
| Engle-Granger + modelo de corrección de errores | ✅ `engle_granger` |
| ARDL con prueba de límites de Pesaran-Shin-Smith | ✅ `ardl_limites` |
| Johansen (traza y λ máx con corrección de muestra chica) + VECM con α, β, IRF | ✅ `johansen_vecm` |
| MCO dinámicos (Stock-Watson) | ✅ `mco_dinamicos` |
| FMOLS / CCR | 🟡 |
| Gregory-Hansen (cointegración con quiebre) | 🟢 — típico de Argentina |
| Cointegración por umbral (Hansen-Seo) | 🟡 — ajuste sólo pasada una banda |
| NARDL (asimetría de largo plazo: suba vs baja) | 🟢 — **traspaso asimétrico** |

### 1.9 No linealidad y regímenes (🔀 `regimenes`)

| Método | Estado |
|---|---|
| Markov-switching (Hamilton) con episodios cruzados con la Línea de Tiempo | ✅ `markov_switching` |
| SETAR con p-valor por bootstrap (Hansen) | ✅ `umbral_setar` |
| LSTAR con prueba de linealidad LM3 | ✅ `transicion_suave` |
| Markov con probabilidades de transición variables (TVTP) | 🟡 — P(recesión) que depende de la curva |
| HMM gaussiano multivariado | 🟢 (aproximado hoy por `clusters_periodos`) |
| ESTAR (ajuste del TCR a la PPA) | 🟢 |

### 1.10 Espacio de estados y factores (🛰 `estado`)

| Método | Estado |
|---|---|
| Regresión con coeficientes variables (Kalman + RTS propio, q por MV) | ✅ `tvp_kalman` |
| Factores dinámicos (EM, tolera faltantes) | ✅ `factor_dinamico` |
| Desagregación temporal Chow-Lin / Denton | ✅ `desagregacion_temporal` |
| Nowcasting con DFM de frecuencias mixtas y noticias (Bańbura-Modugno) | 🟡 — **nowcast del PBI con el EMAE y datos diarios** |
| Litterman / Fernández (desagregación con I(1)) | 🟢 |
| Kalman para imputar faltantes | 🟢 (ya existe en el explorador clásico) |

### 1.11 Inferencia causal y eventos (🎯 `causal`)

| Método | Estado |
|---|---|
| Serie interrumpida con placebo | ✅ `serie_interrumpida` |
| Impacto causal con contrafactual y bootstrap por bloques (estilo CausalImpact) | ✅ `impacto_causal` |
| Control sintético con placebos y ajuste de nivel | ✅ `control_sintetico` |
| Diferencias en diferencias con prueba de pendiente previa | ✅ `diferencias_en_diferencias` |
| Estudio de eventos sobre `data/historia/eventos.csv` | ✅ `estudio_eventos` |
| Control sintético aumentado / SDID (Arkhangelsky et al.) | 🟡 |
| Regresión discontinua en el tiempo (RDiT) | 🟢 |
| Double/Debiased ML (Chernozhukov) | 🟡 — controles de alta dimensión con ML |
| Bosques causales (efectos heterogéneos) | 🟡 `econml` — necesita panel |
| Shocks narrativos (Romer-Romer) como instrumento en LP-IV | 🟢 una vez cargados los shocks en la Línea de Tiempo |
| Event study de mercado (retornos anormales con modelo de mercado, CAR) | ✅ `eventos_mercado` |

### 1.12 Aprendizaje automático (🌲 `ml`)

Todos comparten la misma matriz de diseño (`insumos.Diseno`: rezagos de Y y de X, horizonte h,
estacionales), el mismo origen móvil y la misma lectura (importancia por permutación **fuera de
muestra**, dependencia parcial).

| Método | Estado |
|---|---|
| Ridge, Lasso, Elastic Net (penalización elegida con CV temporal) | ✅ `ml_ridge` `ml_lasso` `ml_elastic_net` |
| K vecinos (analogías históricas) | ✅ `ml_knn` |
| SVR (núcleos RBF, lineal, polinómico) | ✅ `ml_svr` |
| Árbol de decisión (reglas legibles) | ✅ `ml_arbol` |
| Bosque aleatorio, Extra Trees | ✅ `ml_random_forest` `ml_extra_trees` |
| Gradient boosting: sklearn, histogramas, XGBoost, LightGBM | ✅ `ml_gbm` `ml_hist_gbm` `ml_xgboost` `ml_lightgbm` |
| Proceso gaussiano | ✅ `ml_proceso_gaussiano` |
| SHAP exacto para árboles (por qué pronostica lo que pronostica HOY) | ✅ `ml_shap` |
| **Probabilidad de un evento con clasificador calibrado** (logit, RF, GBM, SVM, KNN; Brier, BSS, AUC, curva de calibración) | ✅ `probabilidad_evento` |
| Selección de predictores entre 40 candidatas (estabilidad Lasso + bosque) | ✅ `seleccion_variables` |
| CatBoost | 🟢 dependencia liviana |
| Regresión cuantílica con boosting / bosques cuantílicos (intervalos) | 🟢 |
| Predicción conformal por origen móvil (cobertura medida fuera de muestra) | ✅ `intervalos_conformales` |
| Calibración isotónica / Platt de probabilidades | 🟢 |
| Pronóstico multi-horizonte (estrategias directa, recursiva, DirRec) | 🟢 |
| Validación purgada con embargo (López de Prado) | 🟢 — imprescindible con etiquetas que se solapan |
| Etiquetado de triple barrera + meta-etiquetado con entrenamiento purgado | ✅ `triple_barrera` |
| AutoML (búsqueda de hiperparámetros con Optuna sobre origen móvil) | 🟡 |
| TabPFN (red pre-entrenada para tablas chicas) | 🔴 |

### 1.13 Redes neuronales (🧠 `redes`)

Decisión de esta sesión: **las redes chicas van en numpy puro** (`cueva/metodos/redes_np.py`,
gradiente verificado numéricamente en los tests). Las series de la plataforma tienen cientos o
pocos miles de observaciones; una LSTM de 16 unidades entrena en 1-2 segundos en CPU y no
justifica 2-3 GB de `torch`. Las arquitecturas grandes van al extra `[deep]` con la cola de
trabajos.

| Método | Estado |
|---|---|
| Perceptrón multicapa (sklearn) | ✅ `ml_mlp` |
| LSTM (BPTT + Adam, parada temprana, ensamble de semillas) | ✅ `red_lstm` |
| GRU | ✅ `red_gru` |
| Echo State Network (reservorio) | ✅ `red_reservorio` |
| CNN 1D / TCN (convoluciones causales dilatadas) | 🟡 numpy posible; mejor con torch |
| N-BEATS / N-HiTS | 🔴 `[deep]` |
| DeepAR (probabilístico) | 🔴 |
| Temporal Fusion Transformer (con variables conocidas a futuro, interpretable) | 🔴 |
| PatchTST, iTransformer, TiDE, TSMixer | 🔴 |
| Redes informadas por la economía (restricciones de signo, PINN) | 🔴 investigación |

### 1.14 No supervisado y anomalías (🧩 `no_supervisado`)

| Método | Estado |
|---|---|
| Componentes principales con cargas y criterio de Kaiser | ✅ `componentes_principales` |
| Agrupamiento jerárquico de series (distancia de correlación, silueta) | ✅ `clusters_series` |
| **Agrupamiento de PERÍODOS** (mezcla gaussiana / k-means: regímenes sin etiqueta) con transiciones y eventos | ✅ `clusters_periodos` |
| Anomalías (STL robusto + bosque de aislamiento) cruzadas con eventos | ✅ `anomalias` |
| Clustering por forma (DTW + k-medoids) | 🟡 `tslearn` — patrones de trayectoria |
| Matrix profile (motivos y discordias) | 🟡 `stumpy` — **patrones que se repiten en precios** |
| Autoencoder para anomalías | 🔴 |
| t-SNE / UMAP de ventanas | 🟡 visualización de regímenes |
| PCA dinámico / análisis de correlación canónica | 🟢 |

### 1.15 Finanzas cuantitativas y activos (💹 `finanzas`)

| Método | Estado |
|---|---|
| Rendimiento, Sharpe, Sortino, Calmar, peores caídas y recuperación | ✅ `metricas_rendimiento` |
| Monte Carlo de cartera (normal, t, bootstrap por bloques): VaR, CVaR, P(pérdida) | ✅ `montecarlo_cartera` |
| **Probabilidad de tocar un nivel** antes de una fecha (GBM, bootstrap, GARCH) | ✅ `montecarlo_umbral` |
| Carteras: 1/N, mínima varianza, máximo Sharpe, paridad de riesgo, HRP — **evaluadas fuera de muestra** con covarianza Ledoit-Wolf | ✅ `frontera_eficiente` |
| Backtest de cruce de medias con costos, grilla de robustez y elección en la 1.ª mitad | ✅ `cruce_medias` |
| Momentum (serie de tiempo o transversal) condicionado a régimen de volatilidad, tendencia o serie externa | ✅ `momentum_regimen` |
| Trading de pares (cointegración en formación, vida media OU, operación fuera de muestra) | ✅ `pares_trading` |
| Regímenes y agrupamiento de volatilidad | ✅ `regimenes_volatilidad` |
| Mapa de estacionalidad intradía / día × mes / mes × año | ✅ `estacionalidad_calendario` |
| Chequeo de neutralidad a factores (betas, alfa, betas móviles, descomposición) | ✅ `neutralidad_factores` |
| Sharpe deflactado y probabilidad de sobreajuste del backtest (CSCV) | ✅ `sobreajuste_backtest` |
| Reality check de White (¿la mejor de N estrategias es suerte?) | ✅ `sobreajuste_backtest` · SPA de Hansen 🟢 |
| Contrato binario: valor esperado, Kelly fraccional, sensibilidad a p y riesgo de ruina | ✅ `apuesta_binaria` · volatilidad objetivo 🟢 |
| Bandas de Bollinger / reversión a la media / breakout como reglas de backtest | 🟢 (mismo motor que `cruce_medias`) |
| Probabilidades implícitas en opciones (Breeden-Litzenberger) | 🟡 necesita cadena de opciones |
| Curva de rendimientos: Nelson-Siegel (Diebold-Li) | ✅ `curva_nelson_siegel` · Svensson 🟢 |
| Spread, duration, convexidad de bonos | 🟢 |
| Microestructura: volumen, VWAP, profundidad, order flow | ⚪ necesita datos tick |
| Sentimiento de noticias con LLM como predictor | 🟡 (la plataforma ya tiene el gateway LLM) |

### 1.16 Evaluación y combinación (🏆 `evaluacion`)

| Método | Estado |
|---|---|
| **Torneo de modelos**: AR lineal vs regularizados vs árboles vs boosting vs redes, mismo diseño, Diebold-Mariano contra el ganador, combinación simple | ✅ `torneo_modelos` |
| Curva de especificaciones (todas las transformaciones × rezagos × muestras × controles) | ✅ `curva_especificaciones` |
| Model Confidence Set (Hansen-Lunde-Nason) | ✅ dentro de `torneo_modelos` |
| Giacomini-White (precisión condicional) | 🟢 |
| Combinación con pesos (Bates-Granger, inversa del ECM, stacking temporal) | 🟢 |
| Evaluación de densidades (PIT, CRPS, pinball) | 🟢 — para pronósticos probabilísticos |
| Mincer-Zarnowitz (sesgo y eficiencia del pronóstico) | 🟢 |
| Pronósticos del REM vs modelos (¿le ganamos al consenso?) | 🟢 — el REM ya está en el catálogo |

---

## 2. Tu proyecto de activos dentro de la Cueva

### 2.1 Por qué es la misma plataforma

Macro y activos son series de tiempo con las mismas patologías: raíces unitarias, quiebres,
volatilidad que se agrupa, regímenes y poca historia relevante. Cambian tres cosas, y las tres
ya están resueltas:

1. **Frecuencia**: diaria o intradía. El catálogo de métodos acepta `diaria`, `semanal` y
   `nativa` (tal como viene el archivo, para intradía).
2. **Datos propios**: **Mis series** (`POST /api/v1/mis-series`, botón «Subir mis series» en la
   pantalla). Un CSV con fecha y columnas numéricas (OHLCV) se convierte en una serie por
   columna (`mis_<archivo>__<columna>`). Detecta `;` y coma decimal.
3. **La pregunta**: en activos casi nunca interesa el pronóstico puntual sino la
   **probabilidad de un evento** y su **calibración**. Por eso existen `probabilidad_evento`
   (clasificador calibrado) y `montecarlo_umbral` (probabilidad de tocar un nivel).

### 2.2 Los proyectos que mencionaste, uno por uno

| Proyecto | Cómo se hace hoy en la plataforma |
|---|---|
| Árboles de decisión | `ml_arbol` (reglas legibles), `ml_random_forest`, `ml_xgboost` + `ml_shap` |
| Support vector machines | `ml_svr` (regresión) y `probabilidad_evento` con `modelo=svm` (clasificación) |
| Clusters de volatilidad | `regimenes_volatilidad` (mezcla gaussiana sobre la volatilidad realizada + ACF de \|r\|), `garch_familia`, `cambio_de_punto` con costo `normal` |
| Intraday seasonality map | `estacionalidad_calendario` con `mapa=hora_x_dia` y `medida=volatilidad\|rendimiento\|acierto` |
| Factor neutrality check | `neutralidad_factores`: betas con HAC, alfa, betas móviles contra una tolerancia, descomposición del rendimiento |
| Regime-dependent momentum | `momentum_regimen` (régimen por volatilidad, tendencia o una serie externa como el riesgo país) |
| Monte Carlo portfolio risk | `montecarlo_cartera` (bootstrap por bloques conserva colas y correlaciones) |
| Pairs trading | `pares_trading` (formación / operación separadas) |
| Moving average crossover backtest | `cruce_medias` (con la grilla que muestra si el resultado es una isla o una meseta) |
| Monte Carlo en general | `montecarlo_cartera`, `montecarlo_umbral`, el bootstrap de `impacto_causal` |
| Predicción con información pasada, clusters y multivariados | `torneo_modelos` con `indeps`, `clusters_periodos`, `var_completo`, `bvar_minnesota` |
| Kalshi (mercados de predicción) | ver §2.4 |
| PCA, clusters, regresiones no lineales | `componentes_principales`, `clusters_series`, `clusters_periodos`, `transicion_suave`, `ml_*` |

### 2.3 El flujo para «aumentar la esperanza de que suceda un evento»

Lo que describiste (patrones, clusters, momentos y regímenes que cambian la probabilidad de
un evento) es, formalmente, **estimar P(evento | estado) y verificar que esa probabilidad
condicional esté bien calibrada fuera de muestra**. El flujo completo ya se puede armar
encadenando pasos con «Guardar como serie»:

```
1. Definir el estado         clusters_periodos / markov_switching / regimenes_volatilidad
   (en qué «clima» estamos)  → «Guardar como serie»: la probabilidad del régimen
          │
2. Medir la probabilidad      probabilidad_evento(dep=riesgo país, indeps=[régimen, brecha, …],
   condicional del evento     evento=sube_mas_de, umbral=0,10, horizonte=3)
          │                   → Brier skill score: ¿agrega sobre la frecuencia histórica?
          │                   → curva de calibración: ¿el 30 % que dice ocurre el 30 % de las veces?
3. Contrastar con la          montecarlo_umbral: la probabilidad que da la volatilidad sola
   simulación                 (si el clasificador no le gana, el «patrón» era ruido)
          │
4. Robustez                   curva_especificaciones / torneo_modelos / submuestras
          │
5. Sólo entonces: decidir     tamaño de posición (Kelly fraccional, 🟢), cobertura, alerta
```

La regla que la plataforma impone en cada paso: **un patrón sólo cuenta si mejora una
probabilidad fuera de muestra respecto de la frecuencia histórica**. Esa es la diferencia
entre encontrar un régimen y encontrar una historia linda.

### 2.4 Kalshi, Polymarket y mercados de predicción

Un contrato binario de Kalshi paga 1 si ocurre el evento; su precio es una probabilidad
implícita. Lo que la plataforma aporta:

- **Tu probabilidad**: `probabilidad_evento` (con predictores) o `montecarlo_umbral` (sólo
  con la dinámica de la serie). Para eventos de nivel («¿el dólar supera X el día D?») el
  Monte Carlo da las dos probabilidades que importan: tocar el nivel y terminar más allá.
- **Calibración**: se mide con Brier y curva de calibración; una probabilidad mal calibrada
  hace perder plata aunque «acierte» seguido.
- **Ventaja esperada**: `EV = p_modelo − precio_contrato` (menos comisiones). Con un modelo
  calibrado, Kelly fraccional define el tamaño. ✅ `apuesta_binaria`: elige el lado (SÍ/NO),
  da EV, Kelly, la p mínima para que convenga, y simula la banca con una p verdadera que
  difiere de la del modelo (la incertidumbre de tu p es lo que lleva a la ruina).
- **Sesgos conocidos** para investigar con los datos históricos del mercado: favorito-
  longshot (los eventos improbables están caros), sobrerreacción a noticias.
- **Dato**: Kalshi y Polymarket publican APIs con precios históricos de contratos; un
  adaptador en `cueva/fuentes/` los traería como series (la única capa que sale a la red).

---

## 3. Modelos generativos (la imagen: GAN, VAE, flujos, difusión)

Los cuatro aprenden la **distribución** de los datos para generar trayectorias nuevas. En
economía y finanzas sirven para tres cosas concretas:

| Uso | Para qué | Alternativa clásica con la que tiene que competir |
|---|---|---|
| **Escenarios sintéticos** | stress tests, Monte Carlo con dependencia realista | bootstrap por bloques, GARCH filtrado (ya están) |
| **Imputación de faltantes** | series con huecos (2002, cambios de base) | Kalman, Chow-Lin (ya están) |
| **Aumentar datos** para entrenar otros modelos | pocos años de historia | — (riesgo: el modelo aprende los artefactos del generador) |

| Familia | Idea (la de tu imagen) | Versiones para series de tiempo | Notas |
|---|---|---|---|
| **GAN** | un generador G(z) y un discriminador D(x) compiten | TimeGAN (Yoon et al. 2019), QuantGAN (Wiese et al. 2020, retornos con colas pesadas) | difíciles de entrenar; colapso de modos |
| **VAE** | codificador q(z\|x) → espacio latente → decodificador p(x\|z), maximiza la cota ELBO | TimeVAE (Desai et al. 2021) | estable; el espacio latente sirve también para clusters de trayectorias |
| **Flujos normalizantes** | transformación invertible f(x) con densidad exacta | RealNVP, MAF; flujos condicionales | dan la verosimilitud exacta: sirven para evaluar escenarios |
| **Difusión** | agrega ruido gaussiano de a poco y aprende a sacarlo | TimeGrad (Rasul et al. 2021), CSDI (imputación), TSDiff | el estado del arte en imputación y pronóstico probabilístico; caro |

**Cómo se evalúan** (sin esto no entran a la plataforma): reproducción de los hechos
estilizados (colas pesadas, agrupamiento de volatilidad, autocorrelación de |r| y no de r,
asimetría de apalancamiento), *discriminative score* (un clasificador no distingue real de
sintético) y *predictive score* (entrenar con sintético y evaluar con real).

**Decisión propuesta**: fase 🔴 con `torch` en la cola de trabajos. Antes de eso, un
generador de escenarios 🟢 con **cópula + marginales con colas (EVT) + GARCH-DCC** cubre el 80 %
de los usos con métodos interpretables. Un VAE chico en numpy es viable (el motor de
`redes_np` ya tiene Adam y backprop) si se quiere experimentar antes.

---

## 4. Modelos fundacionales de series de tiempo

Desde 2024 existen modelos pre-entrenados sobre millones de series que pronostican **sin
entrenar** (*zero-shot*): Chronos y Chronos-Bolt (Amazon), TimesFM (Google), Moirai (Salesforce),
Lag-Llama, TiRex, Toto (Datadog), TimeGPT (Nixtla, por API paga). En competencias recientes
(GIFT-Eval) rinden a la par o por encima de los modelos estadísticos en series cortas.

Cómo entran en la Cueva (🔴, extra `[deep]`):

1. Un método por modelo, con la misma interfaz que `ml_*`: entra al **torneo** y se juzga
   igual que todos. Si no le gana al paseo aleatorio en la inflación argentina, no se usa.
2. Corren en la cola de trabajos (minutos en CPU para los chicos: Chronos-Bolt-small, TiRex).
3. Advertencia permanente: fueron entrenados con datos que pueden incluir el período que se
   evalúa (fuga por pre-entrenamiento). La evaluación honesta usa sólo el tramo posterior a su
   fecha de corte.

---

## 5. Cómo está construido (lo que se hizo en esta sesión)

```
cueva/metodos/
├── contrato.py     Param, Metodo (la declaración) y Resultado (bloques tipados)
├── registro.py     @metodo(...), catálogo vivo, validación de argumentos, ejecución segura,
│                   comodines «familia:<id>» para las listas blancas de los agentes
├── insumos.py      series transformadas, panel alineado, matriz de diseño SIN fuga, eventos
├── validacion.py   origen móvil expansivo, métricas, Diebold-Mariano (HLN), R² fuera de muestra
├── redes_np.py     LSTM, GRU y ESN en numpy (gradiente verificado)
└── familias/       un módulo por familia (+ finanzas_avanzadas.py con la fase M1)
cueva/datos/mis_series.py   subir CSV propios y guardar salidas de métodos como series
web/mesa/metodos.{js,css}   la pantalla: catálogo, ficha, formulario y bloques en SVG
tests/test_metodos.py       125 tests; tests/sinteticas_metodos.py el banco de series
```

**Sumar un método** es escribir una función en la familia que corresponde:

```python
@metodo("mi_metodo", "Nombre visible", "pruebas", "¿Qué pregunta responde?",
        params=[P_SERIE(), P_FREQ, P_TRANSF, Param("k", "entero", "Rezagos", defecto=4, minimo=1)],
        supuestos=[...], trampas=[...], referencias=[...], etiquetas=[...])
def mi_metodo(sid, freq, transf, k):
    s, et = serie(sid, freq, transf)
    r = Resultado()
    r.metrica("Algo", 1.23)
    r.lineas("Gráfico", s.index, {et: s.values})
    r.veredicto("Qué significa", "verde")
    r.resumen = "Lo que lee el agente"
    return r
```

…y sumar un caso en `ARGS` de `tests/test_metodos.py` (si no, el test
`test_todo_metodo_tiene_caso` falla). La pantalla, la API y los agentes lo ven solos.

**Bloques que existen**: `metricas`, `tabla` (con columna de p-valores resaltada), `lineas`
(eje derecho, marcas verticales con eventos, estilos), `bandas` (pronóstico con IC),
`barras` (verticales u horizontales, con banda ±), `mapa_calor`, `dispersion` (con recta),
`texto`, `veredicto` (semáforo). Más `advertencias`, `series_salida` y `codigo`.

**Encadenar métodos**: toda serie derivada (tendencia, ciclo, factor, probabilidad de
régimen, residuo, contrafactual, pronóstico) tiene el botón «Guardar como serie»; queda en
Mis series y es insumo de cualquier otro método. Así se combinan estrategias: el ciclo de
Hamilton entra en un Markov; la probabilidad del Markov entra como predictor en un XGBoost; el
factor de un PCA entra en un VAR.

**Agentes**: `herramientas.ejecutar()` resuelve cualquier método del catálogo y
`declaraciones_herramientas()` arma su JSON Schema para function calling. Un skill puede
habilitar una familia entera con `herramientas: [familia:pruebas]`.

---

## 6. Principios anti-engaño (lo que la plataforma impone)

1. **Fuera de muestra o no existe.** Todo pronóstico se evalúa con origen móvil, contra el
   paseo aleatorio y la media histórica, con Diebold-Mariano. Validación cruzada aleatoria en
   series de tiempo: prohibida.
2. **Sin fuga.** La fila t sólo usa información de t; el escalado se re-estima en cada origen;
   los backtests operan en t+1 con la señal de t; los regímenes usan medianas expansivas.
3. **Elegir y evaluar con datos distintos.** El cruce de medias, los pares y el momentum
   eligen parámetros en la primera mitad y se evalúan en la segunda.
4. **Multiplicidad.** El torneo dice cuántos rivales empatan con el ganador y arma el conjunto
   de confianza de modelos (MCS); `sobreajuste_backtest` da PBO, Sharpe deflactado y White.
   Las pruebas de burbuja sólo fechan episodios si la prueba global rechaza.
5. **Robustez visible.** Curva de especificaciones, grillas de parámetros, placebos.
6. **Causalidad declarada.** Todo método causal dice su supuesto de identificación en el
   veredicto.
7. **Estimación ≠ dato.** Lo que sale de desagregación, Kalman o generativos queda marcado
   como estimación (`docs/DATOS.md`).
8. **Probabilidades calibradas.** Brier y calibración, no sólo acierto.

---

## 7. Hoja de ruta propuesta

| Fase | Contenido | Esfuerzo |
|---|---|---|
| **M0 — hecho (esta sesión)** | 90 métodos, pantalla, Mis series, encadenamiento, puente con agentes | ✅ |
| **M1 — activos y robustez** | ✅ hecho en la misma sesión: GSADF, PBO/Sharpe deflactado/White, MCS, `apuesta_binaria`, triple barrera purgada, CAR, Diebold-Yilmaz, DCC, EVT, Nelson-Siegel, conformal (10 métodos, 100 en total). Falta: SPA de Hansen, volatilidad objetivo, Svensson | ✅ / 🟢 |
| **M2 — econometría que falta** | SVAR (largo plazo y signos), descomposición histórica, LP con estado, Gregory-Hansen, NARDL, raíz unitaria con 2 quiebres, HEGY, MIDAS, nowcasting DFM, X-13 | 🟢/🟡 ~1-2 semanas |
| **M3 — ML avanzado** | conformal, cuantílico con boosting, calibración, multi-horizonte, Optuna, DML, CatBoost, DTW, matrix profile | 🟢/🟡 ~1 semana |
| **M4 — cola de trabajos** | lo que tarda minutos sale del request (es la fase 4 del roadmap general) | 🟡 |
| **M5 — profundo** | extra `[deep]` con torch: N-BEATS/N-HiTS, TFT, DeepAR, modelos fundacionales, generativos (VAE → difusión) | 🔴 |
| **M6 — el trabajo completo** | el Estudio como cadena de pasos reproducible: «re-correr todo con datos nuevos», exportar a cuaderno Jupyter / LaTeX, y que el Laboratorio cite pasos por id | 🟡 |

### Decisiones abiertas para Martín

1. **¿M2 (econometría) o M3 (ML avanzado) después de M1?** M1 quedó hecho en esta sesión.
2. **¿Fuente de datos de activos?** Subir CSV ya funciona. Para automatizar: ¿qué proveedor?
   (Yahoo Finance no tiene API oficial; Alpha Vantage, Tiingo, Polygon, o el BYMA/Rava para
   activos argentinos). Va en `cueva/fuentes/`.
3. **¿`torch` en el servidor?** Define si M5 corre en la misma máquina o en un worker aparte.
4. **¿Los agentes pueden correr métodos «minutos» por su cuenta?** Hoy la lista blanca lo
   permite si el skill lo declara; con la cola de trabajos convendría pedir confirmación.

---

## 8. Bibliografía base (para el RAG y las fichas)

- Hamilton (1994), *Time Series Analysis*. — Enders (2015), *Applied Econometric Time Series*
  (**sigue faltando en el corpus**). — Lütkepohl (2005), *New Introduction to Multiple Time
  Series Analysis*. — Kilian y Lütkepohl (2017), *Structural VAR Analysis*.
- Hyndman y Athanasopoulos (2021), *Forecasting: Principles and Practice* (3.ª ed., libre).
- Durbin y Koopman (2012), *Time Series Analysis by State Space Methods*. — Kim y Nelson (1999).
- Angrist y Pischke (2009), *Mostly Harmless Econometrics*. — Cunningham (2021), *Causal
  Inference: The Mixtape* (libre). — Abadie (2021), JEL, control sintético.
- Hastie, Tibshirani y Friedman (2009), *The Elements of Statistical Learning* (libre). —
  James et al. (2023), *ISLP* (libre, con Python).
- Goodfellow, Bengio y Courville (2016), *Deep Learning* (libre).
- López de Prado (2018), *Advances in Financial Machine Learning*. — Bailey, Borwein, López de
  Prado y Zhu (2014), *Pseudo-Mathematics and Financial Charlatanism*.
- Tsay (2010), *Analysis of Financial Time Series*. — McNeil, Frey y Embrechts (2015),
  *Quantitative Risk Management*.
- Gneiting y Raftery (2007), *Strictly Proper Scoring Rules*. — Diebold y Mariano (1995).
- Makridakis, Spiliotis y Assimakopoulos (2020, 2022), competencias M4 y M5.
- Ansari et al. (2024), Chronos. — Das et al. (2024), TimesFM. — Woo et al. (2024), Moirai.
- Yoon, Jarrett y van der Schaar (2019), TimeGAN. — Rasul et al. (2021), TimeGrad. —
  Tashiro et al. (2021), CSDI.
