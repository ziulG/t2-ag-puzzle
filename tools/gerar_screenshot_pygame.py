"""Gera o screenshot do Pygame em modo headless (sem abrir janela).

Pega o melhor run da pasta mais recente, simula a sequência de movimentos
até resolver, e salva o frame final em docs/screenshots/pygame_animacao.png.

Uso: SDL_VIDEODRIVER=dummy python tools/gerar_screenshot_pygame.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Garante headless ANTES de importar pygame
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from puzzle.goal import GOAL  # noqa: E402
from puzzle.movimentos import aplicar_movimento  # noqa: E402
from viz._io import (  # noqa: E402
    carregar_detalhe_json,
    encontrar_melhor_run,
    listar_execucoes,
    mapear_direcoes,
    parse_estado_inicial,
)
from viz.pygame_anim import renderizar_frame_em_arquivo  # noqa: E402


def main() -> int:
    pastas = listar_execucoes(ROOT / "results")
    if not pastas:
        print("Nenhuma pasta de resultados encontrada.", file=sys.stderr)
        return 1
    pasta = pastas[0]
    json_path = encontrar_melhor_run(pasta)
    print(f"→ Usando {pasta.name} / {json_path.name}")

    dados = carregar_detalhe_json(json_path)
    estado_inicial = parse_estado_inicial(dados["estado_inicial"])
    movimentos = mapear_direcoes(dados.get("movimentos_decodificados", []))

    # Simula até o GOAL (ou até o fim)
    estado = estado_inicial
    indice_resolvido = len(movimentos)
    for i, direcao in enumerate(movimentos, start=1):
        estado = aplicar_movimento(estado, direcao)
        if estado == GOAL:
            indice_resolvido = i
            break

    output = ROOT / "docs" / "screenshots" / "pygame_animacao.png"
    renderizar_frame_em_arquivo(
        output,
        estado=estado,
        estado_inicial=estado_inicial,
        indice_movimento=indice_resolvido,
        total_movimentos=len(movimentos),
        melhor_fitness=float(dados.get("melhor_fitness", 0.0)),
        caso_nome=str(dados.get("caso_nome", "?")),
        resolveu_run=bool(dados.get("resolveu", False)),
        mostrar_resolveu=(estado == GOAL),
    )
    print(f"✓ Screenshot salvo em {output.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
