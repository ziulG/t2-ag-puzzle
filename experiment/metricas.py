"""Agregação estatística dos resultados de batch.

Agrupa execuções por ``(caso_nome, tipo_selecao, tipo_crossover, taxa_mutacao)``
e calcula métricas que alimentam o relatório:

- ``n_execucoes``
- ``taxa_sucesso``        — fração de execuções que resolveram o puzzle
- ``geracoes_media``      — média de gerações executadas
- ``geracoes_desvio``     — desvio padrão populacional das gerações
- ``tempo_medio_s``       — tempo médio por execução
- ``manhattan_final_medio`` — Manhattan do melhor estado, média sobre todas
- ``gap_otimo_medio``     — gap (tamanho_solucao_ag − optimal_depth), média
  apenas sobre execuções que resolveram; ``None`` se nenhuma resolveu.

Usa apenas ``statistics`` (stdlib).
"""

import statistics
from collections import defaultdict
from typing import Any

from experiment.runner import RunResult


def chave_de_config(run: RunResult) -> tuple[str, str, str, float]:
    """Chave de agrupamento: ``(caso, selecao, crossover, taxa_mutacao)``."""
    return (
        run.caso_nome,
        run.config.tipo_selecao.value,
        run.config.tipo_crossover.value,
        run.config.taxa_mutacao,
    )


def _media_seguro(valores: list[float]) -> float | None:
    return statistics.fmean(valores) if valores else None


def _desvio_seguro(valores: list[float]) -> float | None:
    return statistics.pstdev(valores) if len(valores) >= 1 else None


def agregar_por_config(runs: list[RunResult]) -> dict[str, dict[str, Any]]:
    """Agrega ``runs`` por chave de configuração.

    Retorna um dict ``{chave_str: estatisticas}`` em que ``chave_str`` é
    ``"<caso>|<selecao>|<crossover>|pm=<taxa>"`` — legível e único mesmo
    quando o batch varia o crossover (matriz estendida).
    """
    grupos: dict[tuple[str, str, str, float], list[RunResult]] = defaultdict(list)
    for r in runs:
        grupos[chave_de_config(r)].append(r)

    resumo: dict[str, dict[str, Any]] = {}
    for (caso, selecao, crossover, pm), itens in sorted(grupos.items()):
        chave_str = f"{caso}|{selecao}|{crossover}|pm={pm}"
        resolvidos = [r for r in itens if r.resolveu]
        geracoes = [r.geracoes_executadas for r in itens]
        tempos = [r.tempo_total_s for r in itens]
        manhattans = [r.manhattan_final for r in itens]
        gaps = [r.gap_otimo for r in resolvidos if r.gap_otimo is not None]

        resumo[chave_str] = {
            "caso": caso,
            "tipo_selecao": selecao,
            "tipo_crossover": crossover,
            "taxa_mutacao": pm,
            "n_execucoes": len(itens),
            "n_resolveram": len(resolvidos),
            "taxa_sucesso": len(resolvidos) / len(itens) if itens else 0.0,
            "geracoes_media": _media_seguro(geracoes),
            "geracoes_desvio": _desvio_seguro(geracoes),
            "tempo_medio_s": _media_seguro(tempos),
            "manhattan_final_medio": _media_seguro(manhattans),
            "gap_otimo_medio": _media_seguro(gaps),
        }

    return resumo


def taxa_sucesso_por_caso(runs: list[RunResult]) -> dict[str, float]:
    """Atalho: taxa de sucesso agrupada apenas por caso (todas configs juntas)."""
    por_caso: dict[str, list[RunResult]] = defaultdict(list)
    for r in runs:
        por_caso[r.caso_nome].append(r)
    return {
        caso: sum(1 for r in itens if r.resolveu) / len(itens)
        for caso, itens in sorted(por_caso.items())
    }
