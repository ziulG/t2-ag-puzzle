"""Batch runner: roda o produto cartesiano (configs × casos × seeds) em paralelo.

Default: paralelo via ``multiprocessing.Pool(spawn)`` com ``imap_unordered`` e
barra de progresso ``tqdm``. ``run(paralelo=False)`` força execução sequencial
(útil para debug e profiling).

Cada task é uma tupla ``(GAConfig, CasoTeste, seed)`` picklável (dataclasses +
tupla + int). O worker reside em escopo de módulo (``_executar_task``) para
funcionar com ``spawn``.
"""

import multiprocessing as mp
import os
from typing import Iterable

from tqdm import tqdm

from config import GAConfig

from experiment.casos_teste import CasoTeste
from experiment.runner import RunResult, Runner


def _executar_task(args: tuple[GAConfig, CasoTeste, int]) -> RunResult:
    """Worker top-level (picklável) para ``multiprocessing``."""
    config, caso, seed = args
    return Runner(config, caso, seed).run()


class BatchRunner:
    """Executa o produto cartesiano de ``configs × casos × seeds``."""

    def __init__(
        self,
        configs: Iterable[GAConfig],
        casos: Iterable[CasoTeste],
        seeds: Iterable[int],
        processos: int | None = None,
    ) -> None:
        self.configs: list[GAConfig] = list(configs)
        self.casos: list[CasoTeste] = list(casos)
        self.seeds: list[int] = list(seeds)
        self.processos = processos if processos is not None else (os.cpu_count() or 1)

    def gerar_tasks(self) -> list[tuple[GAConfig, CasoTeste, int]]:
        """Produto cartesiano de configs × casos × seeds, em ordem natural."""
        return [
            (cfg, caso, seed)
            for cfg in self.configs
            for caso in self.casos
            for seed in self.seeds
        ]

    def run(self, paralelo: bool = True) -> list[RunResult]:
        """Executa todas as tasks; ordena o resultado por (caso, seleção, mutação, seed).

        Em paralelo: usa ``mp.get_context("spawn")`` (portável macOS/Linux) com
        ``imap_unordered`` para devolver resultados conforme finalizam — a
        ordenação é feita ao final para CSV determinístico.
        """
        tasks = self.gerar_tasks()
        total = len(tasks)
        resultados: list[RunResult] = []

        usar_paralelo = paralelo and self.processos > 1 and total > 1
        descricao = f"Batch ({'paralelo' if usar_paralelo else 'sequencial'})"

        if usar_paralelo:
            ctx = mp.get_context("spawn")
            with ctx.Pool(processes=self.processos) as pool:
                iterador = pool.imap_unordered(_executar_task, tasks)
                for r in tqdm(iterador, total=total, desc=descricao):
                    resultados.append(r)
        else:
            for t in tqdm(tasks, total=total, desc=descricao):
                resultados.append(_executar_task(t))

        resultados.sort(
            key=lambda r: (
                r.caso_nome,
                r.config.tipo_selecao.value,
                r.config.taxa_mutacao,
                r.seed,
            )
        )
        return resultados
