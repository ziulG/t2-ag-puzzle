"""Testes do domínio do 8-puzzle (Fase 1).

Cobre todas as operações exigidas no roadmap: posição do vazio, validade e
aplicação de movimentos, checagem de objetivo, heurísticas (Manhattan e
Hamming) e solvabilidade. Os 4 primeiros testes são os obrigatórios da Fase 6
do roadmap; os demais são casos de borda adicionais.
"""

from puzzle.estado import posicao_vazio
from puzzle.movimentos import Direcao, aplicar_movimento, movimentos_validos
from puzzle.goal import GOAL, eh_objetivo
from puzzle.heuristicas import (
    distancia_hamming,
    distancia_manhattan,
    eh_soluvel,
)

Estado = tuple[int, ...]

# Direções inválidas por posição do espaço vazio (tabela do roadmap, Fase 1).
INVALIDOS_POR_POSICAO: dict[int, set[Direcao]] = {
    0: {Direcao.CIMA, Direcao.ESQUERDA},
    1: {Direcao.CIMA},
    2: {Direcao.CIMA, Direcao.DIREITA},
    3: {Direcao.ESQUERDA},
    4: set(),
    5: {Direcao.DIREITA},
    6: {Direcao.BAIXO, Direcao.ESQUERDA},
    7: {Direcao.BAIXO},
    8: {Direcao.BAIXO, Direcao.DIREITA},
}

TODAS_DIRECOES: set[Direcao] = {
    Direcao.CIMA,
    Direcao.BAIXO,
    Direcao.ESQUERDA,
    Direcao.DIREITA,
}


def _estado_com_vazio_em(posicao: int) -> Estado:
    """Constrói um estado com o `0` na posição dada e peças 1..8 no resto.

    A validade de movimentos depende apenas de onde está o vazio, não dos
    valores das demais peças, então qualquer preenchimento serve.
    """
    pecas = iter(range(1, 9))
    return tuple(0 if i == posicao else next(pecas) for i in range(9))


# --------------------------------------------------------------------------- #
# Obrigatórios — Fase 6 do roadmap (seção "Puzzle (essencial)")
# --------------------------------------------------------------------------- #

def test_movimento_cima_em_centro() -> None:
    """Vazio no centro (índice 4): mover CIMA leva o vazio ao índice 1."""
    estado = (1, 2, 3, 4, 0, 5, 6, 7, 8)
    novo = aplicar_movimento(estado, Direcao.CIMA)
    assert novo == (1, 0, 3, 4, 2, 5, 6, 7, 8)


def test_movimento_invalido_nao_altera() -> None:
    """Vazio na borda superior: mover CIMA é inválido e não altera o estado."""
    estado = (0, 1, 2, 3, 4, 5, 6, 7, 8)
    novo = aplicar_movimento(estado, Direcao.CIMA)
    assert novo == estado


def test_solvabilidade() -> None:
    """GOAL é solúvel; uma única inversão (8↔7) torna o estado insolúvel."""
    assert eh_soluvel((1, 2, 3, 4, 5, 6, 7, 8, 0)) is True
    assert eh_soluvel((1, 2, 3, 4, 5, 6, 8, 7, 0)) is False


def test_manhattan_no_goal_eh_zero() -> None:
    """No estado objetivo, a distância de Manhattan é zero."""
    assert distancia_manhattan((1, 2, 3, 4, 5, 6, 7, 8, 0)) == 0


# --------------------------------------------------------------------------- #
# Casos de borda adicionais
# --------------------------------------------------------------------------- #

def test_posicao_vazio() -> None:
    """`posicao_vazio` localiza o índice do 0 em cantos e centro."""
    assert posicao_vazio((0, 1, 2, 3, 4, 5, 6, 7, 8)) == 0
    assert posicao_vazio((1, 2, 3, 4, 0, 5, 6, 7, 8)) == 4
    assert posicao_vazio((1, 2, 3, 4, 5, 6, 7, 8, 0)) == 8


def test_movimentos_validos_centro() -> None:
    """No centro todas as 4 direções são válidas, em ordem de enum."""
    estado = (1, 2, 3, 4, 0, 5, 6, 7, 8)
    assert movimentos_validos(estado) == [
        Direcao.CIMA,
        Direcao.BAIXO,
        Direcao.ESQUERDA,
        Direcao.DIREITA,
    ]


