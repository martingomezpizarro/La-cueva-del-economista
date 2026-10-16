"""historia — la capa de datos del módulo Línea de Tiempo.

Lee `data/historia/` y nada más: es un módulo PURO (disco, no red) igual que
`cueva/datos/series.py`. Contrato completo en `docs/MODULO_LINEA_DE_TIEMPO.md`
Parte II; cómo se presenta cada dato, en `docs/PRESENTACION_DATOS_HISTORIA.md`.

Lo que ofrece:

    cargar_vocabulario()          valores permitidos (categorías, subtipos, niveles…)
    cargar_presidencias()         60 períodos 1880-hoy
    cargar_eventos()              índice de eventos (eventos.csv)
    cargar_ficha(evento_id)       frontmatter + cuerpo renderizado + cifras resueltas
    cargar_series()               catálogo cerrado de troncales (todavía vacío: fase T3)
    gobierno_en(fecha)            derivación del gobierno por fecha (§8.1: NO se guarda)
    referencias()                 registro de obras citables (RAG/referencias.bib)
    validar()                     lista de errores; la usan los tests y chequear_historia.py

Dos decisiones que se ven en el código:

* **El markdown de las fichas se renderiza acá, en el servidor**, a HTML saneado
  (§10.2): el frontend nunca interpreta texto libre. El renderizador es propio y
  deliberadamente chico — escapa TODO primero y después aplica un puñado de
  transformaciones sobre texto ya escapado.
* **El gobierno de un evento se deriva, no se guarda.** Guardarlo duplicaría el
  dato y se desincronizaría al corregir una fecha de traspaso.
"""

from __future__ import annotations

import csv
import html
import json
import re
from dataclasses import dataclass, field
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from cueva import config

RAIZ = config.ROOT
HISTORIA = RAIZ / "data" / "historia"
FICHAS = HISTORIA / "fichas"
BIB = RAIZ / "RAG" / "referencias.bib"

ID_RE = re.compile(r"^[a-z0-9-]+$")
CITA_RE = re.compile(r"\[@([a-zA-Z0-9\-_]+)((?:,\s*[^\]]*)?)\]")
CIFRA_RE = re.compile(r"\{\{c:([a-zA-Z0-9_-]+)\}\}")
BIB_ENTRADA_RE = re.compile(r"@(\w+)\s*\{\s*([^,\s]+)\s*,", re.MULTILINE)
BIB_CAMPO_RE = re.compile(r"(\w+)\s*=\s*\{(.*?)\}\s*[,\n]", re.DOTALL)


class HistoriaNoEncontrada(FileNotFoundError):
    """Falta un archivo de data/historia/."""


class EventoNoEncontrado(KeyError):
    """No hay un evento con ese id."""


# ─────────────────────────────────────────────────────────────── modelos

@dataclass(frozen=True)
class Periodo:
    """Una fila de las tablas de instituciones: un período con quién estaba a cargo."""

    orden: int
    nombre: str
    desde: date
    hasta: date | None
    tipo: str
    fuerza_politica: str = ""
    acceso: str = ""
    salida: str = ""
    fuente: str = ""
    verificado: bool = False
    nota: str = ""

    def contiene(self, f: date) -> bool:
        return self.desde <= f and (self.hasta is None or f < self.hasta)

    def to_dict(self) -> dict[str, Any]:
        return {
            "orden": self.orden,
            "nombre": self.nombre,
            "desde": self.desde.isoformat(),
            "hasta": self.hasta.isoformat() if self.hasta else None,
            "tipo": self.tipo,
            "fuerza_politica": self.fuerza_politica,
            "acceso": self.acceso,
            "salida": self.salida,
            "fuente": self.fuente,
            "verificado": self.verificado,
            "nota": self.nota,
        }


