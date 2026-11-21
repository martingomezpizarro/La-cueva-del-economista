# Valuación de empresas en la Cueva — diseño y decisiones

Documento vivo del módulo de valuación. Manda sobre la plantilla `valuacion_empresa`
(`cueva/sesiones/plantillas.py`). Se trabaja con el método de la Cueva: Aprender → Diseñar →
Construir y probar en vivo → Al informe. Nada se construye sin el visto bueno de Martín, y la
plataforma **no valúa por él**: arma la estructura, explica y calcula lo que él configura.

## 1. Principios (decididos 2026-11-21)

1. **Ningún método es obligatorio para un tipo de empresa.** Al elegir la empresa no se la manda
   a un camino fijo: la Cueva puede *sugerir* qué métodos suelen usarse (industrial/tecnológica,
   financiera, minera o commodity), pero cualquiera se puede usar y se pueden mezclar.
2. **Todo termina en la Mesa de investigación.** La plantilla arma el proyecto con los bloques,
   la metodología y la ficha de cada método; después se le mete mano: agregar métodos, correr
   dos a la vez y comparar, cambiar supuestos, sumar series.
3. **Cada método es un método de la Cueva** (`@metodo`, familia `valuacion`): parámetros tipados
   con su (i) (`Param.ayuda`), supuestos, trampas y referencias declarados, y un `Resultado` con
   bloques. Así sirve solo, dentro de la plantilla, desde los agentes y encadenado con otros.
4. **Los bloques arrancan vacíos.** Cada insumo tiene «Traer de la Ficha», que muestra el valor y
   su procedencia (SEC, FRED, Yahoo…); el usuario decide si lo usa o pone otro.
5. **Historia antes que foto.** Donde se pueda, el insumo se muestra en el tiempo (beta rodante,
   tasa del Tesoro, costo de la deuda) para ver si el número de hoy es representativo.
6. **Herramientas transversales a todos los métodos**:
   - *Sensibilidad*: dos parámetros cualesquiera → mapa de calor del valor.
   - *Escenarios*: juegos de parámetros con nombre (y probabilidad, si se quiere).
   - *Monte Carlo*: distribuciones sobre los parámetros → distribución del valor y su esperanza.
   - *Comparación*: «campo de fútbol» con el rango de valor de cada método contra el precio.

## 2. Métodos y orden de construcción

| Orden | Bloque | Pregunta | Estado |
|---|---|---|---|
| A | Tasa de descuento (CAPM + WACC) | ¿Cuánto rendimiento se le exige a esta empresa? | en aprendizaje |
| B | DCF (flujo de caja libre, por etapas) | ¿Cuánto vale si se cumplen mis supuestos? | por construir |
| C | Gordon (crecimiento estable) | ¿Cuánto vale con crecimiento constante para siempre? | por construir |
| D | DCF inverso | ¿Qué crecimiento descuenta el precio de hoy? | por construir |
| — | Múltiplos contra su historia, Comparables | ¿Cara o barata contra sí misma / contra pares? | por construir |
| — | P/VL justificado, ingreso residual, DDM | Bancos y aseguradoras | por construir |
| — | NAV por mina (suma de las partes), P/NAV | Mineras | por construir |
| — | Gordon / DCF por ciclo del commodity | Commodities (ver §3) | idea de Martín |

Empresa de trabajo para A–D: **NVDA**.

## 3. Idea de Martín: valuar una commodity por ciclo (2026-11-21)

Gordon y el DCF fallan en una minera si se toma el precio de hoy del metal como si fuera para
siempre. La propuesta: **no un valor, sino uno por cada estado del ciclo**.

- Identificar los ciclos del metal con los métodos que la Cueva ya tiene: clusters de PERÍODOS
  (`no_supervisado`), regímenes de Markov / umbral (`regimenes`).
- Valuar la empresa en cada régimen (flujo, margen y crecimiento propios de ese régimen) y
  ponderar por la probabilidad de estar en cada uno (la matriz de transición de Markov da
  además la duración esperada de cada fase).
- Monte Carlo sobre la trayectoria del precio (con la dinámica del régimen) → distribución del
  valor, esperanza y percentiles, contra el precio de mercado.
- Equivale a un Gordon «a precio de mitad de ciclo» bien hecho, con la dispersión a la vista.

Se construye después de A–D, con RIO y MUX (y los datos por mina del otro proyecto).
