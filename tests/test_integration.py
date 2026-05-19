"""Teste de integração ponta-a-ponta (Fase 3).

Roda o AG completo num puzzle solúvel próximo do GOAL via o bridge de
fitness (único acoplador puzzle/↔ga/). O teste end-to-end é @pytest.mark.slow.

Atualizado para a Fase 3: fitness composto (α inválidos, β passos, bônus resolver)
e parada por ``fitness_objetivo_resolveu`` em vez de ``max_score``.
"""

from dataclasses import replace

import pytest

from config import GAConfig
from fitness import (
    cria_fitness,
    decodifica_solucao,
    fitness_objetivo_resolveu,
    SolucaoPuzzle,
)
from ga.engine import executar_ag
from ga.cromossomo import encode
from puzzle.movimentos import Direcao
from puzzle.goal import GOAL, eh_objetivo
from puzzle.heuristicas import eh_soluvel, distancia_manhattan

# Estado solúvel a EXATAMENTE 5 movimentos do GOAL (BFS verificado).
# Solução ótima: BAIXO, DIREITA, CIMA, DIREITA, BAIXO.
ESTADO_INICIAL = (1, 2, 3, 0, 8, 5, 4, 7, 6)


def test_estado_inicial_eh_soluvel() -> None:
    """Pré-condição: o estado do teste é solúvel."""
    assert eh_soluvel(ESTADO_INICIAL) is True
    assert distancia_manhattan(ESTADO_INICIAL) == 5


def test_decodifica_solucao_otima_resolve() -> None:
    """Cromossomo que codifica a solução ótima resolve o puzzle.

    A simulação para no GOAL: ``sol.movimentos`` contém exatamente os 5 passos
    executados (não os 10 do cromossomo).
    """
    cfg = GAConfig(tamanho_cromossomo=10)
    otima = [Direcao.BAIXO, Direcao.DIREITA, Direcao.CIMA,
             Direcao.DIREITA, Direcao.BAIXO]
    codigos = [int(d) for d in otima] + [0] * (cfg.tamanho_cromossomo - len(otima))
    sol = decodifica_solucao(ESTADO_INICIAL, encode(codigos), cfg)
    assert isinstance(sol, SolucaoPuzzle)
    assert sol.resolveu is True
    assert sol.melhor_manhattan == 0
    assert eh_objetivo(sol.melhor_estado)
    assert sol.movimentos == otima
    assert sol.movimentos_invalidos == 0
    assert sol.passos_ate_melhor == 5


def test_fitness_composto_aplica_bonus_ao_resolver() -> None:
    """Fitness ao resolver = max_score - 0 - α·0 - β·passos + bonus."""
    cfg = GAConfig(
        tamanho_cromossomo=10,
        max_score=100.0,
        alfa_invalidos=2.0,
        beta_comprimento=0.5,
        bonus_resolveu=1000.0,
    )
    fitness = cria_fitness(ESTADO_INICIAL, cfg)
    codigos = [1, 3, 0, 3, 1] + [0] * 5          # solução ótima + padding
    # Esperado: 100 - 0 - 2·0 - 0.5·5 + 1000 = 1097.5
    assert fitness(encode(codigos)) == pytest.approx(1097.5)


def test_fitness_composto_penaliza_invalidos() -> None:
    """α > 0 penaliza fitness em cromossomos com inválidos vs. α=0."""
    cfg = GAConfig(
        tamanho_cromossomo=10,
        max_score=100.0,
        alfa_invalidos=2.0,
        beta_comprimento=0.0,
        bonus_resolveu=0.0,
    )
    cfg_sem_alfa = replace(cfg, alfa_invalidos=0.0)

    cromo = encode([0] * 10)                     # todos CIMA → muitos inválidos
    sol = decodifica_solucao(ESTADO_INICIAL, cromo, cfg)
    assert sol.movimentos_invalidos > 0          # garantia do cenário

    f_com_alfa = cria_fitness(ESTADO_INICIAL, cfg)(cromo)
    f_sem_alfa = cria_fitness(ESTADO_INICIAL, cfg_sem_alfa)(cromo)
    assert f_com_alfa == pytest.approx(
        f_sem_alfa - cfg.alfa_invalidos * sol.movimentos_invalidos
    )


def test_fitness_composto_penaliza_passos() -> None:
    """β > 0 penaliza fitness por passos_ate_melhor vs. β=0."""
    cfg = GAConfig(
        tamanho_cromossomo=10,
        max_score=100.0,
        alfa_invalidos=0.0,
        beta_comprimento=0.5,
        bonus_resolveu=0.0,                      # zerado pra isolar β
    )
    cfg_sem_beta = replace(cfg, beta_comprimento=0.0)

    cromo = encode([1, 3, 0, 3, 1] + [0] * 5)    # solução ótima → passos = 5
    sol = decodifica_solucao(ESTADO_INICIAL, cromo, cfg)
    assert sol.passos_ate_melhor == 5

    f_com_beta = cria_fitness(ESTADO_INICIAL, cfg)(cromo)
    f_sem_beta = cria_fitness(ESTADO_INICIAL, cfg_sem_beta)(cromo)
    assert f_com_beta == pytest.approx(
        f_sem_beta - cfg.beta_comprimento * sol.passos_ate_melhor
    )


@pytest.mark.slow
def test_ag_resolve_puzzle_facil_com_seed_fixa() -> None:
    """O AG resolve o puzzle (5 mov. do GOAL) dentro de 200 gerações.

    Config reduzida (pop=20, cromo=10) deliberada: com a config grande o AG
    resolveria na geração 0 por acaso e não exercitaria a evolução.
    Critério de parada usa ``fitness_objetivo_resolveu`` — só dispara quando o
    bônus foi aplicado (i.e., quando o cromossomo de fato resolveu o puzzle).
    """
    cfg = GAConfig(tamanho_populacao=20, tamanho_cromossomo=10,
                   max_geracoes=200, sem_melhoria_limite=200, seed_aleatorio=2)
    fitness = cria_fitness(ESTADO_INICIAL, cfg)
    resultado = executar_ag(cfg, fitness, fitness_objetivo_resolveu(cfg))

    assert resultado.criterio_parada == "fitness_objetivo"
    assert resultado.melhor_fitness >= fitness_objetivo_resolveu(cfg)
    assert len(resultado.historico) <= 200

    sol = decodifica_solucao(ESTADO_INICIAL, resultado.melhor_cromossomo, cfg)
    assert sol.resolveu is True
    assert sol.melhor_manhattan == 0
    assert eh_objetivo(sol.melhor_estado)
