"""Runner: executa UMA configuração com UMA seed em UM caso de teste.

Saída: ``RunResult`` (dataclass denso, picklable) com tudo que o relatório
precisa — métricas, histórico, melhor cromossomo decodificado e gap em
relação à profundidade ótima.
"""

import time
from dataclasses import dataclass, field, replace
from datetime import datetime

from config import GAConfig
from fitness import cria_fitness, decodifica_solucao, fitness_objetivo_resolveu
from ga.cromossomo import Cromossomo
from ga.engine import HistoricoGeracao, executar_ag
from puzzle.estado import Estado
from puzzle.movimentos import Direcao, aplicar_movimento

from experiment.casos_teste import CasoTeste


@dataclass
class RunResult:
    """Resultado completo de uma execução do AG em um caso de teste."""

    run_id: str
    timestamp: str

    # Caso
    caso_nome: str
    estado_inicial: Estado
    manhattan_inicial: int
    optimal_depth: int

    # Execução
    seed: int
    config: GAConfig

    # Métricas do AG
    resolveu: bool
    criterio_parada: str
    geracoes_executadas: int
    tempo_total_s: float
    melhor_fitness: float

    # Métricas da solução (do melhor cromossomo)
    manhattan_final: int
    passos_ate_melhor: int
    movimentos_invalidos: int
    tamanho_solucao_ag: int | None        # nº de movimentos válidos até resolver; None se não resolveu
    gap_otimo: int | None                 # tamanho_solucao_ag - optimal_depth; None se não resolveu

    # Detalhes (vão pro JSON)
    melhor_cromossomo: Cromossomo
    movimentos_decodificados: list[Direcao]              # sequência efetivamente simulada
    movimentos_validos_ate_resolver: list[Direcao]       # subset que de fato mudou o estado

    # Histórico (vai pro CSV de históricos)
    historico: list[HistoricoGeracao] = field(default_factory=list)


class Runner:
    """Encapsula uma execução isolada do AG em um caso de teste."""

    def __init__(self, config: GAConfig, caso: CasoTeste, seed: int):
        self.caso = caso
        self.seed = seed
        # Cópia do config com a seed injetada (não muta o original).
        self.config = replace(config, seed_aleatorio=seed)

    def run(self) -> RunResult:
        t0 = time.perf_counter()
        fitness_fn = cria_fitness(self.caso.estado_inicial, self.config)
        objetivo = fitness_objetivo_resolveu(self.config)
        resultado_ag = executar_ag(self.config, fitness_fn, objetivo)
        tempo_total_s = time.perf_counter() - t0

        solucao = decodifica_solucao(
            self.caso.estado_inicial,
            resultado_ag.melhor_cromossomo,
            self.config,
        )
        validos = _filtrar_movimentos_validos(
            self.caso.estado_inicial, solucao.movimentos
        )
        tamanho_solucao_ag = len(validos) if solucao.resolveu else None
        gap_otimo = (
            tamanho_solucao_ag - self.caso.optimal_depth
            if tamanho_solucao_ag is not None
            else None
        )

        return RunResult(
            run_id=gerar_run_id(self.caso.nome, self.config, self.seed),
            timestamp=datetime.now().isoformat(timespec="seconds"),
            caso_nome=self.caso.nome,
            estado_inicial=self.caso.estado_inicial,
            manhattan_inicial=self.caso.manhattan_inicial,
            optimal_depth=self.caso.optimal_depth,
            seed=self.seed,
            config=self.config,
            resolveu=solucao.resolveu,
            criterio_parada=resultado_ag.criterio_parada,
            geracoes_executadas=resultado_ag.geracoes_executadas,
            tempo_total_s=tempo_total_s,
            melhor_fitness=resultado_ag.melhor_fitness,
            manhattan_final=solucao.melhor_manhattan,
            passos_ate_melhor=solucao.passos_ate_melhor,
            movimentos_invalidos=solucao.movimentos_invalidos,
            tamanho_solucao_ag=tamanho_solucao_ag,
            gap_otimo=gap_otimo,
            melhor_cromossomo=list(resultado_ag.melhor_cromossomo),
            movimentos_decodificados=list(solucao.movimentos),
            movimentos_validos_ate_resolver=validos,
            historico=list(resultado_ag.historico),
        )


def gerar_run_id(caso_nome: str, config: GAConfig, seed: int) -> str:
    """ID legível e determinístico para uma execução.

    Padrão: ``"{caso}-sel{tor|rol}-cx{um|uni}-pm{NNN}-seed{NN}"`` — ex.:
    ``"medio-seltor-cxum-pm005-seed03"``. O sufixo ``cx`` garante unicidade
    quando a matriz varia também o crossover (matriz estendida).
    """
    sel = config.tipo_selecao.value[:3]
    cx = "um" if config.tipo_crossover.value == "um_ponto" else "uni"
    pm = int(round(config.taxa_mutacao * 100))
    return f"{caso_nome}-sel{sel}-cx{cx}-pm{pm:03d}-seed{seed:02d}"


def _filtrar_movimentos_validos(
    estado_inicial: Estado, sequencia: list[Direcao]
) -> list[Direcao]:
    """Re-simula a sequência e devolve apenas os movimentos que alteraram o estado."""
    estado = estado_inicial
    validos: list[Direcao] = []
    for direcao in sequencia:
        novo = aplicar_movimento(estado, direcao)
        if novo is not estado:
            validos.append(direcao)
            estado = novo
    return validos
