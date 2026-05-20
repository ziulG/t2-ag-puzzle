"""Casos de teste padrão para a Fase 3 (fácil / médio / difícil).

Cada caso é um estado solúvel do 8-puzzle com profundidade ótima ANOTADA. A
profundidade é calculada via :func:`distancia_otima` (BFS) no momento da
importação do módulo — então os valores no `__post_init__` servem só para
documentação humana; o valor que vai pros experimentos vem do BFS.

Os estados são gerados por :func:`random_walk_reverso` a partir do GOAL com
seeds fixas. O sweep que escolheu as seeds está em `analise_otima.py` (basta
chamar com ``evitar_reverso=True``); estas seeds foram selecionadas porque
produzem walks cuja profundidade ótima coincide exatamente com o número de
passos pedido:

- Fácil (5 mov, seed=0) — qualquer seed dá 5 (distrib. 100%).
- Médio (15 mov, seed=0) — 83% das seeds dão 15.
- Difícil (25 mov, seed=30) — 4% das seeds dão 25; 30 foi a primeira.
"""

from dataclasses import dataclass

from puzzle.estado import Estado
from puzzle.heuristicas import distancia_manhattan, eh_soluvel

from experiment.analise_otima import distancia_otima, random_walk_reverso


@dataclass(frozen=True)
class CasoTeste:
    """Um caso de teste anotado para experimentos do AG."""

    nome: str
    estado_inicial: Estado
    optimal_depth: int                            # profundidade ótima (BFS) até o GOAL
    manhattan_inicial: int
    descricao: str


def _construir(
    nome: str, passos: int, seed: int, descricao: str
) -> CasoTeste:
    """Gera o estado pelo walk reverso e anota optimal_depth via BFS."""
    estado = random_walk_reverso(passos, seed, evitar_reverso=True)
    assert eh_soluvel(estado), f"caso '{nome}' não é solúvel: {estado}"
    return CasoTeste(
        nome=nome,
        estado_inicial=estado,
        optimal_depth=distancia_otima(estado),
        manhattan_inicial=distancia_manhattan(estado),
        descricao=descricao,
    )


CASOS_PADRAO: list[CasoTeste] = [
    _construir(
        "facil",
        passos=5,
        seed=0,
        descricao="5 movimentos do GOAL (random walk reverso)",
    ),
    _construir(
        "medio",
        passos=15,
        seed=0,
        descricao="15 movimentos do GOAL (random walk reverso)",
    ),
    _construir(
        "dificil",
        passos=25,
        seed=30,
        descricao="25 movimentos do GOAL (random walk reverso)",
    ),
]
