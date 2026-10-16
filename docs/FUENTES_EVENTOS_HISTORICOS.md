# Fuentes para la cronología argentina desde 1880

Investigación del 2026-08-27. Objetivo: poder cruzar cualquier serie de tiempo con **quién
gobernaba** y **qué estaba pasando** — economía, política y sociedad — desde 1880.

---

## 1. Qué hay hoy en La Cueva (y por qué no alcanza)

| Archivo | Qué tiene | Límite |
|---|---|---|
| `dummy_gob.csv` | Una columna 0/1 por presidente, de Menem a Milei | **Arranca en 1999.** Nueve gobiernos de los ~50 desde 1880 |
| `dummy_cepo.csv` | Control de cambios | Desde 1999; hubo cepos en 1931-1933, 1949, 1971-1976… |
| `dummy_elec.csv` | Año electoral | Desde 1999 |
| `defaults_history.csv` | Contador de defaults | Desde 1999; Argentina defaulteó en 1890, 1915, 1930, 1951, 1956, 1982, 1989, 2001, 2014, 2020 |
| `sentimiento_ciclo_politico.csv` | Orientación del gobierno | Desde 1998 |

**El problema no es solo la cobertura, es el diseño.** Una columna por presidente no escala:
de 1880 a hoy son unas cincuenta presidencias, y eso serían cincuenta columnas. Y ninguna
de las dummies actuales declara de dónde salen las fechas.

---

## 2. La advertencia: la extracción automática trae errores

Probé extraer la lista de presidentes de una fuente enciclopédica. Devolvió 47 presidencias
prolijas y verosímiles. Tiene por lo menos **tres errores comprobables**:

1. **Falta Javier Milei.** Da a Alberto Fernández como presidente «hasta presente», cuando
   asumió Milei el 10 de diciembre de 2023.
2. **Faltan dos presidentes de la crisis de 2001**: Ramón Puerta (21-22 de diciembre) y
   Eduardo Camaño (30 de diciembre al 1 de enero de 2002). Justo la semana que cualquier
   trabajo sobre riesgo país necesita fechada al día.
3. **Fechas de traspaso dudosas** en las juntas militares, donde la asunción efectiva y la
   formal no coinciden.

La conclusión no es «no usar esa fuente», sino: **la cronología se arma con fuente oficial
y control humano, serie por serie**, igual que las series económicas. Es exactamente el
mismo criterio de `proc` que ya rige el catálogo.

---

## 3. Fuentes evaluadas

### 3.1 Presidencias y régimen político

| Fuente | Qué da | Cobertura | Acceso | Veredicto |
|---|---|---|---|---|
| **Casa Rosada — Galería de Presidentes** | Listado oficial | 1826-hoy | Web, sin datos estructurados | **Fuente de autoridad** para nombres y fechas. Hay que transcribir a mano |
| **Polity5** | Puntaje de autocracia/democracia, anual | 1800-2018 | Descarga libre (QoG data finder) | Muy bueno para régimen; se corta en 2018 |
| **V-Dem** | Índices de democracia, anual, muchas dimensiones | 1789-hoy | Descarga libre, paquete de R | El más completo y actualizado |
| **Powell & Thyne — Coup d'état dataset** | Golpes exitosos y fallidos, con fecha exacta | 1950-hoy | Descarga libre | Cubre 1955, 1962, 1966, 1976; **no llega a 1930 ni 1943** |
| **Wikidata (SPARQL)** | Presidencias estructuradas | 1826-hoy | Bloqueado por la allowlist de esta sesión | Sirve desde tu terminal |

### 3.2 Crisis económicas

| Fuente | Qué da | Cobertura | Acceso |
|---|---|---|---|
| **Reinhart & Rogoff — Global Crises Data by Country** (Harvard Business School) | Crisis bancarias, cambiarias, de deuda externa y doméstica, inflacionarias, colapsos bursátiles, patrón oro, clasificación cambiaria | **1800-presente**, 70 países | Excel único: `hbs.edu/behavioral-finance-and-financial-stability/Documents/ChartData/MapCharts/20160923_global_crisis_data.xlsx` |
| **Ilzetzki, Reinhart & Rogoff (IRR)** | Clasificación **mensual** del régimen cambiario de facto | 1946-hoy | `ilzetzki.com/irr-data` y `carmenreinhart.com/exchange-rate/` |
| **Laeven & Valencia (FMI)** | Crisis bancarias sistémicas, con fechas de inicio y resolución | 1970-hoy | Working paper del FMI, con anexo de datos |

La base de HBS es la pieza más valiosa del conjunto: **cubre 1800 en adelante y ya trae
fechadas las crisis que a nosotros nos importan**. Es la que conviene bajar primero.

### 3.3 Series económicas largas

| Fuente | Qué da | Cobertura |
|---|---|---|
| **Ferreres — «Dos siglos de economía argentina»** (Fundación Norte y Sur) | La referencia canónica de series argentinas largas: PBI, precios, población, comercio, salarios | 1810-2010, sitio propio en `dossiglos.fundacionnorteysur.org.ar` |
| **MOxLAD** (Montevideo-Oxford) | Series comparables de América Latina | 1900-2010 aprox. |
| **Della Paolera & Taylor** | Historia monetaria y cambiaria argentina, con series | 1880-1935 (*Straining at the Anchor*) |
| **BCRA — API v4.0** | Ya conectada. Inflación mensual desde 1943, agregados monetarios desde 1940 | ver `docs/DATOS.md` §5 |

