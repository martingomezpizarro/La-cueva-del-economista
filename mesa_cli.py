#!/usr/bin/env python3
"""
mesa_cli.py — Corré una sesión de la Mesa de Trabajo desde la terminal (sin abrir la web).

Ejemplos:
    python mesa_cli.py --pregunta "¿Los depósitos explican las reservas?" \
        --series 001_reservas_brutas 021_dep_total --dep 001_reservas_brutas

    python mesa_cli.py --diag           # ver estado de config y datos
    python mesa_cli.py --series reservas  # buscar series por palabra clave
"""
from __future__ import annotations

import argparse
import json

import config
from econ import series as S
from mesa.modelos import Proyecto
from mesa.orquestador import Orquestador


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
    ap.add_argument("--revisar", nargs="?", const="", default=None,
                    help="modo 2: solo el Líder revisa el estado a demanda (no corre toda la mesa). "
                         "Podés pasarle texto: qué acaba de pasar (ej.: 'el usuario agregó una serie')")
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

    proyecto = Proyecto(titulo=args.titulo, pregunta=args.pregunta, hipotesis=args.hipotesis,
                        series=args.ids, serie_dependiente=args.dep, frecuencia=args.freq)
    orq = Orquestador(proyecto)
    iterador = orq.revisar(args.revisar) if args.revisar is not None else orq.correr()
    for m in iterador:
        destino = f" → @{m.dirigido_a}" if m.dirigido_a else ""
        print(f"\n[{m.rol}{destino}]")
        print(m.contenido)
        if m.citas:
            print("   📚 " + "; ".join(m.citas))


if __name__ == "__main__":
    main()
