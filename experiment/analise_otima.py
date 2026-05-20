"""Ferramentas analíticas sobre o espaço de estados do 8-puzzle.

Vive em ``experiment/`` (não em ``puzzle/``) porque é instrumento de análise
para o relatório/experimentação — não faz parte do domínio do puzzle propriamente
dito. Usa apenas o domínio (``puzzle/``); não importa nem o motor de AG
(``ga/``) nem o bridge de fitness (``fitness.py``).

Conteúdo:
- :func:`distancia_otima` — BFS sobre o grafo de estados, devolve a profundidade
  mínima do estado até o GOAL. No 8-puzzle o espaço solúvel tem 181 440 estados
  com profundidade máxima 31, então BFS termina em ~1-2 s mesmo no pior caso.
- :func:`random_walk_reverso` — aplica ``passos`` movimentos aleatórios a partir
  do GOAL (determinístico via ``seed``). O estado resultante é solúvel por
  construção, com profundidade ÓTIMA ≤ ``passos`` (pode ser menor por
  revisitação durante o walk).
"""

import random
from collections import deque

from puzzle.estado import Estado
from puzzle.goal import GOAL, eh_objetivo
from puzzle.movimentos import aplicar_movimento, movimentos_validos


def distancia_otima(estado: Estado) -> int:
    """Profundidade mínima (BFS) de ``estado`` até o GOAL.

    Levanta ``ValueError`` se o estado for insolúvel (BFS esgota a componente
    conexa sem encontrar o GOAL).
    """
    if eh_objetivo(estado):
        return 0

    fila: deque[tuple[Estado, int]] = deque([(estado, 0)])
    visitados: set[Estado] = {estado}

    while fila:
        atual, dist = fila.popleft()
        proxima_dist = dist + 1
        for direcao in movimentos_validos(atual):
            vizinho = aplicar_movimento(atual, direcao)
            if vizinho in visitados:
                continue
            if eh_objetivo(vizinho):
                return proxima_dist
            visitados.add(vizinho)
            fila.append((vizinho, proxima_dist))

    raise ValueError(f"Estado insolúvel: {estado}")


def random_walk_reverso(
    passos: int, seed: int, evitar_reverso: bool = True
) -> Estado:
    """Aplica ``passos`` movimentos válidos aleatórios a partir do GOAL.

    O estado resultante é solúvel por construção (movimentos preservam a
    paridade de inversões). A profundidade ótima até o GOAL é ≤ ``passos``;
    pode ser estritamente menor se o walk revisitar estados.

    Se ``evitar_reverso=True`` (default), o walk não escolhe um movimento que
    volte imediatamente para o estado anterior — isso aproxima muito a
    profundidade real do número de passos solicitado, embora ainda possa
    haver revisitações de ciclo longo.

    Determinístico: a mesma combinação ``(passos, seed, evitar_reverso)``
    sempre devolve o mesmo estado.
    """
    if passos < 0:
        raise ValueError("passos deve ser >= 0")
    rng = random.Random(seed)
    estado: Estado = GOAL
    estado_anterior: Estado | None = None
    for _ in range(passos):
        candidatos = [
            direcao for direcao in movimentos_validos(estado)
            if not (
                evitar_reverso
                and estado_anterior is not None
                and aplicar_movimento(estado, direcao) == estado_anterior
            )
        ]
        if not candidatos:                       # canto degenerado: usa todos os válidos
            candidatos = movimentos_validos(estado)
        direcao = rng.choice(candidatos)
        estado_anterior = estado
        estado = aplicar_movimento(estado, direcao)
    return estado
