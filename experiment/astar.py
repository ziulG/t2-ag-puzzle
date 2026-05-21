"""A* com heurística de Manhattan como baseline para comparar com o AG.

Implementação clássica de A* sobre o grafo implícito do 8-puzzle. Cada nó é
um ``Estado`` (tupla imutável); arestas são os movimentos válidos do espaço
vazio. A heurística Manhattan é admissível e consistente, então A* devolve
**o ótimo** — perfeito para servir de referência ao AG.

Não há ``ga`` envolvido aqui: é um módulo de análise comparativa.
"""

import heapq
import time
from dataclasses import dataclass
from itertools import count
from typing import Callable

from puzzle.estado import Estado
from puzzle.goal import GOAL
from puzzle.heuristicas import distancia_manhattan
from puzzle.movimentos import Direcao, aplicar_movimento, movimentos_validos


@dataclass(frozen=True)
class AStarResult:
    """Resultado de uma execução do A*."""

    estado_inicial: Estado
    passos_otimos: int
    nos_expandidos: int
    nos_gerados: int
    tempo_s: float
    sequencia_movimentos: tuple[Direcao, ...]


def resolver_astar(
    estado_inicial: Estado,
    heuristica: Callable[[Estado], int] = distancia_manhattan,
) -> AStarResult:
    """Resolve o 8-puzzle com A*. Retorna o caminho ótimo + métricas.

    Heurística default: Manhattan (admissível e consistente).
    """
    t0 = time.perf_counter()

    contador = count()                                   # desempate determinístico no heap
    h0 = heuristica(estado_inicial)
    fronteira: list[tuple[int, int, Estado]] = [(h0, next(contador), estado_inicial)]
    g_score: dict[Estado, int] = {estado_inicial: 0}
    came_from: dict[Estado, tuple[Estado, Direcao]] = {}

    nos_expandidos = 0
    nos_gerados = 1                                      # o próprio inicial

    while fronteira:
        _, _, estado = heapq.heappop(fronteira)

        if estado == GOAL:
            tempo_s = time.perf_counter() - t0
            caminho = _reconstruir_caminho(came_from, estado)
            return AStarResult(
                estado_inicial=estado_inicial,
                passos_otimos=len(caminho),
                nos_expandidos=nos_expandidos,
                nos_gerados=nos_gerados,
                tempo_s=tempo_s,
                sequencia_movimentos=tuple(caminho),
            )

        nos_expandidos += 1
        g_atual = g_score[estado]

        for direcao in movimentos_validos(estado):
            vizinho = aplicar_movimento(estado, direcao)
            g_novo = g_atual + 1
            if g_novo < g_score.get(vizinho, 10**9):
                g_score[vizinho] = g_novo
                came_from[vizinho] = (estado, direcao)
                f = g_novo + heuristica(vizinho)
                heapq.heappush(fronteira, (f, next(contador), vizinho))
                nos_gerados += 1

    raise RuntimeError(
        f"A* não encontrou solução para {estado_inicial} — verifique solubilidade."
    )


def _reconstruir_caminho(
    came_from: dict[Estado, tuple[Estado, Direcao]],
    estado_final: Estado,
) -> list[Direcao]:
    """Reconstrói a sequência de movimentos do inicial até o final, em ordem."""
    caminho: list[Direcao] = []
    atual = estado_final
    while atual in came_from:
        anterior, direcao = came_from[atual]
        caminho.append(direcao)
        atual = anterior
    caminho.reverse()
    return caminho
