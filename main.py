"""Entrypoint do projeto. Subcomandos: run, animate, dashboard, test."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
RESULTS_DIR = RAIZ / "results"


def _cmd_run(_args: argparse.Namespace) -> int:
    """Roda o batch completo de experimentos (Fase 3)."""
    from experiment.run_all import main as run_all_main

    run_all_main()
    return 0


def _cmd_animate(args: argparse.Namespace) -> int:
    """Anima uma execução específica no Pygame."""
    from viz._io import encontrar_melhor_run, listar_execucoes
    from viz.pygame_anim import animar

    if args.latest:
        pastas = listar_execucoes(RESULTS_DIR)
        if not pastas:
            print(
                f"Nenhuma execução em {RESULTS_DIR}. Rode `python main.py run` antes.",
                file=sys.stderr,
            )
            return 1
        pasta = pastas[0]
        json_path = encontrar_melhor_run(pasta)
        print(f"→ Usando {pasta.name} / {json_path.name}")
    else:
        if not args.json_path:
            print("Informe um path JSON ou use --latest", file=sys.stderr)
            return 2
        json_path = Path(args.json_path)
        if not json_path.exists():
            print(f"Arquivo não encontrado: {json_path}", file=sys.stderr)
            return 1

    animar(json_path, delay_ms=args.delay)
    return 0


def _cmd_dashboard(_args: argparse.Namespace) -> int:
    """Sobe o Streamlit."""
    script = RAIZ / "viz" / "dashboard.py"
    return subprocess.call(["streamlit", "run", str(script)])


def _cmd_test(_args: argparse.Namespace) -> int:
    """Roda a suíte de testes."""
    return subprocess.call(["pytest", "-v", str(RAIZ / "tests")])


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="main.py", description="8-Puzzle com Algoritmo Genético"
    )
    sub = parser.add_subparsers(dest="comando", required=True)

    sub.add_parser("run", help="Executa o batch completo de experimentos").set_defaults(
        func=_cmd_run
    )

    p_anim = sub.add_parser("animate", help="Anima uma execução no Pygame")
    p_anim.add_argument("json_path", nargs="?", help="Path para detalhes/<run_id>.json")
    p_anim.add_argument(
        "--latest", action="store_true", help="Pega o melhor run da pasta mais recente"
    )
    p_anim.add_argument(
        "--delay", type=int, default=300, help="Delay entre movimentos em ms (default 300)"
    )
    p_anim.set_defaults(func=_cmd_animate)

    sub.add_parser("dashboard", help="Sobe o dashboard Streamlit").set_defaults(
        func=_cmd_dashboard
    )
    sub.add_parser("test", help="Roda pytest").set_defaults(func=_cmd_test)

    return parser


def main() -> int:
    parser = construir_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
