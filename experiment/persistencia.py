"""I/O dos resultados de experimentação.

Layout dos arquivos gerados:

::

    results/<YYYY-MM-DD_HH-MM-SS>/
    ├── runs.csv               # uma linha por execução, schema plano
    ├── historicos.csv         # uma linha por (run_id, geração)
    ├── resumo.json            # estatísticas agregadas por configuração
    ├── config_batch.json      # matriz de configs do batch (reprodutibilidade)
    └── detalhes/
        ├── <run_id>.json      # RunResult completo
        └── ...

Conversões:
- ``GAConfig`` → dict com ``Enum.value`` em vez de ``Enum`` (JSON-safe).
- ``Estado`` (tupla) → string ``"(1,2,3,...)"`` no CSV; lista no JSON.
- ``Direcao`` (IntEnum) → nome (``"CIMA"``) no JSON.
"""

import csv
import json
from dataclasses import asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from config import GAConfig

from experiment.runner import RunResult


# ---------------------------------------------------------------------------
# Pastas
# ---------------------------------------------------------------------------

def criar_pasta_resultados(raiz: Path | None = None) -> Path:
    """Cria ``results/<timestamp>/`` (e subpasta ``detalhes/``) e devolve o caminho.

    ``raiz`` permite redirecionar para um diretório alternativo (útil em testes).
    """
    raiz = Path(raiz) if raiz is not None else Path("results")
    raiz.mkdir(parents=True, exist_ok=True)
    pasta = raiz / datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    pasta.mkdir(parents=True, exist_ok=False)
    (pasta / "detalhes").mkdir()
    return pasta


# ---------------------------------------------------------------------------
# Schemas (uma fonte da verdade para as colunas do CSV principal)
# ---------------------------------------------------------------------------

RUNS_COLUNAS: tuple[str, ...] = (
    # identificação
    "run_id", "timestamp",
    # caso
    "caso_nome", "estado_inicial", "manhattan_inicial", "optimal_depth",
    # execução
    "seed",
    # config (flat)
    "tipo_selecao", "tipo_crossover", "tamanho_populacao", "tamanho_cromossomo",
    "tamanho_torneio", "taxa_crossover", "taxa_mutacao", "tamanho_elite",
    "max_score", "alfa_invalidos", "beta_comprimento", "bonus_resolveu",
    "max_geracoes", "sem_melhoria_limite",
    # resultado
    "resolveu", "criterio_parada", "geracoes_executadas", "tempo_total_s",
    "melhor_fitness", "manhattan_final", "passos_ate_melhor",
    "movimentos_invalidos", "tamanho_solucao_ag", "gap_otimo",
)

HISTORICOS_COLUNAS: tuple[str, ...] = (
    "run_id", "geracao", "melhor_fitness", "fitness_medio", "diversidade",
)


# ---------------------------------------------------------------------------
# Conversores
# ---------------------------------------------------------------------------

def estado_para_csv(estado: tuple[int, ...]) -> str:
    """Tupla → string ``"(1,2,3,...)"`` (formato compacto, parseável)."""
    return "(" + ",".join(str(p) for p in estado) + ")"


def config_para_dict_json(config: GAConfig) -> dict[str, Any]:
    """``GAConfig`` → dict com Enums já como strings (JSON-safe)."""
    d = asdict(config)
    for k, v in d.items():
        if isinstance(v, Enum):
            d[k] = v.value
    # asdict não desce em Enum: precisa converter manualmente os campos
    d["tipo_selecao"] = config.tipo_selecao.value
    d["tipo_crossover"] = config.tipo_crossover.value
    return d


def run_para_linha_csv(run: RunResult) -> dict[str, Any]:
    """Achata o ``RunResult`` em um dict pronto pra ``csv.DictWriter``."""
    cfg = run.config
    return {
        "run_id": run.run_id,
        "timestamp": run.timestamp,
        "caso_nome": run.caso_nome,
        "estado_inicial": estado_para_csv(run.estado_inicial),
        "manhattan_inicial": run.manhattan_inicial,
        "optimal_depth": run.optimal_depth,
        "seed": run.seed,
        "tipo_selecao": cfg.tipo_selecao.value,
        "tipo_crossover": cfg.tipo_crossover.value,
        "tamanho_populacao": cfg.tamanho_populacao,
        "tamanho_cromossomo": cfg.tamanho_cromossomo,
        "tamanho_torneio": cfg.tamanho_torneio,
        "taxa_crossover": cfg.taxa_crossover,
        "taxa_mutacao": cfg.taxa_mutacao,
        "tamanho_elite": cfg.tamanho_elite,
        "max_score": cfg.max_score,
        "alfa_invalidos": cfg.alfa_invalidos,
        "beta_comprimento": cfg.beta_comprimento,
        "bonus_resolveu": cfg.bonus_resolveu,
        "max_geracoes": cfg.max_geracoes,
        "sem_melhoria_limite": cfg.sem_melhoria_limite,
        "resolveu": run.resolveu,
        "criterio_parada": run.criterio_parada,
        "geracoes_executadas": run.geracoes_executadas,
        "tempo_total_s": round(run.tempo_total_s, 6),
        "melhor_fitness": run.melhor_fitness,
        "manhattan_final": run.manhattan_final,
        "passos_ate_melhor": run.passos_ate_melhor,
        "movimentos_invalidos": run.movimentos_invalidos,
        "tamanho_solucao_ag": run.tamanho_solucao_ag if run.tamanho_solucao_ag is not None else "",
        "gap_otimo": run.gap_otimo if run.gap_otimo is not None else "",
    }