@dataclass(frozen=True)
class Evento:
    """Una fila de eventos.csv. Tenga o no ficha."""

    id: str
    titulo: str
    categoria: str
    subtipo: str
    nivel: str  # hito | episodio | regimen
    desde: date
    hasta: date | None
    precision: str  # dia | mes | anio
    resumen: str = ""
    refs: tuple[str, ...] = ()
    fuente: str = ""
    ficha: bool = False
    verificado: bool = False
    nota: str = ""

    @property
    def anio(self) -> int:
        return self.desde.year

    @property
    def anio_fin(self) -> int:
        return (self.hasta or self.desde).year

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "titulo": self.titulo,
            "categoria": self.categoria,
            "subtipo": self.subtipo,
            "nivel": self.nivel,
            "desde": self.desde.isoformat(),
            "hasta": self.hasta.isoformat() if self.hasta else None,
            "anio": self.anio,
            "anio_fin": self.anio_fin,
            "precision": self.precision,
            "resumen": self.resumen,
            "refs": list(self.refs),
            "fuente": self.fuente,
            "ficha": self.ficha,
            "verificado": self.verificado,
            "nota": self.nota,
        }


@dataclass
class Ficha:
    """Una ficha completa: frontmatter + cuerpo ya renderizado a HTML saneado."""

    id: str
    series: list[str] = field(default_factory=list)
    cifras: list[dict[str, Any]] = field(default_factory=list)
    fuentes_primarias: list[dict[str, Any]] = field(default_factory=list)
    medios: list[dict[str, Any]] = field(default_factory=list)
    relacionados: list[dict[str, Any]] = field(default_factory=list)
    redactor: str = ""
    revisado: str = ""
    verificado: bool = False
    secciones: list[dict[str, str]] = field(default_factory=list)
    bibliografia: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "series": self.series,
            "cifras": self.cifras,
            "fuentes_primarias": self.fuentes_primarias,
            "medios": self.medios,
            "relacionados": self.relacionados,
            "redactor": self.redactor,
            "revisado": self.revisado,
            "verificado": self.verificado,
            "secciones": self.secciones,
            "bibliografia": self.bibliografia,
        }


# ─────────────────────────────────────────────────────────────── utilidades

def _fecha(texto: str) -> date | None:
    texto = (texto or "").strip()
    if not texto:
        return None
    return date.fromisoformat(texto)


def _si_no(texto: str) -> bool:
    return (texto or "").strip().lower() in {"si", "sí", "true", "1"}


def _filas(ruta: Path) -> list[dict[str, str]]:
    if not ruta.exists():
        raise HistoriaNoEncontrada(f"falta {ruta.relative_to(RAIZ)}")
    with ruta.open(encoding="utf-8-sig", newline="") as fh:
        return [{(k or ""): (v or "") for k, v in fila.items()} for fila in csv.DictReader(fh)]


# ─────────────────────────────────────────────────────────────── vocabulario

@lru_cache(maxsize=1)
def cargar_vocabulario() -> dict[str, Any]:
    ruta = HISTORIA / "vocabulario.json"
    if not ruta.exists():
        raise HistoriaNoEncontrada("falta data/historia/vocabulario.json")
    return json.loads(ruta.read_text(encoding="utf-8"))


# ─────────────────────────────────────────────────────────────── instituciones

@lru_cache(maxsize=1)
def cargar_presidencias() -> list[Periodo]:
    out = []
    for f in _filas(HISTORIA / "presidencias.csv"):
        out.append(
            Periodo(
                orden=int(f["orden"]),
                nombre=f["nombre"].strip(),
                desde=_fecha(f["desde"]),
                hasta=_fecha(f["hasta"]),
                tipo=f["tipo"].strip(),
                fuerza_politica=f.get("fuerza_politica", "").strip(),
                acceso=f.get("acceso", "").strip(),
                salida=f.get("salida", "").strip(),
                fuente=f.get("fuente", "").strip(),
                verificado=_si_no(f.get("verificado", "")),
                nota=f.get("nota", "").strip(),
            )
        )
    return out


def _tabla_opcional(nombre: str, campos_extra: tuple[str, ...]) -> list[Periodo]:
    """Ministros y autoridades monetarias todavía no existen (fase T1).

    Devolver [] en vez de romper es deliberado: la pantalla tiene que abrir igual y
    mostrar la capa vacía, no fallar."""
    ruta = HISTORIA / nombre
    if not ruta.exists():
        return []
    out = []
    for f in _filas(ruta):
        out.append(
            Periodo(
                orden=int(f.get("orden") or 0),
                nombre=f.get("nombre", "").strip(),
                desde=_fecha(f["desde"]),
                hasta=_fecha(f.get("hasta", "")),
                tipo=" · ".join(f.get(c, "").strip() for c in campos_extra if f.get(c, "").strip()),
                fuente=f.get("fuente", "").strip(),
                verificado=_si_no(f.get("verificado", "")),
                nota=f.get("nota", "").strip(),
            )
        )
    return out


