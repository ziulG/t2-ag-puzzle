"""Operadores de crossover: um-ponto e uniforme, mais o dispatcher.

``aplicar_crossover`` recebe o ``TipoCrossover`` de ``config`` (módulo neutro):
``ga.crossover -> config`` não cria ciclo nem viola a Regra de Ouro (a regra
proíbe ``ga/ -> puzzle/``). Nenhum operador muta os pais.
"""

import random

from config import TipoCrossover
from ga.cromossomo import Cromossomo


def crossover_um_ponto(
    pai1: Cromossomo,
    pai2: Cromossomo,
    rng: random.Random,
) -> tuple[Cromossomo, Cromossomo]:
    """Crossover de um ponto. Corte ``p`` em ``[1, L-1]``.

    ``filho1 = pai1[:p] + pai2[p:]`` ; ``filho2 = pai2[:p] + pai1[p:]``.
    """
    ponto = rng.randint(1, len(pai1) - 1)
    filho1 = pai1[:ponto] + pai2[ponto:]
    filho2 = pai2[:ponto] + pai1[ponto:]
    return filho1, filho2


def crossover_uniforme(
    pai1: Cromossomo,
    pai2: Cromossomo,
    rng: random.Random,
) -> tuple[Cromossomo, Cromossomo]:
    """Crossover uniforme: para cada bit, 50/50 de qual pai herda.

    ``filho2`` recebe sempre o bit do pai NÃO escolhido por ``filho1`` naquela
    posição (filhos complementares quanto à origem).
    """
    filho1: Cromossomo = []
    filho2: Cromossomo = []
    for bit1, bit2 in zip(pai1, pai2):
        if rng.random() < 0.5:
            filho1.append(bit1)
            filho2.append(bit2)
        else:
            filho1.append(bit2)
            filho2.append(bit1)
    return filho1, filho2


def aplicar_crossover(
    pai1: Cromossomo,
    pai2: Cromossomo,
    tipo: TipoCrossover,
    taxa_crossover: float,
    rng: random.Random,
) -> tuple[Cromossomo, Cromossomo]:
    """Aplica crossover com probabilidade ``taxa_crossover``.

    Se ``rng.random() >= taxa_crossover``, devolve CÓPIAS dos pais (objetos
    distintos). Caso contrário despacha pelo ``tipo``.
    """
    if rng.random() >= taxa_crossover:
        return list(pai1), list(pai2)
    if tipo is TipoCrossover.UM_PONTO:
        return crossover_um_ponto(pai1, pai2, rng)
    return crossover_uniforme(pai1, pai2, rng)
