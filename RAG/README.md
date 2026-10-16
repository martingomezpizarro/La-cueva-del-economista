# Base de conocimiento

Dos componentes:

## 1. `corpus/` — la bibliografía
PDFs, papers y trabajos organizados por tema. **No se versionan en git** (son pesados);
viven localmente / en almacenamiento aparte. Taxonomía propuesta:

| Carpeta | Tema | Bibliografía núcleo |
|---|---|---|
| `01_fundamentos/` | Estacionariedad, raíces unitarias, ACF/PACF, ruido blanco | Enders cap. 2-4, Hamilton |
| `02_univariados/` | AR, MA, ARIMA, Box-Jenkins, SARIMA | Enders, Box-Jenkins |
| `03_volatilidad/` | ARCH, GARCH, EGARCH | Enders cap. 3 |
| `04_multivariados/` | VAR, SVAR, IRF, FEVD | Enders cap. 5, Lütkepohl |
| `05_cointegracion/` | Engle-Granger, Johansen, VECM, ARDL bounds | Enders cap. 6, Pesaran |
| `06_quiebres_nolineal/` | Quiebres estructurales, regímenes | Enders cap. 7 |
| `07_pronostico/` | Evaluación, Diebold-Mariano, backtesting | Hamilton |
| `08_ml_dl/` | LSTM, GRU, Transformers para series | papers |
| `09_argentina/` | Riesgo país, balanza de pagos, deuda, inflación | INDEC/BCRA, papers locales |

## 2. `fichas/` — las fichas "cara-al-agente"
Resúmenes de 1 página por tema/método con **supuestos, errores típicos y cuándo usar**.
Son las que el usuario va escribiendo mientras estudia/curaduría (incluso con NotebookLM).
Usar `_plantilla_ficha.md` como base. Ejemplo real: `granger_causalidad.md`.