def cargar_ministros() -> list[Periodo]:
    return _tabla_opcional("ministros_economia.csv", ("cargo", "interino"))


def cargar_autoridades() -> list[Periodo]:
    return _tabla_opcional("autoridades_monetarias.csv", ("institucion", "cargo"))


def gobierno_en(fecha: date) -> Periodo | None:
    """El gobierno vigente en una fecha. §8.1: el evento NO guarda su gobierno."""
    for p in cargar_presidencias():
        if p.contiene(fecha):
            return p
    return None


# ─────────────────────────────────────────────────────────────── eventos

@lru_cache(maxsize=1)
def cargar_eventos() -> list[Evento]:
    out = []
    for f in _filas(HISTORIA / "eventos.csv"):
        refs = tuple(r.strip() for r in (f.get("refs") or "").split(";") if r.strip())
        out.append(
            Evento(
                id=f["id"].strip(),
                titulo=f["titulo"].strip(),
                categoria=f["categoria"].strip(),
                subtipo=f.get("subtipo", "").strip(),
                nivel=f["nivel"].strip(),
                desde=_fecha(f["desde"]),
                hasta=_fecha(f.get("hasta", "")),
                precision=f.get("precision", "anio").strip(),
                resumen=f.get("resumen", "").strip(),
                refs=refs,
                fuente=f.get("fuente", "").strip(),
                ficha=_si_no(f.get("ficha", "")),
                verificado=_si_no(f.get("verificado", "")),
                nota=f.get("nota", "").strip(),
            )
        )
    return sorted(out, key=lambda e: (e.desde, e.id))


def evento(evento_id: str) -> Evento:
    if not ID_RE.match(evento_id or ""):
        raise EventoNoEncontrado(evento_id)
    for e in cargar_eventos():
        if e.id == evento_id:
            return e
    raise EventoNoEncontrado(evento_id)


# ─────────────────────────────────────────────────────────────── series troncales (T3)

@lru_cache(maxsize=1)
def cargar_series() -> list[dict[str, Any]]:
    """Catálogo cerrado de series troncales. Hoy no existe: es la fase T3.

    Devuelve [] sin inventar nada. La pantalla pinta el área del gráfico como
    'sin series todavía' — cobertura honesta, §2.2."""
    ruta = HISTORIA / "series.json"
    if not ruta.exists():
        return []
    catalogo = json.loads(ruta.read_text(encoding="utf-8"))
    salida = []
    for s in catalogo.get("series", []):
        datos = []
        csv_serie = HISTORIA / "series" / f"{s['id']}.csv"
        if csv_serie.exists():
            for fila in _filas(csv_serie):
                datos.append([int(fila["anio"]), float(fila["valor"]), fila.get("tramo", "")])
        salida.append({**s, "datos": datos})
    return salida


def ids_de_series() -> set[str]:
    return {s["id"] for s in cargar_series()}


# ─────────────────────────────────────────────────────────────── bibliografía

@lru_cache(maxsize=1)
def referencias() -> dict[str, dict[str, str]]:
    """`RAG/referencias.bib` parseado a {clave: {campo: valor}}.

    Parser deliberadamente chico: el .bib es nuestro y tiene una forma regular.
    Si algún día se vuelve heterogéneo, esto se reemplaza por bibtexparser."""
    if not BIB.exists():
        return {}
    txt = BIB.read_text(encoding="utf-8")
    entradas: dict[str, dict[str, str]] = {}
    marcas = list(BIB_ENTRADA_RE.finditer(txt))
    for i, m in enumerate(marcas):
        fin = marcas[i + 1].start() if i + 1 < len(marcas) else len(txt)
        cuerpo = txt[m.end():fin]
        campos = {k.lower(): " ".join(v.split()) for k, v in BIB_CAMPO_RE.findall(cuerpo + "\n")}
        campos["tipo"] = m.group(1).lower()
        entradas[m.group(2)] = campos
    return entradas


