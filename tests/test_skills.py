"""Tests del sistema de skills: los agentes se definen en knowledge-base/skills/."""

from cueva.agentes.agentes import AGENTES
from cueva.agentes.pipelines import PIPELINES
from cueva.econometria import declaraciones_herramientas
from cueva.econometria.herramientas import REGISTRO


def test_plantel_completo_desde_skills():
    """Los 12 agentes (4 profesores + líder + 7 especialistas) existen."""
    esperados = {
        "metodologo",
        "critico",
        "interprete",
        "bibliografo",
        "lider",
        "curador_datos",
        "transformaciones",
        "multivariados",
        "volatilidad",
        "pronostico_ml",
        "controles_causal",
        "robustez",
    }
    assert esperados <= set(AGENTES)


def test_skill_manda_sobre_el_default():
    """El cuerpo del markdown es la identidad del agente (editable sin tocar Python)."""
    met = AGENTES["metodologo"]
    assert met.cuerpo, "el skill metodologo.md debería aportar el cuerpo"
    sp = met.system_prompt()
    assert "Metodólogo" in sp
    assert "REGLAS ESTRICTAS" in sp  # las reglas comunes siempre se agregan
    assert "regresión espuria" in sp.lower() or "espuria" in sp.lower()


def test_frontmatter_parseado():
    assert AGENTES["curador_datos"].tier == "barato"
    assert AGENTES["metodologo"].tier == "medio"
    assert "vecm" in AGENTES["metodologo"].herramientas
    assert AGENTES["bibliografo"].sesgo_rag  # vino del frontmatter


def test_lista_blanca_efectiva():
    """Las declaraciones para function calling filtran lo que no existe en el REGISTRO."""
    decl = declaraciones_herramientas(["vecm", "estacionariedad", "herramienta_fantasma"])
    nombres = [d["name"] for d in decl]
    assert nombres == ["vecm", "estacionariedad"]
    assert all("parameters_json_schema" in d for d in decl)
    # el líder declara herramientas de coordinación que NO son ejecutables → lista vacía
    assert declaraciones_herramientas(AGENTES["lider"].herramientas) == []


def test_ejecutar_segura_respeta_lista_blanca(carpeta_series):
    met = AGENTES["metodologo"]
    # fuera de la lista blanca → rechazado sin ejecutar
    r = met._ejecutar_segura("herramienta_fantasma", {})
    assert not r["ok"] and "lista blanca" in r["resumen"]
    # dentro de la lista + saneo de floats integrales (Gemini manda 1.0 por 1)
    r = met._ejecutar_segura("estacionariedad", {"sid": "caminata", "dif": 1.0})
    assert r["ok"]
    assert r["args"]["dif"] == 1


def test_herramientas_de_skills_existen_en_registro():
    """Regla de consistencia (perfeccionismo anti-alucinación): la lista blanca de CADA skill
    debe ser subconjunto del REGISTRO ejecutable. Un skill que promete herramientas
    inexistentes lleva al agente a inventar la evidencia que cree poder pedir. Lo que el
    agente sabe pero la plataforma no ejecuta va en el cuerpo como 'asesorás sin ejecutar'."""
    for aid, agente in AGENTES.items():
        fantasmas = set(agente.herramientas) - set(REGISTRO)
        assert not fantasmas, f"skill '{aid}' declara herramientas inexistentes: {sorted(fantasmas)}"


def test_turnos_con_tool_use_tienen_agente_equipado():
    """Un turno con `herramientas: True` solo tiene sentido si el agente puede ejecutar algo."""
    for nombre, turnos in PIPELINES.items():
        for t in turnos:
            if t.get("herramientas"):
                ejecutables = set(AGENTES[t["agente"]].herramientas) & set(REGISTRO)
                assert ejecutables, (
                    f"{nombre}/{t['fase']}: turno con tool-use pero '{t['agente']}' "
                    f"no tiene herramientas ejecutables"
                )


def test_handoff_ids_dinamicos_en_el_prompt():
    """Las REGLAS ofrecen TODO el plantel como destino de handoff (menos uno mismo):
    antes estaban cableados los 4 profesores clásicos y desinformaban a los especialistas."""
    sp = AGENTES["robustez"].system_prompt()
    linea_ids = sp.split("ids disponibles:")[1].split(")")[0]
    assert "multivariados" in linea_ids and "lider" in linea_ids and "critico" in linea_ids
    assert "robustez" not in linea_ids  # nadie se hace handoff a sí mismo


def test_pipelines_referencian_agentes_existentes():
    """Regla de consistencia: todo turno de todo pipeline apunta a un agente real."""
    for nombre, turnos in PIPELINES.items():
        for t in turnos:
            assert t["agente"] in AGENTES, f"{nombre}: agente inexistente {t['agente']}"
            assert t["fase"] in {
                "encuadre",
                "exploratorio",
                "control",
                "modelizacion",
                "interpretacion",
                "conclusiones",
            }
