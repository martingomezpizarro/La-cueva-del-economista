# -*- coding: utf-8 -*-
"""Agrega los seis eventos ancla de las fichas nuevas y marca ficha=si donde corresponde."""
import csv, pathlib, sys

P = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "data/historia/eventos.csv")
COLS = ["id","titulo","categoria","subtipo","nivel","desde","hasta","precision",
        "resumen","refs","fuente","ficha","verificado","nota"]

NUEVOS = [
("garantias-ferroviarias-1886","Fiebre de garantías ferroviarias","fiscal","norma","episodio",
 "1886-01-01","1889-12-31","anio",
 "Entre fines de 1886 y 1889 se otorgan 350 millones de pesos oro en garantías de rentabilidad a compañías ferroviarias —41,4 de ellos a líneas del Estado que se privatizan—. La garantía obliga al Tesoro a cubrir cada año la diferencia entre la ganancia pactada (5% a 7%) y la efectiva, por plazos de 20 a 55 años.",
 "llach-2007;gomez-2012-crecimiento;lewis-1983","","si","no",
 "La mayoría de esas líneas no se construyó nunca. Treinta de las treinta y dos trazas garantidas apuntaban al Interior. El costo se liquida en el arreglo de 1895-1898 (ver arreglo-garantias-ferroviarias-1895)."),

("venta-ferrocarriles-estado-1888","Privatización del Andino y el Central Norte","fiscal","norma","hito",
 "1888-01-01","","anio",
 "El Estado vende sus dos líneas principales a compañías privadas, con garantía de rentabilidad. El ministro del Interior Wilde le escribe a Roca que ambas le venían 'quemando las manos' y que la ganancia del 2% sólo podía presentarse subestimando fantásticamente el capital inicial.",
 "llach-2007;lopez-1994","Wilde a Roca, 15/1/1888, Archivo del Museo Roca, doc. 83.05","no","no",
 "El libro no da el día. Es el momento en que la política ferroviaria pasa de la obra pública directa al sistema de garantías."),

("ley-saenz-pena-1912","Ley Sáenz Peña","politico","reforma_electoral","hito",
 "1912-02-10","","dia",
 "Sufragio universal, secreto y obligatorio para todos los varones mayores de edad. El debate parlamentario muestra que los representantes del oficialismo estaban confiados en ganar con las nuevas reglas.",
 "resico-2010;gerchunoff-llach-2018","Ley 8871, sancionada el 10/2/1912","si","no",
 "Fecha y número contrastados con el Senado de la Provincia de Buenos Aires y el Museo Casa Rosada el 2026-09-13. El corpus del proyecto sólo dice 'en 1912'."),

("llegada-del-radicalismo-1916","Llegada del radicalismo al gobierno","politico","eleccion","hito",
 "1916-10-12","","dia",
 "Hipólito Yrigoyen asume la presidencia: la primera elección bajo la Ley Sáenz Peña la gana el partido opositor, no el que la sancionó. La fuerza electoral del radicalismo estuvo en los sectores urbanos y rurales intermedios.",
 "resico-2010;gomez-2018","presidencias.csv (Casa Rosada — Galería de Presidentes)","no","no",
 "La fecha es la de asunción, que sale de presidencias.csv. La elección fue en abril de 1916: falta una fuente del proyecto que la feche al día."),

("gran-guerra-1914","Primera Guerra Mundial","internacional","guerra","episodio",
 "1914-08-01","1918-11-01","mes",
 "El conflicto corta el flujo de capitales y el comercio. En 1914 la cuenta capital cae 47,7%, las importaciones 34,7% y las exportaciones 22,0%, y la balanza de pagos se vuelve negativa en 12,6 millones de dólares. Entre 1915 y 1918 el saldo vuelve a ser positivo por efecto precio.",
 "gomez-2018;ford-1966;quinteroramos-1970","","si","no",
 "Las fechas exactas del conflicto (28/7/1914 y 11/11/1918) son las convencionales y no salen de la bibliografía del proyecto: por eso precision=mes. La caída de las exportaciones de 1914 no fue por la guerra sino por el fracaso de la cosecha 1913-14 (el trigo cayó 44% y el maíz 34%)."),

("boom-posguerra-1919","Boom inflacionario de posguerra y recesión de 1920-21","internacional","shock_externo","episodio",
 "1919-01-01","1921-12-31","anio",
 "La demanda reprimida durante la guerra se libera y la oferta no responde: aumento generalizado de precios, agravado por políticas fiscales y monetarias expansivas. La Reserva Federal sube la tasa de descuento ante la salida de reservas y Francia y Gran Bretaña la siguen; la recesión llega a Europa. En el medio, las hiperinflaciones europeas, la alemana de 1923 entre ellas.",
 "gomez-2018;barbero-etal-2007;cortesconde-2003","","no","no",
 "Es el único episodio inflacionario de origen externo del tramo 1880-1935: todos los demás shocks del mundo llegaron a la Argentina como deflación."),
]

CON_FICHA = {"bancos-garantidos-1887", "crack-1929", "control-cambios-1931"}

rows = list(csv.DictReader(P.open(encoding="utf-8")))
ids = {r["id"] for r in rows}
for n in NUEVOS:
    if n[0] in ids:
        print(f"ya existe, se saltea: {n[0]}"); continue
    rows.append(dict(zip(COLS, n)))
for r in rows:
    if r["id"] in CON_FICHA:
        r["ficha"] = "si"

rows.sort(key=lambda r: (r["desde"], r["id"]))
with P.open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=COLS, lineterminator="\n")
    w.writeheader(); w.writerows(rows)
print(f"{len(rows)} eventos · {sum(1 for r in rows if r['ficha']=='si')} con ficha")
