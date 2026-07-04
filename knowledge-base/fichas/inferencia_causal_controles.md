---
metodo: Inferencia causal y controles (control sintético, DiD, IV, RDD)
tema: 08_causal
fuentes: ["Cunningham — Mixtape (2021)", "Huntington-Klein — The Effect (2022)", "Angrist-Pischke (2009)", "Abadie et al. (2010, 2021)", "Callaway-Sant'Anna (2021)"]
---

# Inferencia causal y controles

## ¿Qué es / para qué sirve?
Estimar el **efecto causal** de una intervención, no solo correlación o precedencia. Construye el
**contrafáctico**: qué habría pasado sin el tratamiento. Es otra lógica que la de series de tiempo
predictiva.

## Menú de diseños
- **Control sintético (SCM):** arma un "país/unidad sintético" combinando controles para imitar al
  tratado antes de la intervención (ideal para un caso, ej. una reforma en Argentina).
- **Diferencias-en-diferencias (DiD):** compara el antes/después de tratados vs no tratados.
- **Variables instrumentales (IV):** cuando hay endogeneidad y existe un instrumento válido.
- **Regresión discontinua (RDD):** cuando el tratamiento se asigna por un umbral.

## Supuestos (los que hacen o rompen el diseño)
- **DiD:** tendencias paralelas (los grupos habrían evolucionado igual sin tratamiento).
- **SCM:** buen ajuste pre-tratamiento y un "donor pool" creíble.
- **IV:** relevancia (instrumento fuerte) + exclusión (afecta Y solo vía X).
- **RDD:** continuidad en el umbral; no manipulación del corte.

## Cuándo usarlo
- Evaluar el impacto de una política, reforma, default, cambio de régimen (eventos discretos).

## Cuándo NO usarlo / límites
- Sin variación de tratamiento creíble, no hay diseño causal: no forzar.
- Datos puramente de series de tiempo agregadas suelen no identificar efectos causales limpios.

## ⚠️ Errores típicos (lo que el agente debe advertir)
- **DiD con timing escalonado** usando TWFE clásico → sesgo (Goodman-Bacon, de Chaisemartin):
  usar estimadores modernos (Callaway-Sant'Anna).
- Validar tendencias paralelas solo mirando el gráfico, sin test de pre-tendencias.
- **Instrumentos débiles** (F bajo) → inferencia inválida.
- Confundir un buen ajuste predictivo con identificación causal.

## Cómo se interpreta el resultado
El estimado es el **efecto del tratamiento** (ATT/LATE según el diseño), no una elasticidad
general. Reportar el supuesto de identificación, su chequeo (placebos, pre-tendencias) y el
contrafáctico usado. Siempre distinguir efecto causal de asociación.
