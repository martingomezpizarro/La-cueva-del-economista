"""bcra — cliente de la API de Estadísticas Monetarias del BCRA (v4.0).

QUÉ HACE: lista las variables publicadas (1610 al 2026-08-27), baja la serie histórica
de cada una y trae el texto metodológico oficial con que el BCRA define cada variable.

QUÉ NO HACE: no escribe en el catálogo ni en disco (de eso se ocupa
`scripts/actualizar_bcra.py`) y no transforma las series.

La API es pública y no pide clave. El BCRA controla el tráfico por IP, así que el
cliente espacia los pedidos y siempre filtra por fechas. La cadena TLS del servidor
suele venir incompleta: por eso `verificar_tls` es configurable (default: True, y si
falla se avisa con una excepción clara en vez de romper por dentro de urllib3).

Endpoints (registro en `cueva/fuentes/registro.json`):
    GET /estadisticas/v4.0/Monetarias                 -> índice de variables
    GET /estadisticas/v4.0/Monetarias/{IdVariable}    -> serie, con Desde/Hasta/Limit/Offset
    GET /estadisticas/v4.0/Metodologia[/{idVariable}] -> definición metodológica

DOS TRAMPAS DEL CONTRATO, aprendidas a los golpes:

1. Los nombres de campo del índice son `periodicidad`, `unidadExpresion`, `moneda`,
   `tipoSerie`, `primerFechaInformada` y `ultFechaInformada` — NO `frecuencia`,
   `unidad`, `fechaInicio` ni `fechaFin`.
2. `metadata.resultset.count` NO es el total del catálogo: es cuántos registros quedan
   desde el `Offset` pedido. Con Offset=0 coincide con el total; con Offset=1400 devuelve
   210. Por eso la paginación se corta cuando una página vuelve corta, no comparando
   contra `count`.
"""

from __future__ import annotations

import re
import time
import unicodedata
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import date
from typing import Any

import requests

from cueva.fuentes.registro import organismo

LIMITE_PAGINA_SERIE = 3000  # tope duro que documenta el BCRA para /Monetarias/{id}
LIMITE_PAGINA_INDICE = 500  # el índice tiene 1610 variables; se pagina de a tandas
ESPERA_ENTRE_PEDIDOS = 0.35  # segundos; el control de tráfico del BCRA es por IP
REINTENTOS = 3
PRIMERA_FECHA = "1940-01-01"  # la serie más vieja (reservas mensuales) arranca 1940-02-29


class ErrorBCRA(RuntimeError):
    """La API del BCRA respondió algo que no se puede usar."""


def _slug(descripcion: str, id_variable: int) -> str:
    base = unicodedata.normalize("NFKD", descripcion.lower())
    base = base.encode("ascii", "ignore").decode()
    base = re.sub(r"[^a-z0-9]+", "_", base).strip("_")
    return f"{id_variable:04d}_{base[:60]}"


@dataclass(frozen=True)
class VariableBCRA:
    """Una variable del índice de `/Monetarias`, con los nombres de campo REALES."""

    id: int
    descripcion: str
    categoria: str
    tipo_serie: str        # tipoSerie: "Saldos", "Flujo diario", "Tasa de interés", …
    periodicidad: str      # "D" diaria · "M" mensual
    unidad: str            # unidadExpresion
    moneda: str            # "ML" · "ME" · "MEyML" · "USD"
    desde: str             # primerFechaInformada
    hasta: str             # ultFechaInformada
    ultimo_valor: float | None = None

    @property
    def slug(self) -> str:
        """Nombre de archivo estable y sin acentos para esta variable."""
        return _slug(self.descripcion, self.id)

    @classmethod
    def desde_json(cls, v: dict[str, Any]) -> VariableBCRA:
        return cls(
            id=int(v["idVariable"]),
            descripcion=(v.get("descripcion") or "").strip(),
            categoria=(v.get("categoria") or "").strip(),
            tipo_serie=(v.get("tipoSerie") or "").strip(),
            periodicidad=(v.get("periodicidad") or "").strip(),
            unidad=(v.get("unidadExpresion") or "").strip(),
            moneda=(v.get("moneda") or "").strip(),
            desde=v.get("primerFechaInformada") or "",
            hasta=v.get("ultFechaInformada") or "",
            ultimo_valor=v.get("ultValorInformado"),
        )


