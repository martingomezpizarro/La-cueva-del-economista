"""registro — El catálogo vivo de métodos y su ejecutor.

- `@metodo(...)` registra una función como método del catálogo (ver `contrato.Metodo`).
- `catalogo()` lista todo lo registrado, marcando qué está disponible en ESTA instalación
  (un método cuyo paquete opcional falta aparece con `disponible: False` y la instrucción de
  instalación; nunca rompe la plataforma).
- `ejecutar(id, args)` valida los argumentos contra la declaración, corre el método, mide el
  tiempo y devuelve el dict uniforme que consumen la API, el Estudio y los agentes:

      {"ok", "herramienta", "metodo", "args", "resumen", "bloques", "metricas",
       "advertencias", "semaforo", "series_salida", "codigo", "meta"}

Qué NO hace: no persiste nada (eso lo hace el proyecto en `cueva/sesiones`).
"""

from __future__ import annotations

import importlib.util
import logging
import re
import time
from collections.abc import Callable

from cueva.metodos.contrato import ErrorMetodo, Metodo, Param, Resultado, limpiar

log = logging.getLogger("cueva.metodos")

_REGISTRO: dict[str, Metodo] = {}
_ID = re.compile(r"^[a-z][a-z0-9_]{1,29}$")
_FECHA = re.compile(r"^\d{4}-\d{2}(-\d{2})?$")

# paquete de pip para cada módulo opcional (cuando el nombre difiere)
PIP = {"sklearn": "scikit-learn", "ruptures": "ruptures", "xgboost": "xgboost", "lightgbm": "lightgbm"}


def metodo(
    id: str,
    nombre: str,
    familia: str,
    pregunta: str,
    params: list[Param] | None = None,
    **extra,
) -> Callable:
    """Decorador: registra la función como método del catálogo."""
    if not _ID.match(id):
        raise ValueError(f"id de método inválido: {id!r} (minúsculas, dígitos y _; 2-30)")

    def deco(fn):
        if id in _REGISTRO:
            raise ValueError(f"Método duplicado: {id}")
        _REGISTRO[id] = Metodo(
            id=id, nombre=nombre, familia=familia, fn=fn, pregunta=pregunta, params=params or [], **extra
        )
        return fn

    return deco


def _cargar_familias() -> None:
    """Importa los módulos de familias (cada uno registra sus métodos al importarse)."""
    from cueva.metodos import familias  # noqa: F401


def registro() -> dict[str, Metodo]:
    if not _REGISTRO:
        _cargar_familias()
    return _REGISTRO


def faltantes(m: Metodo) -> list[str]:
    return [d for d in m.deps if importlib.util.find_spec(d) is None]


def catalogo() -> list[dict]:
    out = []
    for m in registro().values():
        f = faltantes(m)
        out.append(m.a_dict(disponible=not f, falta=f))
    return out


def obtener(id: str) -> Metodo:
    try:
        return registro()[id]
    except KeyError as e:
        raise KeyError(f"Método desconocido: {id}") from e


# ──────────────────────────────────────────────────────────────────────────
# Validación de argumentos
# ──────────────────────────────────────────────────────────────────────────
def validar_args(m: Metodo, args: dict) -> dict:
    """Devuelve los argumentos limpios (con defectos aplicados) o levanta ErrorMetodo.
    Los argumentos que el método no declara se descartan (no se pasan a la función)."""
    limpio = {}
    for p in m.params:
        v = args.get(p.nombre, None)
        if v is None or v == "" or v == []:
            if p.requerido:
                raise ErrorMetodo(f"Falta el parámetro «{p.etiqueta}».")
            limpio[p.nombre] = p.defecto
            continue
        limpio[p.nombre] = _coercer(p, v)
    return limpio


def _serie_o_receta(p: Param, v) -> str:
    """Un id de serie, o una receta (dict) que se registra y se vuelve un id «r:<huella>»:
    así CUALQUIER método corre sobre series derivadas sin saber que lo son."""
    from cueva.metodos.insumos import registrar_receta

    if isinstance(v, dict):
        return registrar_receta(v)
    if not isinstance(v, str) or not re.match(r"^[A-Za-z0-9_.:\-]{1,120}$", v):
        raise ErrorMetodo(f"«{p.etiqueta}»: id de serie inválido.")
    return v


