"""Testes da camada ``experiment/`` (Fase 3 + Fase 4).

Cobertura:
- BFS de ``analise_otima`` (GOAL=0, distâncias conhecidas).
- ``random_walk_reverso`` (solúvel, determinístico).
- Casos padrão (solúveis, profundidades anunciadas).
- ``Runner`` (RunResult válido; resolve caso fácil — slow).
- Persistência (CSV round-trip, JSON round-trip, históricos).
- Agregação de métricas.
"""

import csv
import json
from pathlib import Path

import pytest

from config import GAConfig, TipoSelecao
from puzzle.goal import GOAL
from puzzle.heuristicas import eh_soluvel

from experiment.analise_otima import distancia_otima, random_walk_reverso
from experiment.batch import BatchRunner
from experiment.casos_teste import CASOS_PADRAO, CasoTeste
from experiment.metricas import agregar_por_config, taxa_sucesso_por_caso
from experiment.persistencia import (
    HISTORICOS_COLUNAS,
    RUNS_COLUNAS,
    criar_pasta_resultados,
    estado_para_csv,
    salvar_detalhe_json,
    salvar_historicos_csv,
    salvar_runs_csv,
)
from experiment.runner import Runner, gerar_run_id


# ---------------------------------------------------------------------------
# analise_otima
# ---------------------------------------------------------------------------

def test_bfs_goal_eh_zero() -> None:
    assert distancia_otima(GOAL) == 0


def test_bfs_um_movimento() -> None:
    # Vazio na posição 8 (canto inferior direito); 1 movimento (CIMA ou ESQUERDA do GOAL).
    # GOAL aplicando ESQUERDA: vazio vai pra 7. Estado: (1,2,3,4,5,6,7,0,8).
    quase = (1, 2, 3, 4, 5, 6, 7, 0, 8)
    assert distancia_otima(quase) == 1


def test_bfs_dois_movimentos() -> None:
    # Aplicar 2 movimentos ao GOAL; o BFS deve encontrar caminho ≤ 2.
    estado = (1, 2, 3, 4, 5, 6, 0, 7, 8)
    assert distancia_otima(estado) == 2


def test_random_walk_reverso_gera_estado_soluvel() -> None:
    for seed in range(5):
        estado = random_walk_reverso(passos=10, seed=seed)
        assert eh_soluvel(estado)


def test_random_walk_reverso_eh_deterministico() -> None:
    e1 = random_walk_reverso(passos=20, seed=42)
    e2 = random_walk_reverso(passos=20, seed=42)
    assert e1 == e2


def test_random_walk_reverso_zero_passos_eh_goal() -> None:
    assert random_walk_reverso(passos=0, seed=0) == GOAL


# ---------------------------------------------------------------------------
# casos_teste
# ---------------------------------------------------------------------------

def test_casos_padrao_sao_tres() -> None:
    nomes = [c.nome for c in CASOS_PADRAO]
    assert nomes == ["facil", "medio", "dificil"]


def test_casos_padrao_sao_soluveis() -> None:
    for caso in CASOS_PADRAO:
        assert eh_soluvel(caso.estado_inicial), f"{caso.nome} não é solúvel"


def test_casos_padrao_profundidades_anunciadas() -> None:
    """As seeds foram escolhidas pra dar EXATAMENTE 5/15/25 de profundidade ótima."""
    esperado = {"facil": 5, "medio": 15, "dificil": 25}
    for caso in CASOS_PADRAO:
        assert caso.optimal_depth == esperado[caso.nome]


# ---------------------------------------------------------------------------
# runner
# ---------------------------------------------------------------------------

def test_gerar_run_id_padrao() -> None:
    cfg = GAConfig(tipo_selecao=TipoSelecao.TORNEIO, taxa_mutacao=0.05)
    assert gerar_run_id("medio", cfg, seed=3) == "medio-seltor-pm005-seed03"

    cfg2 = GAConfig(tipo_selecao=TipoSelecao.ROLETA, taxa_mutacao=0.10)
    assert gerar_run_id("facil", cfg2, seed=0) == "facil-selrol-pm010-seed00"


