---
metodo: Test de causalidad de Granger
tema: 04_multivariados
fuentes: ["Enders - Applied Econometric Time Series, cap. 5"]
---

# Test de causalidad de Granger

## ¿Qué es / para qué sirve?
Evalúa si los valores pasados de X ayudan a predecir Y por encima de los pasados de Y. Es un
test de **precedencia temporal predictiva**, dentro de un VAR.

## Supuestos
- Series **estacionarias** (o transformadas a estacionarias). Con series I(1) cointegradas,
  usar el marco VECM, no un VAR en niveles.
- El VAR está bien especificado (lags adecuados, residuos ruido blanco).

## Cuándo usarlo
- Para explorar relaciones de precedencia entre variables en un sistema VAR.

## Cuándo NO usarlo / límites
- No con series no estacionarias sin tratar (resultados espurios).
- No para inferir mecanismos causales estructurales.

## ⚠️ Errores típicos (lo que el agente debe advertir)
- **Confundir Granger con causalidad real.** "X causa-Granger a Y" = X precede/predice a Y,
  NO que X sea la causa económica de Y.
- Correr Granger sobre series I(1) sin diferenciar ni verificar cointegración.
- Interpretar la ausencia de causalidad como ausencia de relación (puede ser contemporánea).
- Sensibilidad al número de lags: cambiar lags puede cambiar la conclusión.

## Cómo se interpreta el resultado
p-valor < α (ej. 0.05) ⇒ se rechaza "X no causa-Granger a Y" ⇒ los pasados de X aportan a
predecir Y. Reportar siempre el lag usado y verificar robustez a distintos lags.
