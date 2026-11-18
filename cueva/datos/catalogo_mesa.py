"""catalogo_mesa — el catálogo de la Mesa de investigación, en el formato del mockup «La Cueva».

La Mesa (web/mesa/, portada de docs/mockup/la-cueva.plantilla.html) trabaja en el navegador
con un objeto `CAT`:

    {
      "calendarios": {"diaria": [fechas], "mensual": [...], "trimestral": [...], "anual": [...]},
      "series": {id: {nombre, corto, freq, unidad, fuente, familia, grupo, subgrupo, url?, i0, y}},
      "arbol": [[familia, grupo, subgrupo, nombre, freq, unidad, id, estado, fuente], ...],
      "generado": "AAAA-MM-DD",
    }

`y` son los valores alineados al calendario de su frecuencia desde la posición `i0`
(null donde no hay dato). `estado` es «datos» (se puede traer), «falta» (está en el catálogo
pero no hay archivo) o «terminal» (existe en la Terminal pero no viene precargada).

Reglas de ids (las del mockup, para que sus proyectos y ejemplos sigan andando):
- Serie de La Cueva con una sola frecuencia: su id del catálogo.
- Con varias frecuencias: id + sufijo `_d`, `_m`, `_q` o `_a`.
- Series de la Terminal: las da `terminal.puente.series_mesa()` (ticker, `vix`, `KO_ingresos_T`…).

Qué NO hace: no toca la red ni la base de la Terminal; las series de la Terminal le llegan
ya leídas (las pasa la capa de API).
"""

from __future__ import annotations

import datetime as dt
import logging
from pathlib import Path

from cueva import config
from cueva.datos import series as S

log = logging.getLogger(__name__)

FRECUENCIAS = {"D": "diaria", "W": "semanal", "M": "mensual", "Q": "trimestral", "A": "anual"}
SUFIJO = {"D": "_d", "W": "_w", "M": "_m", "Q": "_q", "A": "_a"}
ORDEN = ("diaria", "semanal", "mensual", "trimestral", "anual")

# Series de la Terminal que la Mesa trae precargadas (las del mockup); el resto del universo
# aparece en el catálogo como «terminal».
TERMINAL_PRECARGADAS = (
    "vix",
    "ust2y",
    "ust10y",
    "ust_10_2",
    "spread_hy",
    "dolar_amplio",
    "ccl",
    "brecha_ccl",
    "SPY",
    "QQQ",
    "IWM",
    "IVE",
    "IVW",
    "SPHQ",
    "RSP",
    "XLE",
    "XLK",
    "XLF",
    "XLV",
    "XLP",
    "XLU",
    "XLY",
    "XLI",
    "XLB",
    "GLD",
    "SLV",
    "GDX",
    "EEM",
    "EWZ",
    "HYG",
    "LQD",
    "KO",
    "PEP",
    "XOM",
    "CVX",
    "AAPL",
    "MSFT",
    "NVDA",
    "MELI",
    "VIST",
    "GGAL",
    "YPFD",
    "PAMP",
    "BMA",
    *(
        f"{t}_{v}_T"
        for t in ("KO", "PEP", "XOM", "CVX", "AAPL", "MSFT", "NVDA", "MELI")
        for v in ("ingresos", "resultado_neto", "flujo_operativo")
    ),
)


def _partes(info_grupo: str, info_subgrupo: str) -> tuple[str, str, str]:
    """(familia, grupo, subgrupo) desde los campos de SerieInfo («grupo › subgrupo»)."""
    trozos = [t.strip() for t in (info_subgrupo or "").split("›")]
    return info_grupo or "", trozos[0] if trozos else "", " › ".join(trozos[1:])


