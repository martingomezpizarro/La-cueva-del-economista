"""construir_presidencias.py — arma la tabla de presidencias argentinas desde 1880.

Genera `data/historia/presidencias.csv`: una fila por presidencia, con cómo llegó, cómo
se fue, qué fuerza política y de dónde sale el dato.

CÓMO LEER ESTA TABLA. Los datos de abajo están transcritos a partir del listado oficial
de la Casa Rosada y de la historiografía estándar, pero **ninguna fila está verificada
todavía**: todas salen con `verificado = no`. La verificación es a mano, contra la fuente
oficial, y es lo que convierte esta tabla en algo citable. La columna `nota` marca los
casos donde la fecha o la inclusión están genuinamente discutidas.

POR QUÉ SE TRANSCRIBE Y NO SE BAJA. Probamos la extracción automática desde una fuente
enciclopédica: devolvió 47 presidencias prolijas con tres errores comprobables —faltaba
Milei, faltaban los dos presidentes interinos de la crisis de diciembre de 2001, y las
fechas de traspaso entre juntas militares no coincidían con la asunción efectiva—.
Para una plataforma que quiere ser citable, eso no sirve.

CRITERIO DE INCLUSIÓN. Entran TODOS los que ejercieron el Poder Ejecutivo Nacional,
por breve que haya sido el período: constitucionales, de facto, provisionales e interinos.
Excluir a los interinos es cómodo y falso: los días de Puerta y Camaño en diciembre de
2001 son justamente los que cualquier trabajo sobre riesgo país necesita fechados.

Uso:
    python scripts/construir_presidencias.py
"""

from __future__ import annotations

import csv
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "data" / "historia" / "presidencias.csv"

CAMPOS = ["orden", "nombre", "desde", "hasta", "tipo", "fuerza_politica",
          "acceso", "salida", "fuente", "verificado", "nota"]

CR = "Casa Rosada — Galería de Presidentes"

