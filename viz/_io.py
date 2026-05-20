"""Utilitários puros de IO para a camada de visualização.

Sem dependências de Pygame ou Streamlit — testável isoladamente.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pandas as pd

from puzzle.estado import Estado
from puzzle.movimentos import Direcao

_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}$")
_TUPLA_RE = re.compile(r"^\(\s*(\d+(?:\s*,\s*\d+)*)\s*\)$")


def parse_estado_inicial(valor: Any) -> Estado:
    """Aceita string '(1,2,3,…)' (formato CSV) ou list[int] (formato JSON)."""
    if isinstance(valor, (list, tuple)):
        return tuple(int(v) for v in valor)
    if isinstance(valor, str):
        m = _TUPLA_RE.match(valor.strip())
        if not m:
            raise ValueError(f"Estado inicial não reconhecido: {valor!r}")
        return tuple(int(v.strip()) for v in m.group(1).split(","))
    raise ValueError(f"Tipo não suportado para estado inicial: {type(valor)}")


def mapear_direcoes(nomes: list[str]) -> list[Direcao]:
    """['CIMA', 'BAIXO', ...] -> [Direcao.CIMA, Direcao.BAIXO, ...]"""
    return [Direcao[n] for n in nomes]


def listar_execucoes(results_dir: Path) -> list[Path]:
    """Pastas timestampadas em `results_dir`, mais recente primeiro."""
    if not results_dir.exists():
        return []
    pastas = [p for p in results_dir.iterdir() if p.is_dir() and _TIMESTAMP_RE.match(p.name)]
    return sorted(pastas, key=lambda p: p.name, reverse=True)


def carregar_runs_csv(path: Path) -> pd.DataFrame:
    """Carrega runs.csv com `resolveu` padronizado como bool."""
    df = pd.read_csv(path)
    df["resolveu"] = df["resolveu"].astype(str).str.lower().eq("true")
    return df


def carregar_historicos_csv(path: Path) -> pd.DataFrame:
    """Carrega historicos.csv (run_id, geracao, melhor_fitness, fitness_medio, diversidade)."""
    return pd.read_csv(path)


def carregar_detalhe_json(path: Path) -> dict[str, Any]:
    """Carrega um JSON individual de execução em detalhes/."""
    return json.loads(path.read_text())


def encontrar_melhor_run(pasta_resultado: Path) -> Path:
    """Critério: `resolveu=True` primeiro; depois `melhor_fitness` decrescente."""
    detalhes = pasta_resultado / "detalhes"
    if not detalhes.exists():
        raise FileNotFoundError(f"Pasta detalhes não existe em {pasta_resultado}")

    melhor_path: Path | None = None
    melhor_chave: tuple[int, float] = (-1, -float("inf"))
    for json_path in detalhes.glob("*.json"):
        dados = json.loads(json_path.read_text())
        chave = (
            1 if dados.get("resolveu") else 0,
            float(dados.get("melhor_fitness", -float("inf"))),
        )
        if chave > melhor_chave:
            melhor_chave = chave
            melhor_path = json_path

    if melhor_path is None:
        raise FileNotFoundError(f"Nenhum JSON em {detalhes}")
    return melhor_path