def _formatear_referencia(clave: str) -> dict[str, Any]:
    """Una línea de bibliografía legible + si la cita es verificable contra el PDF."""
    e = referencias().get(clave)
    if not e:
        return {"clave": clave, "texto": clave, "verificable": False, "falta": True}
    partes = []
    if e.get("author"):
        partes.append(e["author"].replace(" and ", "; "))
    if e.get("year"):
        partes.append(f"({e['year']})")
    if e.get("title"):
        partes.append(f"{e['title']}.")
    if e.get("booktitle"):
        partes.append(f"En {e['booktitle']}.")
    if e.get("journal"):
        rev = e["journal"]
        if e.get("volume"):
            rev += f" {e['volume']}"
        partes.append(f"{rev}.")
    if e.get("publisher"):
        partes.append(f"{e['publisher']}.")
    if e.get("pages"):
        partes.append(f"pp. {e['pages']}.")
    return {
        "clave": clave,
        "texto": " ".join(partes).strip() or clave,
        "verificable": bool(e.get("file")),
        "url": e.get("url", ""),
        "falta": False,
    }


# ─────────────────────────────────────────────────────────────── markdown → HTML

def _inline(texto: str, cifras: dict[str, dict], usadas: set[str]) -> str:
    """Transformaciones en línea sobre texto YA ESCAPADO. Nada de HTML del autor."""
    t = html.escape(texto, quote=True)

    def _cifra(m: re.Match) -> str:
        nombre = m.group(1)
        c = cifras.get(nombre)
        if not c:
            return f'<span class="cifra-rota" title="cifra no declarada">{html.escape(m.group(0))}</span>'
        usadas.add(nombre)
        serie = html.escape(str(c.get("serie") or ""), quote=True)
        anio = html.escape(str(c.get("anio") or ""), quote=True)
        titulo = html.escape(f"{c.get('et', '')} · {c.get('fuente', '')}", quote=True)
        return (
            f'<button class="cifra" data-cifra="{html.escape(nombre, quote=True)}" '
            f'data-serie="{serie}" data-anio="{anio}" title="{titulo}">'
            f'{html.escape(str(c.get("v", "")))}</button>'
        )

    # {{c:x}} se resuelve ANTES que el resto: su contenido ya viene escapado del frontmatter
    t = CIFRA_RE.sub(_cifra, t)

    def _cita(m: re.Match) -> str:
        clave, resto = m.group(1), (m.group(2) or "").strip(" ,")
        ref = _formatear_referencia(clave)
        etiqueta = clave + (f", {resto}" if resto else "")
        clase = "cita" + ("" if ref["verificable"] else " cita-no-verificable")
        titulo = ref["texto"] + ("" if ref["verificable"] else " — cita no verificable (no tenemos el PDF)")
        return (
            f'<span class="{clase}" data-ref="{html.escape(clave, quote=True)}" '
            f'title="{html.escape(titulo, quote=True)}">[{html.escape(etiqueta)}]</span>'
        )

    t = CITA_RE.sub(_cita, t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t, flags=re.DOTALL)
    t = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<em>\1</em>", t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    return t


def _bloques(cuerpo: str) -> list[tuple[str, list[str]]]:
    """Parte el markdown en bloques (tipo, líneas). Tipos: h, li, quote, p."""
    bloques: list[tuple[str, list[str]]] = []
    buffer: list[str] = []
    tipo = ""

    def cerrar():
        nonlocal buffer, tipo
        if buffer:
            bloques.append((tipo, buffer))
        buffer, tipo = [], ""

    for linea in cuerpo.splitlines():
        cruda = linea.rstrip()
        desnuda = cruda.strip()
        if not desnuda:
            cerrar()
            continue
        if desnuda.startswith("#"):
            cerrar()
            bloques.append(("h", [desnuda.lstrip("#").strip()]))
        elif desnuda.startswith("> "):
            if tipo != "quote":
                cerrar()
                tipo = "quote"
            buffer.append(desnuda[2:].strip())
        elif desnuda.startswith("- "):
            if tipo != "li":
                cerrar()
                tipo = "li"
            buffer.append(desnuda[2:].strip())
        elif tipo == "li" and cruda.startswith(("  ", "\t")):
            buffer[-1] += " " + desnuda  # continuación de un ítem
        else:
            if tipo != "p":
                cerrar()
                tipo = "p"
            buffer.append(desnuda)
    cerrar()
    return bloques