def run_para_dict_json(run: RunResult) -> dict[str, Any]:
    """``RunResult`` completo → dict JSON-safe (sem histórico — esse vai no CSV)."""
    return {
        "run_id": run.run_id,
        "timestamp": run.timestamp,
        "caso_nome": run.caso_nome,
        "estado_inicial": list(run.estado_inicial),
        "manhattan_inicial": run.manhattan_inicial,
        "optimal_depth": run.optimal_depth,
        "seed": run.seed,
        "config": config_para_dict_json(run.config),
        "resolveu": run.resolveu,
        "criterio_parada": run.criterio_parada,
        "geracoes_executadas": run.geracoes_executadas,
        "tempo_total_s": run.tempo_total_s,
        "melhor_fitness": run.melhor_fitness,
        "manhattan_final": run.manhattan_final,
        "passos_ate_melhor": run.passos_ate_melhor,
        "movimentos_invalidos": run.movimentos_invalidos,
        "tamanho_solucao_ag": run.tamanho_solucao_ag,
        "gap_otimo": run.gap_otimo,
        "melhor_cromossomo": list(run.melhor_cromossomo),
        "movimentos_decodificados": [d.name for d in run.movimentos_decodificados],
        "movimentos_validos_ate_resolver": [d.name for d in run.movimentos_validos_ate_resolver],
    }


# ---------------------------------------------------------------------------
# Saída
# ---------------------------------------------------------------------------

def salvar_runs_csv(runs: list[RunResult], path: Path) -> None:
    """Escreve ``runs.csv`` com uma linha por execução."""
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(RUNS_COLUNAS))
        writer.writeheader()
        for run in runs:
            writer.writerow(run_para_linha_csv(run))


def salvar_historicos_csv(runs: list[RunResult], path: Path) -> None:
    """Escreve ``historicos.csv`` com uma linha por (run_id, geração)."""
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(HISTORICOS_COLUNAS))
        writer.writeheader()
        for run in runs:
            for h in run.historico:
                writer.writerow({
                    "run_id": run.run_id,
                    "geracao": h.geracao,
                    "melhor_fitness": h.melhor_fitness,
                    "fitness_medio": h.fitness_medio,
                    "diversidade": h.diversidade,
                })


def salvar_detalhe_json(run: RunResult, dir_detalhes: Path) -> None:
    """Escreve ``detalhes/<run_id>.json`` com o ``RunResult`` completo."""
    arquivo = dir_detalhes / f"{run.run_id}.json"
    with arquivo.open("w", encoding="utf-8") as fh:
        json.dump(run_para_dict_json(run), fh, indent=2, ensure_ascii=False)


def salvar_resumo_json(resumo: dict[str, Any], path: Path) -> None:
    """Escreve o ``resumo.json`` (estatísticas agregadas)."""
    with path.open("w", encoding="utf-8") as fh:
        json.dump(resumo, fh, indent=2, ensure_ascii=False, default=_json_fallback)


def salvar_config_batch_json(matriz: dict[str, Any], path: Path) -> None:
    """Escreve a descrição da matriz de configurações do batch."""
    with path.open("w", encoding="utf-8") as fh:
        json.dump(matriz, fh, indent=2, ensure_ascii=False, default=_json_fallback)


def _json_fallback(obj: Any) -> Any:
    """Conversor genérico para objetos não-nativamente serializáveis (Enums, dataclasses)."""
    if isinstance(obj, Enum):
        return obj.value
    if hasattr(obj, "__dataclass_fields__"):
        return config_para_dict_json(obj) if isinstance(obj, GAConfig) else asdict(obj)
    raise TypeError(f"Não-serializável: {type(obj).__name__}")