# (nombre, desde, hasta, tipo, fuerza, acceso, salida, nota)
P: list[tuple] = [
    ("Julio Argentino Roca", "1880-10-12", "1886-10-12", "constitucional", "Partido Autonomista Nacional", "elección", "fin de mandato", ""),
    ("Miguel Juárez Celman", "1886-10-12", "1890-08-06", "constitucional", "Partido Autonomista Nacional", "elección", "renuncia", "Renuncia tras la Revolución del Parque, en plena crisis de 1890."),
    ("Carlos Pellegrini", "1890-08-06", "1892-10-12", "constitucional", "Partido Autonomista Nacional", "sucesión constitucional", "fin de mandato", "Vicepresidente en ejercicio. Gestiona la crisis Baring."),
    ("Luis Sáenz Peña", "1892-10-12", "1895-01-23", "constitucional", "Partido Autonomista Nacional", "elección", "renuncia", ""),
    ("José Evaristo Uriburu", "1895-01-23", "1898-10-12", "constitucional", "Partido Autonomista Nacional", "sucesión constitucional", "fin de mandato", ""),
    ("Julio Argentino Roca", "1898-10-12", "1904-10-12", "constitucional", "Partido Autonomista Nacional", "elección", "fin de mandato", "Segunda presidencia."),
    ("Manuel Quintana", "1904-10-12", "1906-03-12", "constitucional", "Partido Autonomista Nacional", "elección", "muerte", ""),
    ("José Figueroa Alcorta", "1906-03-12", "1910-10-12", "constitucional", "Partido Autonomista Nacional", "sucesión constitucional", "fin de mandato", ""),
    ("Roque Sáenz Peña", "1910-10-12", "1914-08-09", "constitucional", "Partido Autonomista Nacional", "elección", "muerte", "Ley Sáenz Peña (1912): sufragio secreto y obligatorio."),
    ("Victorino de la Plaza", "1914-08-09", "1916-10-12", "constitucional", "Partido Autonomista Nacional", "sucesión constitucional", "fin de mandato", ""),
    ("Hipólito Yrigoyen", "1916-10-12", "1922-10-12", "constitucional", "Unión Cívica Radical", "elección", "fin de mandato", "Primer presidente por voto secreto y obligatorio."),
    ("Marcelo Torcuato de Alvear", "1922-10-12", "1928-10-12", "constitucional", "Unión Cívica Radical", "elección", "fin de mandato", ""),
    ("Hipólito Yrigoyen", "1928-10-12", "1930-09-06", "constitucional", "Unión Cívica Radical", "elección", "golpe", "Segunda presidencia. Derrocado por el primer golpe del siglo XX."),
    ("José Félix Uriburu", "1930-09-06", "1932-02-20", "de_facto", "Fuerzas Armadas", "golpe", "entrega a gobierno electo", ""),
    ("Agustín Pedro Justo", "1932-02-20", "1938-02-20", "constitucional", "Concordancia (UCR Antipersonalista)", "elección", "fin de mandato", "Elección con proscripción del radicalismo yrigoyenista."),
    ("Roberto Marcelino Ortiz", "1938-02-20", "1942-06-27", "constitucional", "Concordancia (UCR Antipersonalista)", "elección", "renuncia", "DISCUTIDO: delegó el mando en Castillo el 1940-07-03 por enfermedad; renunció formalmente el 1942-06-27. Según qué fecha se tome, cambia el corte de la serie."),
    ("Ramón S. Castillo", "1942-06-27", "1943-06-04", "constitucional", "Partido Demócrata Nacional", "sucesión constitucional", "golpe", "DISCUTIDO: ejerce de hecho desde 1940-07-03 como vicepresidente en ejercicio."),
    ("Arturo Rawson", "1943-06-04", "1943-06-07", "de_facto", "Fuerzas Armadas", "golpe", "desplazado", "Tres días. Se omite en casi todos los listados."),
    ("Pedro Pablo Ramírez", "1943-06-07", "1944-03-09", "de_facto", "Fuerzas Armadas", "golpe", "desplazado", ""),
    ("Edelmiro Julián Farrell", "1944-03-09", "1946-06-04", "de_facto", "Fuerzas Armadas", "sucesión de facto", "entrega a gobierno electo", ""),
    ("Juan Domingo Perón", "1946-06-04", "1952-06-04", "constitucional", "Partido Laborista / Peronista", "elección", "fin de mandato", ""),
    ("Juan Domingo Perón", "1952-06-04", "1955-09-21", "constitucional", "Partido Peronista", "elección", "golpe", "Segunda presidencia. Derrocado por la Revolución Libertadora."),
    ("Eduardo Lonardi", "1955-09-23", "1955-11-13", "de_facto", "Fuerzas Armadas", "golpe", "desplazado", "Entre el 21 y el 23 de septiembre gobierna una junta militar."),
    ("Pedro Eugenio Aramburu", "1955-11-13", "1958-05-01", "de_facto", "Fuerzas Armadas", "golpe interno", "entrega a gobierno electo", ""),
    ("Arturo Frondizi", "1958-05-01", "1962-03-29", "constitucional", "Unión Cívica Radical Intransigente", "elección", "destitución", "Depuesto por las Fuerzas Armadas; el peronismo estaba proscripto."),
    ("José María Guido", "1962-03-29", "1963-10-12", "provisional", "Unión Cívica Radical Intransigente", "acefalía (Senado)", "entrega a gobierno electo", "Presidente provisional del Senado; asume por la ley de acefalía."),
    ("Arturo Umberto Illia", "1963-10-12", "1966-06-28", "constitucional", "Unión Cívica Radical del Pueblo", "elección", "golpe", ""),
    ("Juan Carlos Onganía", "1966-06-29", "1970-06-08", "de_facto", "Fuerzas Armadas", "golpe", "desplazado", "«Revolución Argentina»."),
    ("Roberto Marcelo Levingston", "1970-06-18", "1971-03-22", "de_facto", "Fuerzas Armadas", "designación de la Junta", "desplazado", "Del 8 al 18 de junio de 1970 gobierna la Junta de Comandantes."),
    ("Alejandro Agustín Lanusse", "1971-03-26", "1973-05-25", "de_facto", "Fuerzas Armadas", "golpe interno", "entrega a gobierno electo", ""),
    ("Héctor José Cámpora", "1973-05-25", "1973-07-13", "constitucional", "Partido Justicialista", "elección", "renuncia", ""),
    ("Raúl Alberto Lastiri", "1973-07-13", "1973-10-12", "interino", "Partido Justicialista", "acefalía (Diputados)", "entrega a gobierno electo", "Presidente de la Cámara de Diputados."),
    ("Juan Domingo Perón", "1973-10-12", "1974-07-01", "constitucional", "Partido Justicialista", "elección", "muerte", "Tercera presidencia."),
    ("María Estela Martínez de Perón", "1974-07-01", "1976-03-24", "constitucional", "Partido Justicialista", "sucesión constitucional", "golpe", ""),
    ("Jorge Rafael Videla", "1976-03-29", "1981-03-29", "de_facto", "Fuerzas Armadas", "golpe", "fin de mandato de facto", "Del 24 al 29 de marzo de 1976 gobierna la Junta Militar."),
    ("Roberto Eduardo Viola", "1981-03-29", "1981-12-11", "de_facto", "Fuerzas Armadas", "designación de la Junta", "desplazado", ""),
    ("Carlos Alberto Lacoste", "1981-12-11", "1981-12-22", "de_facto", "Fuerzas Armadas", "interinato", "desplazado", "Once días. Se omite en casi todos los listados."),
    ("Leopoldo Fortunato Galtieri", "1981-12-22", "1982-06-18", "de_facto", "Fuerzas Armadas", "designación de la Junta", "desplazado", "Guerra de Malvinas."),
    ("Alfredo Óscar Saint-Jean", "1982-06-18", "1982-07-01", "de_facto", "Fuerzas Armadas", "interinato", "desplazado", "Trece días. Se omite en casi todos los listados."),
    ("Reynaldo Benito Bignone", "1982-07-01", "1983-12-10", "de_facto", "Fuerzas Armadas", "designación de la Junta", "entrega a gobierno electo", ""),
    ("Raúl Ricardo Alfonsín", "1983-12-10", "1989-07-08", "constitucional", "Unión Cívica Radical", "elección", "renuncia anticipada", "Entrega el mando seis meses antes, en plena hiperinflación."),
    ("Carlos Saúl Menem", "1989-07-08", "1995-07-08", "constitucional", "Partido Justicialista", "elección", "fin de mandato", ""),
    ("Carlos Saúl Menem", "1995-07-08", "1999-12-10", "constitucional", "Partido Justicialista", "elección", "fin de mandato", "Segunda presidencia, ya bajo la Constitución de 1994."),
    ("Fernando de la Rúa", "1999-12-10", "2001-12-21", "constitucional", "Alianza (UCR-Frepaso)", "elección", "renuncia", ""),
    ("Ramón Puerta", "2001-12-21", "2001-12-23", "interino", "Partido Justicialista", "acefalía (Senado)", "renuncia", "Dos días. FALTA en la mayoría de los listados automáticos."),
    ("Adolfo Rodríguez Saá", "2001-12-23", "2001-12-30", "provisional", "Partido Justicialista", "Asamblea Legislativa", "renuncia", "Declara el default de la deuda soberana el 2001-12-23."),
    ("Eduardo Camaño", "2001-12-30", "2002-01-02", "interino", "Partido Justicialista", "acefalía (Diputados)", "entrega a designado", "Tres días. FALTA en la mayoría de los listados automáticos."),
    ("Eduardo Duhalde", "2002-01-02", "2003-05-25", "provisional", "Partido Justicialista", "Asamblea Legislativa", "entrega a gobierno electo", "Fin de la convertibilidad y pesificación."),
    ("Néstor Carlos Kirchner", "2003-05-25", "2007-12-10", "constitucional", "Frente para la Victoria (PJ)", "elección", "fin de mandato", ""),
    ("Cristina Fernández de Kirchner", "2007-12-10", "2011-12-10", "constitucional", "Frente para la Victoria (PJ)", "elección", "fin de mandato", ""),
    ("Cristina Fernández de Kirchner", "2011-12-10", "2015-12-09", "constitucional", "Frente para la Victoria (PJ)", "elección", "fin de mandato", "DISCUTIDO: el mandato termina el 2015-12-09 por resolución judicial, no el 10."),
    ("Federico Pinedo", "2015-12-09", "2015-12-10", "provisional", "Propuesta Republicana", "acefalía (Senado)", "entrega a gobierno electo", "Doce horas. Caso límite: se incluye porque el traspaso 2015 se cita en la literatura."),
    ("Mauricio Macri", "2015-12-10", "2019-12-10", "constitucional", "Cambiemos (PRO)", "elección", "fin de mandato", ""),
    ("Alberto Fernández", "2019-12-10", "2023-12-10", "constitucional", "Frente de Todos (PJ)", "elección", "fin de mandato", ""),
    ("Javier Milei", "2023-12-10", "", "constitucional", "La Libertad Avanza", "elección", "", "En ejercicio. `hasta` vacío = mandato abierto."),
]