def _render_quote(lineas: list[str], cifras, usadas) -> str:
    """Cita textual: las líneas que empiezan con — o -- son la atribución."""
    cuerpo = [ln for ln in lineas if not ln.startswith(("—", "--", "–"))]
    firma = [ln.lstrip("—-– ").strip() for ln in lineas if ln.startswith(("—", "--", "–"))]
    html_cuerpo = f"<p>{_inline(' '.join(cuerpo), cifras, usadas)}</p>" if cuerpo else ""
    html_firma = f"<cite>{_inline(' '.join(firma), cifras, usadas)}</cite>" if firma else ""
    return f'<blockquote class="quote">{html_cuerpo}{html_firma}</blockquote>'


def _render_item(item: str, cifras, usadas) -> str:
    """Un ítem de cronología: **1890-10-07** — texto → fecha a un lado, texto al otro."""
    m = re.match(r"^\*\*(.+?)\*\*\s*[—–-]\s*(.*)$", item, flags=re.DOTALL)
    if not m:
        return f"<li><span class=\"ct\">{_inline(item, cifras, usadas)}</span></li>"
    fecha_txt, texto = m.group(1).strip(), m.group(2).strip()
    partes = fecha_txt.split("-")
    anio = partes[0]
    resto = "-".join(partes[1:])
    cf = f'{html.escape(resto)}<br><span class="yy">{html.escape(anio)}</span>' if resto else f'<span class="yy">{html.escape(anio)}</span>'
    return f'<li><span class="cf">{cf}</span><span class="ct">{_inline(texto, cifras, usadas)}</span></li>'


def renderizar(cuerpo: str, cifras: dict[str, dict], usadas: set[str]) -> list[dict[str, str]]:
    """Markdown de ficha → lista de secciones {titulo, html}. HTML saneado por construcción."""
    secciones: list[dict[str, Any]] = []
    actual = {"titulo": "", "piezas": []}
    for tipo, lineas in _bloques(cuerpo):
        if tipo == "h":
            if actual["piezas"] or actual["titulo"]:
                secciones.append(actual)
            actual = {"titulo": lineas[0], "piezas": []}
        elif tipo == "p":
            actual["piezas"].append(f"<p>{_inline(' '.join(lineas), cifras, usadas)}</p>")
        elif tipo == "li":
            es_crono = all(re.match(r"^\*\*", ln) for ln in lineas)
            items = "".join(_render_item(ln, cifras, usadas) for ln in lineas)
            clase = "crono" if es_crono else "lista"
            actual["piezas"].append(f'<ul class="{clase}">{items}</ul>')
        elif tipo == "quote":
            actual["piezas"].append(_render_quote(lineas, cifras, usadas))
    if actual["piezas"] or actual["titulo"]:
        secciones.append(actual)
    return [{"titulo": s["titulo"], "html": "".join(s["piezas"])} for s in secciones]


# ─────────────────────────────────────────────────────────────── fichas

def ruta_ficha(evento_id: str) -> Path:
    if not ID_RE.match(evento_id or ""):
        raise EventoNoEncontrado(evento_id)  # ids validados ANTES de tocar el disco
    return FICHAS / f"{evento_id}.md"


def _partir_frontmatter(texto: str) -> tuple[dict[str, Any], str]:
    if not texto.startswith("---"):
        return {}, texto
    fin = texto.find("\n---", 3)
    if fin == -1:
        return {}, texto
    cabecera = texto[3:fin]
    cuerpo = texto[fin + 4:]
    return yaml.safe_load(cabecera) or {}, cuerpo


