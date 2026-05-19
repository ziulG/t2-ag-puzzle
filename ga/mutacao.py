"""Mutação: bit flip por probabilidade.

Retorna SEMPRE uma nova lista (nunca muta a entrada). Com taxa 0.0 a saída é
idêntica em valor à entrada; com taxa 1.0 todo bit é invertido.
"""

import random

from ga.cromossomo import Cromossomo


def mutacao(
    cromossomo: Cromossomo,
    taxa_mutacao: float,
    rng: random.Random,
) -> Cromossomo:
    """Cada bit inverte (``0<->1``) com probabilidade ``taxa_mutacao``."""
    return [
        (1 - bit) if rng.random() < taxa_mutacao else bit
        for bit in cromossomo
    ]
