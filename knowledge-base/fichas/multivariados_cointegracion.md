---
metodo: VAR / SVAR / VECM / ARDL (multivariados y cointegración)
tema: 04_multivariados
fuentes: ["Lütkepohl (2005)", "Johansen (1995)", "Engle-Granger (1987)", "Pesaran-Shin-Smith (2001)", "Kilian-Lütkepohl (2017)"]
---

# Multivariados y cointegración (VAR · SVAR · VECM · ARDL)

## ¿Qué es / para qué sirve?
Familia de modelos para varias series que se influyen mutuamente. **VAR**: dinámica conjunta sin
imponer teoría. **SVAR**: VAR + identificación para leer shocks estructurales. **VECM**: VAR para
series I(1) **cointegradas** (relación de largo plazo + ajuste de corto). **ARDL/bounds**: relación
de nivel cuando las variables mezclan I(0) e I(1).

## El árbol de decisión (orden correcto)
1. Verificar **orden de integración** de cada serie (ADF/KPSS/DF-GLS) → ¿I(0), I(1)?
2. Si todas I(0): **VAR en niveles**.
3. Si hay I(1): testear **cointegración** (Johansen si todas I(1); ARDL/bounds si mezcla).
   - cointegran → **VECM** (o ARDL con ECM).
   - no cointegran → **VAR en diferencias**.
4. Elegir rezagos por AIC/BIC/HQ y verificar residuos ruido blanco.

## Supuestos
- Estabilidad (raíces del VAR dentro del círculo unitario).
- Residuos sin autocorrelación ni heterocedasticidad fuerte; idealmente normales.
- VECM: el rango de cointegración (Johansen, traza/máx-eigenvalue) está bien determinado.
- SVAR: la identificación (Cholesky, signo, largo plazo) está **justificada por teoría**, no por defecto.

## Cuándo usarlo
- Relaciones dinámicas entre macro/financieras (ej. EMBI ↔ reservas ↔ tipo de cambio).
- Pronóstico multivariado, funciones impulso-respuesta, descomposición de varianza.

## Cuándo NO usarlo / límites
- Pocas observaciones frente a (variables × rezagos): se sobreajusta rapidísimo (maldición de dimensionalidad).
- Si lo que querés es **efecto causal de una intervención**, esto no alcanza → inferencia causal (ficha causal).

## ⚠️ Errores típicos (lo que el agente debe advertir)
- **VAR en niveles con series I(1) no cointegradas** → regresión espuria. Diferenciar o ir a VECM.
- Confundir **Granger** (precedencia predictiva) con causalidad estructural.
- Leer una **IRF de un SVAR mal identificado** como si fuera causal.
- Ignorar **quiebres estructurales**: cambian el rango de cointegración y la estabilidad.
- Elegir rezagos por un solo criterio sin chequear residuos.

## Cómo se interpreta el resultado
- **VECM:** el vector de cointegración = relación de **largo plazo** (equilibrio); los coeficientes α =
  **velocidad de ajuste** al equilibrio (signo correcto y significativo = la serie corrige desvíos).
- **IRF:** respuesta dinámica de una variable a un shock de otra; mirar signo, magnitud y persistencia.
- **Descomposición de varianza:** qué fracción de la variabilidad de Y explica cada shock.
- Reportar siempre rezagos, test de cointegración (estadístico y valor crítico) y diagnóstico de residuos.
