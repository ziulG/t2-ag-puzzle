"""Representação do estado do 8-puzzle e utilidades de geometria.

O estado é uma tupla imutável de 9 inteiros: as peças ``1..8`` e o ``0`` para o
espaço vazio. Tupla (e não lista) porque é imutável e hasheável — impede
mutação acidental e permite detectar ciclos e cachear estados nas fases do AG.
"""

Estado = tuple[int, ...]

LADO: int = 3
N: int = LADO * LADO


def posicao_vazio(estado: Estado) -> int:
    """Retorna o índice (0..8) do espaço vazio (``0``) no estado."""
    return estado.index(0)


def linha(indice: int) -> int:
    """Linha (0..2) de um índice 0..8 no tabuleiro 3x3."""
    return indice // LADO


def coluna(indice: int) -> int:
    """Coluna (0..2) de um índice 0..8 no tabuleiro 3x3."""
    return indice % LADO
