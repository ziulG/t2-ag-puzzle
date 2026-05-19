"""Direções, validação e aplicação de movimentos no 8-puzzle.

Cada direção move o **espaço vazio** naquele sentido (a peça vizinha ocupa o
lugar que era do vazio). O valor inteiro de cada direção é o encoding de 2 bits
reaproveitado pela codificação do cromossomo nas fases do AG.
"""

from enum import IntEnum

from puzzle.estado import LADO, Estado, coluna, linha, posicao_vazio


class Direcao(IntEnum):
    """Direção do movimento do espaço vazio (encoding de 2 bits)."""

    CIMA = 0      # 00
    BAIXO = 1     # 01
    ESQUERDA = 2  # 10
    DIREITA = 3   # 11


_DELTA: dict[Direcao, int] = {
    Direcao.CIMA: -LADO,
    Direcao.BAIXO: LADO,
    Direcao.ESQUERDA: -1,
    Direcao.DIREITA: 1,
}


def movimentos_validos(estado: Estado) -> list[Direcao]:
    """Direções válidas (em ordem de enum) para o estado dado.

    Uma direção é válida quando mover o vazio naquele sentido não sai do
    tabuleiro 3x3.
    """
    pos = posicao_vazio(estado)
    l, c = linha(pos), coluna(pos)
    validos: list[Direcao] = []
    if l > 0:
        validos.append(Direcao.CIMA)
    if l < LADO - 1:
        validos.append(Direcao.BAIXO)
    if c > 0:
        validos.append(Direcao.ESQUERDA)
    if c < LADO - 1:
        validos.append(Direcao.DIREITA)
    return validos


def aplicar_movimento(estado: Estado, direcao: Direcao) -> Estado:
    """Aplica a direção movendo o vazio.

    Em movimento válido devolve uma nova tupla; em movimento inválido devolve
    o próprio objeto recebido. Nunca muta a entrada.
    """
    if direcao not in movimentos_validos(estado):
        return estado
    pos = posicao_vazio(estado)
    alvo = pos + _DELTA[direcao]
    pecas = list(estado)
    pecas[pos], pecas[alvo] = pecas[alvo], pecas[pos]
    return tuple(pecas)
