"""Entry point do batch da Fase 4 do roadmap.

Matriz padrão (180 execuções):

- **Casos**: ``CASOS_PADRAO`` (fácil, médio, difícil).
- **Seleções**: TORNEIO e ROLETA.
- **Taxas de mutação**: 0.01, 0.05, 0.10.
- **Seeds**: 0..9 (10 execuções por combinação).

Demais parâmetros vêm dos defaults de :class:`GAConfig` (pop=200, cromo=80,
max_geracoes=1000, etc.).

Uso::

    python -m experiment.run_all                # paralelo (cpu_count workers)
    python -m experiment.run_all --sequencial   # debug
    python -m experiment.run_all --seeds 3      # subset rápido (3 seeds)
"""

import argparse
import time
from pathlib import Path

from config import GAConfig, TipoSelecao

from experiment.batch import BatchRunner
from experiment.casos_teste import CASOS_PADRAO
from experiment.metricas import agregar_por_config, taxa_sucesso_por_caso
from experiment.persistencia import (
    config_para_dict_json,
    criar_pasta_resultados,
    salvar_config_batch_json,
    salvar_detalhe_json,
    salvar_historicos_csv,
    salvar_resumo_json,
    salvar_runs_csv,
)


SELECOES = [TipoSelecao.TORNEIO, TipoSelecao.ROLETA]
TAXAS_MUTACAO = [0.01, 0.05, 0.10]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Batch da Fase 4: matriz de configurações × seeds × casos."
    )
    parser.add_argument(
        "--sequencial", action="store_true",
        help="Roda em um único processo (debug). Default: paralelo.",
    )
    parser.add_argument(
        "--processos", type=int, default=None,
        help="Número de workers no pool (default: os.cpu_count()).",
    )
    parser.add_argument(
        "--seeds", type=int, default=10,
        help="Número de seeds por combinação (default: 10).",
    )
    parser.add_argument(
        "--casos", nargs="+", default=None,
        choices=[c.nome for c in CASOS_PADRAO],
        help="Filtra quais casos rodar (default: todos).",
    )
    parser.add_argument(
        "--saida", type=Path, default=Path("results"),
        help="Pasta raiz de saída (default: ./results).",
    )
    return parser.parse_args()


def _construir_configs() -> list[GAConfig]:
    """Produto cartesiano de SELECOES × TAXAS_MUTACAO sobre defaults do GAConfig."""
    return [
        GAConfig(tipo_selecao=sel, taxa_mutacao=pm)
        for sel in SELECOES
        for pm in TAXAS_MUTACAO
    ]


def _imprimir_amostra_csv(path: Path, n: int = 6) -> None:
    """Imprime ``n`` primeiras linhas do CSV (1 cabeçalho + 5 dados)."""
    print(f"\nAmostra de {path.name} (primeiras {n} linhas):")
    with path.open(encoding="utf-8") as fh:
        for i, linha in enumerate(fh):
            print("  " + linha.rstrip())
            if i + 1 >= n:
                break


def _imprimir_resumo(resumo: dict, sucesso_por_caso: dict) -> None:
    print("\nTaxa de sucesso por caso:")
    for caso, taxa in sucesso_por_caso.items():
        print(f"  {caso:8s}: {taxa:.1%}")

    print("\nResumo por configuração:")
    print(
        f"  {'config':40s} {'sucesso':>9s} {'ger.med':>9s} "
        f"{'ger.std':>9s} {'gap':>6s} {'tempo':>8s}"
    )
    for chave, stats in resumo.items():
        ger = stats["geracoes_media"] or 0.0
        std = stats["geracoes_desvio"] or 0.0
        gap = stats["gap_otimo_medio"]
        gap_str = f"{gap:.1f}" if gap is not None else "n/a"
        tempo = stats["tempo_medio_s"] or 0.0
        print(
            f"  {chave:40s} {stats['taxa_sucesso']:>8.1%}  "
            f"{ger:>8.1f}  {std:>8.1f}  {gap_str:>6s}  {tempo:>7.2f}s"
        )


def main() -> int:
    args = _parse_args()

    configs = _construir_configs()
    seeds = list(range(args.seeds))
    if args.casos:
        casos = [c for c in CASOS_PADRAO if c.nome in args.casos]
    else:
        casos = list(CASOS_PADRAO)

    total = len(configs) * len(casos) * len(seeds)
    modo = "sequencial" if args.sequencial else "paralelo"
    print(
        f"Matriz: {len(configs)} configs × {len(casos)} casos × {len(seeds)} seeds "
        f"= {total} execuções ({modo})"
    )
    print(f"Casos: {', '.join(f'{c.nome} (d={c.optimal_depth})' for c in casos)}")

    pasta = criar_pasta_resultados(raiz=args.saida)
    print(f"Saída: {pasta}")

    # Salva a matriz ANTES do batch (referência se interromper)
    salvar_config_batch_json(
        {
            "casos": [
                {
                    "nome": c.nome,
                    "estado_inicial": list(c.estado_inicial),
                    "optimal_depth": c.optimal_depth,
                    "manhattan_inicial": c.manhattan_inicial,
                    "descricao": c.descricao,
                }
                for c in casos
            ],
            "configs": [config_para_dict_json(cfg) for cfg in configs],
            "seeds": seeds,
            "total_execucoes": total,
        },
        pasta / "config_batch.json",
    )

    runner = BatchRunner(
        configs=configs, casos=casos, seeds=seeds, processos=args.processos
    )
    t_inicio = time.perf_counter()
    resultados = runner.run(paralelo=not args.sequencial)
    duracao = time.perf_counter() - t_inicio

    salvar_runs_csv(resultados, pasta / "runs.csv")
    salvar_historicos_csv(resultados, pasta / "historicos.csv")
    for r in resultados:
        salvar_detalhe_json(r, pasta / "detalhes")

    resumo = agregar_por_config(resultados)
    salvar_resumo_json(resumo, pasta / "resumo.json")

    sucesso_por_caso = taxa_sucesso_por_caso(resultados)

    print(f"\n=== Batch concluído em {duracao:.1f}s ({len(resultados)} runs) ===")
    print(f"Pasta: {pasta}")
    _imprimir_resumo(resumo, sucesso_por_caso)
    _imprimir_amostra_csv(pasta / "runs.csv", n=6)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
