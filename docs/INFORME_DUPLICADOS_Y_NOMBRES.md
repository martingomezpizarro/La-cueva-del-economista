# Informe: series repetidas por frecuencia y nombres que colisionan

Investigación pedida el 2026-08-27. **Nada se aplicó todavía**: los dos scripts corren en
modo simulación y hay que pasarles `--aplicar` cuando estés de acuerdo.

---

## Resumen

| | Situación | Propuesta |
|---|---|---|
| **Nombres ambiguos** | 82 etiquetas usadas por más de una serie, afectan a **281 series** | Regla de cualificación: quedan **0 ambiguas**, 366 renombradas |
| **Misma serie en varias frecuencias** | 100 series | **48 se unifican a mensual** (verificado), 44 **no se tocan**, 8 quedan aparte |

---

## Caso 1 · Nombres que colisionan

### Qué encontré

82 etiquetas están usadas por más de una serie. Dentro del árbol se entienden; el problema
es que la etiqueta **viaja sola**: al buscador, a la leyenda de un gráfico, a la cita de un
informe. Ahí «Moneda Local» —54 series distintas— no significa nada.

Las colisiones no son azarosas. Responden a cuatro patrones, y por eso se arreglan con
reglas en vez de a mano:

| Patrón | Series | Ejemplo del choque |
|---|---|---|
| **A · Vencimientos, hoja por moneda** | 108 | «Moneda Local» ×54 y «Moneda Extranjera» ×54 |
| **B · Deuda: el mismo acreedor en tres contextos** | 39 | «FMI» es saldo de deuda, vencimiento a 1 año y a 2 años |
| **C · País que es socio comercial y componente del ITCRM** | 24 | «Brasil» es un índice y un saldo en USD |
| **D · Cuentas nacionales: constante / corriente / implícitos** | ~110 | «Importaciones FOB» ×3, dos en pesos y una en USD del BdP |

### Qué propongo

Cualificar la etiqueta con el contexto que la distingue. **No se tocan los `id`** — son el
contrato con los proyectos guardados.

```
'Brasil'              -> 'ITCRM bilateral — Brasil'
'Brasil'              -> 'Saldo comercial — Brasil'
'FMI'                 -> 'Saldo de deuda — FMI'
'FMI'                 -> 'Vencimientos 1a — FMI'
'Moneda Local'        -> 'Vencimientos 2a — Club de París — moneda local'
'Importaciones FOB'   -> 'Importaciones FOB (constante 2004)'
'Importaciones FOB'   -> 'Importaciones FOB (corriente)'
'Importaciones FOB'   -> 'Importaciones FOB (BdP)'
```

Cuatro casos no los resolvía ninguna regla de patrón, porque son **dos conceptos distintos
con el mismo nombre dentro de la misma rama**. Una segunda pasada los cualifica con su
padre inmediato:

```
'Otra Inversión'      -> 'Rentas de Inversión — Otra Inversión (BdP)'   (cuenta corriente: la renta)
'Otra Inversión'      -> 'Cuenta Financiera — Otra Inversión (BdP)'     (cuenta financiera: el flujo)
'Pasivos: Inst. Deuda'-> 'Inversión Directa — Pasivos: Inst. Deuda (BdP)'
'Pasivos: Inst. Deuda'-> 'Inversión de Cartera — Pasivos: Inst. Deuda (BdP)'
```

### Resultado

```bash
python scripts/normalizar_nombres_series.py --ver 0      # revisar el antes/después
python scripts/normalizar_nombres_series.py --aplicar
```

**82 etiquetas ambiguas → 0.** 366 series renombradas.

---

## Caso 2 · La misma serie en varias frecuencias

### El pedido no se puede aplicar tal cual, y conviene decirlo

Pediste unificar y «dejarlas solo en términos mensuales». Al mirarlas, las 100 series
multi-frecuencia son **tres casos distintos**, y tratarlos igual destruiría datos:

