"""Bridge entre o puzzle e o motor de AG (único acoplador ``puzzle/``↔``ga/``).

Vive na raiz, fora de ``ga/``, para preservar a Regra de Ouro: ``ga/`` nunca
importa ``puzzle/``. Aqui o cromossomo (bits genéricos) é decodificado em
``Direcao`` e simulado no puzzle.

Fitness da Fase 3 — COMPOSTO::

    fitness = max_score
            - melhor_manhattan
            - α × movimentos_invalidos
            - β × passos_ate_melhor
            + (bonus_resolveu  se resolveu, senão 0)

Coeficientes α, β, ``max_score`` e ``bonus_resolveu`` vêm do :class:`GAConfig`.
A simulação rastreia o MELHOR estado intermediário (menor Manhattan) e PARA na
primeira vez que toca o GOAL — movimentos posteriores ao GOAL não mudam o
melhor_manhattan (já é 0) e seriam contagem inútil.
"""

from collections.abc import Callable
from dataclasses import dataclass

from config import GAConfig
from ga.cromossomo import Cromossomo, decode
from puzzle.estado import Estado
from puzzle.movimentos import Direcao, aplicar_movimento
from puzzle.heuristicas import distancia_manhattan
from puzzle.goal import eh_objetivo


@dataclass
class SolucaoPuzzle:
    """Resultado de decodificar + simular um cromossomo no puzzle."""

    movimentos: list[Direcao]      # sequência decodificada efetivamente percorrida
    estado_final: Estado           # estado após o último movimento simulado
    melhor_estado: Estado          # estado de menor Manhattan na trajetória
    melhor_manhattan: int
    passos_ate_melhor: int         # índice 1-based do passo que alcançou o melhor (0 se inicial)
    movimentos_invalidos: int      # nº de aplicações que não mudaram o estado
    resolveu: bool                 # algum estado da trajetória == GOAL


def decodifica_solucao(
    estado_inicial: Estado,
    cromossomo: Cromossomo,
    config: GAConfig,
) -> SolucaoPuzzle:
    """Decodifica o cromossomo e simula a trajetória no puzzle.

    ``decode`` (ga puro) → ``Direcao(codigo)`` (IntEnum) → ``aplicar_movimento``.
    Movimento inválido devolve o MESMO objeto (identidade): detectamos via
    ``novo_estado is estado`` e contabilizamos em ``movimentos_invalidos``.
    A simulação PARA na primeira vez que o estado atinge o GOAL — os
    ``movimentos`` retornados refletem apenas os passos efetivamente executados.
    """
    todas = [Direcao(codigo) for codigo in decode(cromossomo)]

    estado = estado_inicial
    melhor_estado = estado_inicial
    melhor_manhattan = distancia_manhattan(estado_inicial)
    passos_ate_melhor = 0
    movimentos_invalidos = 0
    resolveu = eh_objetivo(estado_inicial)
    executados: list[Direcao] = []

    if not resolveu:
        for passo, direcao in enumerate(todas, start=1):
            novo_estado = aplicar_movimento(estado, direcao)
            if novo_estado is estado:
                movimentos_invalidos += 1
            estado = novo_estado
            executados.append(direcao)

            manhattan = distancia_manhattan(estado)
            if manhattan < melhor_manhattan:
                melhor_estado = estado
                melhor_manhattan = manhattan
                passos_ate_melhor = passo

            if eh_objetivo(estado):
                resolveu = True
                break

    return SolucaoPuzzle(
        movimentos=executados,
        estado_final=estado,
        melhor_estado=melhor_estado,
        melhor_manhattan=melhor_manhattan,
        passos_ate_melhor=passos_ate_melhor,
        movimentos_invalidos=movimentos_invalidos,
        resolveu=resolveu,
    )


def cria_fitness(
    estado_inicial: Estado,
    config: GAConfig,
) -> Callable[[Cromossomo], float]:
    """Fábrica do callable de fitness COMPOSTO da Fase 3.

    Aplica a fórmula:
        ``max_score - melhor_manhattan - α·invalidos - β·passos + (bonus se resolveu)``

    Reaproveita :func:`decodifica_solucao` (fonte única da simulação).
    """

    def fitness(cromossomo: Cromossomo) -> float:
        solucao = decodifica_solucao(estado_inicial, cromossomo, config)
        score = (
            config.max_score
            - solucao.melhor_manhattan
            - config.alfa_invalidos * solucao.movimentos_invalidos
            - config.beta_comprimento * solucao.passos_ate_melhor
        )
        if solucao.resolveu:
            score += config.bonus_resolveu
        return score

    return fitness


def fitness_objetivo_resolveu(config: GAConfig) -> float:
    """Threshold de parada do engine que dispara APENAS quando o cromossomo resolveu.

    Com os defaults do roadmap (max_score=100, bonus=1000), o limiar fica em
    600. O melhor fitness possível sem bônus é ``max_score`` (cromossomo já no
    GOAL); o pior fitness COM bônus, ainda com todas as penalidades máximas, é
    da ordem de ``max_score + bonus/2``. O limiar separa nitidamente os dois
    regimes — o critério "fitness_objetivo" do engine só dispara quando o
    bônus foi aplicado.
    """
    return config.max_score + config.bonus_resolveu / 2
