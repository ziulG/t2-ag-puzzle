"""Heurísticas e solvabilidade do 8-puzzle.

- Manhattan: soma das distâncias de cada peça até sua casa-objetivo.
- Hamming: número de peças fora do lugar.
- Solvabilidade: paridade do número de inversões (válida para grade 3x3,
  de largura ímpar — solúvel se o número de inversões for par).
"""

from puzzle.estado import Estado, coluna, linha
from puzzle.goal import GOAL


def distancia_manhattan(estado: Estado) -> int:
    """Soma das distâncias de Manhattan de cada peça (ignora o vazio).

    A casa-objetivo da peça ``v`` é o índice ``v - 1``.
    """
    total = 0
    for indice, peca in enumerate(estado):
        if peca == 0:
            continue
        objetivo = peca - 1
        total += abs(linha(indice) - linha(objetivo))
        total += abs(coluna(indice) - coluna(objetivo))
    return total


def distancia_hamming(estado: Estado) -> int:
    """Número de peças fora do lugar (ignora o vazio)."""
    return sum(
        1
        for indice, peca in enumerate(estado)
        if peca != 0 and peca != GOAL[indice]
    )


def eh_soluvel(estado: Estado) -> bool:
    """True se o estado é solúvel: número de inversões par (grade 3x3).

    Conta inversões entre as peças, ignorando o ``0``.
    """
    pecas = [p for p in estado if p != 0]
    inversoes = sum(
        1
        for i in range(len(pecas))
        for j in range(i + 1, len(pecas))
        if pecas[i] > pecas[j]
    )
    return inversoes % 2 == 0
