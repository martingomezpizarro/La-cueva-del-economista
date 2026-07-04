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
