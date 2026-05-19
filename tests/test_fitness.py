"""Testes unitários do bridge ``fitness.py`` (Fase 3 — composto).

Cobertura:
- Contagem de ``movimentos_invalidos`` em :func:`decodifica_solucao`.
- Parada no GOAL (``break`` quando ``eh_objetivo(estado)``).
- Fórmula exata de :func:`cria_fitness` (sem e com bônus).
- Helper :func:`fitness_objetivo_resolveu`.
"""

import pytest

from config import GAConfig
from fitness import (
    cria_fitness,
    decodifica_solucao,
    fitness_objetivo_resolveu,
)
from ga.cromossomo import encode
from puzzle.goal import GOAL
from puzzle.heuristicas import distancia_manhattan
from puzzle.movimentos import Direcao


def test_decodifica_conta_movimentos_invalidos() -> None:
    """Movimentos que não alteram o estado entram em ``movimentos_invalidos``."""
    cfg = GAConfig(tamanho_cromossomo=2)
    # Vazio no canto sup. esquerdo (pos 0): CIMA e ESQUERDA são inválidos.
    estado = (0, 1, 2, 3, 4, 5, 6, 7, 8)
    cromo = encode([int(Direcao.CIMA), int(Direcao.ESQUERDA)])

    sol = decodifica_solucao(estado, cromo, cfg)

    assert sol.movimentos_invalidos == 2
    assert sol.estado_final == estado            # nada mudou
    assert sol.resolveu is False
    assert sol.melhor_manhattan == distancia_manhattan(estado)
    assert sol.passos_ate_melhor == 0


def test_decodifica_para_no_goal() -> None:
    """A simulação interrompe assim que atinge o GOAL: movimentos posteriores são ignorados."""
    cfg = GAConfig(tamanho_cromossomo=10)
    estado = (1, 2, 3, 4, 5, 6, 0, 7, 8)         # 2 movimentos do GOAL
    cromo = encode([int(Direcao.DIREITA), int(Direcao.DIREITA)] + [0] * 8)

    sol = decodifica_solucao(estado, cromo, cfg)

    assert sol.resolveu is True
    assert sol.estado_final == GOAL
    assert len(sol.movimentos) == 2              # parou no GOAL
    assert sol.passos_ate_melhor == 2
    assert sol.movimentos_invalidos == 0
    assert sol.melhor_manhattan == 0


def test_decodifica_estado_inicial_eh_goal() -> None:
    """Se o estado inicial já é o GOAL, ``resolveu=True`` e nada é simulado."""
    cfg = GAConfig(tamanho_cromossomo=5)
    cromo = encode([0] * 5)

    sol = decodifica_solucao(GOAL, cromo, cfg)

    assert sol.resolveu is True
    assert sol.movimentos == []
    assert sol.movimentos_invalidos == 0
    assert sol.passos_ate_melhor == 0
    assert sol.estado_final == GOAL


def test_fitness_composto_formula_exata_sem_resolver() -> None:
    """Sem resolver: ``fitness = max_score - manhattan - α·invalidos - β·passos``."""
    cfg = GAConfig(
        tamanho_cromossomo=3,
        max_score=100.0,
        alfa_invalidos=2.0,
        beta_comprimento=0.5,
        bonus_resolveu=1000.0,
    )
    estado = (0, 1, 2, 3, 4, 5, 6, 7, 8)         # vazio no canto sup. esq.
    cromo = encode([int(Direcao.CIMA)] * 3)      # 3 inválidos consecutivos

    f = cria_fitness(estado, cfg)(cromo)

    # melhor_manhattan = manhattan_inicial (nada melhorou)
    # invalidos = 3, passos_ate_melhor = 0, resolveu = False
    esperado = 100.0 - distancia_manhattan(estado) - 2.0 * 3 - 0.5 * 0
    assert f == pytest.approx(esperado)


def test_fitness_composto_formula_exata_com_bonus() -> None:
    """Resolvendo: ``fitness = max_score - 0 - α·invalidos - β·passos + bonus_resolveu``."""
    cfg = GAConfig(
        tamanho_cromossomo=5,
        max_score=100.0,
        alfa_invalidos=2.0,
        beta_comprimento=0.5,
        bonus_resolveu=1000.0,
    )
    estado = (1, 2, 3, 4, 5, 6, 0, 7, 8)         # 2 mov do GOAL
    cromo = encode([int(Direcao.DIREITA), int(Direcao.DIREITA), 0, 0, 0])

    f = cria_fitness(estado, cfg)(cromo)

    # melhor_manhattan = 0, invalidos = 0, passos = 2, resolveu = True
    esperado = 100.0 - 0 - 0 - 0.5 * 2 + 1000.0
    assert f == pytest.approx(esperado)


def test_fitness_composto_combina_invalidos_e_resolver() -> None:
    """Cromossomo que tem inválidos no caminho mas resolve aplica ambas: penalidade + bônus."""
    cfg = GAConfig(
        tamanho_cromossomo=5,
        max_score=100.0,
        alfa_invalidos=2.0,
        beta_comprimento=0.5,
        bonus_resolveu=1000.0,
    )
    estado = (1, 2, 3, 4, 5, 6, 0, 7, 8)
    # ESQUERDA (inválida — vazio na pos 6, col 0), depois DIREITA, DIREITA resolve.
    cromo = encode(
        [int(Direcao.ESQUERDA), int(Direcao.DIREITA), int(Direcao.DIREITA), 0, 0]
    )

    sol = decodifica_solucao(estado, cromo, cfg)
    assert sol.resolveu is True
    assert sol.movimentos_invalidos == 1
    assert sol.passos_ate_melhor == 3

    f = cria_fitness(estado, cfg)(cromo)
    esperado = 100.0 - 0 - 2.0 * 1 - 0.5 * 3 + 1000.0
    assert f == pytest.approx(esperado)


def test_fitness_objetivo_resolveu_helper() -> None:
    """``fitness_objetivo_resolveu`` = ``max_score + bonus_resolveu / 2``."""
    cfg_default = GAConfig()
    assert fitness_objetivo_resolveu(cfg_default) == pytest.approx(100.0 + 500.0)

    cfg = GAConfig(max_score=50.0, bonus_resolveu=400.0)
    assert fitness_objetivo_resolveu(cfg) == pytest.approx(50.0 + 200.0)


def test_fitness_objetivo_resolveu_e_alcancavel_apenas_resolvendo() -> None:
    """O limiar separa nitidamente fitness com bônus de fitness sem bônus.

    Mesmo com penalidades máximas (todos os passos do cromossomo), o fitness
    com bônus deve ficar > limiar; sem bônus deve ficar < limiar.
    """
    cfg = GAConfig()                              # defaults do roadmap
    limiar = fitness_objetivo_resolveu(cfg)

    # Pior caso COM bônus: Manhattan máximo (~30 no 8-puzzle), todos passos contam,
    # todos os passos foram inválidos.
    pior_com_bonus = (
        cfg.max_score
        - 30
        - cfg.alfa_invalidos * cfg.tamanho_cromossomo
        - cfg.beta_comprimento * cfg.tamanho_cromossomo
        + cfg.bonus_resolveu
    )
    melhor_sem_bonus = cfg.max_score              # cromossomo "no GOAL desde o início" sem bônus é impossível, mas é o teto

    assert pior_com_bonus > limiar
    assert melhor_sem_bonus < limiar
