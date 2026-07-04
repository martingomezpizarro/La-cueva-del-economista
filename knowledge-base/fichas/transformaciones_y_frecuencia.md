---
metodo: Transformaciones y cambio de frecuencia
tema: 03_transformaciones
fuentes: ["Hyndman-Athanasopoulos FPP3 (2021)", "Box-Cox (1964)", "Chow-Lin (1971)", "Harvey (1989)", "Sax-Steiner tempdisagg (2013)"]
---

# Transformaciones y cambio de frecuencia

## ¿Qué es / para qué sirve?
Preparar las series para modelar: estabilizar varianza, estacionarizar, desestacionalizar, deflactar
y **convertir de frecuencia** (mensualizar una trimestral, etc.). Cada elección cambia lo que mide la serie.

## Menú de métodos (con criterio)
- **Estabilizar varianza:** log o Box-Cox (cuando la varianza crece con el nivel).
- **Estacionarizar:** diferenciar (Δ), o quitar tendencia/estacionalidad. No sobre-diferenciar.
- **Desestacionalizar:** X-13ARIMA-SEATS (oficial) o STL.
- **Deflactar:** dividir por índice de precios con **año base explícito** (real vs nominal).
- **Cambio de frecuencia (desagregación temporal):**
  - **Interpolación simple** (lineal/spline): rápida, pero inventa dinámica.
  - **Chow-Lin / Fernández / Litterman:** usan una serie indicador de alta frecuencia (mejor).
  - **Denton:** benchmarking a totales (preserva el agregado).
  - **Filtro de Kalman / espacio de estados (Harvey):** el más general; modela el proceso latente.

## Supuestos
- La transformación es **reversible y documentada** (se puede deshacer e informar).
- En desagregación con indicador: el indicador está correlacionado con la serie objetivo.

## Cuándo NO usarlo / límites
- No deflactar con un índice de base o cobertura distinta a la serie.
- No desagregar a una frecuencia que la fuente no soporta como si fuera dato real.

## ⚠️ Errores típicos (lo que el agente debe advertir)
- **Sobre-diferenciar** (introduce MA negativa, infla la varianza).
- Tomar log de series con ceros o negativos sin tratarlas.
- Interpolar con spline y luego **tratar los puntos interpolados como observaciones reales** en los tests.
- Deflactar dos veces, o mezclar año base.
- No registrar qué transformación se aplicó (rompe reproducibilidad).

## Cómo se interpreta el resultado
Toda serie transformada debe llevar la **cadena de transformaciones** en su ficha. Al pasar a
modelar, recordar que diferenciar cambia la interpretación (niveles → tasas/variaciones) y que la
desagregación temporal **agrega incertidumbre** que conviene explicitar.