| Tipo | Series | Qué pasa si dejo solo la mensual |
|---|---|---|
| **Mensual observada** (EMAE, ICA del INDEC) | 50 | Nada: el trimestral y el anual son agregaciones del mensual, se reconstruyen |
| **Mensual estimada** (PBI, cuentas nacionales) | 44 | **Se pierde el dato oficial.** Acá el dato nativo es el TRIMESTRAL del INDEC; la mensual es una estimación propia por filtro de Kalman |
| **Sin mensual** (balance de pagos, A+Q) | 6 | No hay nada que unificar |

El segundo grupo es el importante. En `pbi_constante`, la fuente trimestral es el INDEC y
la mensual es `pbi_constante_kalman.csv`, columna `y_pred`: una **predicción**. Quedarse
solo con ella sería reemplazar la cuenta nacional oficial por nuestra estimación. **Esas 44
no las toco.**

Aparte, hay **285 series que solo existen en trimestral** (vencimientos de deuda, PBI por
sector, resultado fiscal estructural, balance de pagos). No tienen versión mensual y no
pueden tenerla sin estimarla.

### Cómo verifiqué que las 50 sí se pueden unificar

No lo supuse: el script **prueba las tres formas de agregar** —suma, promedio y último
valor del período— y se queda con la que reproduce el archivo trimestral y anual que ya
existe, con tolerancia del 0,5 % para el redondeo del INDEC.

```
EMAE nivel general (índice)     trimestral = promedio del mensual   error 0,0000 %
                                anual      = promedio del mensual   error 0,0000 %
ICA exportaciones (flujo USD)   trimestral = suma del mensual       error 0,0320 %
                                anual      = suma del mensual       error 0,0070 %
```

Exacto. El índice se promedia, el flujo se suma — y **la regla queda guardada en la serie**
(campo `agregacion`), así el explorador puede recalcular el trimestral y el anual al vuelo
en vez de guardarlos.

### Las dos que no pasan la verificación

De las 50, **48 pasan y 2 no**. Se quedan como están, y quiero que las mires:

| Serie | Qué pasa |
|---|---|
| `ica_icmb` | El anual sí se reconstruye (suma, 0,12 %), pero el **trimestral no**: error 0,82 %, por encima de la tolerancia. O el INDEC lo revisó y no rearmó el mensual, o hay un mes faltante que la suma trimestral sí incluye. Vale la pena abrirla. |
| `sc_asia` | No se pudo leer el mensual. Probablemente la columna cambió de nombre. |

### Resultado

```bash
python scripts/unificar_frecuencias.py --ver 0       # verifica y reporta
python scripts/unificar_frecuencias.py --aplicar
```

**48 series pasan a una sola fuente · −90 entradas del catálogo** (de 739 a 649).

---

## Lo que esto deja al descubierto

**Falta el campo `naturaleza`.** Para agregar una serie hay que saber si es un flujo (se
suma), un stock (se toma el último del período) o un índice (se promedia). El catálogo no
lo dice. Acá lo descubrí empíricamente comparando contra los archivos existentes, pero eso
solo funciona cuando el archivo agregado ya existe. Para las 285 series solo-trimestrales,
o para cualquier serie nueva del BCRA, no hay contra qué comparar.

El BCRA sí lo publica: su campo `tipoSerie` distingue «Saldos», «Flujo diario», «Tasa de
interés», «Variación». Convendría incorporarlo en la fase 0 del plan del catálogo, junto
con la descomposición de unidades que ya está hecha.

---

## Orden sugerido

1. **Nombres primero.** No toca datos, no rompe nada, y hace que el cuadro y el buscador
   sirvan. Es reversible con git.
2. **Revisar `ica_icmb` y `sc_asia`** — son dos, y las dos tienen algo que contar.
3. **Unificar frecuencias después**, ya con los nombres claros.
4. **`naturaleza` como campo**, cuando se encare la fase 0.
