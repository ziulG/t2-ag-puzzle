"""Testes da camada de IO de visualização (`viz/_io.py`)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from puzzle.movimentos import Direcao
from viz._io import (
    encontrar_melhor_run,
    listar_execucoes,
    mapear_direcoes,
    parse_estado_inicial,
)


def test_parse_estado_inicial_tupla_string() -> None:
    assert parse_estado_inicial("(1,2,3,4,5,6,7,8,0)") == (1, 2, 3, 4, 5, 6, 7, 8, 0)


def test_parse_estado_inicial_lista_json() -> None:
    assert parse_estado_inicial([1, 2, 3, 5, 6, 0, 4, 7, 8]) == (1, 2, 3, 5, 6, 0, 4, 7, 8)


def test_parse_estado_inicial_invalido_levanta() -> None:
    with pytest.raises(ValueError):
        parse_estado_inicial("nao-eh-estado")


def test_mapear_direcoes_strings_para_enum() -> None:
    nomes = ["CIMA", "BAIXO", "ESQUERDA", "DIREITA"]
    esperado = [Direcao.CIMA, Direcao.BAIXO, Direcao.ESQUERDA, Direcao.DIREITA]
    assert mapear_direcoes(nomes) == esperado


def test_mapear_direcoes_nome_invalido_levanta() -> None:
    with pytest.raises(KeyError):
        mapear_direcoes(["FRENTE"])


def test_listar_execucoes_ordenado_por_nome_desc(tmp_path: Path) -> None:
    (tmp_path / "2026-05-19_10-00-00").mkdir()
    (tmp_path / "2026-05-20_09-22-32").mkdir()
    (tmp_path / "nao-eh-timestamp").mkdir()
    pastas = listar_execucoes(tmp_path)
    nomes = [p.name for p in pastas]
    assert nomes == ["2026-05-20_09-22-32", "2026-05-19_10-00-00"]


def test_encontrar_melhor_run_prefere_resolveu_e_maior_fitness(tmp_path: Path) -> None:
    detalhes = tmp_path / "detalhes"
    detalhes.mkdir()
    (detalhes / "a.json").write_text(json.dumps({"resolveu": False, "melhor_fitness": 90.0}))
    (detalhes / "b.json").write_text(json.dumps({"resolveu": True, "melhor_fitness": 1050.0}))
    (detalhes / "c.json").write_text(json.dumps({"resolveu": True, "melhor_fitness": 1090.0}))
    melhor = encontrar_melhor_run(tmp_path)
    assert melhor.name == "c.json"
