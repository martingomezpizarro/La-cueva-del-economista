---
metodo: Pronóstico, machine learning y deep learning para series
tema: 07_pronostico
fuentes: ["Hyndman-Athanasopoulos FPP3 (2021)", "Diebold-Mariano (1995)", "Athey-Imbens (2019)", "Oreshkin N-BEATS (2020)", "Survey arXiv:2401.13912 (2024)"]
---

# Pronóstico, ML y deep learning

## ¿Qué es / para qué sirve?
Predecir valores futuros y evaluar/combinar pronósticos. Va de los modelos clásicos (ARIMA, ETS)
a ML y **foundation models** de series (zero-shot).

## Menú de métodos (de menos a más complejo)
- **Benchmarks ingenuos:** naïve, media, deriva. Siempre primero (si no les ganás, no sigas).
- **Clásicos:** ARIMA, ETS (suavizado exponencial), regresión dinámica.
- **ML tabular:** árboles/boosting (XGBoost) con rezagos y features de calendario.
- **Deep learning:** N-BEATS, DeepAR, temporales con atención/transformers.
- **Foundation models:** TimeGPT, TimesFM (pronóstico zero-shot, frontera 2024-2026).

## Supuestos / buenas prácticas
- **Validación temporal** (rolling/expanding window), nunca k-fold aleatorio (filtra el futuro).
- Separar train/validation/test respetando el orden temporal.
- Comparar siempre contra un benchmark ingenuo.

## Cuándo usarlo
- Horizontes de pronóstico; relaciones no lineales complejas; muchas series a la vez.

## Cuándo NO usarlo / límites
- Pocos datos → DL sobreajusta; un ARIMA simple suele ganar.
- DL es **caja negra**: si necesitás interpretar mecanismos, preferí modelos estructurales.

## ⚠️ Errores típicos (lo que el agente debe advertir)
- **Data leakage:** usar información del futuro (normalizar con toda la muestra, k-fold aleatorio).
- No comparar contra benchmark ingenuo (y creer que el modelo "anda bien").
- Evaluar in-sample en vez de out-of-sample.
- Comparar modelos sin **Diebold-Mariano** (diferencia de error puede no ser significativa).
- Sobreajuste de DL con series cortas.

## Cómo se interpreta el resultado
- Métricas out-of-sample (RMSE, MAE, MASE) **relativas al benchmark**.
- **Diebold-Mariano** para decir si un modelo es significativamente mejor que otro.
- Reportar el esquema de validación, el horizonte y la incertidumbre (intervalos de predicción).
