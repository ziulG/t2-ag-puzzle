"""Loop principal do Algoritmo Genético.

Motor genérico: o ``fitness`` (e o ``fitness_objetivo``) são injetados. NÃO
importa ``puzzle/``. Reprodutível via ``random.Random(config.seed_aleatorio)``.
Critério de parada composto: ``max_geracoes`` | ``fitness_objetivo`` |
``estagnacao``.
"""

import random
import statistics
from collections.abc import Callable
from dataclasses import dataclass, field

from config import GAConfig, TipoSelecao
from ga.cromossomo import Cromossomo
from ga.populacao import populacao_inicial, avaliar_populacao
from ga.selecao import torneio, roleta
from ga.crossover import aplicar_crossover
from ga.mutacao import mutacao
from ga.elitismo import extrai_elite


@dataclass
class HistoricoGeracao:
    """Métricas de UMA geração."""

    geracao: int
    melhor_fitness: float
    fitness_medio: float
    diversidade: float            # statistics.pstdev dos fitness
    melhor_cromossomo: Cromossomo


@dataclass
class ResultadoAG:
    """Resultado final da execução (dados PUROS de GA)."""

    melhor_cromossomo: Cromossomo
    melhor_fitness: float
    criterio_parada: str          # "max_geracoes" | "fitness_objetivo" | "estagnacao"
    geracoes_executadas: int
    historico: list[HistoricoGeracao] = field(default_factory=list)


def executar_ag(
    config: GAConfig,
    fitness: Callable[[Cromossomo], float],
    fitness_objetivo: float,
) -> ResultadoAG:
    """Executa o AG e devolve o melhor indivíduo + histórico completo."""
    rng = random.Random(config.seed_aleatorio)

    populacao = populacao_inicial(
        config.tamanho_populacao, config.tamanho_cromossomo, rng
    )

    melhor_cromossomo_global: Cromossomo | None = None
    melhor_fitness_global = float("-inf")
    geracoes_sem_melhoria = 0
    historico: list[HistoricoGeracao] = []
    criterio = "max_geracoes"

    for geracao in range(config.max_geracoes):
        avaliados = avaliar_populacao(populacao, fitness)
        avaliados.sort(key=lambda par: par[1], reverse=True)

        fits = [f for _, f in avaliados]
        melhor_cromo_ger, melhor_fit_ger = avaliados[0]

        historico.append(
            HistoricoGeracao(
                geracao=geracao,
                melhor_fitness=melhor_fit_ger,
                fitness_medio=statistics.fmean(fits),
                diversidade=statistics.pstdev(fits) if len(fits) > 1 else 0.0,
                melhor_cromossomo=list(melhor_cromo_ger),
            )
        )

        if melhor_fit_ger > melhor_fitness_global:
            melhor_fitness_global = melhor_fit_ger
            melhor_cromossomo_global = list(melhor_cromo_ger)
            geracoes_sem_melhoria = 0
        else:
            geracoes_sem_melhoria += 1

        if melhor_fitness_global >= fitness_objetivo:
            criterio = "fitness_objetivo"
            break
        if geracoes_sem_melhoria >= config.sem_melhoria_limite:
            criterio = "estagnacao"
            break

        elite = extrai_elite(avaliados, config.tamanho_elite)
        vagas = config.tamanho_populacao - len(elite)
        filhos: list[Cromossomo] = []
        while len(filhos) < vagas:
            if config.tipo_selecao is TipoSelecao.TORNEIO:
                pai1 = torneio(avaliados, rng, config.tamanho_torneio)
                pai2 = torneio(avaliados, rng, config.tamanho_torneio)
            else:
                pai1 = roleta(avaliados, rng)
                pai2 = roleta(avaliados, rng)

            filho1, filho2 = aplicar_crossover(
                pai1, pai2, config.tipo_crossover, config.taxa_crossover, rng
            )

            filhos.append(mutacao(filho1, config.taxa_mutacao, rng))
            if len(filhos) < vagas:
                filhos.append(mutacao(filho2, config.taxa_mutacao, rng))

        populacao = elite + filhos
    else:
        criterio = "max_geracoes"

    return ResultadoAG(
        melhor_cromossomo=melhor_cromossomo_global,
        melhor_fitness=melhor_fitness_global,
        criterio_parada=criterio,
        geracoes_executadas=len(historico),
        historico=historico,
    )
