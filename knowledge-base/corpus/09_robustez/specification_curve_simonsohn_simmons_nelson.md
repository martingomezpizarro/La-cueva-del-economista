# Simonsohn, Simmons & Nelson — Specification Curve Analysis

> Fuente: "Specification Curve: Descriptive and Inferential Statistics on All Reasonable
> Specifications" (working paper, 2018; publicado en *Nature Human Behaviour*, 2020).
> Texto extraído/estructurado por La Cueva-LM desde copia de acceso abierto (urisohn.com).
> Categoría: 09_robustez.

## Abstract
Los resultados empíricos dependen de decisiones analíticas defendibles, arbitrarias y motivadas.
Esas decisiones introducen sesgo (hacia la narrativa del autor) y variabilidad no incluida en los
errores estándar. Para atacar este ruido y sesgo, se introduce el **Specification-Curve Analysis**,
en tres pasos: (i) identificar el conjunto de especificaciones teóricamente justificadas,
estadísticamente válidas y no redundantes; (ii) mostrar los resultados gráficamente; (iii) hacer
inferencia conjunta sobre todas las especificaciones. Con tres hallazgos de dos papers: uno resulta
robusto, uno débil, uno nada robusto.

## El problema
Para convertir una hipótesis en un test, hay que tomar decisiones (qué variables usar, qué
observaciones excluir, qué forma funcional). Muchas son arbitrarias y defendibles. Lo que se reporta
en un paper (π) es una muestra **pequeña, curada y no independiente** del conjunto de todas las
especificaciones razonables (Π). Eso hace que los resultados sean más ruidosos de lo reportado (los
SE no incluyen la variación entre especificaciones) y probablemente sesgados (selección post-hoc).

## La solución
Reportar el resultado de **todas (o una muestra aleatoria grande de) las "especificaciones
razonables"**: las que son (1) tests sensatos de la pregunta, (2) estadísticamente válidas, (3) no
redundantes. Specification-curve no termina los debates sobre qué especificaciones correr, pero los
**hace transparentes**: separa el desacuerdo por "qué es válido" (distintos círculos rojos) del
desacuerdo por "qué pocas se reportaron" (distintos puntos grises).

## Relación con enfoques previos
- **Extreme bounds analysis** (Leamer 1983; Sala-i-Martin 1997): correr todas las combinaciones de
  covariables; robusto si significativo en todas (Leamer) o si el promedio ponderado de los t lo es
  (Sala-i-Martin).
- **Young & Holsteen (2015):** estimar muchas especificaciones (no solo covariables: también forma
  funcional y modelo) y graficar la distribución.
- Specification-curve agrega: (i) guía paso a paso para generar el conjunto; (ii) curva descriptiva
  que identifica qué decisiones son consecuentes; (iii) **test de significancia conjunta** formal.
- Complementa los **planes de pre-análisis**: uno puede pre-registrar la curva de especificación
  entera, en vez de pre-comprometerse a una sola especificación.

## Decisiones arbitrarias vs. teóricas
- **Covariables NO suelen ser tema de robustez:** qué controlar suele guiarse por teoría; incluir/
  excluir covariables que uno cree que pertenecen no es un test de robustez (es evaluar el impacto
  de heterogeneidad no observada).
- **Operacionalizaciones arbitrarias SÍ:** definiciones de "largo plazo" (¿15, 16, 26 meses?),
  cómo medir una variable (satisfacción vs felicidad; empleo full-time equivalente). Los resultados
  deberían ser robustos a estas decisiones atheóricas.

## Los tres pasos
1. **Identificar el conjunto de especificaciones:** enumerar las decisiones analíticas necesarias,
   sus alternativas razonables, y combinarlas (eliminando inválidas/redundantes). Si el conjunto es
   enorme, tomar una muestra aleatoria.
2. **Estimar y describir (curva descriptiva):** muestra la distribución de estimados y **qué
   decisiones** producen distintos resultados (panel inferior con las decisiones detrás de cada punto).
3. **Inferencia conjunta:** ¿cuán inconsistente es el conjunto con la hipótesis nula? Se resuelve por
   **permutación** (datos con asignación aleatoria) o **bootstrap** (sin ella), generando la
   distribución esperada de curvas bajo H0. Se usa el **signo dominante** (la mayoría de los estimados
   de un dataset comparten signo por dependencia) y estadísticos como: mediana del estimado, fracción
   con el signo predicho, fracción con signo predicho y p<.05.

## Ejemplos
- **Huracanes con nombre femenino más letales** (Jung et al. 2014): 1.728 especificaciones; la
  mayoría del signo predicho pero **casi ninguna significativa**; el test conjunto **no rechaza** H0
  (p≈.85). PNAS podría haber publicado ~1.700 cartas mostrando que el efecto desaparece. → no robusto.
- **Discriminación por nombres "negros"** (Bertrand & Mullainathan 2004): la curva observada cae
  **fuera** del IC del 95% bajo el nulo → la H0 se rechaza (callbacks menores). El segundo hallazgo
  (menor beneficio del CV de calidad) es **menos claro/robusto**.

## Conclusiones
Specification-curve es una solución **parcial** al reporte selectivo. No elimina la subjetividad:
solo un experto (no un algoritmo) define el conjunto de especificaciones válidas, y distintos
expertos definen conjuntos distintos. Pero hace **transparente** de dónde viene el desacuerdo y
reduce el reporte selectivo. Reportar 1.728 especificaciones es órdenes de magnitud más que las 1-20
típicas, y contiene mucha menos selección post-hoc.

## Por qué importa para La Cueva (especialista 🔬 robustez/minería)
Es el marco moderno para "ver lo que el ojo no ve" entre miles de modelos: el agente debe (a)
construir el universo de especificaciones con criterio, (b) reportar la curva entera (no el punto
conveniente), (c) hacer inferencia conjunta por permutación/bootstrap, (d) distinguir decisiones
arbitrarias (sí robustez) de teóricas (no).
