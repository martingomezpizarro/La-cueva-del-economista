# Guía de datos — Gómez, M. (2018), *Avatares de un sistema monetario*

Acompaña al archivo `Gomez_2018_Avatares_base_de_datos.xlsx`.

---

## 1. Qué tiene el libro, en números

207 páginas de PDF, 188 de texto. **94 elementos numéricos: 30 cuadros y 64 gráficos.**

De esos 94:

- **26 cuadros tienen datos transcribibles** → están todos en el Excel.
- **64 gráficos son imágenes vectoriales sin tabla ni etiquetas de valor** → sus series **no** están en el PDF. Ni un solo número recuperable.
- 4 cuadros son cualitativos (matriz de funciones, requisitos legales, nómina de bancos).

Esa asimetría es lo que hay que entender antes de planificar cualquier carga de datos: el libro **publica los resultados, no la base**. Lo cual tiene sentido, porque la base está publicada aparte.

---

## 2. La cadena de fuentes (esto es lo que más te sirve)

El libro se apoya en tres fuentes que hacen el 90% del trabajo:

### 2.1. La base madre — Baiocco (1937) vía el Apéndice

Dice el Apéndice (p. 195): la autora construyó una base en Excel con **10 tablas, 59 variables y 420 registros mensuales, de enero de 1901 a diciembre de 1935**, levantada íntegramente de:

> Baiocco, Pedro (1937). *La economía bancaria argentina*. Instituto Bancario, Facultad de Ciencias Económicas, UBA.

La base incluye **una tabla propia de fuentes y notas** que reproduce, variable por variable, de dónde salió el dato y cómo lo construyó el equipo de Baiocco. Eso es exactamente el nivel de trazabilidad que buscás.

Todo lo que en el libro dice *"Fuente: véase Apéndice"* viene de ahí: tipo de cambio mensual, base monetaria, reservas metálicas, depósitos por grupo de bancos, reservas bancarias, redescuentos, nivel de liquidez, activos domésticos de la Caja.

**El link publicado (`https://goo.gl/CZtJLZ`) está muerto**: Google discontinuó el acortador en 2019. Dos caminos: pedirla directamente a Mónica Gómez (FCE-UNC, es tu facultad) o reconstruirla desde Baiocco (1937) en biblioteca. El primero es obviamente el correcto y probablemente el más productivo: pedirle la base y contarle el proyecto.

### 2.2. Ferreres (2005), *Dos siglos de economía argentina*

Sostiene **todos** los gráficos de balanza de pagos, quantum y precios de comercio exterior, resultados fiscales e ingresos y gastos como % del PIB, y la población rural. Unos 20 gráficos. Es la fuente más accesible de las tres y sus series circulan digitalizadas.

### 2.3. BNA (1941), *Banco de la Nación Argentina en su cincuentenario*

Sostiene todos los cuadros de financiamiento del BNA al Estado. Esos **sí** están transcriptos en el Excel (hojas 14 y 15), y son probablemente los datos más difíciles de conseguir en otro lado: la serie anual 1900-1934 de Cuenta Tesorería, límite legal, excesos, redescuentos de Letras, préstamos oficiales, fondos públicos y adelantos.

El resto (Salama, García Vizcaino, Gerchunoff-Rocchi-Rossi, Cortés Conde, Vázquez Presedo, Rayes, Della Paolera-Taylor) aporta cuadros puntuales, todos detallados en la hoja `02_Fuentes`.

---

## 3. Trampas de unidades

El libro mezcla **cinco unidades** y no siempre lo aclara en el mismo lugar:

| Unidad | Dónde aparece |
|---|---|
| Pesos moneda nacional (m$n) o "pesos papel" | Depósitos, redescuentos, financiamiento al Estado, base monetaria |
| Pesos oro | Fondo de Conversión, arreglos de deuda, reservas |
| Libras esterlinas | Arreglo Romero, exportaciones del gráfico I.4 |
| Dólares | Toda la balanza de pagos |
| Índices | Comercio exterior (base 1993=100), precios (base 1886=100), tipos de cambio (base ene-1929) |

**Paridad legal 1899-1929: 2,27 m$n por peso oro.** Es la que la autora usa para valuar reservas en las regresiones. Fuera de ese rango hay que usar el tipo de cambio observado, que no está publicado.

Dos ejemplos de conversión que el propio libro da y sirven de control: 20 millones de pesos oro = 45,45 millones de m$n (1914); 200 millones de pesos oro = 454,54 millones de m$n (1918).

---

## 4. Erratas y detalles detectados

Vale registrarlos si vas a cargar los datos:

