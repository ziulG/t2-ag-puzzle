"""Elitismo: preservação dos melhores indivíduos.

Extrai os ``N`` melhores cromossomos como CÓPIAS, antes de gerar os filhos —
sem elitismo o AG perde solução boa por azar de sorteio.
"""

from ga.cromossomo import Cromossomo
from ga.populacao import Individuo


def extrai_elite(
    avaliados: list[Individuo],
    tamanho_elite: int,
) -> list[Cromossomo]:
    """Retorna os ``tamanho_elite`` melhores cromossomos como CÓPIAS.

    Ordena por fitness desc e pega os N primeiros. ``tamanho_elite <= 0`` →
    ``[]``; satura naturalmente em ``len(avaliados)`` (fatiamento).
    """
    ordenados = sorted(avaliados, key=lambda par: par[1], reverse=True)
    return [
        list(cromossomo)
        for cromossomo, _ in ordenados[: max(0, tamanho_elite)]
    ]