def cargar_ficha(evento_id: str) -> Ficha | None:
    """La ficha de un evento, o None si todavía no está redactada."""
    ruta = ruta_ficha(evento_id)
    if not ruta.exists():
        return None
    fm, cuerpo = _partir_frontmatter(ruta.read_text(encoding="utf-8"))

    cifras_lista = [c for c in (fm.get("cifras") or []) if isinstance(c, dict)]
    cifras = {str(c.get("id")): c for c in cifras_lista}
    usadas: set[str] = set()
    secciones = renderizar(cuerpo, cifras, usadas)

    # títulos de los eventos relacionados: el rail necesita el texto, no el id
    por_id = {e.id: e for e in cargar_eventos()}
    relacionados = []
    for rid in fm.get("relacionados") or []:
        e = por_id.get(str(rid))
        relacionados.append(
            {"id": str(rid), "titulo": e.titulo if e else str(rid), "anio": e.anio if e else None, "existe": bool(e)}
        )

    ev = por_id.get(evento_id)
    claves = list(ev.refs) if ev else []
    for s in secciones:  # las claves citadas en el cuerpo también entran a la bibliografía
        for m in re.finditer(r'data-ref="([^"]+)"', s["html"]):
            if m.group(1) not in claves:
                claves.append(m.group(1))

    troncales = ids_de_series()
    cifras_salida = []
    for c in cifras_lista:
        serie = c.get("serie")
        cifras_salida.append(
            {
                "id": str(c.get("id", "")),
                "v": str(c.get("v", "")),
                "et": str(c.get("et", "")),
                "serie": serie,
                # una serie declarada que todavía no existe no finge un vínculo (§5.3)
                "serie_disponible": bool(serie) and serie in troncales,
                "anio": c.get("anio"),
                "fuente": str(c.get("fuente", "")),
                "en_relato": str(c.get("id", "")) in usadas,
            }
        )

    return Ficha(
        id=evento_id,
        series=[str(s) for s in (fm.get("series") or [])],
        cifras=cifras_salida,
        fuentes_primarias=[dict(f) for f in (fm.get("fuentes_primarias") or []) if isinstance(f, dict)],
        medios=[dict(m) for m in (fm.get("medios") or []) if isinstance(m, dict)],
        relacionados=relacionados,
        redactor=str(fm.get("redactor") or ""),
        revisado=str(fm.get("revisado") or ""),
        verificado=bool(fm.get("verificado")),
        secciones=secciones,
        bibliografia=[_formatear_referencia(k) for k in claves],
    )


# ─────────────────────────────────────────────────────────────── payload de la API

def resumen_estado() -> dict[str, Any]:
    """Lo que la pantalla dice de sí misma en el encabezado. Números CALCULADOS."""
    ev = cargar_eventos()
    por_categoria: dict[str, int] = {}
    por_nivel: dict[str, int] = {}
    for e in ev:
        por_categoria[e.categoria] = por_categoria.get(e.categoria, 0) + 1
        por_nivel[e.nivel] = por_nivel.get(e.nivel, 0) + 1
    con_ficha = sum(1 for e in ev if e.ficha or ruta_ficha(e.id).exists())
    return {
        "eventos": len(ev),
        "eventos_por_categoria": por_categoria,
        "eventos_por_nivel": por_nivel,
        "eventos_con_ficha": con_ficha,
        "eventos_verificados": sum(1 for e in ev if e.verificado),
        "presidencias": len(cargar_presidencias()),
        "presidencias_verificadas": sum(1 for p in cargar_presidencias() if p.verificado),
        "ministros": len(cargar_ministros()),
        "autoridades": len(cargar_autoridades()),
        "series_troncales": len(cargar_series()),
        "referencias": len(referencias()),
        "referencias_con_pdf": sum(1 for r in referencias().values() if r.get("file")),
    }


def payload() -> dict[str, Any]:
    """Todo lo necesario al abrir /tiempo, en una sola respuesta (§10.1)."""
    ev = cargar_eventos()
    pres = cargar_presidencias()
    cubierto_hasta = max((e.anio_fin for e in ev), default=1880)
    fin = max(cubierto_hasta, date.today().year)
    return {
        "rango": {"desde": 1880, "hasta": fin, "eventos_hasta": cubierto_hasta},
        "presidencias": [p.to_dict() for p in pres],
        "ministros": [m.to_dict() for m in cargar_ministros()],
        "autoridades": [a.to_dict() for a in cargar_autoridades()],
        "eventos": [
            {**e.to_dict(), "gobierno": (g.nombre if (g := gobierno_en(e.desde)) else None)} for e in ev
        ],
        "series": cargar_series(),
        "vocabulario": cargar_vocabulario(),
        "estado": resumen_estado(),
    }


def payload_evento(evento_id: str) -> dict[str, Any]:
    e = evento(evento_id)
    g = gobierno_en(e.desde)
    f = cargar_ficha(evento_id)
    return {
        "evento": {**e.to_dict(), "gobierno": g.to_dict() if g else None},
        "ficha": f.to_dict() if f else None,
        "bibliografia_evento": [_formatear_referencia(k) for k in e.refs],
    }


