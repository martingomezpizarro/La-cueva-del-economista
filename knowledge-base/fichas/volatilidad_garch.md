---
metodo: Volatilidad condicional (ARCH/GARCH y familia)
tema: 05_volatilidad
fuentes: ["Tsay (2010)", "Engle (1982)", "Bollerslev (1986)", "Nelson EGARCH (1991)", "GJR (1993)", "Francq-Zakoïan (2019)"]
---

# Volatilidad condicional (familia GARCH)

## ¿Qué es / para qué sirve?
Modela cómo cambia la **varianza** de una serie en el tiempo (volatility clustering: tormentas
seguidas de calma). Clave en finanzas y riesgo (retornos, spreads, tipo de cambio).

## Menú de modelos
- **ARCH(q):** varianza depende de shocks pasados al cuadrado.
- **GARCH(p,q):** agrega varianza pasada; el caballito de batalla (suele bastar GARCH(1,1)).
- **EGARCH / GJR-GARCH:** capturan **asimetría** (las malas noticias suben más la volatilidad).
- **GARCH-M:** la volatilidad entra en la media (prima por riesgo).
- Distribución de errores: t-Student o GED para capturar **colas pesadas**.

## Supuestos
- Se modela sobre **retornos/variaciones** (serie de media aproximadamente estacionaria), no niveles.
- La media está bien especificada antes de modelar la varianza.

## Cuándo usarlo
- Series financieras de alta frecuencia con clustering de volatilidad; cálculo de VaR; riesgo país.

## Cuándo NO usarlo / límites
- Series de baja frecuencia o sin heterocedasticidad condicional (un test ARCH-LM lo confirma).
- No sustituye un modelo de la media: es un complemento.

## ⚠️ Errores típicos (lo que el agente debe advertir)
- Ajustar GARCH a **niveles** en vez de retornos.
- No testear **efecto ARCH** antes (test ARCH-LM de Engle).
- Ignorar la **asimetría** cuando existe (usar EGARCH/GJR).
- Sobre-parametrizar (GARCH de orden alto rara vez mejora a GARCH(1,1)).
- Asumir normalidad cuando hay colas pesadas.

## Cómo se interpreta el resultado
- **α + β ≈ persistencia** de la volatilidad: cerca de 1 → los shocks de volatilidad duran mucho.
- En EGARCH/GJR, el término asimétrico significativo confirma efecto apalancamiento.
- Reportar el test ARCH-LM previo, la distribución usada y diagnósticos sobre residuos estandarizados.
