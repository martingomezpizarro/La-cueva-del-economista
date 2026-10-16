# Sala-i-Martin (1997) — "I Just Ran Two Million Regressions"

> Fuente: *American Economic Review* 87(2), Papers and Proceedings, May 1997, pp. 178-183.
> Texto extraído por La Cueva-LM desde copia de acceso abierto (puede tener ruido de OCR).
> Categoría: 09_robustez. Tema: robustez de determinantes / alternativa al extreme-bounds.

## Idea central
Frente al *extreme-bounds test* de Leamer (1985), aplicado por Levine & Renelt (1992) a las
regresiones de crecimiento —que concluye que **casi ninguna variable es "robusta"**—, Sala-i-Martin
propone **abandonar la etiqueta binaria robusto/no-robusto** y, en su lugar, mirar **toda la
distribución** de los estimadores del coeficiente de cada variable a través de los miles de modelos.

## El problema
La metodología típica corre regresiones de corte transversal:
`y = a + β1·x1 + … + βn·xn + ε`, donde y es el crecimiento. La teoría no dice qué variables xj
pertenecen al modelo "verdadero": una variable xi puede ser significativa con x2, x3 y dejar de
serlo al incluir x4. ¿Cuáles están realmente correlacionadas con el crecimiento?

## El extreme-bounds test (Leamer / Levine-Renelt)
Para una variable z, se estiman regresiones `y = aj + βy·y + βz·z + βx·xj + ε`, donde xj son hasta
tres variables tomadas de un pool de N. Se busca la cota inferior (mínimo de βz − 2σz) y la superior
(máximo de βz + 2σz). **Si el signo cambia o se vuelve insignificante en una sola regresión, z se
declara "no robusta".** Es un test demasiado fuerte: con suficientes regresiones, casi cualquier
variable lo falla.

## La propuesta: mirar toda la distribución
En vez del test extremo, calcular el **CDF(0)**: la fracción de la densidad del estimador de βz que
queda de un lado de cero. Si el 95% de la densidad de β1 está a la derecha de cero y solo el 52% de
β2, entonces la variable 1 es más probablemente relevante que la 2.
- **Caso normal:** media ponderada de los M estimados puntuales, con pesos proporcionales a la
  verosimilitud integrada de cada modelo (dar más peso a los modelos más probablemente verdaderos);
  análogo para la varianza; luego CDF(0) con la normal estándar.
- **Caso no normal:** promediar los CDF(0) individuales de cada regresión con los mismos pesos.
- Advertencia: si hay modelos con buen ajuste **espurio** (p. ej. variables endógenas), los pesos
  pueden estar dominados por ellos; conviene comparar con el promedio **no ponderado**.

## Diseño empírico
62 variables del literatura; 3 fijas en todas las regresiones (ingreso en 1960, esperanza de vida
1960, matrícula primaria 1960, elegidas a priori por ser robustas y poco endógenas); las 59
restantes combinadas de a tres → ~30.856 regresiones por variable, ~2 millones en total. Variables
medidas al inicio del período (1960) para minimizar endogeneidad.

## Resultados
22 de 59 variables resultan "significativas" (CDF(0) ponderado > 0.95), entre ellas:
inversión en equipo, años de economía abierta, fracción confuciana/musulmana/budista (positivas),
rule of law, derechos políticos y libertades civiles, dummies de África subsahariana y América
Latina (negativas), revoluciones/golpes y guerra (negativas), distorsiones cambiarias, fracción
del PBI en minería, exportaciones primarias, grado de capitalismo, latitud absoluta, etc. El gasto
público, la sofisticación financiera y la inflación **no** aparecen como significativos en forma lineal.

## Conclusión
Si interesa el coeficiente de una variable particular, el panorama de la literatura empírica de
crecimiento **no** es el pesimista "nada es robusto" del extreme-bounds: un número sustancial de
variables está fuertemente relacionado con el crecimiento cuando se mira la distribución completa.

## Por qué importa para La Cueva (especialista 🔬 robustez/minería)
Es el antecedente directo de "minar miles de especificaciones para separar lo robusto del ruido":
el agente debe (a) reportar la **distribución completa** de coeficientes, no la regresión que
conviene; (b) usar promedios ponderados por verosimilitud con cautela ante endogeneidad/espuria;
(c) cuidar que el universo de especificaciones sea razonable.
