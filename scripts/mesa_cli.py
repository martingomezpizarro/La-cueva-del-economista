#!/usr/bin/env python3
"""mesa_cli — Corré una sesión de la Mesa de Trabajo desde la terminal (sin abrir la web).

Ejemplos:
    python scripts/mesa_cli.py --pregunta "¿Los depósitos explican las reservas?" \
        --ids 001_reservas_brutas 021_dep_total --dep 001_reservas_brutas

    python scripts/mesa_cli.py --diag             # ver estado de config y datos
    python scripts/mesa_cli.py --series reservas  # buscar series por palabra clave
    python scripts/mesa_cli.py --revisar "agregué una serie" --pregunta "..."  # modo Líder
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# La consola de Windows usa cp1252 y la mesa imprime emojis/flechas: sin esto,
# el primer mensaje del orquestador tira UnicodeEncodeError.
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cueva import config  # noqa: E402
from cueva.agentes import Orquestador, Proyecto  # noqa: E402
from cueva.datos import series as S  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="Mesa de Trabajo — CLI")
    ap.add_argument("--diag", action="store_true", help="mostrar diagnóstico de configuración")
    ap.add_argument("--series", nargs="?", const="", help="buscar series por palabra clave")
    ap.add_argument("--pregunta", default="", help="pregunta de investigación")
    ap.add_argument("--titulo", default="Investigación")
    ap.add_argument("--hipotesis", nargs="*", default=[])
    ap.add_argument("--series-ids", "--ids", dest="ids", nargs="*", default=[], help="IDs de series a usar")
    ap.add_argument("--dep", default=None, help="ID de la serie dependiente (Y)")
    ap.add_argument("--freq", default="mensual")
    ap.add_argument(
        "--pipeline",
        default="clasica",
        help="guion de la mesa: clasica (4 profesores) o equipo_completo (10 especialistas)",
    )
    ap.add_argument(
        "--revisar",
        nargs="?",
        const="",
        default=None,
        help="modo 2: solo el Líder revisa el estado a demanda (no corre toda la mesa). "
        "Podés pasarle texto: qué acaba de pasar (ej.: 'el usuario agregó una serie')",
    )
    args = ap.parse_args()

    if args.diag:
        d = config.diagnostico()
        d["n_series"] = len(S.catalogo())
        print(json.dumps(d, indent=2, ensure_ascii=False))
        return

    if args.series is not None:
        for s in S.listar(filtro=args.series, limite=40):
            print(f"  {s['id']:50s} {s['origen']:12s} n={s['n']:>5}  {s['desde']}→{s['hasta']}")
        return

    if not args.pregunta:
        ap.error("indicá --pregunta (o usá --diag / --series)")

    proyecto = Proyecto(
        titulo=args.titulo,
        pregunta=args.pregunta,
        hipotesis=args.hipotesis,
        series=args.ids,
        serie_dependiente=args.dep,
        frecuencia=args.freq,
    )
    orq = Orquestador(proyecto, pipeline=args.pipeline)
    iterador = orq.revisar(args.revisar) if args.revisar is not None else orq.correr()
    for m in iterador:
        destino = f" → @{m.dirigido_a}" if m.dirigido_a else ""
        print(f"\n[{m.rol}{destino}]")
        print(m.contenido)
        if m.citas:
            print("   📚 " + "; ".join(m.citas))
    uso = orq.contador.to_dict()
    print(f"\n— uso LLM: {uso['llamadas']} llamadas, {uso['tokens_entrada']}+{uso['tokens_salida']} tokens —")


if __name__ == "__main__":
    main()
