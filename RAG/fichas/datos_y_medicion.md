---
metodo: Datos y medición (calidad, procedencia, reproducibilidad)
tema: 00_datos
fuentes: ["Croushore-Stark (2001)", "FAIR Principles (Wilkinson 2016)", "SDMX", "AEA Data Policy", "Gentzkow-Shapiro (2014)"]
---

# Datos y medición

## ¿Qué es / para qué sirve?
La base de todo: garantizar que cada serie sea **trazable, reproducible y veraz** antes de que
alguien la modele. Sin esto, los mejores modelos producen conclusiones falsas.

## La ficha mínima obligatoria de una serie
1. nombre + descripción (qué mide exactamente)
2. fuente primaria (organismo + dataset) — **no** un agregador/blog
3. enlace (URL/DOI)
4. fecha de extracción (el **vintage**)
5. frecuencia y cobertura (desde–hasta)
6. unidad (y si es nominal/real → año base; y SA/NSA)
7. método de construcción / empalmes / transformaciones (si no es cruda)
8. licencia / términos de uso

## Supuestos / buenas prácticas
- **Trazabilidad a fuente primaria** y reproducibilidad (espíritu de la AEA Data Policy: datos + método).
- **Vintages:** las series macro se revisan; registrar *cuándo* se bajó (Croushore-Stark).
- Estándares de metadatos: **FAIR** y **SDMX** (el que usan BCRA/INDEC/FMI).

## Cuándo NO confiar / límites
- Series empalmadas sin documentar el método de empalme.
- Cambios de metodología o de base no señalados.
- Datos de períodos con problemas de medición conocidos.

## ⚠️ Errores típicos (lo que el agente debe advertir)
- **Mezclar vintages** (datos revisados con datos en tiempo real) sin avisar.
- Empalmar series de **distinta definición o base** como si fueran una.
- 🇦🇷 No marcar el **período de intervención del INDEC (2007-2015)** en IPC/PBI (bandera de veracidad).
- Tomar un agregador secundario como si fuera la fuente primaria.
- Ignorar diferencias SA vs NSA o nominal vs real.

## Cómo se interpreta el resultado
Una serie "aprobada" tiene los 8 campos completos y rastrea a su fuente. Solo entonces puede
**graduar al catálogo compartido** vía curación. Para bibliografía, además: solo pasa al canon si
es legalmente compartible (acceso abierto / dominio público).