- **Cuadro I.6**: la suma de la columna da 89,8 millones de pesos oro, pero el texto de la p. 50 dice 89,6. La discrepancia es del original.
- **Cuadro V.4**: el total de la última fila figura como 0; debería ser 14.
- **Gráfico I.4**: el pie cita "Reyes (2014)"; la bibliografía la registra correctamente como **Rayes**, Agustina.
- **Cuadro II.4 y IV.5**: hay celdas vacías que no son ceros, son ausencia de dato. En el Excel las dejé vacías a propósito.
- **Cuadros III.4 y IV.4**: el original usa un guion "–" para 1918-1920; lo transcribí como 0 porque el texto confirma que no hubo redescuentos.

---

## 5. Ruta de lectura sugerida

Si el objetivo es aprender con los números y no sólo leer el argumento:

1. **Capítulo I** para el marco: las tres condiciones (tierra, capital, refinanciación de la deuda) y por qué la convertibilidad tardó nueve años en llegar.
2. **Hoja `26_Contingencia_Caja` mientras leés II.2, III.3, IV.2 y V.3.** Esas seis tablas son el corazón empírico del libro: muestran mes a mes si la Caja respetó la regla. El quiebre de 1932 (cuando la base monetaria pasa a seguir los activos internos con correspondencia perfecta, en vez del oro) es el hallazgo más limpio.
3. **Hoja `19_Liquidez_por_periodo` mientras leés el capítulo VII.** Los contrafactuales muestran que el deterioro del BNA vino del financiamiento al Estado (32 puntos porcentuales en 1929-34), no de los redescuentos a otros bancos (6 puntos). Ese es el argumento de todo el libro condensado en una tabla.
4. **Hojas 13, 14, 15 y 18** para la mecánica del financiamiento: cómo se sorteaba el límite legal vía redescuentos de Letras de Tesorería, y cómo desde 1931 la emisión de la Caja reemplaza a los fondos propios del BNA.

---

## 6. Para la Cueva del Economista

Lo que este libro aporta al proyecto, en orden de valor:

**Alto — cargar directo.** Las series anuales 1900-1934 de financiamiento del BNA al Estado (hojas 14 y 15). No las vi consolidadas en ningún otro lado; vienen del BNA (1941), que es una fuente difícil. Con la columna "límite legal" al lado del saldo efectivo tenés una serie de *incumplimiento fiscal institucionalizado* que es muy potente narrativamente.

**Alto — cargar directo.** El Fondo de Conversión 1900-1928 (hoja 12) y los redescuentos 1908-1934 (hoja 13). Series cortas pero limpias y con hitos identificados.

**Medio — requiere ir a la fuente.** Todo lo mensual: tipo de cambio, base monetaria, reservas, depósitos. Es el material más valioso del libro y **no está en el libro**. Conseguir la base de la autora debería ser una prioridad del proyecto: 59 variables mensuales de 1901 a 1935 con notas de construcción es exactamente el tipo de activo que justifica una plataforma.

**Medio — verificar contra Ferreres.** Balanza de pagos y cuentas fiscales (hoja 21). Los valores del libro son medias y medianas de subperíodos, con subperíodos que se solapan entre capítulos. Sirven como *control de calidad* de la serie anual que bajes de Ferreres, no como serie en sí.

**Estructural.** La hoja `27_BCRA_1935` tiene los parámetros del régimen (encajes, topes, respaldos mínimos, composición del Directorio) comparados con el proyecto Niemeyer. Si la plataforma va a tener una capa de "reglas institucionales vigentes en cada momento", esto es una fila de esa tabla.

Una observación metodológica que vale para el diseño de la base: el libro fecha los cambios de régimen **por comportamiento observado**, no por la norma. La convertibilidad es de 1899 pero Argentina entra al patrón oro *de hecho* en octubre de 1902; el BCRA es de 1935 pero la Caja ejerce de prestamista de última instancia desde abril de 1931. Si la plataforma va a periodizar, conviene tener las dos fechas: la legal y la efectiva.

---

## 7. Cómo citar

Formato sugerido, citando siempre los dos niveles:

> Gómez, M. (2018). *Avatares de un sistema monetario*. Buenos Aires: Teseo, cuadro IV.5, p. 117. Fuente primaria: BNA (1941).

Para las series de la base madre:

> Gómez, M. (2018), base de datos del Apéndice, elaborada sobre Baiocco, P. (1937), *La economía bancaria argentina*, Instituto Bancario, FCE-UBA.

La obra está bajo **Creative Commons Atribución – No Comercial – Sin Obra Derivada 4.0**. Reproducir los datos con atribución está bien; una plataforma pública no comercial encaja. Si en algún momento la Cueva tiene un componente comercial, hay que pedir permiso.