@dataclass
class ClienteBCRA:
    """Cliente HTTP de la API v4.0. Reusa una sesión y respeta el ritmo del BCRA."""

    verificar_tls: bool = True
    idioma: str = "es-AR"
    espera: float = ESPERA_ENTRE_PEDIDOS
    tiempo_maximo: int = 60
    _sesion: requests.Session = field(default_factory=requests.Session, repr=False)

    @property
    def base(self) -> str:
        return organismo("bcra").api["base"].rstrip("/")

    # ---------------------------------------------------------------- HTTP

    def _pedir(self, ruta: str, **params: Any) -> dict:
        url = f"{self.base}{ruta}"
        cabeceras = {"Accept-Language": self.idioma}
        limpios = {k: v for k, v in params.items() if v is not None}
        ultimo: Exception | None = None
        for intento in range(1, REINTENTOS + 1):
            try:
                r = self._sesion.get(
                    url, params=limpios, headers=cabeceras,
                    verify=self.verificar_tls, timeout=self.tiempo_maximo,
                )
            except requests.exceptions.SSLError as exc:
                raise ErrorBCRA(
                    "La cadena TLS del BCRA no validó. Reintentá con "
                    "ClienteBCRA(verificar_tls=False) si confiás en la red desde la que corrés."
                ) from exc
            except requests.RequestException as exc:
                ultimo = exc
                time.sleep(self.espera * intento * 2)
                continue
            if r.status_code == 200:
                time.sleep(self.espera)
                return r.json()
            if r.status_code in (429, 500, 502, 503, 504):
                # control de tráfico por IP o caída momentánea: se espera más y se reintenta
                time.sleep(self.espera * intento * 4)
                ultimo = ErrorBCRA(f"HTTP {r.status_code} en {url}")
                continue
            raise ErrorBCRA(f"HTTP {r.status_code} en {url}: {r.text[:200]}")
        raise ErrorBCRA(f"{url} falló tras {REINTENTOS} intentos: {ultimo}")

    # ------------------------------------------------------------ catálogo

    def variables(
        self,
        categoria: str | None = None,
        periodicidad: str | None = None,
    ) -> list[VariableBCRA]:
        """Índice de variables monetarias, paginado hasta el final.

        `categoria` y `periodicidad` se pasan como filtros a la API (`Categoria`,
        `Periodicidad`), que es mucho más barato que traer las 1610 y filtrar acá.
        """
        encontradas: dict[int, VariableBCRA] = {}
        offset = 0
        while True:
            payload = self._pedir(
                "/estadisticas/v4.0/Monetarias",
                Categoria=categoria, Periodicidad=periodicidad,
                Limit=LIMITE_PAGINA_INDICE, Offset=offset,
            )
            pagina = payload.get("results") or []
            for v in pagina:
                var = VariableBCRA.desde_json(v)
                encontradas[var.id] = var
            # `count` es lo que queda desde el offset, no el total: se corta por página corta.
            if len(pagina) < LIMITE_PAGINA_INDICE:
                break
            offset += LIMITE_PAGINA_INDICE
        return sorted(encontradas.values(), key=lambda v: v.id)

    def categorias(self) -> dict[str, int]:
        """Cuántas variables hay por categoría. Útil para ver qué publicó el BCRA de nuevo."""
        conteo: dict[str, int] = {}
        for v in self.variables():
            conteo[v.categoria] = conteo.get(v.categoria, 0) + 1
        return dict(sorted(conteo.items(), key=lambda par: -par[1]))

    def metodologia(self, id_variable: int | None = None) -> dict[int, str]:
        """Texto metodológico oficial, por idVariable.

        Sin argumento trae el corpus completo paginando; con uno, solo esa variable.
        """
        if id_variable is not None:
            payload = self._pedir(f"/estadisticas/v4.0/Metodologia/{id_variable}")
            return {int(r["id"]): (r.get("detalle") or "").strip()
                    for r in payload.get("results", [])}

        textos: dict[int, str] = {}
        offset, limite = 0, LIMITE_PAGINA_INDICE
        while True:
            payload = self._pedir("/estadisticas/v4.0/Metodologia", Limit=limite, Offset=offset)
            pagina = _aplanar_metodologia(payload.get("results", []))
            for r in pagina:
                textos[int(r["id"])] = (r.get("detalle") or "").strip()
            if len(pagina) < limite:
                break
            offset += limite
        return textos

    # ---------------------------------------------------------------- serie

    def serie(
        self,
        id_variable: int,
        desde: str = PRIMERA_FECHA,
        hasta: str | None = None,
    ) -> list[tuple[str, float]]:
        """Serie histórica completa de una variable, como [(fecha ISO, valor), …].

        Pagina sola: la API devuelve como mucho `LIMITE_PAGINA_SERIE` observaciones.
        """
        hasta = hasta or date.today().isoformat()
        filas: list[tuple[str, float]] = []
        offset = 0
        while True:
            payload = self._pedir(
                f"/estadisticas/v4.0/Monetarias/{id_variable}",
                Desde=desde, Hasta=hasta, Limit=LIMITE_PAGINA_SERIE, Offset=offset,
            )
            tramo = list(_observaciones(payload))
            if not tramo:
                break
            filas.extend(tramo)
            if len(tramo) < LIMITE_PAGINA_SERIE:
                break
            offset += LIMITE_PAGINA_SERIE
        # La API puede repetir el borde entre páginas: se deduplica por fecha.
        return sorted({fecha: valor for fecha, valor in filas}.items())


def _aplanar_metodologia(resultados: list) -> list[dict]:
    """`/Metodologia` devuelve results como lista de listas en algunas versiones."""
    planos: list[dict] = []
    for r in resultados:
        if isinstance(r, list):
            planos.extend(r)
        else:
            planos.append(r)
    return planos


def _observaciones(payload: dict) -> Iterator[tuple[str, float]]:
    """Aplana la respuesta de /Monetarias/{id}.

    La v4 anida las observaciones en results[].detalle[]; algunas variantes las
    devuelven planas en results[]. Se contemplan las dos.
    """
    for bloque in payload.get("results", []):
        detalle = bloque.get("detalle") if isinstance(bloque, dict) else None
        if detalle is None:
            detalle = [bloque]
        for obs in detalle:
            fecha = obs.get("fecha")
            valor = obs.get("valor")
            if fecha is None or valor is None:
                continue
            yield str(fecha)[:10], float(valor)