def test_runner_retorna_runresult_com_campos_obrigatorios() -> None:
    """Mesmo em config minúscula, o RunResult deve ser bem-formado."""
    cfg = GAConfig(tamanho_populacao=10, tamanho_cromossomo=20, max_geracoes=3,
                   sem_melhoria_limite=3)
    r = Runner(cfg, CASOS_PADRAO[2], seed=0).run()           # caso difícil

    assert r.run_id and r.timestamp
    assert r.caso_nome == "dificil"
    assert r.estado_inicial == CASOS_PADRAO[2].estado_inicial
    assert r.optimal_depth == 25
    assert isinstance(r.resolveu, bool)
    assert r.criterio_parada in {"max_geracoes", "fitness_objetivo", "estagnacao"}
    assert r.geracoes_executadas >= 1
    assert r.tempo_total_s >= 0.0
    assert isinstance(r.historico, list) and len(r.historico) == r.geracoes_executadas
    assert isinstance(r.melhor_cromossomo, list) and r.melhor_cromossomo
    # Se não resolveu, gap_otimo/tamanho_solucao_ag devem ser None
    if not r.resolveu:
        assert r.tamanho_solucao_ag is None
        assert r.gap_otimo is None


@pytest.mark.slow
def test_runner_caso_facil_resolve() -> None:
    """O AG resolve o caso fácil (5 mov.) com a config default."""
    cfg = GAConfig()                                 # defaults do roadmap
    r = Runner(cfg, CASOS_PADRAO[0], seed=0).run()
    assert r.resolveu is True
    assert r.manhattan_final == 0
    assert r.tamanho_solucao_ag is not None
    assert r.gap_otimo is not None
    assert r.gap_otimo >= 0                          # ótimo é o piso


# ---------------------------------------------------------------------------
# persistência
# ---------------------------------------------------------------------------

def test_estado_para_csv_formato() -> None:
    assert estado_para_csv((1, 2, 3, 0, 5)) == "(1,2,3,0,5)"


def test_persistencia_csv_round_trip(tmp_path: Path) -> None:
    """Escreve runs.csv, lê de volta com csv.DictReader, compara campos-chave."""
    cfg = GAConfig(tamanho_populacao=10, tamanho_cromossomo=20, max_geracoes=3,
                   sem_melhoria_limite=3)
    runs = [Runner(cfg, CASOS_PADRAO[0], seed=s).run() for s in range(2)]

    arquivo = tmp_path / "runs.csv"
    salvar_runs_csv(runs, arquivo)

    with arquivo.open() as fh:
        reader = csv.DictReader(fh)
        assert tuple(reader.fieldnames) == RUNS_COLUNAS
        linhas = list(reader)

    assert len(linhas) == 2
    for run, linha in zip(runs, linhas):
        assert linha["run_id"] == run.run_id
        assert linha["caso_nome"] == "facil"
        assert linha["seed"] == str(run.seed)
        assert linha["resolveu"] == str(run.resolveu)
        # tamanho_solucao_ag pode ser "" se não resolveu — testamos esse caso explicitamente em outro teste


def test_persistencia_csv_tamanho_solucao_none_eh_vazio(tmp_path: Path) -> None:
    """RunResult sem solução (não resolveu) → CSV escreve "" em tamanho_solucao_ag/gap_otimo."""
    # Config tão restritiva que provavelmente não resolve o caso difícil
    cfg = GAConfig(tamanho_populacao=4, tamanho_cromossomo=10, max_geracoes=1,
                   sem_melhoria_limite=1)
    r = Runner(cfg, CASOS_PADRAO[2], seed=99).run()   # caso difícil, seed estranha
    # Não exigimos !resolveu (poderia por sorte), mas se resolveu, troca pra um seed que falhou.
    # Suficiente: testar o COMPORTAMENTO do escritor com None — simulamos forçando:
    if r.resolveu:
        r.resolveu = False
        r.tamanho_solucao_ag = None
        r.gap_otimo = None
        r.movimentos_validos_ate_resolver = []

    arquivo = tmp_path / "runs.csv"
    salvar_runs_csv([r], arquivo)
    with arquivo.open() as fh:
        linha = next(csv.DictReader(fh))
    assert linha["tamanho_solucao_ag"] == ""
    assert linha["gap_otimo"] == ""