# ─────────────────────────────────────────────────────────────── validación

def validar() -> list[str]:
    """Los datos se testean como código. Devuelve la lista de errores (vacía = todo bien)."""
    errores: list[str] = []
    try:
        vocab = cargar_vocabulario()
    except HistoriaNoEncontrada as exc:
        return [str(exc)]

    categorias = set(vocab.get("categorias", {}))
    subtipos = set(vocab.get("subtipos", []))
    niveles = set(vocab.get("niveles", []))
    precisiones = set(vocab.get("precision", []))
    tipos_gob = set(vocab.get("tipos_gobierno", []))
    claves = set(referencias())
    troncales = ids_de_series()

    for p in cargar_presidencias():
        if p.tipo not in tipos_gob:
            errores.append(f"presidencias: {p.nombre} tiene tipo '{p.tipo}' fuera del vocabulario")
        if p.hasta and p.hasta <= p.desde:
            errores.append(f"presidencias: {p.nombre} termina antes de empezar")
        if not p.fuente:
            errores.append(f"presidencias: {p.nombre} sin fuente")

    vistos: set[str] = set()
    eventos = cargar_eventos()
    for e in eventos:
        if not ID_RE.match(e.id):
            errores.append(f"eventos: id mal formado '{e.id}'")
        if e.id in vistos:
            errores.append(f"eventos: id duplicado '{e.id}'")
        vistos.add(e.id)
        if e.categoria not in categorias:
            errores.append(f"eventos[{e.id}]: categoría '{e.categoria}' fuera del vocabulario")
        if e.subtipo and e.subtipo not in subtipos:
            errores.append(f"eventos[{e.id}]: subtipo '{e.subtipo}' fuera del vocabulario")
        if e.nivel not in niveles:
            errores.append(f"eventos[{e.id}]: nivel '{e.nivel}' fuera del vocabulario")
        if e.precision not in precisiones:
            errores.append(f"eventos[{e.id}]: precisión '{e.precision}' fuera del vocabulario")
        if e.hasta and e.hasta < e.desde:
            errores.append(f"eventos[{e.id}]: termina antes de empezar")
        if not e.refs and not e.fuente:
            errores.append(f"eventos[{e.id}]: sin refs ni fuente — sin fuente no hay evento")
        for r in e.refs:
            if claves and r not in claves:
                errores.append(f"eventos[{e.id}]: refs '{r}' no está en referencias.bib")
        if e.ficha and not ruta_ficha(e.id).exists():
            errores.append(f"eventos[{e.id}]: ficha=si pero no existe fichas/{e.id}.md")

    ids = {e.id for e in eventos}
    for ruta in sorted(FICHAS.glob("*.md")):
        if ruta.stem.startswith("_"):
            continue
        if ruta.stem not in ids:
            errores.append(f"fichas/{ruta.name}: no tiene fila en eventos.csv")
            continue
        f = cargar_ficha(ruta.stem)
        if f is None:
            continue
        for c in f.cifras:
            if not c["fuente"]:
                errores.append(f"fichas/{ruta.name}: la cifra '{c['id']}' no declara fuente")
            if c["serie"] and troncales and not c["serie_disponible"]:
                errores.append(f"fichas/{ruta.name}: la cifra '{c['id']}' apunta a la serie '{c['serie']}' inexistente")
        for s in f.secciones:
            if 'class="cifra-rota"' in s["html"]:
                errores.append(f"fichas/{ruta.name}: hay un {{{{c:...}}}} que no está en `cifras`")
        for b in f.bibliografia:
            if b.get("falta") and claves:
                errores.append(f"fichas/{ruta.name}: cita [@{b['clave']}] no está en referencias.bib")
        for r in f.relacionados:
            if not r["existe"]:
                errores.append(f"fichas/{ruta.name}: relacionado '{r['id']}' no existe en eventos.csv")
        for m in f.medios:
            faltan = [c for c in ("credito", "licencia", "url_origen") if not m.get(c)]
            if faltan:
                errores.append(f"fichas/{ruta.name}: el medio '{m.get('archivo', '?')}' no declara {', '.join(faltan)}")

    return errores
