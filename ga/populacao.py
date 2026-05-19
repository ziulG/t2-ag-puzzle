"""População: inicialização e avaliação em lote.

A função de fitness é injetada (``Callable``); ``populacao.py`` não conhece o
domínio do problema — não importa ``puzzle/``.
"""

import random
from collections.abc import Callable

from ga.cromossomo import Cromossomo, cromossomo_aleatorio

Individuo = tuple[Cromossomo, float]                       # (cromossomo, fitness)
FuncaoFitness = Callable[[Cromossomo], float]


def populacao_inicial(
    tamanho_populacao: int,
    tamanho_cromossomo: int,
    rng: random.Random,
) -> list[Cromossomo]:
    """Cria ``tamanho_populacao`` cromossomos de bits aleatórios."""
    return [
        cromossomo_aleatorio(tamanho_cromossomo, rng)
        for _ in range(tamanho_populacao)
    ]


def avaliar_populacao(
    populacao: list[Cromossomo],
    fitness: FuncaoFitness,
) -> list[Individuo]:
    """Avalia toda a população, retornando pares ``(cromossomo, float)``.

    Mantém a ordem da população recebida.
    """
    return [(cromossomo, float(fitness(cromossomo))) for cromossomo in populacao]
