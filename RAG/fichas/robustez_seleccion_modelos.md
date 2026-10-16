---
metodo: Robustez y selección de modelos (EBA, curva de especificación, model averaging)
tema: 09_robustez
fuentes: ["Leamer (1983, 1985)", "Sala-i-Martin (1997)", "Granger-Uhlig (1990)", "Simonsohn et al. (2020)", "Hansen (2007)", "Steel (2020)"]
---

# Robustez y selección de modelos (minería de especificaciones)

## ¿Qué es / para qué sirve?
Cuando hay muchas variables candidatas y muchas formas de modelar, correr **miles de
especificaciones** y separar lo **robusto** del artefacto. Es el cazador de patrones: ve lo que el
ojo humano no puede entre 120.000 modelos.

## Menú de técnicas
- **Extreme Bounds Analysis (EBA):** una relación es robusta si se mantiene en (casi) todas las
  especificaciones. Leamer = en todas; **Sala-i-Martin = promedio ponderado de los t**.
- **Curva de especificación / multiverso:** correr todas las combinaciones razonables (controles,
  forma funcional, muestra) y graficar la distribución de resultados.
- **Model averaging:** en vez de elegir un modelo, **promediar** ponderando por calidad
  (BMA bayesiano — Raftery; least-squares averaging — Hansen).
- **Selección con ML:** LASSO/elastic-net para muchas variables (Belloni-Chernozhukov).

## Supuestos / buenas prácticas
- El **universo de especificaciones** se define con criterio (no todo vale: deben ser razonables).
- Las series ya pasaron el control (estacionariedad, etc.) antes de minar.

## Cuándo usarlo
- Identificar **determinantes robustos** (ej. qué variables explican el EMBI+ de verdad).
- Chequear si un resultado "lindo" sobrevive a cambiar controles/muestra.

## Cuándo NO usarlo / límites
- No reemplaza la teoría: encontrar correlación robusta ≠ mecanismo causal.
- Con muchísimas pruebas, sube el riesgo de **falsos positivos** (multiple testing): ajustar.

## ⚠️ Errores típicos (lo que el agente debe advertir)
- **p-hacking / cherry-picking:** reportar solo la especificación que "funciona". La curva entera es el dato.
- Minar sobre series I(1) sin tratar → robustez de relaciones **espurias**.
- Confundir robustez estadística con relevancia económica.
- No corregir por **comparaciones múltiples**.

## Cómo se interpreta el resultado
- En EBA: una variable es **robusta** si su signo se mantiene y es significativa en la gran mayoría
  de modelos (o el promedio de t supera el umbral).
- La **curva de especificación** muestra cuán sensible es la conclusión: una nube apretada de un
  solo signo = robusto; una nube que cruza el cero = frágil.
- Reportar siempre el universo de especificaciones y la fracción que sostiene el resultado.