def _freq_detectada(fechas) -> str:
    if len(fechas) < 3:
        return "mensual"
    dias = sorted((fechas[i] - fechas[i - 1]).days for i in range(1, min(len(fechas), 80)))
    m = dias[len(dias) // 2]
    return (
        "diaria"
        if m <= 4
        else "semanal"
        if m <= 10
        else "mensual"
        if m <= 45
        else "trimestral"
        if m <= 120
        else "anual"
    )


def _relativa(ruta: str) -> str:
    try:
        return Path(ruta).resolve().relative_to(config.carpeta_series().resolve()).as_posix()
    except (ValueError, OSError):
        return Path(ruta).name


def series_cueva() -> list[dict]:
    """Las series de La Cueva con datos: una entrada por (serie, frecuencia), con sus puntos."""
    salida = []
    for sid, info in S.catalogo().items():
        fuentes = info.fuentes or [{"freq": "", "path": info.archivo}]
        varias = len(fuentes) > 1
        familia, grupo, subgrupo = _partes(info.grupo, info.subgrupo)
        for f in fuentes:
            codigo = (f.get("freq") or "").upper()[:1]
            try:
                s = S.cargar(sid, codigo or None)
            except Exception as e:  # una serie rota no tumba el catálogo
                log.warning("mesa: no se pudo leer %s (%s): %s", sid, codigo, e)
                continue
            if s.empty:
                continue
            fechas = [d.date() for d in s.index]
            freq = FRECUENCIAS.get(codigo) or _freq_detectada(fechas)
            salida.append(
                {
                    "id": sid + SUFIJO.get(codigo, "") if varias else sid,
                    "corto": info.nombre,
                    "freq": freq,
                    "unidad": info.unidad,
                    "fuente": f"Cueva · {_relativa(f.get('path') or info.archivo)}",
                    "familia": familia,
                    "grupo": grupo,
                    "subgrupo": subgrupo,
                    "puntos": list(
                        zip((d.isoformat() for d in fechas), (float(v) for v in s.values), strict=True)
                    ),
                }
            )
    return salida


def faltantes_cueva(con_datos: set[str]) -> list[list]:
    """Filas «falta» del árbol: lo que el catálogo curado declara pero no tiene archivo."""
    filas = []
    resueltas = set(S.catalogo())
    for hoja in S._cargar_definicion_curada():
        if hoja["id"] in resueltas or hoja["id"] in con_datos:
            continue
        fuente = hoja["fuentes"][0] if hoja["fuentes"] else {}
        familia, grupo, subgrupo = _partes(hoja["grupo"], hoja["subgrupo"])
        freq = FRECUENCIAS.get((fuente.get("freq") or "").upper()[:1], "mensual")
        filas.append(
            [
                familia,
                grupo,
                subgrupo,
                hoja["etiqueta"],
                freq,
                hoja["unidad"],
                hoja["id"],
                "falta",
                Path(fuente.get("file", "")).name,
            ]
        )
    return filas


def armar(terminal: list[dict] | None = None) -> dict:
    """El objeto CAT completo: series de La Cueva + las de la Terminal (si se pasan)."""
    entradas = series_cueva()
    terminal = terminal or []
    for t in terminal:
        entradas.append({**t, "corto": t.get("corto") or t["nombre"], "puntos": t.get("puntos")})

    calendarios: dict[str, list[str]] = {}
    for freq in ORDEN:
        fechas = sorted(
            {f for e in entradas if e["freq"] == freq and e.get("puntos") for f, _ in e["puntos"]}
        )
        if fechas:
            calendarios[freq] = fechas
    posicion = {freq: {f: i for i, f in enumerate(fs)} for freq, fs in calendarios.items()}

    series, arbol, vistos = {}, [], set()
    for e in entradas:
        if e["id"] in vistos:
            continue
        vistos.add(e["id"])
        corto = e["corto"]
        nombre = f"{corto} · {e['subgrupo'] or e['grupo']}" if (e["subgrupo"] or e["grupo"]) else corto
        if e.get("puntos"):
            pos = posicion[e["freq"]]
            idx = [pos[f] for f, _ in e["puntos"]]
            i0 = min(idx)
            y = [None] * (max(idx) - i0 + 1)
            for (_, v), i in zip(e["puntos"], idx, strict=True):
                y[i - i0] = v
            ficha = {
                "nombre": nombre,
                "corto": corto,
                "freq": e["freq"],
                "unidad": e.get("unidad") or "",
                "fuente": e["fuente"],
                "familia": e["familia"],
                "grupo": e["grupo"],
                "subgrupo": e["subgrupo"],
                "i0": i0,
                "y": y,
            }
            if e.get("url"):
                ficha["url"] = e["url"]
            series[e["id"]] = ficha
            estado = "datos"
        else:
            estado = "terminal"
        arbol.append(
            [
                e["familia"],
                e["grupo"],
                e["subgrupo"],
                corto,
                e["freq"],
                e.get("unidad") or "",
                e["id"],
                estado,
                e["fuente"],
            ]
        )
    arbol += faltantes_cueva(vistos)
    arbol.sort(key=lambda a: (a[0], a[1], a[2], a[7] != "datos", a[3]))
    return {
        "calendarios": calendarios,
        "series": series,
        "arbol": arbol,
        "generado": dt.date.today().isoformat(),
    }
