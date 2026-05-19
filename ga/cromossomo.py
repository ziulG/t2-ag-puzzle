"""Cromossomo: representação binária de uma sequência de movimentos.

Módulo base do ``ga/``. Um cromossomo é uma lista de bits (0/1). Cada
movimento ocupa 2 bits, decodificados em um código inteiro genérico 0..3
(``alto * 2 + baixo``). ``ga/`` não conhece o domínio: a tradução de código
para ``Direcao`` acontece no bridge de fitness, fora deste pacote.
"""

import random

Cromossomo = list[int]            # bits 0/1; comprimento = 2 * número de movimentos

BITS_POR_MOVIMENTO: int = 2


def cromossomo_aleatorio(tamanho_cromossomo: int, rng: random.Random) -> Cromossomo:
    """Gera um cromossomo de bits aleatórios.

    ``tamanho_cromossomo`` é o número de movimentos; o comprimento em bits é
    ``BITS_POR_MOVIMENTO * tamanho_cromossomo``.
    """
    return [
        rng.randint(0, 1)
        for _ in range(BITS_POR_MOVIMENTO * tamanho_cromossomo)
    ]


def decode(cromossomo: Cromossomo) -> list[int]:
    """Decodifica pares de bits em códigos inteiros de direção (0..3).

    Cada par ``(bit_alto, bit_baixo)`` vira ``bit_alto * 2 + bit_baixo``.
    Retorna ``list[int]`` genérico (NÃO ``Direcao``) para manter ``ga/`` puro.
    """
    return [
        cromossomo[i] * 2 + cromossomo[i + 1]
        for i in range(0, len(cromossomo), BITS_POR_MOVIMENTO)
    ]


def encode(codigos: list[int]) -> Cromossomo:
    """Codifica códigos inteiros de direção (0..3) em pares de bits.

    Inverso de :func:`decode` (roundtrip). ``c -> [c >> 1, c & 1]``.
    """
    return [bit for codigo in codigos for bit in (codigo >> 1, codigo & 1)]


def cromossomo_valido(cromossomo: Cromossomo, tamanho_cromossomo: int) -> bool:
    """True se todos os elementos ∈ {0,1} e o comprimento é o esperado."""
    return (
        len(cromossomo) == BITS_POR_MOVIMENTO * tamanho_cromossomo
        and all(bit in (0, 1) for bit in cromossomo)
    )
