# Inventario de series — La Cueva del Economista

> Generado por `python scripts/auditar_series.py`. **No editar a mano.**
> La fuente de verdad es `cueva/datos/catalogo.json`; el esquema está en `docs/DATOS.md`.

## Resumen

- Entradas del catálogo (serie × frecuencia): **1245**
- Con procedencia documentada (`proc.fuente`): **1245** (100 %)
- Pendientes de descarga (tienen script que las repone): **563**
- Archivos referenciados que no se encontraron ni tienen script: **35**

## Series

| Serie | Base | Origen | Final | Frec. | Fuente | Descripción | Magnitud | Escala | Moneda |
|---|---|---|---|---|---|---|---|---|---|
| Reservas Brutas BCRA | `001_reservas_brutas.csv` |  |  | D | bcra | Saldo diario de reservas internacionales publicado por Comunicación «C». Excluye las asignaciones de DEG de 20… | moneda | millones | USD |
| Reservas Internacionales (saldo a fin de mes, histórica) | `1605_reservas_internacionales.csv` |  |  | M | bcra | Saldo de reservas internacionales del BCRA a fin de mes. Es la versión mensual y larga de la serie diaria (idV… | moneda | millones | USD |
| M2 / PBI | `m2_pbi.csv` |  |  | M | propia | M2 como porcentaje del PBI nominal: profundidad del sistema de pagos. | porcentaje | unidad |  |
| Depósitos Totales (ARS) | `021_dep_total.csv` |  |  | D | bcra | Depósitos en efectivo del total de sectores en las entidades financieras, en moneda nacional y extranjera. | moneda | millones | ARS |
| Depósitos USD — Total | `depositos_usd_totales.csv` |  |  | D | bcra | Depósitos en dólares en el sistema financiero — total de sectores. | moneda | millones | USD |
| Depósitos USD — Residentes | `depositos_usd_residentes.csv` |  |  | D | bcra | Depósitos en dólares de residentes en el sistema financiero. | moneda | millones | USD |
| Depósitos USD — Sec. Priv. | `depositos_usd_secprivnofin.csv` |  |  | D | bcra | Depósitos en dólares del sector privado no financiero. | moneda | millones | USD |
| Depósitos en Cuenta Corriente | `0022_depositos_en_cuentas_corrientes_neto_de_utilizacion_fuco.csv` |  |  | D | bcra | Depósitos en efectivo en cuenta corriente del total de sectores, neto de la utilización de Fondos Unificados d… | moneda | millones | ARS |
| Depósitos en Caja de Ahorro | `0023_depositos_en_cajas_de_ahorro.csv` |  |  | D | bcra | Depósitos en efectivo bajo el sistema de caja de ahorros, del total de sectores. | moneda | millones | ARS |
| Depósitos a Plazo Fijo | `0024_depositos_a_plazo_en_efectivo_incluye_inversiones_excluye_ce.csv` |  |  | D | bcra | Depósitos a plazo del total de sectores; incluye inversiones a plazo y excluye CEDROs. | moneda | millones | ARS |
| Préstamos Privados USD | `prestamos_privados_usd_q.csv` |  |  | D | bcra | Préstamos en dólares otorgados al sector privado no financiero. | moneda | millones | USD |
| Préstamos al Sector Privado | `0026_prestamos_de_las_entidades_financieras_al_sector_privado.csv` |  |  | D | bcra | Préstamos de efectivo de las entidades financieras al sector privado no financiero, en moneda nacional y extra… | moneda | millones | ARS |
| TC MEP (dólar financiero) | `brecha_cambiaria.csv` |  |  | D | argentinadatos | Tipo de cambio implícito en la compraventa de bonos con liquidación local (dólar MEP). | tipo_de_cambio | unidad | ARS |
| TC Oficial (A3500) | `brecha_cambiaria.csv` |  |  | D | bcra | Tipo de cambio mayorista de referencia peso/dólar calculado por el BCRA según Comunicación A 3500. | tipo_de_cambio | unidad | ARS |
| Brecha Cambiaria MEP/Oficial | `brecha_cambiaria.csv` |  |  | D | propia | Brecha cambiaria: cuánto se aparta el dólar financiero del oficial. | ratio | unidad |  |
| TC Minorista (promedio vendedor) | `0004_tipo_de_cambio_minorista_promedio_vendedor.csv` |  |  | D | bcra | Tipo de cambio peso/dólar minorista informado según Comunicación B 9791. | tipo_de_cambio | unidad | ARS |
| ITCRM Multilateral | `itcrm_diario.csv` |  |  | D | bcra | Índice de Tipo de Cambio Real Multilateral: tipo de cambio real de Argentina contra una canasta de socios come… | indice | unidad |  |
| Brasil | `itcrm_diario.csv` |  |  | D | bcra | Índice de Tipo de Cambio Real Multilateral: tipo de cambio real de Argentina contra una canasta de socios come… | indice | unidad |  |
| EEUU | `itcrm_diario.csv` |  |  | D | bcra | Índice de Tipo de Cambio Real Multilateral: tipo de cambio real de Argentina contra una canasta de socios come… | indice | unidad |  |
| Chile | `itcrm_diario.csv` |  |  | D | bcra | Índice de Tipo de Cambio Real Multilateral: tipo de cambio real de Argentina contra una canasta de socios come… | indice | unidad |  |
| Uruguay | `itcrm_diario.csv` |  |  | D | bcra | Índice de Tipo de Cambio Real Multilateral: tipo de cambio real de Argentina contra una canasta de socios come… | indice | unidad |  |
| México | `itcrm_diario.csv` |  |  | D | bcra | Índice de Tipo de Cambio Real Multilateral: tipo de cambio real de Argentina contra una canasta de socios come… | indice | unidad |  |
| Canadá | `itcrm_diario.csv` |  |  | D | bcra | Índice de Tipo de Cambio Real Multilateral: tipo de cambio real de Argentina contra una canasta de socios come… | indice | unidad |  |
| Sudamérica | `itcrm_diario.csv` |  |  | D | bcra | Índice de Tipo de Cambio Real Multilateral: tipo de cambio real de Argentina contra una canasta de socios come… | indice | unidad |  |
| Zona Euro | `itcrm_diario.csv` |  |  | D | bcra | Índice de Tipo de Cambio Real Multilateral: tipo de cambio real de Argentina contra una canasta de socios come… | indice | unidad |  |
| Reino Unido | `itcrm_diario.csv` |  |  | D | bcra | Índice de Tipo de Cambio Real Multilateral: tipo de cambio real de Argentina contra una canasta de socios come… | indice | unidad |  |
| Suiza | `itcrm_diario.csv` |  |  | D | bcra | Índice de Tipo de Cambio Real Multilateral: tipo de cambio real de Argentina contra una canasta de socios come… | indice | unidad |  |
| China | `itcrm_diario.csv` |  |  | D | bcra | Índice de Tipo de Cambio Real Multilateral: tipo de cambio real de Argentina contra una canasta de socios come… | indice | unidad |  |
| Japón | `itcrm_diario.csv` |  |  | D | bcra | Índice de Tipo de Cambio Real Multilateral: tipo de cambio real de Argentina contra una canasta de socios come… | indice | unidad |  |
| India | `itcrm_diario.csv` |  |  | D | bcra | Índice de Tipo de Cambio Real Multilateral: tipo de cambio real de Argentina contra una canasta de socios come… | indice | unidad |  |
| Vietnam | `itcrm_diario.csv` |  |  | D | bcra | Índice de Tipo de Cambio Real Multilateral: tipo de cambio real de Argentina contra una canasta de socios come… | indice | unidad |  |
| Base Monetaria (mensual, histórica) | `1606_base_monetaria.csv` |  |  | M | bcra | Base monetaria | moneda | miles | ARS |
| Circulación Monetaria (mensual, histórica) | `1607_circulacion_monetaria.csv` |  |  | M | bcra | Circulación monetaria | moneda | miles | ARS |
| Billetes y Monedas en Poder del Público (histórica) | `1608_billetes_y_monedas_en_poder_del_publico.csv` |  |  | M | bcra | Billetes y monedas en poder del público | moneda | miles | ARS |
| Efectivo en Entidades Financieras (histórica) | `1609_efectivo_en_entidades_financieras.csv` |  |  | M | bcra | Efectivo en entidades financieras | moneda | miles | ARS |
| Depósitos de EEFF en Cta. Cte. en el BCRA (histórica) | `1610_depositos_de_las_entidades_financieras_en_cuenta_corriente_e.csv` |  |  | M | bcra | Depósitos de las entidades financieras en cuenta corriente en el BCRA | moneda | miles | ARS |
| M1 — moneda local y extranjera | `1611_m1_en_moneda_local_y_extranjera.csv` |  |  | M | bcra | M1: billetes y monedas en poder del público más depósitos en cuenta corriente, sumando las partidas en moneda … | moneda | miles | ARS |
| M1 — moneda local | `1612_m1_en_moneda_local.csv` |  |  | M | bcra | M1 en moneda local: billetes y monedas en poder del público más depósitos en cuenta corriente en pesos. | moneda | miles | ARS |
| M2 — moneda local y extranjera | `1617_m2_en_moneda_local_y_extranjera.csv` |  |  | M | bcra | M2: M1 más cajas de ahorro, sumando moneda local y extranjera. | moneda | miles | ARS |
| M2 — moneda local | `1618_m2_en_moneda_local.csv` |  |  | M | bcra | M2 en moneda local: M1 en pesos más cajas de ahorro en pesos. | moneda | miles | ARS |
| M3 — moneda local y extranjera | `1623_m3_en_moneda_local_y_extranjera.csv` |  |  | M | bcra | M3: M2 más depósitos a plazo fijo y otros depósitos, sumando moneda local y extranjera. Es el agregado más amp… | moneda | miles | ARS |
| M3 — moneda local | `1624_m3_en_moneda_local.csv` |  |  | M | bcra | M3 en moneda local: M2 en pesos más plazos fijos y otros depósitos en pesos. | moneda | miles | ARS |
| Cuentas Corrientes — sector privado (ARS) | `1613_cuentas_corrientes_del_sector_privado.csv` |  |  | M | bcra | Cuentas corrientes del sector privado | moneda | miles | ARS |
| Cuentas Corrientes — sector público (ARS) | `1614_cuentas_corrientes_del_sector_publico.csv` |  |  | M | bcra | Cuentas corrientes del sector público | moneda | miles | ARS |
| Cuentas Corrientes — sector privado (m. extranjera, valuada en ARS) | `1615_cuentas_corrientes_del_sector_privado.csv` |  |  | M | bcra | Cuentas corrientes del sector privado | moneda | miles | ARS |
| Cuentas Corrientes — sector público (m. extranjera, valuada en ARS) | `1616_cuentas_corrientes_del_sector_publico.csv` |  |  | M | bcra | Cuentas corrientes del sector público | moneda | miles | ARS |
| Cajas de Ahorro — sector privado (ARS) | `1619_cajas_de_ahorro_del_sector_privado.csv` |  |  | M | bcra | Cajas de ahorro del sector privado | moneda | miles | ARS |
| Cajas de Ahorro — sector público (ARS) | `1620_cajas_de_ahorro_del_sector_publico.csv` |  |  | M | bcra | Cajas de ahorro del sector público | moneda | miles | ARS |
| Cajas de Ahorro — sector privado (m. extranjera, valuada en ARS) | `1621_cajas_de_ahorro_del_sector_privado.csv` |  |  | M | bcra | Cajas de ahorro del sector privado | moneda | miles | ARS |
| Cajas de Ahorro — sector público (m. extranjera, valuada en ARS) | `1622_cajas_de_ahorro_del_sector_publico.csv` |  |  | M | bcra | Cajas de ahorro del sector público | moneda | miles | ARS |
| Depósitos a Plazo Fijo — sector privado (ARS) | `1625_depositos_a_plazo_fijo_del_sector_privado.csv` |  |  | M | bcra | Depósitos a plazo fijo del sector privado | moneda | miles | ARS |
| Depósitos a Plazo Fijo — sector público (ARS) | `1626_depositos_a_plazo_fijo_del_sector_publico.csv` |  |  | M | bcra | Depósitos a plazo fijo del sector público | moneda | miles | ARS |
| Depósitos a Plazo Fijo — sector privado (m. extranjera, valuada en ARS) | `1630_depositos_a_plazo_fijo_del_sector_privado.csv` |  |  | M | bcra | Depósitos a plazo fijo del sector privado | moneda | miles | ARS |
| Depósitos a Plazo Fijo — sector público (m. extranjera, valuada en ARS) | `1631_depositos_a_plazo_fijo_del_sector_publico.csv` |  |  | M | bcra | Depósitos a plazo fijo del sector público | moneda | miles | ARS |
| Otros Depósitos — sector privado (ARS) | `1627_otros_depositos_del_sector_privado.csv` |  |  | M | bcra | Otros depósitos del sector privado | moneda | miles | ARS |
| Otros Depósitos — sector público (ARS) | `1628_otros_depositos_del_sector_publico.csv` |  |  | M | bcra | Otros depósitos del sector público | moneda | miles | ARS |
| Otros Depósitos — sector privado (m. extranjera, valuada en ARS) | `1632_otros_depositos_del_sector_privado.csv` |  |  | M | bcra | Otros depósitos del sector privado | moneda | miles | ARS |
| Otros Depósitos — sector público (m. extranjera, valuada en ARS) | `1633_otros_depositos_del_sector_publico.csv` |  |  | M | bcra | Otros depósitos del sector público | moneda | miles | ARS |
| Aceptaciones | `1629_aceptaciones.csv` |  |  | M | bcra | Aceptaciones bancarias: obligaciones que la entidad asume por cuenta de un cliente y que integran el agregado … | moneda | miles | ARS |
| Tasa de Plazo Fijo a 30 días | `0012_tasa_de_interes_de_depositos_a_30_dias_de_plazo_en_entidades.csv` |  |  | D | bcra | Tasa promedio ponderada por monto de los plazos fijos a 30 días en moneda nacional, total de entidades (SISCEN… | porcentaje | unidad |  |
| BADLAR — bancos privados (TNA) | `0007_tasa_de_interes_badlar_de_bancos_privados.csv` |  |  | D | bcra | Tasa promedio ponderada de los plazos fijos de un millón de pesos o más, de 30 a 35 días, en bancos privados. … | porcentaje | unidad |  |
| BADLAR — bancos privados (TEA) | `0035_tasa_de_interes_badlar_de_bancos_privados_tea.csv` |  |  | D | bcra | La misma BADLAR expresada en tasa efectiva anual. | porcentaje | unidad |  |
| TM20 — bancos privados | `0008_tasa_de_interes_tm20_de_bancos_privados.csv` |  |  | D | bcra | Tasa de los plazos fijos de veinte millones de pesos o más, de 30 a 35 días, en bancos privados. | porcentaje | unidad |  |
| TAMAR — bancos privados | `0044_tasa_de_interes_tamar_de_bancos_privados.csv` |  |  | D | bcra | Tasa mayorista de plazo fijo de 30 a 35 días. Reemplaza a la BADLAR como referencia a partir de octubre de 202… | porcentaje | unidad |  |
| Adelantos en cuenta corriente | `0013_tasa_de_interes_por_adelantos_en_cuenta_corriente.csv` |  |  | D | bcra | Tasa de los adelantos en cuenta corriente con acuerdo, de 1 a 7 días y de diez millones de pesos o más, a empr… | porcentaje | unidad |  |
| Préstamos personales | `0014_tasa_de_interes_de_prestamos_personales.csv` |  |  | D | bcra | Tasa promedio ponderada de los préstamos personales en pesos a tasa fija o repactable. | porcentaje | unidad |  |
| BAIBAR — préstamos entre bancos privados | `0011_tasa_de_interes_de_prestamos_entre_entidades_financieras_pri.csv` |  |  | D | bcra | Tasa del mercado interbancario: préstamos de efectivo entre entidades privadas hasta 15 días de plazo. | porcentaje | unidad |  |
| Tasa Comunicado P 14.290 (uso de justicia) | `0043_tasa_de_interes_comunicado_p_14_290_uso_de_justicia.csv` |  |  | D | bcra | Serie de capitalización diaria basada en las tasas de caja de ahorro y plazo fijo. Es la que usan los tribunal… | porcentaje | unidad |  |
| Base Monetaria (diaria) | `0015_base_monetaria.csv` |  |  | D | bcra | Circulación monetaria total más los depósitos en cuenta corriente en pesos de las entidades financieras en el … | moneda | millones | ARS |
| Circulación Monetaria (diaria) | `0016_circulacion_monetaria.csv` |  |  | D | bcra | Billetes y monedas emitidos por el BCRA y puestos en circulación, más cheques cancelatorios en pesos. | moneda | millones | ARS |
| Billetes y Monedas en Poder del Público (diaria) | `0017_billetes_y_monedas_en_poder_del_publico.csv` |  |  | D | bcra | Circulación monetaria que no está en poder de las entidades financieras. | moneda | millones | ARS |
| Efectivo en Entidades Financieras (diaria) | `0018_efectivo_en_entidades_financieras.csv` |  |  | D | bcra | Billetes y monedas en cajas y cajeros de las entidades. Se publica con dos días hábiles de rezago. | moneda | millones | ARS |
| Depósitos de EEFF en Cta. Cte. en el BCRA (diaria) | `0019_depositos_de_las_entidades_financieras_en_cuenta_corriente_e.csv` |  |  | D | bcra | Depósitos en cuenta corriente en pesos de las entidades financieras en el BCRA; integran la base monetaria. | moneda | millones | ARS |
| M2 privado — variación interanual | `0025_variacion_interanual_del_promedio_movil_de_30_dias_del_m2_pr.csv` |  |  | D | bcra | Variación interanual del promedio móvil de 30 días del M2 privado (circulante en poder del público más depósit… | porcentaje | unidad |  |
| Pasivos Monetarios del BCRA | `1247_pasivos_monetarios_base_monetaria_pasivos_en_moneda_extranje.csv` |  |  | D | bcra | Base monetaria más depósitos y otros pasivos monetarios en moneda extranjera en el BCRA. | moneda | millones | ARS |
| LELIQ y NOTALIQ | `1260_leliq_y_notaliq.csv` |  |  | D | bcra | Saldo de Letras y Notas de Liquidez del BCRA en cartera de entidades financieras. | moneda | millones | ARS |
| LEBAC, NOBAC y otras letras en pesos | `1258_lebac_nobac_y_otras_letras_del_bcra_en_pesos.csv` |  |  | D | bcra | Saldo de letras y notas del BCRA en pesos; no incluye LELIQ ni NOTALIQ. | moneda | millones | ARS |
| Posición Neta de Pases | `1261_posicion_neta_de_pases_pasivos_activos.csv` |  |  | D | bcra | Pases pasivos menos pases activos del BCRA. Positivo = el BCRA absorbe liquidez. | moneda | millones | ARS |
| Depósitos del Gobierno en el BCRA | `1264_depositos_del_gobierno_en_el_bcra.csv` |  |  | D | bcra | Saldo de las cuentas del Gobierno Nacional en el Banco Central. | moneda | millones | ARS |
| Redescuentos y Adelantos por Iliquidez | `1267_redescuentos_y_adelantos_por_iliquidez_al_sistema_financiero.csv` |  |  | D | bcra | Asistencia del BCRA a entidades financieras con problemas de liquidez. | moneda | millones | ARS |
| Adelantos Transitorios al Tesoro | `1268_adelantos_transitorios_del_bcra_al_gobierno_nacional.csv` |  |  | D | bcra | Stock de adelantos transitorios al Gobierno Nacional (artículo 20 de la Carta Orgánica). Es la medida directa … | moneda | millones | ARS |
| Total | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Cultivos agrícolas | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Cultivos agrícolas | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Cría de animales | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Cría de animales | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Servicios agrícolas y pecuarios, excepto los veterinarios | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Servicios agrícolas y pecuarios, excepto los veterinarios | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Caza, repoblación de animales de caza y servicios conexos | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Caza, repoblación de animales de caza y servicios conexos | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Construcciones agropecuarias | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Construcciones agropecuarias | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Silvicultura, extracción de madera y servicios conexos | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Silvicultura, extracción de madera y servicios conexos | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Extracción de carbón y lignito; extracción de turba. Extracción de petróleo crudo y gas natural; actividades de servicios relacionadas con la extracción de petróleo y gas, excepto las actividades de prospección | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Extracción de carbón y lignito; extracción de turba. Extracción de petróleo crudo y gas natural; actividades de servicios relacionadas con la extracción de petróleo y gas, excepto las actividades de prospección | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Extracción de minerales metalíferos. Explotación de minas y canteras n.c.p. | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Extracción de minerales metalíferos. Explotación de minas y canteras n.c.p. | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Elaboración de productos alimenticios y bebidas | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Elaboración de productos alimenticios y bebidas | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Elaboración de productos de tabaco | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Elaboración de productos de tabaco | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de productos textiles | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de productos textiles | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de prendas de vestir; terminación y teñido de pieles | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de prendas de vestir; terminación y teñido de pieles | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Curtido y terminación de cueros; fabricación de artículos de marroquinería, talabartería y calzado y de sus partes | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Curtido y terminación de cueros; fabricación de artículos de marroquinería, talabartería y calzado y de sus partes | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Producción de madera y fabricación de productos de madera y corcho, excepto muebles; fabricación de artículos de paja y de materiales trenzables | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Producción de madera y fabricación de productos de madera y corcho, excepto muebles; fabricación de artículos de paja y de materiales trenzables | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de papel y de productos de papel | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de papel y de productos de papel | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Edición e impresión; reproducción de grabaciones | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Edición e impresión; reproducción de grabaciones | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de coque, productos de la refinación del petróleo y combustible nuclear | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de coque, productos de la refinación del petróleo y combustible nuclear | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de sustancias y productos químicos | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de sustancias y productos químicos | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de productos de caucho y plástico | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de productos de caucho y plástico | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de productos minerales no metálicos | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de productos minerales no metálicos | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de metales comunes | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de metales comunes | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de productos elaborados de metal, excepto maquinaria y equipo | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de productos elaborados de metal, excepto maquinaria y equipo | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de maquinaria y equipo n.c.p. | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de maquinaria y equipo n.c.p. | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de maquinaria de oficina, contabilidad e informática | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de maquinaria de oficina, contabilidad e informática | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de maquinaria y aparatos eléctricos n.c.p. | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de maquinaria y aparatos eléctricos n.c.p. | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de equipos y aparatos de radio, televisión y comunicaciones | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de equipos y aparatos de radio, televisión y comunicaciones | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de instrumentos médicos, ópticos y de precisión; fabricación de relojes | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de instrumentos médicos, ópticos y de precisión; fabricación de relojes | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de vehículos automotores, remolques y semirremolques | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de vehículos automotores, remolques y semirremolques | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de equipo de transporte n.c.p. | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de equipo de transporte n.c.p. | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de muebles y colchones; industrias manufactureras n.c.p. | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de muebles y colchones; industrias manufactureras n.c.p. | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Reciclamiento | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Reciclamiento | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Reparación, mantenimiento e instalación de maquinas y equipos | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Reparación, mantenimiento e instalación de maquinas y equipos | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Generación captación y distribución de energía eléctrica | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Generación captación y distribución de energía eléctrica | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de gas; distribución de combustibles gaseosos por tuberías | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de gas; distribución de combustibles gaseosos por tuberías | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Captación, depuración y distribución de agua | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Captación, depuración y distribución de agua | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Hoteles; campamentos y otros tipos de hospedaje temporal | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Hoteles; campamentos y otros tipos de hospedaje temporal | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Restaurantes, bares y cantinas | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Restaurantes, bares y cantinas | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Transporte | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Transporte | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Comunicaciones | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Comunicaciones | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Intermediación financiera y otros servicios financieros | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Intermediación financiera y otros servicios financieros | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Servicios de seguros | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Servicios de seguros | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Servicios auxiliares a la actividad financiera | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Servicios auxiliares a la actividad financiera | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Servicios inmobiliarios con bienes propios y arrendados | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Servicios inmobiliarios con bienes propios y arrendados | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Resto | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Resto | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Enseñanza Pública | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Enseñanza Pública | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Enseñanza Privada | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Enseñanza Privada | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Salud Pública | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Salud Pública | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Salud Privada | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Salud Privada | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Eliminación de desperdicios y aguas residuales, saneamiento y servicios similares | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Eliminación de desperdicios y aguas residuales, saneamiento y servicios similares | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Asociaciones | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Asociaciones | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Servicios culturales y deportivos. Otras actividades | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Servicios culturales y deportivos. Otras actividades | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vab_rama_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vab_rama_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Cultivos agrícolas | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Cultivos agrícolas | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Cría de animales | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Cría de animales | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Servicios agrícolas y pecuarios, excepto los veterinarios | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Servicios agrícolas y pecuarios, excepto los veterinarios | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Caza, repoblación de animales de caza y servicios conexos | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Caza, repoblación de animales de caza y servicios conexos | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Construcciones agropecuarias | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Construcciones agropecuarias | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Silvicultura, extracción de madera y servicios conexos | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Silvicultura, extracción de madera y servicios conexos | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Extracción de carbón y lignito; extracción de turba. Extracción de petróleo crudo y gas natural; actividades de servicios relacionadas con la extracción de petróleo y gas, excepto las actividades de prospección | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Extracción de carbón y lignito; extracción de turba. Extracción de petróleo crudo y gas natural; actividades de servicios relacionadas con la extracción de petróleo y gas, excepto las actividades de prospección | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Extracción de minerales metalíferos. Explotación de minas y canteras n.c.p. | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Extracción de minerales metalíferos. Explotación de minas y canteras n.c.p. | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Elaboración de productos alimenticios y bebidas | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Elaboración de productos alimenticios y bebidas | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Elaboración de productos de tabaco | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Elaboración de productos de tabaco | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de productos textiles | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de productos textiles | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de prendas de vestir; terminación y teñido de pieles | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de prendas de vestir; terminación y teñido de pieles | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Curtido y terminación de cueros; fabricación de artículos de marroquinería, talabartería y calzado y de sus partes | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Curtido y terminación de cueros; fabricación de artículos de marroquinería, talabartería y calzado y de sus partes | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Producción de madera y fabricación de productos de madera y corcho, excepto muebles; fabricación de artículos de paja y de materiales trenzables | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Producción de madera y fabricación de productos de madera y corcho, excepto muebles; fabricación de artículos de paja y de materiales trenzables | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de papel y de productos de papel | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de papel y de productos de papel | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Edición e impresión; reproducción de grabaciones | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Edición e impresión; reproducción de grabaciones | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de coque, productos de la refinación del petróleo y combustible nuclear | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de coque, productos de la refinación del petróleo y combustible nuclear | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de sustancias y productos químicos | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de sustancias y productos químicos | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de productos de caucho y plástico | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de productos de caucho y plástico | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de productos minerales no metálicos | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de productos minerales no metálicos | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de metales comunes | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de metales comunes | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de productos elaborados de metal, excepto maquinaria y equipo | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de productos elaborados de metal, excepto maquinaria y equipo | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de maquinaria y equipo n.c.p. | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de maquinaria y equipo n.c.p. | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de maquinaria de oficina, contabilidad e informática | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de maquinaria de oficina, contabilidad e informática | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de maquinaria y aparatos eléctricos n.c.p. | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de maquinaria y aparatos eléctricos n.c.p. | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de equipos y aparatos de radio, televisión y comunicaciones | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de equipos y aparatos de radio, televisión y comunicaciones | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de instrumentos médicos, ópticos y de precisión; fabricación de relojes | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de instrumentos médicos, ópticos y de precisión; fabricación de relojes | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de vehículos automotores, remolques y semirremolques | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de vehículos automotores, remolques y semirremolques | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de equipo de transporte n.c.p. | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de equipo de transporte n.c.p. | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de muebles y colchones; industrias manufactureras n.c.p. | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de muebles y colchones; industrias manufactureras n.c.p. | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Reciclamiento | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Reciclamiento | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Reparación, mantenimiento e instalación de maquinas y equipos | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Reparación, mantenimiento e instalación de maquinas y equipos | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Generación captación y distribución de energía eléctrica | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Generación captación y distribución de energía eléctrica | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de gas; distribución de combustibles gaseosos por tuberías | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Fabricación de gas; distribución de combustibles gaseosos por tuberías | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Captación, depuración y distribución de agua | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Captación, depuración y distribución de agua | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Hoteles; campamentos y otros tipos de hospedaje temporal | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Hoteles; campamentos y otros tipos de hospedaje temporal | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Restaurantes, bares y cantinas | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Restaurantes, bares y cantinas | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Transporte | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Transporte | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Comunicaciones | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Comunicaciones | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Intermediación financiera y otros servicios financieros | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Intermediación financiera y otros servicios financieros | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Servicios de seguros | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Servicios de seguros | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Servicios auxiliares a la actividad financiera | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Servicios auxiliares a la actividad financiera | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Servicios inmobiliarios con bienes propios y arrendados | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Servicios inmobiliarios con bienes propios y arrendados | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Resto | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Resto | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Enseñanza Pública | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Enseñanza Pública | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Enseñanza Privada | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Enseñanza Privada | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Salud Pública | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Salud Pública | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Salud Privada | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Salud Privada | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Eliminación de desperdicios y aguas residuales, saneamiento y servicios similares | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Eliminación de desperdicios y aguas residuales, saneamiento y servicios similares | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Asociaciones | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Asociaciones | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Servicios culturales y deportivos. Otras actividades | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Servicios culturales y deportivos. Otras actividades | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vbp_rama_constante.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vbp_rama_corriente.csv` | 2004-01-01 | 2025-01-01 | A | indec | Valor bruto de producción a precios básicos por rama de actividad económica. | moneda | millones | ARS |
| Total | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Total | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Cultivos agrícolas | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Cría de animales | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Servicios agrícolas y pecuarios, excepto los veterinarios | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Caza, repoblación de animales de caza y servicios conexos | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Construcciones agropecuarias | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Silvicultura, extracción de madera y servicios conexos | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Total | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Total | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Extracción de carbón y lignito; extracción de turba. Extracción de petróleo crudo y gas natural; actividades de servicios relacionadas con la extracción de petróleo y gas, excepto las actividades de prospección | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Extracción de minerales metalíferos. Explotación de minas y canteras n.c.p. | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Total | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Elaboración de productos alimenticios y bebidas | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Elaboración de productos de tabaco | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Fabricación de productos textiles | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Fabricación de prendas de vestir; terminación y teñido de pieles | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Curtido y terminación de cueros; fabricación de artículos de marroquinería, talabartería y calzado y de sus partes | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Producción de madera y fabricación de productos de madera y corcho, excepto muebles; fabricación de artículos de paja y de materiales trenzables | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Fabricación de papel y de productos de papel | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Edición e impresión; reproducción de grabaciones | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Fabricación de coque, productos de la refinación del petróleo y combustible nuclear | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Fabricación de sustancias y productos químicos | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Fabricación de productos de caucho y plástico | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Fabricación de productos minerales no metálicos | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Fabricación de metales comunes | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Fabricación de productos elaborados de metal, excepto maquinaria y equipo | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Fabricación de maquinaria y equipo n.c.p. | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Fabricación de maquinaria de oficina, contabilidad e informática | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Fabricación de maquinaria y aparatos eléctricos n.c.p. | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Fabricación de equipos y aparatos de radio, televisión y comunicaciones | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Fabricación de instrumentos médicos, ópticos y de precisión; fabricación de relojes | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Fabricación de vehículos automotores, remolques y semirremolques | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Fabricación de equipo de transporte n.c.p. | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Fabricación de muebles y colchones; industrias manufactureras n.c.p. | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Reciclamiento | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Reparación, mantenimiento e instalación de maquinas y equipos | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Total | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Generación captación y distribución de energía eléctrica | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Fabricación de gas; distribución de combustibles gaseosos por tuberías | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Captación, depuración y distribución de agua | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Total | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Total | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Total | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Hoteles; campamentos y otros tipos de hospedaje temporal | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Restaurantes, bares y cantinas | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Total | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Transporte | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Comunicaciones | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Total | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Intermediación financiera y otros servicios financieros | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Servicios de seguros | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Servicios auxiliares a la actividad financiera | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Total | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Servicios inmobiliarios con bienes propios y arrendados | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Resto | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Total | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Total | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Enseñanza Pública | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Enseñanza Privada | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Total | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Salud Pública | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Salud Privada | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Total | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Eliminación de desperdicios y aguas residuales, saneamiento y servicios similares | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Asociaciones | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Servicios culturales y deportivos. Otras actividades | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Total | `cn_vab_rama_ivf.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Índice de volumen físico del VAB a precios básicos, por rama de actividad. | indice | unidad |  |
| Total | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Total | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Cultivos agrícolas | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Cría de animales | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Servicios agrícolas y pecuarios, excepto los veterinarios | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Caza, repoblación de animales de caza y servicios conexos | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Construcciones agropecuarias | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Silvicultura, extracción de madera y servicios conexos | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Total | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Total | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Extracción de carbón y lignito; extracción de turba. Extracción de petróleo crudo y gas natural; actividades de servicios relacionadas con la extracción de petróleo y gas, excepto las actividades de prospección | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Extracción de minerales metalíferos. Explotación de minas y canteras n.c.p. | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Total | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Elaboración de productos alimenticios y bebidas | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Elaboración de productos de tabaco | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Fabricación de productos textiles | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Fabricación de prendas de vestir; terminación y teñido de pieles | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Curtido y terminación de cueros; fabricación de artículos de marroquinería, talabartería y calzado y de sus partes | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Producción de madera y fabricación de productos de madera y corcho, excepto muebles; fabricación de artículos de paja y de materiales trenzables | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Fabricación de papel y de productos de papel | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Edición e impresión; reproducción de grabaciones | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Fabricación de coque, productos de la refinación del petróleo y combustible nuclear | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Fabricación de sustancias y productos químicos | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Fabricación de productos de caucho y plástico | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Fabricación de productos minerales no metálicos | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Fabricación de metales comunes | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Fabricación de productos elaborados de metal, excepto maquinaria y equipo | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Fabricación de maquinaria y equipo n.c.p. | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Fabricación de maquinaria de oficina, contabilidad e informática | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Fabricación de maquinaria y aparatos eléctricos n.c.p. | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Fabricación de equipos y aparatos de radio, televisión y comunicaciones | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Fabricación de instrumentos médicos, ópticos y de precisión; fabricación de relojes | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Fabricación de vehículos automotores, remolques y semirremolques | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Fabricación de equipo de transporte n.c.p. | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Fabricación de muebles y colchones; industrias manufactureras n.c.p. | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Reciclamiento | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Reparación, mantenimiento e instalación de maquinas y equipos | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Total | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Generación captación y distribución de energía eléctrica | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Fabricación de gas; distribución de combustibles gaseosos por tuberías | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Captación, depuración y distribución de agua | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Total | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Total | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Total | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Hoteles; campamentos y otros tipos de hospedaje temporal | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Restaurantes, bares y cantinas | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Total | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Transporte | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Comunicaciones | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Total | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Intermediación financiera y otros servicios financieros | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Servicios de seguros | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Servicios auxiliares a la actividad financiera | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Total | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Servicios inmobiliarios con bienes propios y arrendados | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Resto | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Total | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Total | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Enseñanza Pública | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Enseñanza Privada | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Total | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Salud Pública | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Salud Privada | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Total | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Eliminación de desperdicios y aguas residuales, saneamiento y servicios similares | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Asociaciones | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Servicios culturales y deportivos. Otras actividades | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Total | `cn_vab_rama_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Valor agregado bruto a precios básicos por rama de actividad económica. | indice | unidad |  |
| Impuesto a los productos netos de subsidios (a los ingresos brutos, específicos, a los débitos y créditos bancarios, a las exportaciones) | `cn_pbi_categoria_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por categoría de tabulación, cuentas nacionales. | moneda | millones | ARS |
| Impuesto a los productos netos de subsidios (a los ingresos brutos, específicos, a los débitos y créditos bancarios, a las exportaciones) | `cn_pbi_categoria_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por categoría de tabulación, cuentas nacionales. | moneda | millones | ARS |
| IVA | `cn_pbi_categoria_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | moneda | millones | ARS |
| IVA | `cn_pbi_categoria_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | moneda | millones | ARS |
| Impuesto a los productos importados (derechos de importación) | `cn_pbi_categoria_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | moneda | millones | ARS |
| Impuesto a los productos importados (derechos de importación) | `cn_pbi_categoria_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | moneda | millones | ARS |
| Valor agregado bruto a precios básicos | `cn_pbi_categoria_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | moneda | millones | ARS |
| Valor agregado bruto a precios básicos | `cn_pbi_categoria_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | moneda | millones | ARS |
| Total | `cn_pbi_categoria_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | moneda | millones | ARS |
| Total | `cn_pbi_categoria_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | moneda | millones | ARS |
| Total | `cn_pbi_categoria_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | moneda | millones | ARS |
| Total | `cn_pbi_categoria_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | moneda | millones | ARS |
| Total | `cn_pbi_categoria_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | moneda | millones | ARS |
| Total | `cn_pbi_categoria_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | moneda | millones | ARS |
| Total | `cn_pbi_categoria_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | moneda | millones | ARS |
| Total | `cn_pbi_categoria_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | moneda | millones | ARS |
| Total | `cn_pbi_categoria_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | moneda | millones | ARS |
| Total | `cn_pbi_categoria_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | moneda | millones | ARS |
| Total | `cn_pbi_categoria_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | moneda | millones | ARS |
| Total | `cn_pbi_categoria_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | moneda | millones | ARS |
| Total | `cn_pbi_categoria_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | moneda | millones | ARS |
| Total | `cn_pbi_categoria_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | moneda | millones | ARS |
| Total | `cn_pbi_categoria_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | moneda | millones | ARS |
| Total | `cn_pbi_categoria_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | moneda | millones | ARS |
| Total | `cn_pbi_categoria_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | moneda | millones | ARS |
| Total | `cn_pbi_categoria_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | moneda | millones | ARS |
| Total | `cn_pbi_categoria_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | moneda | millones | ARS |
| Total | `cn_pbi_categoria_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | moneda | millones | ARS |
| Total | `cn_pbi_categoria_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | moneda | millones | ARS |
| Total | `cn_pbi_categoria_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | moneda | millones | ARS |
| Total | `cn_pbi_categoria_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | moneda | millones | ARS |
| Total | `cn_pbi_categoria_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | moneda | millones | ARS |
| Total | `cn_pbi_categoria_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | moneda | millones | ARS |
| Total | `cn_pbi_categoria_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | moneda | millones | ARS |
| Total | `cn_pbi_categoria_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | moneda | millones | ARS |
| Total | `cn_pbi_categoria_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | moneda | millones | ARS |
| Total | `cn_pbi_categoria_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | moneda | millones | ARS |
| Total | `cn_pbi_categoria_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | moneda | millones | ARS |
| Total | `cn_pbi_categoria_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | moneda | millones | ARS |
| Total | `cn_pbi_categoria_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | moneda | millones | ARS |
| Total | `cn_pbi_categoria_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | indice | unidad |  |
| Impuesto a los productos netos de subsidios (a los ingresos brutos, específicos, a los débitos y créditos bancarios, a las exportaciones) | `cn_pbi_categoria_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por categoría de tabulación, cuentas nacionales. | indice | unidad |  |
| IVA | `cn_pbi_categoria_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por categoría de tabulación, cuentas nacionales. | indice | unidad |  |
| Impuesto a los productos importados (derechos de importación) | `cn_pbi_categoria_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por categoría de tabulación, cuentas nacionales. | indice | unidad |  |
| Valor agregado bruto a precios básicos | `cn_pbi_categoria_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | indice | unidad |  |
| Total | `cn_pbi_categoria_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | indice | unidad |  |
| Total | `cn_pbi_categoria_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | indice | unidad |  |
| Total | `cn_pbi_categoria_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | indice | unidad |  |
| Total | `cn_pbi_categoria_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | indice | unidad |  |
| Total | `cn_pbi_categoria_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | indice | unidad |  |
| Total | `cn_pbi_categoria_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | indice | unidad |  |
| Total | `cn_pbi_categoria_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | indice | unidad |  |
| Total | `cn_pbi_categoria_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | indice | unidad |  |
| Total | `cn_pbi_categoria_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | indice | unidad |  |
| Total | `cn_pbi_categoria_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | indice | unidad |  |
| Total | `cn_pbi_categoria_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | indice | unidad |  |
| Total | `cn_pbi_categoria_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | indice | unidad |  |
| Total | `cn_pbi_categoria_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | indice | unidad |  |
| Total | `cn_pbi_categoria_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | indice | unidad |  |
| Total | `cn_pbi_categoria_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | indice | unidad |  |
| Total | `cn_pbi_categoria_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI por sector de actividad económica, cuentas nacionales. | indice | unidad |  |
| Producto Interno Bruto | `pbi_constante_kalman.csv` |  |  | M | propia |  | moneda | millones | ARS |
| Producto Interno Bruto | `cn_oferta_demanda_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI a precios constantes de 2004, cuentas nacionales trimestrales (serie desestacionalizada y original según c… | moneda | millones | ARS |
| Producto Interno Bruto | `pbi_nominal_kalman.csv` |  |  | M | propia |  | moneda | millones | ARS |
| Producto Interno Bruto | `cn_oferta_demanda_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | PBI a precios corrientes, cuentas nacionales trimestrales, base 2004. | moneda | millones | ARS |
| Importaciones FOB (bienes y servicios reales) | `od_impo_kalman.csv` |  |  | M | propia |  | moneda | millones | ARS |
| Importaciones FOB (bienes y servicios reales) | `cn_oferta_demanda_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Cuenta de oferta y demanda globales de las cuentas nacionales. | moneda | millones | ARS |
| Importaciones FOB (bienes y servicios reales) | `od_impo_nominal_kalman.csv` |  |  | M | propia |  | moneda | millones | ARS |
| Importaciones FOB (bienes y servicios reales) | `cn_oferta_demanda_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Cuenta de oferta y demanda globales de las cuentas nacionales. | moneda | millones | ARS |
| Total | `cn_oferta_demanda_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Cuenta de oferta y demanda globales de las cuentas nacionales. | moneda | millones | ARS |
| Total | `cn_oferta_demanda_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Cuenta de oferta y demanda globales de las cuentas nacionales. | moneda | millones | ARS |
| Total | `cn_oferta_demanda_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Cuenta de oferta y demanda globales de las cuentas nacionales. | moneda | millones | ARS |
| Total | `cn_oferta_demanda_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Cuenta de oferta y demanda globales de las cuentas nacionales. | moneda | millones | ARS |
| Consumo privado | `od_cpriv_kalman.csv` |  |  | M | propia |  | moneda | millones | ARS |
| Consumo privado | `cn_oferta_demanda_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Cuenta de oferta y demanda globales de las cuentas nacionales. | moneda | millones | ARS |
| Consumo privado | `od_cpriv_nominal_kalman.csv` |  |  | M | propia |  | moneda | millones | ARS |
| Consumo privado | `cn_oferta_demanda_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Cuenta de oferta y demanda globales de las cuentas nacionales. | moneda | millones | ARS |
| Consumo público | `od_cpub_kalman.csv` |  |  | M | propia |  | moneda | millones | ARS |
| Consumo público | `cn_oferta_demanda_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Cuenta de oferta y demanda globales de las cuentas nacionales. | moneda | millones | ARS |
| Consumo público | `od_cpub_nominal_kalman.csv` |  |  | M | propia |  | moneda | millones | ARS |
| Consumo público | `cn_oferta_demanda_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Cuenta de oferta y demanda globales de las cuentas nacionales. | moneda | millones | ARS |
| Exportaciones FOB (bienes y servicios reales) | `od_expo_kalman.csv` |  |  | M | propia |  | moneda | millones | ARS |
| Exportaciones FOB (bienes y servicios reales) | `cn_oferta_demanda_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Cuenta de oferta y demanda globales de las cuentas nacionales. | moneda | millones | ARS |
| Exportaciones FOB (bienes y servicios reales) | `od_expo_nominal_kalman.csv` |  |  | M | propia |  | moneda | millones | ARS |
| Exportaciones FOB (bienes y servicios reales) | `cn_oferta_demanda_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Cuenta de oferta y demanda globales de las cuentas nacionales. | moneda | millones | ARS |
| Formación bruta de capital fijo | `od_fbkf_kalman.csv` |  |  | M | propia |  | moneda | millones | ARS |
| Formación bruta de capital fijo | `cn_oferta_demanda_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Cuenta de oferta y demanda globales de las cuentas nacionales. | moneda | millones | ARS |
| Formación bruta de capital fijo | `od_fbkf_nominal_kalman.csv` |  |  | M | propia |  | moneda | millones | ARS |
| Formación bruta de capital fijo | `cn_oferta_demanda_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Cuenta de oferta y demanda globales de las cuentas nacionales. | moneda | millones | ARS |
| Variación de existencias | `cn_oferta_demanda_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Cuenta de oferta y demanda globales de las cuentas nacionales. | moneda | millones | ARS |
| Variación de existencias | `cn_oferta_demanda_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Cuenta de oferta y demanda globales de las cuentas nacionales. | moneda | millones | ARS |
| Objetos valiosos | `cn_oferta_demanda_constante.csv` | 2015-03-01 | 2025-12-01 | Q | indec | Cuenta de oferta y demanda globales de las cuentas nacionales. | moneda | millones | ARS |
| Objetos valiosos | `cn_oferta_demanda_corriente.csv` | 2016-03-01 | 2025-12-01 | Q | indec | Cuenta de oferta y demanda globales de las cuentas nacionales. | moneda | millones | ARS |
| Discrepancia estadística | `cn_oferta_demanda_constante.csv` | 2023-03-01 | 2025-12-01 | Q | indec | Cuenta de oferta y demanda globales de las cuentas nacionales. | moneda | millones | ARS |
| Discrepancia estadística | `cn_oferta_demanda_corriente.csv` | 2023-03-01 | 2025-12-01 | Q | indec | Cuenta de oferta y demanda globales de las cuentas nacionales. | moneda | millones | ARS |
| PIB | `cn_oferta_demanda_desest.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Oferta y demanda globales, serie desestacionalizada del INDEC. | moneda | millones | ARS |
| Importaciones | `cn_oferta_demanda_desest.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Oferta y demanda globales, serie desestacionalizada del INDEC. | moneda | millones | ARS |
| Consumo privado | `cn_oferta_demanda_desest.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Oferta y demanda globales, serie desestacionalizada del INDEC. | moneda | millones | ARS |
| Consumo público | `cn_oferta_demanda_desest.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Oferta y demanda globales, serie desestacionalizada del INDEC. | moneda | millones | ARS |
| FBCF | `cn_oferta_demanda_desest.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Oferta y demanda globales, serie desestacionalizada del INDEC. | moneda | millones | ARS |
| Exportaciones | `cn_oferta_demanda_desest.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Oferta y demanda globales, serie desestacionalizada del INDEC. | moneda | millones | ARS |
| Producto Interno Bruto | `cn_oferta_demanda_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Cuenta de oferta y demanda globales de las cuentas nacionales. | indice | unidad |  |
| Importaciones FOB (bienes y servicios reales) | `cn_oferta_demanda_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Cuenta de oferta y demanda globales de las cuentas nacionales. | indice | unidad |  |
| Total | `cn_oferta_demanda_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Cuenta de oferta y demanda globales de las cuentas nacionales. | indice | unidad |  |
| Total | `cn_oferta_demanda_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Cuenta de oferta y demanda globales de las cuentas nacionales. | indice | unidad |  |
| Consumo privado | `cn_oferta_demanda_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Cuenta de oferta y demanda globales de las cuentas nacionales. | indice | unidad |  |
| Consumo público | `cn_oferta_demanda_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Cuenta de oferta y demanda globales de las cuentas nacionales. | indice | unidad |  |
| Exportaciones FOB (bienes y servicios reales) | `cn_oferta_demanda_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Cuenta de oferta y demanda globales de las cuentas nacionales. | indice | unidad |  |
| Formación bruta de capital fijo | `cn_oferta_demanda_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Cuenta de oferta y demanda globales de las cuentas nacionales. | indice | unidad |  |
| Variación de existencias | `cn_oferta_demanda_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Cuenta de oferta y demanda globales de las cuentas nacionales. | indice | unidad |  |
| Objetos valiosos | `cn_oferta_demanda_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Cuenta de oferta y demanda globales de las cuentas nacionales. | indice | unidad |  |
| Discrepancia estadística | `cn_oferta_demanda_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Cuenta de oferta y demanda globales de las cuentas nacionales. | indice | unidad |  |
| Total | `cn_fbkf_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Formación Bruta de Capital Fijo, cuentas nacionales. | moneda | millones | ARS |
| Total | `cn_fbkf_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Formación Bruta de Capital Fijo, cuentas nacionales. | moneda | millones | ARS |
| Total | `cn_fbkf_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Formación Bruta de Capital Fijo, cuentas nacionales. | moneda | millones | ARS |
| Total | `cn_fbkf_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Formación Bruta de Capital Fijo, cuentas nacionales. | moneda | millones | ARS |
| Otras construcciones | `cn_fbkf_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Formación bruta de capital fijo, cuentas nacionales. | moneda | millones | ARS |
| Otras construcciones | `cn_fbkf_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Formación bruta de capital fijo, cuentas nacionales. | moneda | millones | ARS |
| Total | `cn_fbkf_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Formación Bruta de Capital Fijo, cuentas nacionales. | moneda | millones | ARS |
| Total | `cn_fbkf_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Formación Bruta de Capital Fijo, cuentas nacionales. | moneda | millones | ARS |
| Nacional | `cn_fbkf_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Formación Bruta de Capital Fijo, cuentas nacionales. | moneda | millones | ARS |
| Nacional | `cn_fbkf_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Formación Bruta de Capital Fijo, cuentas nacionales. | moneda | millones | ARS |
| Importado | `cn_fbkf_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Formación Bruta de Capital Fijo, cuentas nacionales. | moneda | millones | ARS |
| Importado | `cn_fbkf_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Formación Bruta de Capital Fijo, cuentas nacionales. | moneda | millones | ARS |
| Total | `cn_fbkf_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Formación Bruta de Capital Fijo, cuentas nacionales. | moneda | millones | ARS |
| Total | `cn_fbkf_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Formación Bruta de Capital Fijo, cuentas nacionales. | moneda | millones | ARS |
| Nacional | `cn_fbkf_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Formación bruta de capital fijo, cuentas nacionales. | moneda | millones | ARS |
| Nacional | `cn_fbkf_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Formación bruta de capital fijo, cuentas nacionales. | moneda | millones | ARS |
| Importado | `cn_fbkf_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Formación bruta de capital fijo, cuentas nacionales. | moneda | millones | ARS |
| Importado | `cn_fbkf_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Formación bruta de capital fijo, cuentas nacionales. | moneda | millones | ARS |
| Total | `cn_fbkf_constante.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Formación Bruta de Capital Fijo, cuentas nacionales. | moneda | millones | ARS |
| Total | `cn_fbkf_corriente.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Formación Bruta de Capital Fijo, cuentas nacionales. | moneda | millones | ARS |
| Total | `cn_fbkf_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Formación bruta de capital fijo, cuentas nacionales. | indice | unidad |  |
| Total | `cn_fbkf_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Formación bruta de capital fijo, cuentas nacionales. | indice | unidad |  |
| Otras construcciones | `cn_fbkf_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Formación bruta de capital fijo, cuentas nacionales. | indice | unidad |  |
| Total | `cn_fbkf_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Formación bruta de capital fijo, cuentas nacionales. | indice | unidad |  |
| Nacional | `cn_fbkf_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Formación bruta de capital fijo, cuentas nacionales. | indice | unidad |  |
| Importado | `cn_fbkf_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Formación bruta de capital fijo, cuentas nacionales. | indice | unidad |  |
| Total | `cn_fbkf_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Formación bruta de capital fijo, cuentas nacionales. | indice | unidad |  |
| Nacional | `cn_fbkf_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Formación bruta de capital fijo, cuentas nacionales. | indice | unidad |  |
| Importado | `cn_fbkf_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Formación bruta de capital fijo, cuentas nacionales. | indice | unidad |  |
| Total | `cn_fbkf_ipi.csv` | 2004-03-01 | 2025-12-01 | Q | indec | Formación bruta de capital fijo, cuentas nacionales. | indice | unidad |  |
| Total | `uci_bloques.csv` | 2016-01-01 | 2026-02-01 | M | indec | Utilización de la capacidad instalada en la industria, por bloque sectorial. | porcentaje | unidad |  |
| Productos alimenticios y bebidas | `uci_bloques.csv` | 2016-01-01 | 2026-02-01 | M | indec | Utilización de la capacidad instalada en la industria, por bloque sectorial. | porcentaje | unidad |  |
| Productos del tabaco | `uci_bloques.csv` | 2016-01-01 | 2026-02-01 | M | indec | Utilización de la capacidad instalada en la industria, por bloque sectorial. | porcentaje | unidad |  |
| Productos textiles | `uci_bloques.csv` | 2016-01-01 | 2026-02-01 | M | indec | Utilización de la capacidad instalada en la industria, por bloque sectorial. | porcentaje | unidad |  |
| Papel y cartón | `uci_bloques.csv` | 2016-01-01 | 2026-02-01 | M | indec | Utilización de la capacidad instalada en la industria, por bloque sectorial. | porcentaje | unidad |  |
| Edición e impresión | `uci_bloques.csv` | 2016-01-01 | 2026-02-01 | M | indec | Utilización de la capacidad instalada en la industria, por bloque sectorial. | porcentaje | unidad |  |
| Refinación del petróleo | `uci_bloques.csv` | 2016-01-01 | 2026-02-01 | M | indec | Utilización de la capacidad instalada en la industria, por bloque sectorial. | porcentaje | unidad |  |
| Sustancias y productos químicos | `uci_bloques.csv` | 2016-01-01 | 2026-02-01 | M | indec | Utilización de la capacidad instalada en la industria, por bloque sectorial. | porcentaje | unidad |  |
| Productos de caucho y plástico | `uci_bloques.csv` | 2016-01-01 | 2026-02-01 | M | indec | Utilización de la capacidad instalada en la industria, por bloque sectorial. | porcentaje | unidad |  |
| Productos minerales no metálicos | `uci_bloques.csv` | 2016-01-01 | 2026-02-01 | M | indec | Utilización de la capacidad instalada en la industria, por bloque sectorial. | porcentaje | unidad |  |
| Industrias metálicas básicas | `uci_bloques.csv` | 2016-01-01 | 2026-02-01 | M | indec | Utilización de la capacidad instalada en la industria, por bloque sectorial. | porcentaje | unidad |  |
| Industria automotriz | `uci_bloques.csv` | 2016-01-01 | 2026-02-01 | M | indec | Utilización de la capacidad instalada en la industria, por bloque sectorial. | porcentaje | unidad |  |
| Metalmecánica excluida industria automotriz | `uci_bloques.csv` | 2016-01-01 | 2026-02-01 | M | indec | Utilización de la capacidad instalada en la industria, por bloque sectorial. | porcentaje | unidad |  |
| Serie original | `emae_nivel_general_mensual.csv` | 2004-01-01 | 2026-02-01 | M | indec | Estimador Mensual de Actividad Económica, índice base 2004 = 100. | indice | unidad |  |
| Serie original | `emae_nivel_general_trimestral.csv` | 2004-01-01 | 2025-10-01 | Q | indec | Estimador Mensual de Actividad Económica, índice base 2004 = 100. | indice | unidad |  |
| Serie original | `emae_nivel_general_anual.csv` | 2004-01-01 | 2025-01-01 | A | indec | Estimador Mensual de Actividad Económica, índice base 2004 = 100. | indice | unidad |  |
| Serie desestacionalizada | `emae_nivel_general_mensual.csv` | 2004-01-01 | 2026-02-01 | M | indec | Estimador Mensual de Actividad Económica, índice base 2004 = 100. | indice | unidad |  |
| Serie desestacionalizada | `emae_nivel_general_trimestral.csv` | 2004-01-01 | 2025-10-01 | Q | indec | Estimador Mensual de Actividad Económica, índice base 2004 = 100. | indice | unidad |  |
| Serie desestacionalizada | `emae_nivel_general_anual.csv` | 2004-01-01 | 2025-01-01 | A | indec | Estimador Mensual de Actividad Económica, índice base 2004 = 100. | indice | unidad |  |
| Serie tendencia-ciclo | `emae_nivel_general_mensual.csv` | 2004-01-01 | 2026-02-01 | M | indec | Estimador Mensual de Actividad Económica, serie tendencia-ciclo, índice base 2004 = 100. | indice | unidad |  |
| Serie tendencia-ciclo | `emae_nivel_general_trimestral.csv` | 2004-01-01 | 2025-10-01 | Q | indec | Estimador Mensual de Actividad Económica, serie tendencia-ciclo, índice base 2004 = 100. | indice | unidad |  |
| Serie tendencia-ciclo | `emae_nivel_general_anual.csv` | 2004-01-01 | 2025-01-01 | A | indec | Estimador Mensual de Actividad Económica, serie tendencia-ciclo, índice base 2004 = 100. | indice | unidad |  |
| Total | `emae_sectorial_mensual.csv` |  |  | M | indec | Estimador Mensual de Actividad Económica, índice base 2004 = 100. | indice | unidad |  |
| Total | `emae_sectorial_trimestral.csv` |  |  | Q | indec | Estimador Mensual de Actividad Económica, índice base 2004 = 100. | indice | unidad |  |
| Total | `emae_sectorial_anual.csv` |  |  | A | indec | Estimador Mensual de Actividad Económica, índice base 2004 = 100. | indice | unidad |  |
| Total | `emae_sectorial_mensual.csv` |  |  | M | indec | Estimador Mensual de Actividad Económica, índice base 2004 = 100. | indice | unidad |  |
| Total | `emae_sectorial_trimestral.csv` |  |  | Q | indec | Estimador Mensual de Actividad Económica, índice base 2004 = 100. | indice | unidad |  |
| Total | `emae_sectorial_anual.csv` |  |  | A | indec | Estimador Mensual de Actividad Económica, índice base 2004 = 100. | indice | unidad |  |
| Total | `emae_sectorial_mensual.csv` |  |  | M | indec | Estimador Mensual de Actividad Económica, índice base 2004 = 100. | indice | unidad |  |
| Total | `emae_sectorial_trimestral.csv` |  |  | Q | indec | Estimador Mensual de Actividad Económica, índice base 2004 = 100. | indice | unidad |  |
| Total | `emae_sectorial_anual.csv` |  |  | A | indec | Estimador Mensual de Actividad Económica, índice base 2004 = 100. | indice | unidad |  |
| Total | `emae_sectorial_mensual.csv` |  |  | M | indec | Estimador Mensual de Actividad Económica, índice base 2004 = 100. | indice | unidad |  |
| Total | `emae_sectorial_trimestral.csv` |  |  | Q | indec | Estimador Mensual de Actividad Económica, índice base 2004 = 100. | indice | unidad |  |
| Total | `emae_sectorial_anual.csv` |  |  | A | indec | Estimador Mensual de Actividad Económica, índice base 2004 = 100. | indice | unidad |  |
| Total | `emae_sectorial_mensual.csv` |  |  | M | indec | Estimador Mensual de Actividad Económica, índice base 2004 = 100. | indice | unidad |  |
| Total | `emae_sectorial_trimestral.csv` |  |  | Q | indec | Estimador Mensual de Actividad Económica, índice base 2004 = 100. | indice | unidad |  |
| Total | `emae_sectorial_anual.csv` |  |  | A | indec | Estimador Mensual de Actividad Económica, índice base 2004 = 100. | indice | unidad |  |
| Total | `emae_sectorial_mensual.csv` |  |  | M | indec | Estimador Mensual de Actividad Económica, índice base 2004 = 100. | indice | unidad |  |
| Total | `emae_sectorial_trimestral.csv` |  |  | Q | indec | Estimador Mensual de Actividad Económica, índice base 2004 = 100. | indice | unidad |  |
| Total | `emae_sectorial_anual.csv` |  |  | A | indec | Estimador Mensual de Actividad Económica, índice base 2004 = 100. | indice | unidad |  |
| Total | `emae_sectorial_mensual.csv` |  |  | M | indec | Estimador Mensual de Actividad Económica, índice base 2004 = 100. | indice | unidad |  |
| Total | `emae_sectorial_trimestral.csv` |  |  | Q | indec | Estimador Mensual de Actividad Económica, índice base 2004 = 100. | indice | unidad |  |
| Total | `emae_sectorial_anual.csv` |  |  | A | indec | Estimador Mensual de Actividad Económica, índice base 2004 = 100. | indice | unidad |  |
| Total | `emae_sectorial_mensual.csv` |  |  | M | indec | Estimador Mensual de Actividad Económica, índice base 2004 = 100. | indice | unidad |  |
| Total | `emae_sectorial_trimestral.csv` |  |  | Q | indec | Estimador Mensual de Actividad Económica, índice base 2004 = 100. | indice | unidad |  |
| Total | `emae_sectorial_anual.csv` |  |  | A | indec | Estimador Mensual de Actividad Económica, índice base 2004 = 100. | indice | unidad |  |
| Total | `emae_sectorial_mensual.csv` |  |  | M | indec | Estimador Mensual de Actividad Económica, índice base 2004 = 100. | indice | unidad |  |
| Total | `emae_sectorial_trimestral.csv` |  |  | Q | indec | Estimador Mensual de Actividad Económica, índice base 2004 = 100. | indice | unidad |  |
| Total | `emae_sectorial_anual.csv` |  |  | A | indec | Estimador Mensual de Actividad Económica, índice base 2004 = 100. | indice | unidad |  |
| Total | `emae_sectorial_mensual.csv` |  |  | M | indec | Estimador Mensual de Actividad Económica, índice base 2004 = 100. | indice | unidad |  |
| Total | `emae_sectorial_trimestral.csv` |  |  | Q | indec | Estimador Mensual de Actividad Económica, índice base 2004 = 100. | indice | unidad |  |
| Total | `emae_sectorial_anual.csv` |  |  | A | indec | Estimador Mensual de Actividad Económica, índice base 2004 = 100. | indice | unidad |  |
| Total | `emae_sectorial_mensual.csv` |  |  | M | indec | Estimador Mensual de Actividad Económica, índice base 2004 = 100. | indice | unidad |  |
| Total | `emae_sectorial_trimestral.csv` |  |  | Q | indec | Estimador Mensual de Actividad Económica, índice base 2004 = 100. | indice | unidad |  |
| Total | `emae_sectorial_anual.csv` |  |  | A | indec | Estimador Mensual de Actividad Económica, índice base 2004 = 100. | indice | unidad |  |
| Total | `emae_sectorial_mensual.csv` |  |  | M | indec | Estimador Mensual de Actividad Económica, índice base 2004 = 100. | indice | unidad |  |
| Total | `emae_sectorial_trimestral.csv` |  |  | Q | indec | Estimador Mensual de Actividad Económica, índice base 2004 = 100. | indice | unidad |  |
| Total | `emae_sectorial_anual.csv` |  |  | A | indec | Estimador Mensual de Actividad Económica, índice base 2004 = 100. | indice | unidad |  |
| Total | `emae_sectorial_mensual.csv` |  |  | M | indec | Estimador Mensual de Actividad Económica, índice base 2004 = 100. | indice | unidad |  |
| Total | `emae_sectorial_trimestral.csv` |  |  | Q | indec | Estimador Mensual de Actividad Económica, índice base 2004 = 100. | indice | unidad |  |
| Total | `emae_sectorial_anual.csv` |  |  | A | indec | Estimador Mensual de Actividad Económica, índice base 2004 = 100. | indice | unidad |  |
| Total | `emae_sectorial_mensual.csv` |  |  | M | indec | Estimador Mensual de Actividad Económica, índice base 2004 = 100. | indice | unidad |  |
| Total | `emae_sectorial_trimestral.csv` |  |  | Q | indec | Estimador Mensual de Actividad Económica, índice base 2004 = 100. | indice | unidad |  |
| Total | `emae_sectorial_anual.csv` |  |  | A | indec | Estimador Mensual de Actividad Económica, índice base 2004 = 100. | indice | unidad |  |
| Total | `emae_sectorial_mensual.csv` |  |  | M | indec | Estimador Mensual de Actividad Económica, índice base 2004 = 100. | indice | unidad |  |
| Total | `emae_sectorial_trimestral.csv` |  |  | Q | indec | Estimador Mensual de Actividad Económica, índice base 2004 = 100. | indice | unidad |  |
| Total | `emae_sectorial_anual.csv` |  |  | A | indec | Estimador Mensual de Actividad Económica, índice base 2004 = 100. | indice | unidad |  |
| Total | `emae_sectorial_mensual.csv` |  |  | M | indec | Estimador Mensual de Actividad Económica, índice base 2004 = 100. | indice | unidad |  |
| Total | `emae_sectorial_trimestral.csv` |  |  | Q | indec | Estimador Mensual de Actividad Económica, índice base 2004 = 100. | indice | unidad |  |
| Total | `emae_sectorial_anual.csv` |  |  | A | indec | Estimador Mensual de Actividad Económica, índice base 2004 = 100. | indice | unidad |  |
| PBI en USD | `pbi_usd_kalman.csv` |  |  | M | propia |  | moneda | millones | USD |
| PBI en USD | `pbi_trimestral_usd_mep.csv` |  |  | Q | propia | PBI trimestral convertido a dólares al tipo de cambio MEP. | moneda | millones | USD |
| PBI per cápita (USD) | `pbi_per_capita_usd.csv` |  |  | M | propia | PBI per cápita en dólares. | moneda | unidad | USD |
| PBI per cápita (USD) | `pbi_per_capita_usd_anual.csv` |  |  | A | propia | PBI per cápita en dólares, frecuencia anual. | moneda | unidad | USD |
| Índice Líder (nivel) | `utdt_il.csv` |  |  | M | utdt | Índice Líder de la actividad económica (UTDT/CIF). | indice | unidad |  |
| Índice de Difusión | `utdt_il.csv` |  |  | M | utdt | Índice Líder de la actividad económica (UTDT/CIF). | proporcion | unidad |  |
| IPC Nivel General (índice) | `ipc_nacional.csv` |  |  | M | indec | Índice de Precios al Consumidor Nacional, nivel general, base diciembre 2016 = 100. | indice | unidad |  |
| Inflación mensual (realizada) | `ipc_nacional.csv` |  |  | M | indec | Índice de Precios al Consumidor Nacional, nivel general, base diciembre 2016 = 100. | tasa | unidad |  |
| CER — Coeficiente de Estabilización de Referencia | `0030_coeficiente_de_estabilizacion_de_referencia_cer.csv` |  |  | D | bcra | Índice base 2/2/2002 = 1 construido sobre la variación del IPC. Es el coeficiente con que se ajusta la deuda i… | indice | unidad |  |
| UVA — Unidad de Valor Adquisitivo | `0031_unidad_de_valor_adquisitivo_uva.csv` |  |  | D | bcra | Vale la milésima parte del costo de construcción de un metro cuadrado de vivienda al 31/3/2016; se actualiza p… | moneda | unidad | ARS |
| UVI — Unidad de Vivienda | `0032_unidad_de_vivienda_uvi.csv` |  |  | D | bcra | Como la UVA pero ajustada por el Índice del Costo de la Construcción (CAICC). | moneda | unidad | ARS |
| ICL — Índice para Contratos de Locación | `0040_indice_para_contratos_de_locacion_icl.csv` |  |  | D | bcra | Índice diario que combina la variación del IPC y la del RIPTE. Es el que ajusta los alquileres. | indice | unidad |  |
| Inflación mensual (serie larga BCRA) | `0027_inflacion_mensual.csv` |  |  | M | bcra | Variación mensual del IPC informado por INDEC. Entre noviembre de 2015 y abril de 2016 se empalma con el IPC d… | porcentaje | unidad |  |
| Inflación interanual (serie larga BCRA) | `0028_inflacion_interanual.csv` |  |  | M | bcra | Variación interanual del IPC informado por INDEC, con el mismo empalme 2015-2016. Arranca en enero de 1944. | porcentaje | unidad |  |
| Saldo Comercial | `ica_intercambio_comercial_argentino_valores_mensuales.csv` | 1992-01-01 | 2026-03-01 | M | indec | Intercambio Comercial Argentino: exportaciones, importaciones y saldo comercial. | moneda | millones | USD |
| Saldo Comercial | `ica_intercambio_comercial_argentino_valores_trimestrales.csv` | 1992-01-01 | 2026-01-01 | Q | indec | Intercambio Comercial Argentino: exportaciones, importaciones y saldo comercial. | moneda | millones | USD |
| Saldo Comercial | `ica_intercambio_comercial_argentino_valores_anuales.csv` | 1910-01-01 | 2025-01-01 | A | indec | Intercambio Comercial Argentino: exportaciones, importaciones y saldo comercial. | moneda | millones | USD |
| Exportaciones — Total | `ica_intercambio_comercial_argentino_valores_mensuales.csv` | 1992-01-01 | 2026-03-01 | M | indec | Intercambio Comercial Argentino: exportaciones, importaciones y saldo comercial. | moneda | millones | USD |
| Exportaciones — Total | `ica_intercambio_comercial_argentino_valores_trimestrales.csv` | 1992-01-01 | 2026-01-01 | Q | indec | Intercambio Comercial Argentino: exportaciones, importaciones y saldo comercial. | moneda | millones | USD |
| Exportaciones — Total | `ica_intercambio_comercial_argentino_valores_anuales.csv` | 1910-01-01 | 2025-01-01 | A | indec | Intercambio Comercial Argentino: exportaciones, importaciones y saldo comercial. | moneda | millones | USD |
| Importaciones — Total | `ica_intercambio_comercial_argentino_valores_mensuales.csv` | 1992-01-01 | 2026-03-01 | M | indec | Intercambio Comercial Argentino: exportaciones, importaciones y saldo comercial. | moneda | millones | USD |
| Importaciones — Total | `ica_intercambio_comercial_argentino_valores_trimestrales.csv` | 1992-01-01 | 2026-01-01 | Q | indec | Intercambio Comercial Argentino: exportaciones, importaciones y saldo comercial. | moneda | millones | USD |
| Importaciones — Total | `ica_intercambio_comercial_argentino_valores_anuales.csv` | 1910-01-01 | 2025-01-01 | A | indec | Intercambio Comercial Argentino: exportaciones, importaciones y saldo comercial. | moneda | millones | USD |
| Prod. Primarios (PP) | `ica_intercambio_comercial_argentino_valores_mensuales.csv` | 1992-01-01 | 2026-03-01 | M | indec | Intercambio Comercial Argentino: exportaciones, importaciones y saldo comercial. | moneda | millones | USD |
| Prod. Primarios (PP) | `ica_intercambio_comercial_argentino_valores_trimestrales.csv` | 1992-01-01 | 2026-01-01 | Q | indec | Intercambio Comercial Argentino: exportaciones, importaciones y saldo comercial. | moneda | millones | USD |
| Prod. Primarios (PP) | `ica_intercambio_comercial_argentino_valores_anuales.csv` | 1992-01-01 | 2025-01-01 | A | indec | Intercambio Comercial Argentino: exportaciones, importaciones y saldo comercial. | moneda | millones | USD |
| MOA | `ica_intercambio_comercial_argentino_valores_mensuales.csv` | 1992-01-01 | 2026-03-01 | M | indec | Intercambio Comercial Argentino: exportaciones, importaciones y saldo comercial. | moneda | millones | USD |
| MOA | `ica_intercambio_comercial_argentino_valores_trimestrales.csv` | 1992-01-01 | 2026-01-01 | Q | indec | Intercambio Comercial Argentino: exportaciones, importaciones y saldo comercial. | moneda | millones | USD |
| MOA | `ica_intercambio_comercial_argentino_valores_anuales.csv` | 1992-01-01 | 2025-01-01 | A | indec | Intercambio Comercial Argentino: exportaciones, importaciones y saldo comercial. | moneda | millones | USD |
| MOI | `ica_intercambio_comercial_argentino_valores_mensuales.csv` | 1992-01-01 | 2026-03-01 | M | indec | Intercambio Comercial Argentino: exportaciones, importaciones y saldo comercial. | moneda | millones | USD |
| MOI | `ica_intercambio_comercial_argentino_valores_trimestrales.csv` | 1992-01-01 | 2026-01-01 | Q | indec | Intercambio Comercial Argentino: exportaciones, importaciones y saldo comercial. | moneda | millones | USD |
| MOI | `ica_intercambio_comercial_argentino_valores_anuales.csv` | 1992-01-01 | 2025-01-01 | A | indec | Intercambio Comercial Argentino: exportaciones, importaciones y saldo comercial. | moneda | millones | USD |
| Combustible y Energía | `ica_intercambio_comercial_argentino_valores_mensuales.csv` | 1992-01-01 | 2026-03-01 | M | indec | Intercambio Comercial Argentino: exportaciones, importaciones y saldo comercial. | moneda | millones | USD |
| Combustible y Energía | `ica_intercambio_comercial_argentino_valores_trimestrales.csv` | 1992-01-01 | 2026-01-01 | Q | indec | Intercambio Comercial Argentino: exportaciones, importaciones y saldo comercial. | moneda | millones | USD |
| Combustible y Energía | `ica_intercambio_comercial_argentino_valores_anuales.csv` | 1992-01-01 | 2025-01-01 | A | indec | Intercambio Comercial Argentino: exportaciones, importaciones y saldo comercial. | moneda | millones | USD |
| Bienes de Capital | `ica_intercambio_comercial_argentino_valores_mensuales.csv` | 1992-01-01 | 2026-03-01 | M | indec | Intercambio Comercial Argentino: exportaciones, importaciones y saldo comercial. | moneda | millones | USD |
| Bienes de Capital | `ica_intercambio_comercial_argentino_valores_trimestrales.csv` | 1992-01-01 | 2026-01-01 | Q | indec | Intercambio Comercial Argentino: exportaciones, importaciones y saldo comercial. | moneda | millones | USD |
| Bienes de Capital | `ica_intercambio_comercial_argentino_valores_anuales.csv` | 1992-01-01 | 2025-01-01 | A | indec | Intercambio Comercial Argentino: exportaciones, importaciones y saldo comercial. | moneda | millones | USD |
| Bienes Intermedios | `ica_intercambio_comercial_argentino_valores_mensuales.csv` | 1992-01-01 | 2026-03-01 | M | indec | Intercambio Comercial Argentino: exportaciones, importaciones y saldo comercial. | moneda | millones | USD |
| Bienes Intermedios | `ica_intercambio_comercial_argentino_valores_trimestrales.csv` | 1992-01-01 | 2026-01-01 | Q | indec | Intercambio Comercial Argentino: exportaciones, importaciones y saldo comercial. | moneda | millones | USD |
| Bienes Intermedios | `ica_intercambio_comercial_argentino_valores_anuales.csv` | 1992-01-01 | 2025-01-01 | A | indec | Intercambio Comercial Argentino: exportaciones, importaciones y saldo comercial. | moneda | millones | USD |
| Combustibles/Lubric. | `ica_intercambio_comercial_argentino_valores_mensuales.csv` | 1992-01-01 | 2026-03-01 | M | indec | Intercambio Comercial Argentino: exportaciones, importaciones y saldo comercial. | moneda | millones | USD |
| Combustibles/Lubric. | `ica_intercambio_comercial_argentino_valores_trimestrales.csv` | 1992-01-01 | 2026-01-01 | Q | indec | Intercambio Comercial Argentino: exportaciones, importaciones y saldo comercial. | moneda | millones | USD |
| Combustibles/Lubric. | `ica_intercambio_comercial_argentino_valores_anuales.csv` | 1992-01-01 | 2025-01-01 | A | indec | Intercambio Comercial Argentino: exportaciones, importaciones y saldo comercial. | moneda | millones | USD |
| Piezas y Acces. BK | `ica_intercambio_comercial_argentino_valores_mensuales.csv` | 1992-01-01 | 2026-03-01 | M | indec | Intercambio Comercial Argentino: exportaciones, importaciones y saldo comercial. | moneda | millones | USD |
| Piezas y Acces. BK | `ica_intercambio_comercial_argentino_valores_trimestrales.csv` | 1992-01-01 | 2026-01-01 | Q | indec | Intercambio Comercial Argentino: exportaciones, importaciones y saldo comercial. | moneda | millones | USD |
| Piezas y Acces. BK | `ica_intercambio_comercial_argentino_valores_anuales.csv` | 1992-01-01 | 2025-01-01 | A | indec | Intercambio Comercial Argentino: exportaciones, importaciones y saldo comercial. | moneda | millones | USD |
| Bienes de Consumo | `ica_intercambio_comercial_argentino_valores_mensuales.csv` | 1992-01-01 | 2026-03-01 | M | indec | Intercambio Comercial Argentino: exportaciones, importaciones y saldo comercial. | moneda | millones | USD |
| Bienes de Consumo | `ica_intercambio_comercial_argentino_valores_trimestrales.csv` | 1992-01-01 | 2026-01-01 | Q | indec | Intercambio Comercial Argentino: exportaciones, importaciones y saldo comercial. | moneda | millones | USD |
| Bienes de Consumo | `ica_intercambio_comercial_argentino_valores_anuales.csv` | 1992-01-01 | 2025-01-01 | A | indec | Intercambio Comercial Argentino: exportaciones, importaciones y saldo comercial. | moneda | millones | USD |
| Vehículos Automotores | `ica_intercambio_comercial_argentino_valores_mensuales.csv` | 1992-01-01 | 2026-03-01 | M | indec | Intercambio Comercial Argentino: exportaciones, importaciones y saldo comercial. | moneda | millones | USD |
| Vehículos Automotores | `ica_intercambio_comercial_argentino_valores_trimestrales.csv` | 1992-01-01 | 2026-01-01 | Q | indec | Intercambio Comercial Argentino: exportaciones, importaciones y saldo comercial. | moneda | millones | USD |
| Vehículos Automotores | `ica_intercambio_comercial_argentino_valores_anuales.csv` | 1992-01-01 | 2025-01-01 | A | indec | Intercambio Comercial Argentino: exportaciones, importaciones y saldo comercial. | moneda | millones | USD |
| Términos de Intercambio (nominal) | `ti_mensual.csv` |  |  | M | indec | Términos del intercambio: relación entre índices de precios de exportación e importación. | indice | unidad |  |
| Términos de Intercambio (base 100) | `ti_mensual.csv` |  |  | M | indec | Términos del intercambio: relación entre índices de precios de exportación e importación. | indice | unidad |  |
| Precios Exportaciones | `ti_mensual.csv` |  |  | M | indec | Términos del intercambio: relación entre índices de precios de exportación e importación. | indice | unidad |  |
| Cantidades Exportadas | `ti_mensual.csv` |  |  | M | indec | Términos del intercambio: relación entre índices de precios de exportación e importación. | indice | unidad |  |
| Precios Importaciones | `ti_mensual.csv` |  |  | M | indec | Términos del intercambio: relación entre índices de precios de exportación e importación. | indice | unidad |  |
| Cantidades Importadas | `ti_mensual.csv` |  |  | M | indec | Términos del intercambio: relación entre índices de precios de exportación e importación. | indice | unidad |  |
| Total Mundial | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv` |  |  | M | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Total Mundial | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_trimes.csv` |  |  | Q | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Total Mundial | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_anuale.csv` |  |  | A | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| América Latina | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv` |  |  | M | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| América Latina | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_trimes.csv` |  |  | Q | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| América Latina | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_anuale.csv` |  |  | A | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Mercosur | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv` |  |  | M | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Mercosur | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_trimes.csv` |  |  | Q | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Mercosur | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_anuale.csv` |  |  | A | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Alianza del Pacífico | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv` |  |  | M | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Alianza del Pacífico | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_anuale.csv` |  |  | A | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Unión Europea | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv` |  |  | M | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Unión Europea | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_trimes.csv` |  |  | Q | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Unión Europea | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_anuale.csv` |  |  | A | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Asia Pacífico | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv` |  |  | M | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Asia Pacífico | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_trimes.csv` |  |  | Q | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Asia Pacífico | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_anuale.csv` |  |  | A | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| África | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv` |  |  | M | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| NAFTA | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv` |  |  | M | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| NAFTA | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_anuale.csv` |  |  | A | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| ALADI | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv` |  |  | M | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| ALADI | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_anuale.csv` |  |  | A | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| ASEAN | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv` |  |  | M | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Brasil | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv` |  |  | M | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Brasil | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_trimes.csv` |  |  | Q | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Brasil | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_anuale.csv` |  |  | A | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| EEUU | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv` |  |  | M | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| EEUU | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_trimes.csv` |  |  | Q | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| EEUU | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_anuale.csv` |  |  | A | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Uruguay | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv` |  |  | M | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Uruguay | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_trimes.csv` |  |  | Q | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Uruguay | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_anuale.csv` |  |  | A | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Paraguay | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv` |  |  | M | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Paraguay | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_trimes.csv` |  |  | Q | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Paraguay | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_anuale.csv` |  |  | A | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Chile | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv` |  |  | M | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Chile | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_trimes.csv` |  |  | Q | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Chile | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_anuale.csv` |  |  | A | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Venezuela | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv` |  |  | M | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Bolivia | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv` |  |  | M | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Colombia | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv` |  |  | M | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| México | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv` |  |  | M | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Perú | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv` |  |  | M | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Ecuador | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv` |  |  | M | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Canadá | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv` |  |  | M | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Resto Am. Lat. | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv` |  |  | M | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Alemania | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv` |  |  | M | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Alemania | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_anuale.csv` |  |  | A | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| España | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv` |  |  | M | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| España | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_anuale.csv` |  |  | A | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Francia | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv` |  |  | M | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Italia | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv` |  |  | M | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Países Bajos | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv` |  |  | M | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Reino Unido | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv` |  |  | M | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Polonia | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv` |  |  | M | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Portugal | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv` |  |  | M | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Austria | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv` |  |  | M | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Bélgica | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv` |  |  | M | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Suiza | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv` |  |  | M | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Resto UE | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv` |  |  | M | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| China | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv` |  |  | M | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| China | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_trimes.csv` |  |  | Q | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| China | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_anuale.csv` |  |  | A | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Japón | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv` |  |  | M | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Japón | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_trimes.csv` |  |  | Q | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Japón | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_anuale.csv` |  |  | A | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| India | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv` |  |  | M | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| India | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_trimes.csv` |  |  | Q | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| India | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_anuale.csv` |  |  | A | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Rusia | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv` |  |  | M | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Rusia | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_trimes.csv` |  |  | Q | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Corea | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv` |  |  | M | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Tailandia | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv` |  |  | M | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Taiwán | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv` |  |  | M | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Vietnam | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv` |  |  | M | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Indonesia | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv` |  |  | M | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Israel | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv` |  |  | M | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Australia | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv` |  |  | M | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Nueva Zelanda | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv` |  |  | M | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Resto Asia Pac. | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv` |  |  | M | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Angola | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv` |  |  | M | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Argelia | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv` |  |  | M | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Egipto | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv` |  |  | M | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Marruecos | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv` |  |  | M | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Sudáfrica | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv` |  |  | M | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Resto África | `saldo_comercial_paises_saldo_comercial_por_pa_ses_y_regiones_fob_cif_valores_mensua.csv` |  |  | M | indec | Saldo comercial por países y regiones, valores FOB/CIF. | moneda | millones | USD |
| Total Cuenta Corriente | `total_cuenta_corriente_kalman.csv` |  |  | M | propia |  | moneda | millones | USD |
| Total Cuenta Corriente | `balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv` |  |  | Q | indec | Balance de pagos según el MBP6 (sexta edición del manual del FMI). | moneda | millones | USD |
| Total Cuenta Corriente | `balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_anuales.csv` |  |  | A | indec | Balance de pagos según el MBP6 (sexta edición del manual del FMI). | moneda | millones | USD |
| Bienes y Servicios | `bp_bys_kalman.csv` |  |  | M | propia |  | moneda | millones | USD |
| Bienes y Servicios | `balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv` |  |  | Q | indec | Balance de pagos según el MBP6 (sexta edición del manual del FMI). | moneda | millones | USD |
| Bienes y Servicios | `balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_anuales.csv` |  |  | A | indec | Balance de pagos según el MBP6 (sexta edición del manual del FMI). | moneda | millones | USD |
| Bienes (neto) | `bp_bienes_kalman.csv` |  |  | M | propia |  | moneda | millones | USD |
| Bienes (neto) | `balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv` |  |  | Q | indec | Balance de pagos según el MBP6 (sexta edición del manual del FMI). | moneda | millones | USD |
| Bienes (neto) | `balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_anuales.csv` |  |  | A | indec | Balance de pagos según el MBP6 (sexta edición del manual del FMI). | moneda | millones | USD |
| Exportaciones FOB | `balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv` |  |  | Q | indec | Balance de pagos según el MBP6 (sexta edición del manual del FMI). | moneda | millones | USD |
| Exportaciones FOB | `balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_anuales.csv` |  |  | A | indec | Balance de pagos según el MBP6 (sexta edición del manual del FMI). | moneda | millones | USD |
| Importaciones FOB | `balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv` |  |  | Q | indec | Balance de pagos según el MBP6 (sexta edición del manual del FMI). | moneda | millones | USD |
| Importaciones FOB | `balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_anuales.csv` |  |  | A | indec | Balance de pagos según el MBP6 (sexta edición del manual del FMI). | moneda | millones | USD |
| Servicios (neto) | `bp_serv_kalman.csv` |  |  | M | propia |  | moneda | millones | USD |
| Servicios (neto) | `balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv` |  |  | Q | indec | Balance de pagos según el MBP6 (sexta edición del manual del FMI). | moneda | millones | USD |
| Servicios (neto) | `balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_anuales.csv` |  |  | A | indec | Balance de pagos según el MBP6 (sexta edición del manual del FMI). | moneda | millones | USD |
| Ingresos de Servicios | `balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv` |  |  | Q | indec | Balance de pagos según el MBP6 (sexta edición del manual del FMI). | moneda | millones | USD |
| Egresos de Servicios | `balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv` |  |  | Q | indec | Balance de pagos según el MBP6 (sexta edición del manual del FMI). | moneda | millones | USD |
| Ingresos Primarios | `bp_ip_kalman.csv` |  |  | M | propia |  | moneda | millones | USD |
| Ingresos Primarios | `balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv` |  |  | Q | indec | Balance de pagos según el MBP6 (sexta edición del manual del FMI). | moneda | millones | USD |
| Ingresos Primarios | `balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_anuales.csv` |  |  | A | indec | Balance de pagos según el MBP6 (sexta edición del manual del FMI). | moneda | millones | USD |
| Remuneración de Empleados | `balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv` |  |  | Q | indec | Balance de pagos según el MBP6 (sexta edición del manual del FMI). | moneda | millones | USD |
| Remuneración de Empleados | `balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_anuales.csv` |  |  | A | indec | Balance de pagos según el MBP6 (sexta edición del manual del FMI). | moneda | millones | USD |
| Rentas de Inversión | `balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv` |  |  | Q | indec | Balance de pagos según el MBP6 (sexta edición del manual del FMI). | moneda | millones | USD |
| Rentas de Inversión | `balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_anuales.csv` |  |  | A | indec | Balance de pagos según el MBP6 (sexta edición del manual del FMI). | moneda | millones | USD |
| Inv. Directa | `balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv` |  |  | Q | indec | Balance de pagos según el MBP6 (sexta edición del manual del FMI). | moneda | millones | USD |
| Inv. Directa | `balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_anuales.csv` |  |  | A | indec | Balance de pagos según el MBP6 (sexta edición del manual del FMI). | moneda | millones | USD |
| Inv. de Cartera | `balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv` |  |  | Q | indec | Balance de pagos según el MBP6 (sexta edición del manual del FMI). | moneda | millones | USD |
| Inv. de Cartera | `balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_anuales.csv` |  |  | A | indec | Balance de pagos según el MBP6 (sexta edición del manual del FMI). | moneda | millones | USD |
| Otra Inversión | `balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv` |  |  | Q | indec | Balance de pagos según el MBP6 (sexta edición del manual del FMI). | moneda | millones | USD |
| Ingresos Secundarios | `bp_is_kalman.csv` |  |  | M | propia |  | moneda | millones | USD |
| Ingresos Secundarios | `balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv` |  |  | Q | indec | Balance de pagos según el MBP6 (sexta edición del manual del FMI). | moneda | millones | USD |
| Ingresos Secundarios | `balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_anuales.csv` |  |  | A | indec | Balance de pagos según el MBP6 (sexta edición del manual del FMI). | moneda | millones | USD |
| Cuenta Capital | `bp_cap_kalman.csv` |  |  | M | propia |  | moneda | millones | USD |
| Cuenta Capital | `balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv` |  |  | Q | indec | Balance de pagos según el MBP6 (sexta edición del manual del FMI). | moneda | millones | USD |
| Cuenta Capital | `balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_anuales.csv` |  |  | A | indec | Balance de pagos según el MBP6 (sexta edición del manual del FMI). | moneda | millones | USD |
| Total Cuenta Financiera | `total_cuenta_financiera_kalman.csv` |  |  | M | propia |  | moneda | millones | USD |
| Total Cuenta Financiera | `balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv` |  |  | Q | indec | Balance de pagos según el MBP6 (sexta edición del manual del FMI). | moneda | millones | USD |
| Total Cuenta Financiera | `balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_anuales.csv` |  |  | A | indec | Balance de pagos según el MBP6 (sexta edición del manual del FMI). | moneda | millones | USD |
| Inversión Directa | `bp_id_kalman.csv` |  |  | M | propia |  | moneda | millones | USD |
| Inversión Directa | `balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv` |  |  | Q | indec | Balance de pagos según el MBP6 (sexta edición del manual del FMI). | moneda | millones | USD |
| Inversión Directa | `balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_anuales.csv` |  |  | A | indec | Balance de pagos según el MBP6 (sexta edición del manual del FMI). | moneda | millones | USD |
| Activos: Particip. Capital | `balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv` |  |  | Q | indec | Balance de pagos según el MBP6 (sexta edición del manual del FMI). | moneda | millones | USD |
| Pasivos: Particip. Capital | `balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv` |  |  | Q | indec | Balance de pagos según el MBP6 (sexta edición del manual del FMI). | moneda | millones | USD |
| Pasivos: Inst. Deuda | `balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv` |  |  | Q | indec | Balance de pagos según el MBP6 (sexta edición del manual del FMI). | moneda | millones | USD |
| Inversión de Cartera | `bp_ic_kalman.csv` |  |  | M | propia |  | moneda | millones | USD |
| Inversión de Cartera | `balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv` |  |  | Q | indec | Balance de pagos según el MBP6 (sexta edición del manual del FMI). | moneda | millones | USD |
| Inversión de Cartera | `balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_anuales.csv` |  |  | A | indec | Balance de pagos según el MBP6 (sexta edición del manual del FMI). | moneda | millones | USD |
| Activos: Participaciones | `balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv` |  |  | Q | indec | Balance de pagos según el MBP6 (sexta edición del manual del FMI). | moneda | millones | USD |
| Activos: Inst. Deuda | `balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv` |  |  | Q | indec | Balance de pagos según el MBP6 (sexta edición del manual del FMI). | moneda | millones | USD |
| Pasivos: Participaciones | `balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv` |  |  | Q | indec | Balance de pagos según el MBP6 (sexta edición del manual del FMI). | moneda | millones | USD |
| Pasivos: Inst. Deuda | `balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv` |  |  | Q | indec | Balance de pagos según el MBP6 (sexta edición del manual del FMI). | moneda | millones | USD |
| Derivados Financieros | `balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv` |  |  | Q | indec | Balance de pagos según el MBP6 (sexta edición del manual del FMI). | moneda | millones | USD |
| Otra Inversión | `bp_oi_kalman.csv` |  |  | M | propia |  | moneda | millones | USD |
| Otra Inversión | `balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv` |  |  | Q | indec | Balance de pagos según el MBP6 (sexta edición del manual del FMI). | moneda | millones | USD |
| Otra Inversión | `balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_anuales.csv` |  |  | A | indec | Balance de pagos según el MBP6 (sexta edición del manual del FMI). | moneda | millones | USD |
| Activos (adquisición neta) | `balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv` |  |  | Q | indec | Balance de pagos según el MBP6 (sexta edición del manual del FMI). | moneda | millones | USD |
| Pasivos (emisión neta) | `balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv` |  |  | Q | indec | Balance de pagos según el MBP6 (sexta edición del manual del FMI). | moneda | millones | USD |
| Activos de Reserva | `bp_res_kalman.csv` |  |  | M | propia |  | moneda | millones | USD |
| Activos de Reserva | `balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv` |  |  | Q | indec | Balance de pagos según el MBP6 (sexta edición del manual del FMI). | moneda | millones | USD |
| Activos de Reserva | `balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_anuales.csv` |  |  | A | indec | Balance de pagos según el MBP6 (sexta edición del manual del FMI). | moneda | millones | USD |
| Errores y Omisiones | `bp_err_kalman.csv` |  |  | M | propia |  | moneda | millones | USD |
| Errores y Omisiones | `balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv` |  |  | Q | indec | Balance de pagos según el MBP6 (sexta edición del manual del FMI). | moneda | millones | USD |
| Errores y Omisiones | `balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_anuales.csv` |  |  | A | indec | Balance de pagos según el MBP6 (sexta edición del manual del FMI). | moneda | millones | USD |
| Superávit Primario | `Resultado fiscal-unificado.xlsx` |  |  | M | mecon | Esquema Ahorro-Inversión-Financiamiento del Sector Público Nacional, empalmado entre los cortes 1993-2006, 200… | moneda | millones | ARS |
| Superávit Primario s/ privat. | `Resultado fiscal-unificado.xlsx` |  |  | M | mecon | Esquema Ahorro-Inversión-Financiamiento del Sector Público Nacional, empalmado entre los cortes 1993-2006, 200… | moneda | millones | ARS |
| Resultado Financiero | `Resultado fiscal-unificado.xlsx` |  |  | M | mecon | Esquema Ahorro-Inversión-Financiamiento del Sector Público Nacional, empalmado entre los cortes 1993-2006, 200… | moneda | millones | ARS |
| Resultado Financiero s/ privat. | `Resultado fiscal-unificado.xlsx` |  |  | M | mecon | Esquema Ahorro-Inversión-Financiamiento del Sector Público Nacional, empalmado entre los cortes 1993-2006, 200… | moneda | millones | ARS |
| Resultado Económico | `Resultado fiscal-unificado.xlsx` |  |  | M | mecon | Esquema Ahorro-Inversión-Financiamiento del Sector Público Nacional, empalmado entre los cortes 1993-2006, 200… | moneda | millones | ARS |
| Resultado Primario s/ rentas | `Resultado fiscal-unificado.xlsx` |  |  | M | mecon | Esquema Ahorro-Inversión-Financiamiento del Sector Público Nacional, empalmado entre los cortes 1993-2006, 200… | moneda | millones | ARS |
| SE — Resultado Estructural (% PBI) | `fis_se_pctpib_kalman.csv` |  |  | M | propia |  | porcentaje | unidad |  |
| SE — Resultado Estructural (% PBI) | `resultado_fiscal_estructural.csv` |  |  | Q | propia | Resultado fiscal estructural: resultado primario corregido por el ciclo económico. | porcentaje | unidad |  |
| SCA — Cíclicamente Ajustado (% PBI) | `resultado_fiscal_estructural.csv` |  |  | Q | propia | Resultado fiscal estructural: resultado primario corregido por el ciclo económico. | porcentaje | unidad |  |
| SP — Primario observado (% PBI) | `resultado_fiscal_estructural.csv` |  |  | Q | propia | Resultado fiscal estructural: resultado primario corregido por el ciclo económico. | porcentaje | unidad |  |
| Tx — Derechos exportación (% PBI) | `resultado_fiscal_estructural.csv` |  |  | Q | propia | Resultado fiscal estructural: resultado primario corregido por el ciclo económico. | porcentaje | unidad |  |
| Componente cíclico commodity | `resultado_fiscal_estructural.csv` |  |  | Q | propia | Resultado fiscal estructural: resultado primario corregido por el ciclo económico. | moneda | millones | ARS |
| Brecha del Producto (Y-Y*)/Y* | `resultado_fiscal_estructural.csv` |  |  | Q | propia | Resultado fiscal estructural: resultado primario corregido por el ciclo económico. | ratio | unidad |  |
| PBI Potencial (Cobb-Douglas) | `resultado_fiscal_estructural.csv` |  |  | Q | propia | Resultado fiscal estructural: resultado primario corregido por el ciclo económico. | moneda | millones | ARS |
| Términos de Intercambio | `resultado_fiscal_estructural.csv` |  |  | Q | propia | Resultado fiscal estructural: resultado primario corregido por el ciclo económico. | indice | unidad |  |
| TI* (largo plazo, MA10y) | `resultado_fiscal_estructural.csv` |  |  | Q | propia | Resultado fiscal estructural: resultado primario corregido por el ciclo económico. | indice | unidad |  |
| NAIRU (HP filter EPH) | `resultado_fiscal_estructural.csv` |  |  | Q | propia | Resultado fiscal estructural: resultado primario corregido por el ciclo económico. | ratio | unidad |  |
| Tasa desempleo EPH | `resultado_fiscal_estructural.csv` |  |  | Q | propia | Resultado fiscal estructural: resultado primario corregido por el ciclo económico. | ratio | unidad |  |
| Tasa empleo EPH | `resultado_fiscal_estructural.csv` |  |  | Q | propia | Resultado fiscal estructural: resultado primario corregido por el ciclo económico. | ratio | unidad |  |
| Tasa actividad (derivada) | `resultado_fiscal_estructural.csv` |  |  | Q | propia | Resultado fiscal estructural: resultado primario corregido por el ciclo económico. | ratio | unidad |  |
| Stock de Capital K | `resultado_fiscal_estructural.csv` |  |  | Q | propia | Resultado fiscal estructural: resultado primario corregido por el ciclo económico. | moneda | millones | ARS |
| L — Ocupados | `resultado_fiscal_estructural.csv` |  |  | Q | propia | Resultado fiscal estructural: resultado primario corregido por el ciclo económico. | personas | unidad |  |
| L — Pleno empleo | `resultado_fiscal_estructural.csv` |  |  | Q | propia | Resultado fiscal estructural: resultado primario corregido por el ciclo económico. | personas | unidad |  |
| PTF suavizada (Productividad) | `resultado_fiscal_estructural.csv` |  |  | Q | propia | Resultado fiscal estructural: resultado primario corregido por el ciclo económico. | indice | unidad |  |
| SE — Nivel (Mill. ARS) | `resultado_fiscal_estructural.csv` |  |  | Q | propia | Resultado fiscal estructural: resultado primario corregido por el ciclo económico. | moneda | millones | ARS |
| Ingresos Corrientes — Total | `Resultado fiscal-unificado.xlsx` |  |  | M | mecon | Esquema Ahorro-Inversión-Financiamiento del Sector Público Nacional, empalmado entre los cortes 1993-2006, 200… | moneda | millones | ARS |
| Tributarios | `Resultado fiscal-unificado.xlsx` |  |  | M | mecon | Esquema Ahorro-Inversión-Financiamiento del Sector Público Nacional, empalmado entre los cortes 1993-2006, 200… | moneda | millones | ARS |
| Aportes Seg. Social | `Resultado fiscal-unificado.xlsx` |  |  | M | mecon | Esquema Ahorro-Inversión-Financiamiento del Sector Público Nacional, empalmado entre los cortes 1993-2006, 200… | moneda | millones | ARS |
| No Tributarios | `Resultado fiscal-unificado.xlsx` |  |  | M | mecon | Esquema Ahorro-Inversión-Financiamiento del Sector Público Nacional, empalmado entre los cortes 1993-2006, 200… | moneda | millones | ARS |
| Rentas de la Propiedad | `Resultado fiscal-unificado.xlsx` |  |  | M | mecon | Esquema Ahorro-Inversión-Financiamiento del Sector Público Nacional, empalmado entre los cortes 1993-2006, 200… | moneda | millones | ARS |
| Rentas percibidas BCRA | `Resultado fiscal-unificado.xlsx` |  |  | M | mecon | Esquema Ahorro-Inversión-Financiamiento del Sector Público Nacional, empalmado entre los cortes 1993-2006, 200… | moneda | millones | ARS |
| Transf. Corrientes | `Resultado fiscal-unificado.xlsx` |  |  | M | mecon | Esquema Ahorro-Inversión-Financiamiento del Sector Público Nacional, empalmado entre los cortes 1993-2006, 200… | moneda | millones | ARS |
| Gastos Corrientes — Total | `Resultado fiscal-unificado.xlsx` |  |  | M | mecon | Esquema Ahorro-Inversión-Financiamiento del Sector Público Nacional, empalmado entre los cortes 1993-2006, 200… | moneda | millones | ARS |
| Remuneraciones | `Resultado fiscal-unificado.xlsx` |  |  | M | mecon | Esquema Ahorro-Inversión-Financiamiento del Sector Público Nacional, empalmado entre los cortes 1993-2006, 200… | moneda | millones | ARS |
| Bienes y Servicios | `Resultado fiscal-unificado.xlsx` |  |  | M | mecon | Esquema Ahorro-Inversión-Financiamiento del Sector Público Nacional, empalmado entre los cortes 1993-2006, 200… | moneda | millones | ARS |
| Intereses Deuda Interna | `Resultado fiscal-unificado.xlsx` |  |  | M | mecon | Esquema Ahorro-Inversión-Financiamiento del Sector Público Nacional, empalmado entre los cortes 1993-2006, 200… | moneda | millones | ARS |
| Intereses Deuda Externa | `Resultado fiscal-unificado.xlsx` |  |  | M | mecon | Esquema Ahorro-Inversión-Financiamiento del Sector Público Nacional, empalmado entre los cortes 1993-2006, 200… | moneda | millones | ARS |
| Intereses Netos | `Resultado fiscal-unificado.xlsx` |  |  | M | mecon | Esquema Ahorro-Inversión-Financiamiento del Sector Público Nacional, empalmado entre los cortes 1993-2006, 200… | moneda | millones | ARS |
| Prestaciones Seg. Social | `Resultado fiscal-unificado.xlsx` |  |  | M | mecon | Esquema Ahorro-Inversión-Financiamiento del Sector Público Nacional, empalmado entre los cortes 1993-2006, 200… | moneda | millones | ARS |
| Transf. Corrientes Prov. | `Resultado fiscal-unificado.xlsx` |  |  | M | mecon | Esquema Ahorro-Inversión-Financiamiento del Sector Público Nacional, empalmado entre los cortes 1993-2006, 200… | moneda | millones | ARS |
| Transf. Corrientes Univ. | `Resultado fiscal-unificado.xlsx` |  |  | M | mecon | Esquema Ahorro-Inversión-Financiamiento del Sector Público Nacional, empalmado entre los cortes 1993-2006, 200… | moneda | millones | ARS |
| Gastos de Capital — Total | `Resultado fiscal-unificado.xlsx` |  |  | M | mecon | Esquema Ahorro-Inversión-Financiamiento del Sector Público Nacional, empalmado entre los cortes 1993-2006, 200… | moneda | millones | ARS |
| Inversión Real Directa | `Resultado fiscal-unificado.xlsx` |  |  | M | mecon | Esquema Ahorro-Inversión-Financiamiento del Sector Público Nacional, empalmado entre los cortes 1993-2006, 200… | moneda | millones | ARS |
| Riesgo País ARG (EMBI+) | `riesgo_pais_arg.csv` |  |  | D | argentinadatos | Riesgo país de Argentina (EMBI+ Argentina), en puntos básicos. | puntos_basicos | unidad |  |
| EMBI Global Latinoamérica | `embi_latam.csv` |  |  | D | bcrp | EMBI Global América Latina (spread soberano de la región), en puntos básicos. | puntos_basicos | unidad |  |
| EMBIG Argentina | `embig_bcrp.csv` |  |  | D | bcrp | EMBI Global por país, difundido por el BCRP. | puntos_basicos | unidad |  |
| EMBIG Brasil | `embig_bcrp.csv` |  |  | D | bcrp | EMBI Global por país, difundido por el BCRP. | puntos_basicos | unidad |  |
| EMBIG México | `embig_bcrp.csv` |  |  | D | bcrp | EMBI Global por país, difundido por el BCRP. | puntos_basicos | unidad |  |
| EMBIG Chile | `embig_bcrp.csv` |  |  | D | bcrp | EMBI Global por país, difundido por el BCRP. | puntos_basicos | unidad |  |
| EMBIG Colombia | `embig_bcrp.csv` |  |  | D | bcrp | EMBI Global por país, difundido por el BCRP. | puntos_basicos | unidad |  |
| EMBIG Perú | `embig_bcrp.csv` |  |  | D | bcrp | EMBI Global por país, difundido por el BCRP. | puntos_basicos | unidad |  |
| EMBIG Ecuador | `embig_bcrp.csv` |  |  | D | bcrp | EMBI Global por país, difundido por el BCRP. | puntos_basicos | unidad |  |
| EMBIG Venezuela | `embig_bcrp.csv` |  |  | D | bcrp | EMBI Global por país, difundido por el BCRP. | puntos_basicos | unidad |  |
| EMBIG Economías Emergentes | `embig_bcrp.csv` |  |  | D | bcrp | EMBI Global por país, difundido por el BCRP. | puntos_basicos | unidad |  |
| Nº de Defaults (histórico) | `defaults_history.csv` |  |  | D | propia | Cronología de episodios de default soberano argentino. | conteo | unidad |  |
| Años desde último Default | `years_since_default.csv` |  |  | D | propia | Años transcurridos desde el último default soberano. | tiempo | unidad |  |
| Deuda Bruta Total | `deuda_bruta_total_kalman.csv` |  |  | M | propia |  | moneda | millones | USD |
| Deuda Bruta Total | `saldo_deuda.csv` |  |  | Q | finanzas | Saldo de la deuda bruta de la Administración Central, por instrumento y moneda. | moneda | millones | USD |
| En situación de pago normal | `saldo_deuda.csv` |  |  | Q | finanzas | Saldo de la deuda bruta de la Administración Central, por instrumento y moneda. | moneda | millones | USD |
| Títulos Públicos | `saldo_deuda.csv` |  |  | Q | finanzas | Saldo de la deuda bruta de la Administración Central, por instrumento y moneda. | moneda | millones | USD |
| Bonos | `saldo_deuda.csv` |  |  | Q | finanzas | Saldo de la deuda bruta de la Administración Central, por instrumento y moneda. | moneda | millones | USD |
| Letras (total) | `saldo_deuda.csv` |  |  | Q | finanzas | Saldo de la deuda bruta de la Administración Central, por instrumento y moneda. | moneda | millones | USD |
| Letras del Tesoro | `saldo_deuda.csv` |  |  | Q | finanzas | Saldo de la deuda bruta de la Administración Central, por instrumento y moneda. | moneda | millones | USD |
| Préstamos | `saldo_deuda.csv` |  |  | Q | finanzas | Saldo de la deuda bruta de la Administración Central, por instrumento y moneda. | moneda | millones | USD |
| Préstamos Garantizados | `saldo_deuda.csv` |  |  | Q | finanzas | Saldo de la deuda bruta de la Administración Central, por instrumento y moneda. | moneda | millones | USD |
| Organismos Internacionales | `deuda_org_int_kalman.csv` |  |  | M | propia |  | moneda | millones | USD |
| Organismos Internacionales | `saldo_deuda.csv` |  |  | Q | finanzas | Saldo de la deuda bruta de la Administración Central, por instrumento y moneda. | moneda | millones | USD |
| FMI | `saldo_deuda.csv` |  |  | Q | finanzas | Saldo de la deuda bruta de la Administración Central, por instrumento y moneda. | moneda | millones | USD |
| BID | `saldo_deuda.csv` |  |  | Q | finanzas | Saldo de la deuda bruta de la Administración Central, por instrumento y moneda. | moneda | millones | USD |
| BIRF | `saldo_deuda.csv` |  |  | Q | finanzas | Saldo de la deuda bruta de la Administración Central, por instrumento y moneda. | moneda | millones | USD |
| CAF | `saldo_deuda.csv` |  |  | Q | finanzas | Saldo de la deuda bruta de la Administración Central, por instrumento y moneda. | moneda | millones | USD |
| Bilaterales | `saldo_deuda.csv` |  |  | Q | finanzas | Saldo de la deuda bruta de la Administración Central, por instrumento y moneda. | moneda | millones | USD |
| Club de París | `saldo_deuda.csv` |  |  | Q | finanzas | Saldo de la deuda bruta de la Administración Central, por instrumento y moneda. | moneda | millones | USD |
| Banca Comercial | `saldo_deuda.csv` |  |  | Q | finanzas | Saldo de la deuda bruta de la Administración Central, por instrumento y moneda. | moneda | millones | USD |
| Anticipos BCRA | `saldo_deuda.csv` |  |  | Q | finanzas | Saldo de la deuda bruta de la Administración Central, por instrumento y moneda. | moneda | millones | USD |
| En situación de pago diferido | `saldo_deuda.csv` |  |  | Q | finanzas | Saldo de la deuda bruta de la Administración Central, por instrumento y moneda. | moneda | millones | USD |
| Deuda elegible pendiente reestr. | `saldo_deuda.csv` |  |  | Q | finanzas | Saldo de la deuda bruta de la Administración Central, por instrumento y moneda. | moneda | millones | USD |
| Vencimientos Totales | `venc_2y_total_kalman.csv` |  |  | M | propia |  | moneda | millones | USD |
| Vencimientos Totales | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Local (ARS) | `venc_2y_ml_kalman.csv` |  |  | M | propia |  | moneda | millones | USD |
| Moneda Local (ARS) | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera (USD+) | `venc_2y_me_kalman.csv` |  |  | M | propia |  | moneda | millones | USD |
| Moneda Extranjera (USD+) | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Anticipos BCRA | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Local | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Avales | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Local | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Banca Comercial | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Local | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| BCIE | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Local | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| BEI | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Local | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| BID | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Local | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Bilaterales | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Local | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| BIRF | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Local | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| BOCON 9ª Serie/2010/PR16 | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Local | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Bonos | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Local | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| CAF | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Local | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Club de París | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Local | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Decreto 1579 | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Local | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Decreto 977 | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Local | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| FIDA | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Local | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| FMI | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Local | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| FONPLATA | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Local | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Letras del Tesoro | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Local | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Letras en Garantía | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Local | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| OFID | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Local | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Organ. Ofic. Bilateral Interna | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Local | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Otros | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Local | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Otros Acreeds. — Proveed. Externa | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Local | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Otros Acreeds. — Proveed. Interna | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Local | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Pagarés | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Local | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Préstamos Garantizados | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Local | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Títulos Públicos — BOCON | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Local | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera | `vencimientos_2y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 2 años vista, por moneda. | moneda | millones | USD |
| Vencimientos Totales | `venc_1y_total_kalman.csv` |  |  | M | propia |  | moneda | millones | USD |
| Vencimientos Totales | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Local (ARS) | `venc_1y_ml_kalman.csv` |  |  | M | propia |  | moneda | millones | USD |
| Moneda Local (ARS) | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera (USD+) | `venc_1y_me_kalman.csv` |  |  | M | propia |  | moneda | millones | USD |
| Moneda Extranjera (USD+) | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Anticipos BCRA | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Local | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Avales | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Local | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Banca Comercial | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Local | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| BCIE | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Local | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| BEI | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Local | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| BID | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Local | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Bilaterales | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Local | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| BIRF | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Local | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| BOCON 9ª Serie/2010/PR16 | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Local | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Bonos | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Local | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| CAF | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Local | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Club de París | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Local | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Decreto 1579 | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Local | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Decreto 977 | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Local | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| FIDA | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Local | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| FMI | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Local | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| FONPLATA | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Local | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Letras del Tesoro | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Local | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Letras en Garantía | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Local | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| OFID | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Local | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Organ. Ofic. Bilateral Interna | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Local | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Otros | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Local | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Otros Acreeds. — Proveed. Externa | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Local | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Otros Acreeds. — Proveed. Interna | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Local | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Pagarés | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Local | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Préstamos Garantizados | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Local | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Títulos Públicos — BOCON | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Local | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Moneda Extranjera | `vencimientos_1y_nuevo.csv` |  |  | Q | finanzas | Vencimientos de deuda a 1 año vista, por moneda. | moneda | millones | USD |
| Deuda Externa Bruta Total | `deuda_externa_bruta_total_kalman.csv` |  |  | M | propia |  | moneda | millones | USD |
| Deuda Externa Bruta Total | `deuda_externa_sectores.csv` |  |  | Q | indec | Deuda externa bruta total por sector residente (cuadro 23 de Cuentas Internacionales, MBP6). | moneda | millones | USD |
| Gobierno General | `dext_gobierno_kalman.csv` |  |  | M | propia |  | moneda | millones | USD |
| Gobierno General | `deuda_externa_sectores.csv` |  |  | Q | indec | Deuda externa bruta total por sector residente (cuadro 23 de Cuentas Internacionales, MBP6). | moneda | millones | USD |
| Banco Central | `dext_bcra_kalman.csv` |  |  | M | propia |  | moneda | millones | USD |
| Banco Central | `deuda_externa_sectores.csv` |  |  | Q | indec | Deuda externa bruta total por sector residente (cuadro 23 de Cuentas Internacionales, MBP6). | moneda | millones | USD |
| Bancos (Soc. captadoras de dep.) | `dext_bancos_kalman.csv` |  |  | M | propia |  | moneda | millones | USD |
| Bancos (Soc. captadoras de dep.) | `deuda_externa_sectores.csv` |  |  | Q | indec | Deuda externa bruta total por sector residente (cuadro 23 de Cuentas Internacionales, MBP6). | moneda | millones | USD |
| Otros Sectores | `dext_otros_sec_kalman.csv` |  |  | M | propia |  | moneda | millones | USD |
| Otros Sectores | `deuda_externa_sectores.csv` |  |  | Q | indec | Deuda externa bruta total por sector residente (cuadro 23 de Cuentas Internacionales, MBP6). | moneda | millones | USD |
| Otras Soc. Financieras | `deuda_externa_sectores.csv` |  |  | Q | indec | Deuda externa bruta total por sector residente (cuadro 23 de Cuentas Internacionales, MBP6). | moneda | millones | USD |
| Soc. No Financieras | `deuda_externa_sectores.csv` |  |  | Q | indec | Deuda externa bruta total por sector residente (cuadro 23 de Cuentas Internacionales, MBP6). | moneda | millones | USD |
| Inversión Directa (crédito entre empresas) | `deuda_externa_sectores.csv` |  |  | Q | indec | Deuda externa bruta total por sector residente (cuadro 23 de Cuentas Internacionales, MBP6). | moneda | millones | USD |
| Corto Plazo | `dextp_corto_kalman.csv` |  |  | M | propia |  | moneda | millones | USD |
| Corto Plazo | `deuda_externa_plazo.csv` |  |  | Q | indec | Deuda externa bruta por plazo contractual original (corto y largo plazo), Cuentas Internacionales MBP6. | moneda | millones | USD |
| Largo Plazo | `dextp_largo_kalman.csv` |  |  | M | propia |  | moneda | millones | USD |
| Largo Plazo | `deuda_externa_plazo.csv` |  |  | Q | indec | Deuda externa bruta por plazo contractual original (corto y largo plazo), Cuentas Internacionales MBP6. | moneda | millones | USD |
| Inversión Directa | `dextp_invdir_kalman.csv` |  |  | M | propia |  | moneda | millones | USD |
| Inversión Directa | `deuda_externa_plazo.csv` |  |  | Q | indec | Deuda externa bruta por plazo contractual original (corto y largo plazo), Cuentas Internacionales MBP6. | moneda | millones | USD |
| Vencimientos próx. 12m — Total | `deuda_externa_calendario_serie.csv` |  |  | Q | finanzas | Calendario de vencimientos de deuda externa, construido desde las planillas SIGADE. | moneda | millones | USD |
| Vencimientos próx. 24m — Total | `deuda_externa_calendario_serie.csv` |  |  | Q | finanzas | Calendario de vencimientos de deuda externa, construido desde las planillas SIGADE. | moneda | millones | USD |
| Vencimientos próx. 12m — Gobierno | `deuda_externa_calendario_serie.csv` |  |  | Q | finanzas | Calendario de vencimientos de deuda externa, construido desde las planillas SIGADE. | moneda | millones | USD |
| Vencimientos próx. 24m — Gobierno | `deuda_externa_calendario_serie.csv` |  |  | Q | finanzas | Calendario de vencimientos de deuda externa, construido desde las planillas SIGADE. | moneda | millones | USD |
| Market Turbulence Index (MTI) | `MTI.csv` |  |  | M | propia | Market Turbulence Index: índice sintético de turbulencia de mercado. | indice | unidad |  |
| VIX — CBOE Volatility Index | `vix.csv` |  |  | D | yahoo | Índice de volatilidad implícita del S&P 500 (CBOE VIX). | indice | unidad |  |
| DXY — US Dollar Index | `dxy.csv` |  |  | D | yahoo | Índice del dólar estadounidense contra una canasta de seis monedas (ICE DXY). | indice | unidad |  |
| US Treasury 2Y | `ust2y.csv` |  |  | D | yahoo | Rendimiento del bono del Tesoro de EE.UU. a 2 años. | porcentaje | unidad |  |
| US Treasury 5Y | `ust5y.csv` |  |  | D | yahoo | Rendimiento del bono del Tesoro de EE.UU. a 5 años. | porcentaje | unidad |  |
| US Treasury 10Y | `ust10y.csv` |  |  | D | yahoo | Rendimiento del bono del Tesoro de EE.UU. a 10 años. | porcentaje | unidad |  |
| US Treasury 30Y | `ust30y.csv` |  |  | D | yahoo | Rendimiento del bono del Tesoro de EE.UU. a 30 años. | porcentaje | unidad |  |
| OFR FSI — Total | `ofr_fsi.csv` |  |  | D | ofr | OFR Financial Stress Index: índice diario de estrés financiero global construido con 33 variables de mercado. | indice | unidad |  |
|   ↳ Crédito | `ofr_fsi.csv` |  |  | D | ofr | OFR Financial Stress Index: índice diario de estrés financiero global construido con 33 variables de mercado. | indice | unidad |  |
|   ↳ Acciones (valuación) | `ofr_fsi.csv` |  |  | D | ofr | OFR Financial Stress Index: índice diario de estrés financiero global construido con 33 variables de mercado. | indice | unidad |  |
|   ↳ Activos Seguros | `ofr_fsi.csv` |  |  | D | ofr | OFR Financial Stress Index: índice diario de estrés financiero global construido con 33 variables de mercado. | indice | unidad |  |
|   ↳ Financiamiento | `ofr_fsi.csv` |  |  | D | ofr | OFR Financial Stress Index: índice diario de estrés financiero global construido con 33 variables de mercado. | indice | unidad |  |
|   ↳ Volatilidad | `ofr_fsi.csv` |  |  | D | ofr | OFR Financial Stress Index: índice diario de estrés financiero global construido con 33 variables de mercado. | indice | unidad |  |
|   ↳ Componente EEUU | `ofr_fsi.csv` |  |  | D | ofr | OFR Financial Stress Index: índice diario de estrés financiero global construido con 33 variables de mercado. | indice | unidad |  |
|   ↳ Otras Ec. Avanzadas | `ofr_fsi.csv` |  |  | D | ofr | OFR Financial Stress Index: índice diario de estrés financiero global construido con 33 variables de mercado. | indice | unidad |  |
|   ↳ Mercados Emergentes | `ofr_fsi.csv` |  |  | D | ofr | OFR Financial Stress Index: índice diario de estrés financiero global construido con 33 variables de mercado. | indice | unidad |  |
| Estabilidad Política (WGI, percentil) — proxy ICRG/EIU | `wgi_political_stability_arg.csv` |  |  | A | banco_mundial | Worldwide Governance Indicators — Estabilidad política y ausencia de violencia, puntaje de Argentina. | score | unidad |  |
| Government Integrity — Bongiorni | `heritage_mensual_arg.csv` |  |  | M | heritage | Índice de Libertad Económica de Argentina (Heritage Foundation), anual interpolado a frecuencia mensual. | score | unidad |  |
| Índice General de Libertad Económica | `heritage_mensual_arg.csv` |  |  | M | heritage | Índice de Libertad Económica de Argentina (Heritage Foundation), anual interpolado a frecuencia mensual. | score | unidad |  |
| Property Rights | `heritage_mensual_arg.csv` |  |  | M | heritage | Índice de Libertad Económica de Argentina (Heritage Foundation), anual interpolado a frecuencia mensual. | score | unidad |  |
| Judicial Effectiveness | `heritage_mensual_arg.csv` |  |  | M | heritage | Índice de Libertad Económica de Argentina (Heritage Foundation), anual interpolado a frecuencia mensual. | score | unidad |  |
| Tax Burden | `heritage_mensual_arg.csv` |  |  | M | heritage | Índice de Libertad Económica de Argentina (Heritage Foundation), anual interpolado a frecuencia mensual. | score | unidad |  |
| Government Spending | `heritage_mensual_arg.csv` |  |  | M | heritage | Índice de Libertad Económica de Argentina (Heritage Foundation), anual interpolado a frecuencia mensual. | score | unidad |  |
| Fiscal Health | `heritage_mensual_arg.csv` |  |  | M | heritage | Índice de Libertad Económica de Argentina (Heritage Foundation), anual interpolado a frecuencia mensual. | score | unidad |  |
| Business Freedom | `heritage_mensual_arg.csv` |  |  | M | heritage | Índice de Libertad Económica de Argentina (Heritage Foundation), anual interpolado a frecuencia mensual. | score | unidad |  |
| Labor Freedom | `heritage_mensual_arg.csv` |  |  | M | heritage | Índice de Libertad Económica de Argentina (Heritage Foundation), anual interpolado a frecuencia mensual. | score | unidad |  |
| Monetary Freedom | `heritage_mensual_arg.csv` |  |  | M | heritage | Índice de Libertad Económica de Argentina (Heritage Foundation), anual interpolado a frecuencia mensual. | score | unidad |  |
| Trade Freedom | `heritage_mensual_arg.csv` |  |  | M | heritage | Índice de Libertad Económica de Argentina (Heritage Foundation), anual interpolado a frecuencia mensual. | score | unidad |  |
| Investment Freedom | `heritage_mensual_arg.csv` |  |  | M | heritage | Índice de Libertad Económica de Argentina (Heritage Foundation), anual interpolado a frecuencia mensual. | score | unidad |  |
| Financial Freedom | `heritage_mensual_arg.csv` |  |  | M | heritage | Índice de Libertad Económica de Argentina (Heritage Foundation), anual interpolado a frecuencia mensual. | score | unidad |  |
| REM: inflación mensual esperada | `rem_expectativas.csv` |  |  | M | bcra | Relevamiento de Expectativas de Mercado (REM): pronósticos macroeconómicos de analistas relevados por el BCRA. | tasa | unidad |  |
| REM: crecimiento PBI esperado | `rem_expectativas.csv` |  |  | M | bcra | Relevamiento de Expectativas de Mercado (REM): pronósticos macroeconómicos de analistas relevados por el BCRA. | tasa | unidad |  |
| EI: expectativas inflación (mediana) | `utdt_ei.csv` |  |  | M | utdt | Expectativas de Inflación a 12 meses (UTDT/CIF). | porcentaje | unidad |  |
| EI: expectativas inflación (promedio) | `utdt_ei.csv` |  |  | M | utdt | Expectativas de Inflación a 12 meses (UTDT/CIF). | porcentaje | unidad |  |
| ICC — Nacional | `ICC.csv` |  |  | M | utdt | Índice de Confianza del Consumidor (UTDT/CIF), relevamiento mensual de hogares. | indice | unidad |  |
| ICC — Capital | `ICC.csv` |  |  | M | utdt | Índice de Confianza del Consumidor (UTDT/CIF), relevamiento mensual de hogares. | indice | unidad |  |
| ICC — Gran Buenos Aires | `ICC.csv` |  |  | M | utdt | Índice de Confianza del Consumidor (UTDT/CIF), relevamiento mensual de hogares. | indice | unidad |  |
| ICC — Interior | `ICC.csv` |  |  | M | utdt | Índice de Confianza del Consumidor (UTDT/CIF), relevamiento mensual de hogares. | indice | unidad |  |
| Situación Personal | `ICC.csv` |  |  | M | utdt | Índice de Confianza del Consumidor (UTDT/CIF), relevamiento mensual de hogares. | indice | unidad |  |
| Situación Macroeconómica | `ICC.csv` |  |  | M | utdt | Índice de Confianza del Consumidor (UTDT/CIF), relevamiento mensual de hogares. | indice | unidad |  |
| Bienes Durables e Inmuebles | `ICC.csv` |  |  | M | utdt | Índice de Confianza del Consumidor (UTDT/CIF), relevamiento mensual de hogares. | indice | unidad |  |
| Expectativas a corto plazo | `ICC.csv` |  |  | M | utdt | Índice de Confianza del Consumidor (UTDT/CIF), relevamiento mensual de hogares. | indice | unidad |  |
| Expectativas a mediano plazo | `ICC.csv` |  |  | M | utdt | Índice de Confianza del Consumidor (UTDT/CIF), relevamiento mensual de hogares. | indice | unidad |  |
| ICG — Nivel General (UTDT) | `ICG_utdt.csv` |  |  | M | utdt | Índice de Confianza en el Gobierno (UTDT/CIF), relevamiento mensual. | score | unidad |  |
| ICG — Variación mensual | `ICG_utdt.csv` |  |  | M | utdt | Índice de Confianza en el Gobierno (UTDT/CIF), relevamiento mensual. | tasa | unidad |  |
| Orientación de Gobierno (±1) | `sentimiento_ciclo_politico.csv` |  |  | M | propia | Índices de confianza ajustados por el ciclo político: recogen cuánto de la variación de la confianza se explic… | score | unidad |  |
| ICG transformado  D·(ICG−2,0) | `sentimiento_ciclo_politico.csv` |  |  | M | propia | Índices de confianza ajustados por el ciclo político: recogen cuánto de la variación de la confianza se explic… | indice | unidad |  |
| ICC transformado  D·(ICC−45) | `sentimiento_ciclo_politico.csv` |  |  | M | propia | Índices de confianza ajustados por el ciclo político: recogen cuánto de la variación de la confianza se explic… | indice | unidad |  |
| Dummy_elecciones | `dummy_elec.csv` |  |  | D | propia | Variable binaria que marca un régimen o un evento estructural. | binaria | unidad |  |
| Dummy_cepo | `dummy_cepo.csv` |  |  | D | propia | Variable binaria que marca un régimen o un evento estructural. | binaria | unidad |  |
| Dummy_covid | `dummy_covid.csv` |  |  | M | propia | Variable binaria que marca un régimen o un evento estructural. | binaria | unidad |  |
| Dummy_Menem | `dummy_gob.csv` |  |  | D | propia | Variable binaria que marca un régimen o un evento estructural. | binaria | unidad |  |
| Dummy_De_la_Rua | `dummy_gob.csv` |  |  | D | propia | Variable binaria que marca un régimen o un evento estructural. | binaria | unidad |  |
| Dummy_Transicion_2001 | `dummy_gob.csv` |  |  | D | propia | Variable binaria que marca un régimen o un evento estructural. | binaria | unidad |  |
| Dummy_Duhalde | `dummy_gob.csv` |  |  | D | propia | Variable binaria que marca un régimen o un evento estructural. | binaria | unidad |  |
| Dummy_Nestor_Kirchner | `dummy_gob.csv` |  |  | D | propia | Variable binaria que marca un régimen o un evento estructural. | binaria | unidad |  |
| Dummy_Cristina_Kirchner | `dummy_gob.csv` |  |  | D | propia | Variable binaria que marca un régimen o un evento estructural. | binaria | unidad |  |
| Dummy_Macri | `dummy_gob.csv` |  |  | D | propia | Variable binaria que marca un régimen o un evento estructural. | binaria | unidad |  |
| Dummy_Alberto_Fernandez | `dummy_gob.csv` |  |  | D | propia | Variable binaria que marca un régimen o un evento estructural. | binaria | unidad |  |
| Dummy_Milei | `dummy_gob.csv` |  |  | D | propia | Variable binaria que marca un régimen o un evento estructural. | binaria | unidad |  |
| Dummy_Gobiernos | `dummy_gob.csv` |  |  | D | propia | Variable binaria que marca un régimen o un evento estructural. | categorica | unidad |  |

## Archivos no encontrados

- `Resultado fiscal-unificado.xlsx`
- `brecha_cambiaria.csv`
- `defaults_history.csv`
- `pbi_trimestral_usd_mep.csv`
- `riesgo_pais_arg.csv`
- `ti_mensual.csv`
- `years_since_default.csv`