def test_persistencia_historicos_csv(tmp_path: Path) -> None:
    """historicos.csv tem 1 linha por (run_id, geracao)."""
    cfg = GAConfig(tamanho_populacao=8, tamanho_cromossomo=10, max_geracoes=5,
                   sem_melhoria_limite=5)
    runs = [Runner(cfg, CASOS_PADRAO[0], seed=s).run() for s in range(2)]
    total_geracoes = sum(len(r.historico) for r in runs)

    arquivo = tmp_path / "historicos.csv"
    salvar_historicos_csv(runs, arquivo)
    with arquivo.open() as fh:
        reader = csv.DictReader(fh)
        assert tuple(reader.fieldnames) == HISTORICOS_COLUNAS
        linhas = list(reader)
    assert len(linhas) == total_geracoes


def test_persistencia_detalhe_json_round_trip(tmp_path: Path) -> None:
    """JSON do detalhe é parseável e tem todos os campos esperados."""
    cfg = GAConfig(tamanho_populacao=10, tamanho_cromossomo=20, max_geracoes=3,
                   sem_melhoria_limite=3)
    r = Runner(cfg, CASOS_PADRAO[0], seed=7).run()

    dir_detalhes = tmp_path
    salvar_detalhe_json(r, dir_detalhes)

    arquivo = dir_detalhes / f"{r.run_id}.json"
    payload = json.loads(arquivo.read_text(encoding="utf-8"))

    assert payload["run_id"] == r.run_id
    assert payload["estado_inicial"] == list(r.estado_inicial)
    assert payload["config"]["tipo_selecao"] in {"torneio", "roleta"}
    assert isinstance(payload["melhor_cromossomo"], list)
    # Movimentos serializados como nomes
    if r.movimentos_validos_ate_resolver:
        assert payload["movimentos_validos_ate_resolver"][0] in {
            "CIMA", "BAIXO", "ESQUERDA", "DIREITA"
        }


def test_criar_pasta_resultados(tmp_path: Path) -> None:
    """Cria estrutura ``<raiz>/<timestamp>/detalhes/``."""
    pasta = criar_pasta_resultados(raiz=tmp_path)
    assert pasta.parent == tmp_path
    assert (pasta / "detalhes").is_dir()


# ---------------------------------------------------------------------------
# métricas e batch
# ---------------------------------------------------------------------------

def test_metricas_agregacao_basica() -> None:
    """Agregação por config produz chaves e métricas esperadas."""
    cfg = GAConfig(tamanho_populacao=10, tamanho_cromossomo=20, max_geracoes=3,
                   sem_melhoria_limite=3)
    runs = [Runner(cfg, CASOS_PADRAO[0], seed=s).run() for s in range(3)]

    resumo = agregar_por_config(runs)
    chave = f"facil|torneio|pm={cfg.taxa_mutacao}"
    assert chave in resumo
    stats = resumo[chave]
    assert stats["n_execucoes"] == 3
    assert 0.0 <= stats["taxa_sucesso"] <= 1.0
    assert stats["geracoes_media"] is not None


def test_taxa_sucesso_por_caso() -> None:
    cfg = GAConfig(tamanho_populacao=10, tamanho_cromossomo=20, max_geracoes=3,
                   sem_melhoria_limite=3)
    runs = [Runner(cfg, CASOS_PADRAO[0], seed=s).run() for s in range(2)]
    por_caso = taxa_sucesso_por_caso(runs)
    assert "facil" in por_caso
    assert 0.0 <= por_caso["facil"] <= 1.0


def test_batchrunner_sequencial_pequeno() -> None:
    """BatchRunner com pequeno produto cartesiano e modo sequencial."""
    cfg = GAConfig(tamanho_populacao=8, tamanho_cromossomo=10, max_geracoes=3,
                   sem_melhoria_limite=3)
    batch = BatchRunner(
        configs=[cfg], casos=[CASOS_PADRAO[0]], seeds=[0, 1], processos=1
    )
    tasks = batch.gerar_tasks()
    assert len(tasks) == 2

    resultados = batch.run(paralelo=False)
    assert len(resultados) == 2
    # Ordenação determinística por seed
    assert resultados[0].seed == 0
    assert resultados[1].seed == 1
