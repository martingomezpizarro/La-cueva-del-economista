"""plantillas — proyectos predeterminados de la Mesa («Valuación de empresa», …).

Una plantilla es un proyecto guardado con la estructura armada: el usuario elige la
empresa y los valores de los parámetros; los datos los carga él desde la Ficha.
Qué hace: declara las plantillas y arma el estado inicial de la Mesa de un proyecto nuevo.
Qué NO hace: no calcula nada ni baja datos (eso lo hacen los métodos y la Terminal).
"""

from __future__ import annotations

import copy

# Cada método de la valuación lleva una línea que dice qué pregunta responde; la ficha
# grande del método y el (i) de cada parámetro se escriben cuando se construye el bloque.
METODOS_VALUACION: list[dict] = [
    {
        "id": "dcf",
        "nombre": "Flujo de fondos descontado (DCF)",
        "pregunta": "¿Cuánto vale si se cumplen mis supuestos de flujo, crecimiento y tasa?",
        "estado": "en construcción · paso 1 de 6",
        "guia": "https://claude.ai/artifact/GGutPT2ZtgZ8VDWW94DyVi",
        # Se construye de a un paso con Martín (Aprender → Diseñar → Construir → Al informe).
        "pasos": [
            {"id": "flujo", "nombre": "Flujo de caja libre histórico", "estado": "en curso",
             "metodo": "flujo_caja_libre",
             "nota": "herramienta «Flujo de caja libre de la firma (FCFF)», en Traer"},
            {"id": "reinversion", "nombre": "Reinversión y retorno del capital", "estado": "por construir"},
            {"id": "crecimiento", "nombre": "Crecimiento esperado", "estado": "por construir"},
            {"id": "tasa", "nombre": "Tasa de descuento (WACC)", "estado": "por construir"},
            {"id": "etapas", "nombre": "DCF por etapas y valor final", "estado": "por construir"},
            {"id": "inverso", "nombre": "DCF inverso", "estado": "por construir"},
        ],
    },
    {
        "id": "gordon",
        "nombre": "Valor intrínseco por crecimiento (Gordon)",
        "pregunta": "¿Cuánto vale con un crecimiento estable para siempre?",
        "estado": "por construir",
    },
    {
        "id": "dcf_inverso",
        "nombre": "DCF inverso",
        "pregunta": "¿Qué crecimiento está descontando el precio de hoy?",
        "estado": "por construir",
    },
    {
        "id": "multiplos_historia",
        "nombre": "Múltiplos contra su historia",
        "pregunta": "¿Está cara o barata contra sí misma?",
        "estado": "por construir",
    },
    {
        "id": "comparables",
        "nombre": "Comparables",
        "pregunta": "¿Está cara o barata contra empresas parecidas?",
        "estado": "por construir",
    },
    {
        "id": "nav_minero",
        "nombre": "NAV por suma de las partes (minería)",
        "pregunta": "¿Cuánto vale cada mina y cada proyecto?",
        "estado": "por construir",
        "sector": "minería",
    },
]

PLANTILLAS: dict[str, dict] = {
    "valuacion_empresa": {
        "id": "valuacion_empresa",
        "titulo": "Valuación de empresa",
        "descripcion": "Elegís la empresa y los métodos; cada método trae su ficha para "
        "aprenderlo y un (i) por parámetro. Los datos los cargás vos desde la Ficha.",
        "metodos": METODOS_VALUACION,
        "mesa": {"valuacion": {"activo": None, "metodos": [], "bloques": {}}},
    },
}


def listar() -> list[dict]:
    return [{k: v for k, v in p.items() if k != "mesa"} for p in PLANTILLAS.values()]


def estado_inicial(plantilla_id: str, metodos: list[str] | None = None, activo: str | None = None) -> dict:
    """Estado de la Mesa para un proyecto nuevo nacido de la plantilla."""
    p = PLANTILLAS[plantilla_id]
    mesa = copy.deepcopy(p["mesa"])
    if plantilla_id == "valuacion_empresa":
        validos = [m["id"] for m in METODOS_VALUACION]
        elegidos = [m for m in (metodos or []) if m in validos] or validos
        mesa["valuacion"]["metodos"] = elegidos
        mesa["valuacion"]["activo"] = activo
        # cada bloque arranca VACÍO: los insumos se cargan a mano desde la Ficha
        mesa["valuacion"]["bloques"] = {m: {"insumos": {}, "parametros": {}} for m in elegidos}
    return mesa