# Las juntas militares que ejercieron el Ejecutivo entre dos presidencias. Sin ellas la
# línea de tiempo queda con cinco huecos y una fecha cualquiera de esos días no resuelve
# a nadie. Duraron de uno a diez días, pero en esos días se decidieron cosas.
JUNTAS: list[tuple] = [
    ("Junta Militar (Revolución Libertadora)", "1955-09-21", "1955-09-23", "junta_militar", "Fuerzas Armadas", "golpe", "designa presidente", "Entre la caída de Perón y la asunción de Lonardi."),
    ("Junta Revolucionaria", "1966-06-28", "1966-06-29", "junta_militar", "Fuerzas Armadas", "golpe", "designa presidente", "Entre la caída de Illia y la asunción de Onganía."),
    ("Junta de Comandantes en Jefe", "1970-06-08", "1970-06-18", "junta_militar", "Fuerzas Armadas", "golpe interno", "designa presidente", "Diez días entre Onganía y Levingston."),
    ("Junta de Comandantes en Jefe", "1971-03-22", "1971-03-26", "junta_militar", "Fuerzas Armadas", "golpe interno", "designa presidente", "Entre Levingston y Lanusse."),
    ("Junta Militar (Proceso de Reorganización Nacional)", "1976-03-24", "1976-03-29", "junta_militar", "Fuerzas Armadas", "golpe", "designa presidente", "Entre el golpe del 24 de marzo y la asunción de Videla."),
]


def main() -> None:
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    todas = sorted(P + JUNTAS, key=lambda r: r[1])
    with SALIDA.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CAMPOS)
        w.writeheader()
        for n, (nombre, desde, hasta, tipo, fuerza, acceso, salida, nota) in enumerate(todas, 1):
            w.writerow({
                "orden": n, "nombre": nombre, "desde": desde, "hasta": hasta,
                "tipo": tipo, "fuerza_politica": fuerza, "acceso": acceso,
                "salida": salida, "fuente": CR, "verificado": "no", "nota": nota,
            })
    print(f"{len(todas)} períodos ({len(P)} presidencias + {len(JUNTAS)} juntas) -> {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