def _coercer(p: Param, v):
    t = p.tipo
    if t == "serie":
        return _serie_o_receta(p, v)
    if t == "series":
        if isinstance(v, str):
            v = [x.strip() for x in v.split(",") if x.strip()]
        if not isinstance(v, list):
            raise ErrorMetodo(f"«{p.etiqueta}»: lista de series inválida.")
        v = [_serie_o_receta(p, x) for x in v]
        v = list(dict.fromkeys(v))  # sin repetidos, en orden
        if p.min_items and len(v) < p.min_items:
            raise ErrorMetodo(f"«{p.etiqueta}»: hacen falta al menos {p.min_items} series.")
        if p.max_items and len(v) > p.max_items:
            raise ErrorMetodo(f"«{p.etiqueta}»: como máximo {p.max_items} series.")
        return v
    if t in ("entero", "real"):
        try:
            x = int(v) if t == "entero" else float(v)
        except (TypeError, ValueError) as e:
            raise ErrorMetodo(f"«{p.etiqueta}» tiene que ser un número.") from e
        if t == "entero" and isinstance(v, float) and not v.is_integer():
            raise ErrorMetodo(f"«{p.etiqueta}» tiene que ser entero.")
        if p.minimo is not None and x < p.minimo:
            raise ErrorMetodo(f"«{p.etiqueta}» tiene que ser ≥ {p.minimo}.")
        if p.maximo is not None and x > p.maximo:
            raise ErrorMetodo(f"«{p.etiqueta}» tiene que ser ≤ {p.maximo}.")
        return x
    if t == "opcion":
        if v not in (p.opciones or []):
            raise ErrorMetodo(f"«{p.etiqueta}»: opción inválida {v!r} (hay: {', '.join(p.opciones or [])}).")
        return v
    if t == "opciones":
        if isinstance(v, str):
            v = [x.strip() for x in v.split(",") if x.strip()]
        malas = [x for x in v if x not in (p.opciones or [])]
        if malas:
            raise ErrorMetodo(f"«{p.etiqueta}»: opciones inválidas {malas}.")
        return list(dict.fromkeys(v))
    if t == "bool":
        if isinstance(v, str):
            return v.lower() in ("1", "si", "sí", "true", "verdadero")
        return bool(v)
    if t == "fecha":
        if not isinstance(v, str) or not _FECHA.match(v):
            raise ErrorMetodo(f"«{p.etiqueta}»: fecha inválida (AAAA-MM o AAAA-MM-DD).")
        return v
    if not isinstance(v, str) or len(v) > 400:
        raise ErrorMetodo(f"«{p.etiqueta}»: texto inválido.")
    return v


# ──────────────────────────────────────────────────────────────────────────
# Ejecución
# ──────────────────────────────────────────────────────────────────────────
def _versiones(deps: list[str]) -> dict[str, str]:
    import importlib

    out = {}
    for mod in ["numpy", "pandas", "statsmodels", *deps]:
        try:
            out[mod] = getattr(importlib.import_module(mod), "__version__", "?")
        except Exception:
            continue
    return out


def ejecutar(id: str, args: dict | None = None) -> dict:
    """Corre un método del catálogo. Nunca levanta: los errores vuelven como ok=False."""
    args = dict(args or {})
    base = {"herramienta": id, "metodo": id, "args": args}
    try:
        m = obtener(id)
    except KeyError as e:
        return {**base, "ok": False, "resumen": str(e)}
    falta = faltantes(m)
    if falta:
        pips = " ".join(PIP.get(d, d) for d in falta)
        return {
            **base,
            "ok": False,
            "no_disponible": True,
            "resumen": f"«{m.nombre}» necesita paquetes que no están instalados: {', '.join(falta)}. "
            f"Instalá: pip install {pips}",
        }
    t0 = time.perf_counter()
    try:
        limpio = validar_args(m, args)
        r = m.fn(**limpio)
        if not isinstance(r, Resultado):
            raise TypeError(f"{id} no devolvió un Resultado")
    except ErrorMetodo as e:
        return {**base, "ok": False, "resumen": f"{m.nombre}: {e}"}
    except KeyError as e:
        return {**base, "ok": False, "resumen": f"{m.nombre}: {e.args[0] if e.args else e}"}
    except Exception as e:  # un bug o un caso que el método no previó: se informa, no se cae
        log.exception("Falló el método %s", id)
        return {**base, "ok": False, "resumen": f"Error ejecutando {m.nombre}: {type(e).__name__}: {e}"}
    seg = time.perf_counter() - t0
    salida = r.a_dict()
    if not salida["resumen"]:
        salida["resumen"] = f"{m.nombre}: listo."
    return limpiar(
        {
            **base,
            "ok": True,
            "args": limpio,
            "nombre": m.nombre,
            "familia": m.familia,
            **salida,
            "meta": {"segundos": round(seg, 3), "versiones": _versiones(m.deps)},
        }
    )


def expandir(nombres: list[str]) -> list[str]:
    """Expande comodines de familia en listas blancas: «familia:pruebas» → todos los ids de
    esa familia. Lo demás pasa tal cual (así un skill puede habilitar una familia entera)."""
    out: list[str] = []
    for n in nombres or []:
        if isinstance(n, str) and n.startswith("familia:"):
            fam = n.split(":", 1)[1]
            out.extend(m.id for m in registro().values() if m.familia == fam)
        else:
            out.append(n)
    return list(dict.fromkeys(out))


def declaraciones(ids: list[str] | None = None) -> list[dict]:
    """Declaraciones de function calling (formato Gemini/OpenAI) de los métodos pedidos."""
    out = []
    for m in registro().values():
        if ids is not None and m.id not in ids:
            continue
        if faltantes(m):
            continue
        out.append(
            {
                "name": m.id,
                "description": f"{m.nombre}. {m.pregunta}",
                "parameters": m.esquema(),
            }
        )
    return out
