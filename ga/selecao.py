"""Operadores de seleção: torneio e roleta.

Cada operador recebe a população avaliada (pares ``(cromossomo, fitness)``) e
devolve UM cromossomo (um pai). O engine chama duas vezes por casal.
"""

import random

from ga.cromossomo import Cromossomo
from ga.populacao import Individuo


def torneio(
    avaliados: list[Individuo],
    rng: random.Random,
    tamanho_torneio: int,
) -> Cromossomo:
    """Seleção por torneio SEM reposição. Retorna o cromossomo vencedor.

    Sorteia ``min(tamanho_torneio, len(avaliados))`` indivíduos via
    ``rng.sample`` (sem reposição) e devolve o de maior fitness. Sem reposição:
    evita o mesmo indivíduo competir contra si próprio e garante que, quando
    ``k >= |população|``, todos competem (comportamento exigido pelo teste
    estatístico do roadmap).
    """
    k = min(tamanho_torneio, len(avaliados))
    competidores = rng.sample(avaliados, k)
    melhor = max(competidores, key=lambda par: par[1])
    return melhor[0]


def roleta(avaliados: list[Individuo], rng: random.Random) -> Cromossomo:
    """Seleção por roleta proporcional ao fitness. Retorna um cromossomo.

    Normaliza para pesos sempre positivos: ``peso = f - min_f + 1``. Isso
    funciona mesmo com fitness negativo e nunca zera a soma dos pesos.
    """
    minimo = min(fitness for _, fitness in avaliados)
    pesos = [fitness - minimo + 1.0 for _, fitness in avaliados]
    cromossomos = [cromossomo for cromossomo, _ in avaliados]
    return rng.choices(cromossomos, weights=pesos, k=1)[0]