### 3.4 Política económica interna

Para planes de estabilización, ministros de economía y cambios de régimen no hay una base
descargable: hay que construirla desde la literatura. Las referencias que la fijan son
**Gerchunoff & Llach**, *El ciclo de la ilusión y el desencanto*, y **Della Paolera &
Taylor**, *A New Economic History of Argentina*. Se transcribe a mano y se cita.

---

## 4. Modelo de datos propuesto

Dos tablas, no cincuenta columnas de dummies. **Las dummies se generan** a partir de estas.

### `data/historia/presidencias.csv`

```
id, nombre, desde, hasta, tipo, fuerza_politica, acceso, salida, fuente, verificado
```

`tipo`: constitucional · de_facto · provisional · interino
`acceso`: elección · golpe · sucesión constitucional · asamblea legislativa
`salida`: fin de mandato · golpe · renuncia · muerte · destitución

### `data/historia/eventos.csv`

```
id, fecha_inicio, fecha_fin, ambito, tipo, titulo, descripcion, magnitud, fuente, verificado
```

`ambito`: económico · político · social · externo
`tipo`: default · crisis bancaria · crisis cambiaria · plan de estabilización ·
cambio de régimen cambiario · cepo · golpe · elección · conflicto externo · pandemia

Un evento puede ser **puntual** (`fecha_fin` vacío: un default, un golpe) o un **período**
(`fecha_fin` cargado: un cepo, un plan, una guerra).

### Por qué así

- **Escala**: agregar un presidente es una fila, no una columna nueva en todos los CSV.
- **Se cruza con cualquier serie**: dada una fecha, se resuelve quién gobernaba y qué
  eventos estaban activos, sin importar la frecuencia de la serie.
- **Las dummies se derivan**: `dummy_cepo`, `dummy_elec`, `dummy_gob` pasan a generarse
  con un script desde estas tablas, para el rango y la frecuencia que pida cada estudio.
  Hoy están congeladas en 1999-hoy y diarias.
- **Cada fila lleva `fuente` y `verificado`**, igual que el bloque `proc` de las series. Sin
  eso, una cronología es una opinión.

---

## 5. Qué quedó hecho (2026-08-27)

### Presidencias — HECHO, falta verificar

`data/historia/presidencias.csv` · `scripts/construir_presidencias.py`

**60 períodos, de 1880-10-12 a hoy: 55 presidencias + 5 juntas militares.** Las juntas
están porque sin ellas la línea de tiempo tiene cinco huecos —los traspasos de 1955, 1966,
1970, 1971 y 1976—, y una fecha de esos días no resolvía a nadie.

Verificación estructural, en `tests/test_historia.py`:

- **0 huecos y 0 solapamientos.** Cualquier fecha entre 1880 y hoy resuelve a exactamente
  un gobierno.
- Están los que los listados automáticos pierden: Rawson (3 días, 1943), Lacoste (11 días,
  1981), Saint-Jean (13 días, 1982), Puerta y Camaño (diciembre de 2001) y Pinedo (12 horas,
  2015).
- 33 constitucionales · 15 de facto · 5 juntas · 4 provisionales · 3 interinos.
- **14,8 % del período 1880-hoy transcurrió bajo gobierno de facto** (7.899 días de 53.279).

Todas las filas salen con `verificado = no` y una columna `nota` que marca los casos
genuinamente discutidos: la delegación de Ortiz en Castillo (1940 vs 1942) y el fin del
mandato de CFK (2015-12-09 vs 12-10). Eso es lo que tenés que controlar.

### Crisis desde 1800 — script listo, falta correrlo

`scripts/bajar_crisis_rr.py` baja el Excel de HBS, encuentra la hoja de Argentina y
convierte las banderas anuales en episodios con fecha de inicio y fin, ya en el esquema de
`eventos.csv`.

**No lo pude probar contra la fuente**: desde el sandbox de Cowork `hbs.edu` está bloqueado
por la allowlist de egress. Por eso trae `--inspeccionar`:

```bash
python scripts/bajar_crisis_rr.py --inspeccionar   # ver hojas y columnas reales
python scripts/bajar_crisis_rr.py                  # extraer Argentina
```

Si los nombres de hoja o columna no son los que espera, se ajusta el diccionario
`COLUMNAS` del script y listo.

## 6. Lo que sigue

1. **Controlar las 60 presidencias** contra Casa Rosada y pasar `verificado` a `sí`.
2. **Correr el script de HBS** desde tu terminal: da defaults y crisis desde 1800 fechados,
   sin transcribir nada.
3. **Régimen cambiario mensual** con IRR desde 1946.
4. **Eventos de política económica** desde la literatura — planes de estabilización,
   ministros, cepos. Es lo que más trabajo manual lleva y donde tu criterio decide.
5. **Generador de dummies** desde las dos tablas, que reemplace a los CSV congelados en
   1999. Criterio acordado: no se pisan los actuales hasta que el generador reproduzca
   exactamente sus valores en el tramo que comparten.