def test_movimentos_validos_todas_posicoes() -> None:
    """Para cada uma das 9 posições do vazio, os movimentos válidos batem
    exatamente com o complemento da tabela de inválidos do roadmap."""
    for posicao, invalidos in INVALIDOS_POR_POSICAO.items():
        estado = _estado_com_vazio_em(posicao)
        esperado = TODAS_DIRECOES - invalidos
        assert set(movimentos_validos(estado)) == esperado


def test_aplicar_cada_direcao_do_centro() -> None:
    """A partir do centro, cada direção troca o vazio com a peça correta."""
    estado = (1, 2, 3, 4, 0, 5, 6, 7, 8)
    assert aplicar_movimento(estado, Direcao.CIMA) == (1, 0, 3, 4, 2, 5, 6, 7, 8)
    assert aplicar_movimento(estado, Direcao.BAIXO) == (1, 2, 3, 4, 7, 5, 6, 0, 8)
    assert aplicar_movimento(estado, Direcao.ESQUERDA) == (1, 2, 3, 0, 4, 5, 6, 7, 8)
    assert aplicar_movimento(estado, Direcao.DIREITA) == (1, 2, 3, 4, 5, 0, 6, 7, 8)


def test_aplicar_invalido_em_cada_borda() -> None:
    """Qualquer movimento inválido (em qualquer posição) não altera o estado."""
    for posicao, invalidos in INVALIDOS_POR_POSICAO.items():
        estado = _estado_com_vazio_em(posicao)
        for direcao in invalidos:
            assert aplicar_movimento(estado, direcao) == estado


def test_aplicar_nao_muta_entrada() -> None:
    """Aplicar movimento não muta a entrada; movimento válido devolve nova
    tupla e movimento inválido devolve o próprio objeto recebido."""
    estado = (1, 2, 3, 4, 0, 5, 6, 7, 8)
    novo = aplicar_movimento(estado, Direcao.CIMA)
    assert estado == (1, 2, 3, 4, 0, 5, 6, 7, 8)
    assert isinstance(novo, tuple)
    assert novo != estado

    borda = (0, 1, 2, 3, 4, 5, 6, 7, 8)
    assert aplicar_movimento(borda, Direcao.CIMA) is borda


def test_eh_objetivo() -> None:
    """`eh_objetivo` é verdadeiro só para o GOAL exato."""
    assert eh_objetivo(GOAL) is True
    assert eh_objetivo((1, 2, 3, 4, 5, 6, 7, 0, 8)) is False


def test_manhattan_estado_conhecido() -> None:
    """Trocar as peças 1 e 2 custa 1+1 = 2 de distância de Manhattan."""
    assert distancia_manhattan((2, 1, 3, 4, 5, 6, 7, 8, 0)) == 2


def test_hamming_no_goal_eh_zero() -> None:
    """No estado objetivo, a distância de Hamming é zero."""
    assert distancia_hamming(GOAL) == 0


def test_hamming_estado_conhecido() -> None:
    """Com as peças 1 e 2 trocadas, 2 peças estão fora do lugar."""
    assert distancia_hamming((2, 1, 3, 4, 5, 6, 7, 8, 0)) == 2


def test_solvabilidade_varios() -> None:
    """Paridade de inversões decide a solvabilidade: 8 inversões (par) é
    solúvel; 1 inversão (ímpar) não é."""
    assert eh_soluvel((2, 5, 1, 0, 7, 4, 3, 6, 8)) is True
    assert eh_soluvel((2, 1, 3, 4, 5, 6, 7, 8, 0)) is False


def test_direcao_encoding_bits() -> None:
    """As direções têm os valores do encoding de 2 bits do roadmap (0..3),
    base para a codificação do cromossomo nas fases do AG."""
    assert int(Direcao.CIMA) == 0
    assert int(Direcao.BAIXO) == 1
    assert int(Direcao.ESQUERDA) == 2
    assert int(Direcao.DIREITA) == 3
    for direcao in Direcao:
        assert 0 <= int(direcao) <= 3
