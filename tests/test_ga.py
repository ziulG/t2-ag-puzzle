"""Testes do motor do Algoritmo Genético (Fase 2).

Cobre config, invariantes de cromossomo, operadores (seleção, crossover,
mutação), elitismo e o engine. ``ga/`` não importa ``puzzle/``; o fitness é
injetado. Convenções idênticas às de ``tests/test_puzzle.py``.
"""

import random

from config import GAConfig, TipoSelecao, TipoCrossover
from ga.cromossomo import cromossomo_aleatorio, cromossomo_valido, decode, encode
from ga.populacao import populacao_inicial, avaliar_populacao
from ga.selecao import torneio, roleta
from ga.crossover import crossover_um_ponto, crossover_uniforme, aplicar_crossover
from ga.mutacao import mutacao
from ga.elitismo import extrai_elite
from ga.engine import executar_ag, ResultadoAG, HistoricoGeracao


def test_config_defaults_exatos() -> None:
    """GAConfig nasce com os defaults exatos da Fase 3 do roadmap."""
    cfg = GAConfig()
    assert cfg.tamanho_populacao == 200
    assert cfg.tamanho_cromossomo == 80
    assert cfg.tipo_selecao is TipoSelecao.TORNEIO
    assert cfg.tipo_crossover is TipoCrossover.UM_PONTO
    assert cfg.tamanho_torneio == 3
    assert cfg.taxa_crossover == 0.85
    assert cfg.taxa_mutacao == 0.02
    assert cfg.tamanho_elite == 3
    assert cfg.max_score == 100.0
    assert cfg.alfa_invalidos == 2.0
    assert cfg.beta_comprimento == 0.5
    assert cfg.bonus_resolveu == 1000.0
    assert cfg.max_geracoes == 1000
    assert cfg.sem_melhoria_limite == 200
    assert cfg.seed_aleatorio is None


def test_config_enums_valores() -> None:
    """Os enums têm exatamente os valores string do contrato."""
    assert TipoSelecao.TORNEIO.value == "torneio"
    assert TipoSelecao.ROLETA.value == "roleta"
    assert TipoCrossover.UM_PONTO.value == "um_ponto"
    assert TipoCrossover.UNIFORME.value == "uniforme"


def test_cromossomo_aleatorio_comprimento_e_dominio() -> None:
    """Cromossomo aleatório tem 2*tam bits, todos ∈ {0,1}."""
    rng = random.Random(123)
    c = cromossomo_aleatorio(80, rng)
    assert len(c) == 160
    assert all(b in (0, 1) for b in c)
    assert cromossomo_valido(c, 80) is True


def test_cromossomo_valido_rejeita_invalidos() -> None:
    """cromossomo_valido rejeita comprimento errado e bits fora de {0,1}."""
    assert cromossomo_valido([0, 1, 1, 0], 2) is True
    assert cromossomo_valido([0, 1, 1], 2) is False
    assert cromossomo_valido([0, 2, 1, 0], 2) is False


def test_decode_dois_bits_para_codigo() -> None:
    """decode: (alto,baixo) -> alto*2+baixo. 00->0,01->1,10->2,11->3."""
    assert decode([0, 0, 0, 1, 1, 0, 1, 1]) == [0, 1, 2, 3]


def test_decode_retorna_int_generico() -> None:
    """decode devolve ints puros (não Direcao) — ga/ não conhece o domínio."""
    saida = decode([1, 0, 0, 1])
    assert saida == [2, 1]
    assert all(type(x) is int for x in saida)


def test_encode_decode_roundtrip() -> None:
    """encode é inverso de decode para todos os códigos 0..3."""
    codigos = [0, 1, 2, 3, 3, 2, 1, 0]
    assert decode(encode(codigos)) == codigos


def test_decode_roundtrip_aleatorio() -> None:
    """Cromossomo aleatório -> decode -> encode reproduz os mesmos bits."""
    rng = random.Random(7)
    c = cromossomo_aleatorio(40, rng)
    assert encode(decode(c)) == c


def test_populacao_inicial_tamanho_correto() -> None:
    """populacao_inicial cria exatamente N cromossomos válidos."""
    rng = random.Random(1)
    pop = populacao_inicial(50, 30, rng)
    assert len(pop) == 50
    assert all(cromossomo_valido(c, 30) for c in pop)


def test_avaliar_populacao_retorna_pares() -> None:
    """avaliar_populacao devolve pares (cromossomo, float) na ordem dada."""
    rng = random.Random(2)
    pop = populacao_inicial(5, 4, rng)
    fitness = lambda c: float(sum(c))
    avaliados = avaliar_populacao(pop, fitness)
    assert len(avaliados) == 5
    for cromo, fit in avaliados:
        assert cromo in pop
        assert isinstance(fit, float)
    assert avaliados[0][1] == float(sum(pop[0]))


def test_torneio_seleciona_melhor_majoritariamente() -> None:
    """Teste estatístico do roadmap: 3 indivíduos, k=3, 1000 amostragens.

    Torneio SEM reposição (rng.sample) com k=3 de 3 sempre pega os 3 →
    o melhor (c2, fitness 50) vence todas as vezes (>900, de fato 1000).
    """
    c1, c2, c3 = [0, 0], [1, 1], [1, 0]
    avaliados = [(c1, 10.0), (c2, 50.0), (c3, 30.0)]
    rng = random.Random(42)
    vezes_c2 = sum(1 for _ in range(1000) if torneio(avaliados, rng, 3) == c2)
    assert vezes_c2 > 900


def test_torneio_k_menor_que_populacao() -> None:
    """Com k < tamanho, ainda retorna um cromossomo da população."""
    rng = random.Random(0)
    avaliados = [([0], 1.0), ([1], 2.0), ([0, 1], 3.0), ([1, 0], 0.5)]
    for _ in range(50):
        venc = torneio(avaliados, rng, 2)
        assert venc in [c for c, _ in avaliados]


def test_roleta_retorna_cromossomo_valido() -> None:
    """Roleta sempre retorna um cromossomo da população avaliada."""
    rng = random.Random(3)
    avaliados = [([0, 0], 1.0), ([1, 1], 5.0), ([1, 0], 2.0)]
    for _ in range(100):
        sel = roleta(avaliados, rng)
        assert sel in [c for c, _ in avaliados]


def test_roleta_enviesa_para_maior_fitness() -> None:
    """Roleta escolhe o de fitness muito maior na grande maioria das vezes."""
    bom, ruim = [1, 1], [0, 0]
    avaliados = [(ruim, 1.0), (bom, 99.0)]
    rng = random.Random(11)
    vezes_bom = sum(1 for _ in range(1000) if roleta(avaliados, rng) == bom)
    assert vezes_bom > 900


def test_roleta_normaliza_fitness_negativo() -> None:
    """Com fitness negativo, roleta normaliza (f-min+1) e não quebra."""
    a, b = [0], [1]
    avaliados = [(a, -50.0), (b, -10.0)]
    rng = random.Random(5)
    vezes_b = sum(1 for _ in range(1000) if roleta(avaliados, rng) == b)
    assert vezes_b > 600


def test_crossover_um_ponto_preserva_comprimento() -> None:
    """Crossover um-ponto preserva 160 bits (teste do roadmap)."""
    rs = random.Random(99)
    pai1 = [rs.randint(0, 1) for _ in range(160)]
    pai2 = [rs.randint(0, 1) for _ in range(160)]
    f1, f2 = crossover_um_ponto(pai1, pai2, random.Random(1))
    assert len(f1) == 160 and len(f2) == 160
    assert all(b in (0, 1) for b in f1 + f2)


def test_crossover_um_ponto_nao_muta_pais() -> None:
    """Crossover não muta os pais; filhos são prefixo/sufixo trocados."""
    pai1 = [0] * 10
    pai2 = [1] * 10
    f1, f2 = crossover_um_ponto(pai1, pai2, random.Random(0))
    assert pai1 == [0] * 10 and pai2 == [1] * 10
    assert all(f1[i] + f2[i] == 1 for i in range(10))


def test_crossover_uniforme_preserva_comprimento() -> None:
    """Crossover uniforme preserva 160 bits e domínio {0,1}."""
    rs = random.Random(77)
    pai1 = [rs.randint(0, 1) for _ in range(160)]
    pai2 = [rs.randint(0, 1) for _ in range(160)]
    f1, f2 = crossover_uniforme(pai1, pai2, random.Random(2))
    assert len(f1) == 160 and len(f2) == 160
    assert all(b in (0, 1) for b in f1 + f2)


def test_crossover_uniforme_filhos_complementares() -> None:
    """Cada bit do filho vem de um dos pais; f2 é complemento de f1."""
    pai1 = [0] * 20
    pai2 = [1] * 20
    f1, f2 = crossover_uniforme(pai1, pai2, random.Random(4))
    assert all(b in (0, 1) for b in f1)
    assert all(f1[i] + f2[i] == 1 for i in range(20))


def test_aplicar_crossover_taxa_zero_copia_pais() -> None:
    """Com taxa 0.0, filhos são cópias exatas dos pais (objetos distintos)."""
    pai1 = [0, 1, 0, 1]
    pai2 = [1, 1, 0, 0]
    f1, f2 = aplicar_crossover(pai1, pai2, TipoCrossover.UM_PONTO, 0.0,
                               random.Random(0))
    assert f1 == pai1 and f2 == pai2
    assert f1 is not pai1 and f2 is not pai2


def test_aplicar_crossover_taxa_um_recombina() -> None:
    """Com taxa 1.0 e pais distintos, sempre recombina."""
    pai1 = [0] * 6
    pai2 = [1] * 6
    f1, f2 = aplicar_crossover(pai1, pai2, TipoCrossover.UM_PONTO, 1.0,
                               random.Random(7))
    assert len(f1) == 6 and len(f2) == 6
    assert all(f1[i] + f2[i] == 1 for i in range(6))


def test_mutacao_taxa_zero_nao_altera() -> None:
    """Mutação com taxa 0.0 não altera (teste do roadmap)."""
    cromo = [0, 1, 0, 1, 0, 1]
    resultado = mutacao(cromo, 0.0, random.Random(0))
    assert resultado == cromo
    assert resultado is not cromo


def test_mutacao_retorna_nova_lista() -> None:
    """Mutação nunca muta a entrada."""
    cromo = [0, 0, 0, 0]
    original = list(cromo)
    _ = mutacao(cromo, 1.0, random.Random(0))
    assert cromo == original


def test_mutacao_taxa_um_inverte_tudo() -> None:
    """Com taxa 1.0, todo bit inverte."""
    assert mutacao([0, 1, 0, 1], 1.0, random.Random(0)) == [1, 0, 1, 0]


def test_mutacao_preserva_comprimento_e_dominio() -> None:
    """Mutação preserva comprimento e bits ∈ {0,1}."""
    rs = random.Random(3)
    cromo = [rs.randint(0, 1) for _ in range(160)]
    m = mutacao(cromo, 0.05, random.Random(9))
    assert len(m) == 160 and all(b in (0, 1) for b in m)


def test_elitismo_extrai_top_n_em_ordem() -> None:
    """extrai_elite devolve os N melhores (fitness desc)."""
    avaliados = [([0], 1.0), ([1], 9.0), ([0, 1], 5.0), ([1, 0], 7.0)]
    assert extrai_elite(avaliados, 2) == [[1], [1, 0]]


def test_elitismo_retorna_copias() -> None:
    """Elite são cópias — mutar a elite não afeta os originais."""
    cromo = [0, 1, 1]
    elite = extrai_elite([(cromo, 5.0)], 1)
    elite[0][0] = 9
    assert cromo == [0, 1, 1]


def test_elitismo_zero_retorna_vazio() -> None:
    """tamanho_elite <= 0 → lista vazia."""
    assert extrai_elite([([0], 1.0), ([1], 2.0)], 0) == []


def test_elitismo_satura_no_tamanho_da_populacao() -> None:
    """Pedir mais elite que indivíduos não estoura — satura."""
    assert len(extrai_elite([([0], 1.0), ([1], 2.0)], 10)) == 2


def _fitness_soma(cromo: list[int]) -> float:
    """Fitness fake: soma dos bits. Sem domínio."""
    return float(sum(cromo))


def test_engine_reprodutivel_com_seed() -> None:
    """Mesma seed → mesmo resultado."""
    cfg = GAConfig(tamanho_populacao=20, tamanho_cromossomo=8,
                   max_geracoes=15, seed_aleatorio=42)
    r1 = executar_ag(cfg, _fitness_soma, fitness_objetivo=16.0)
    r2 = executar_ag(cfg, _fitness_soma, fitness_objetivo=16.0)
    assert r1.melhor_fitness == r2.melhor_fitness
    assert r1.melhor_cromossomo == r2.melhor_cromossomo
    assert r1.criterio_parada == r2.criterio_parada


def test_engine_alcanca_fitness_objetivo() -> None:
    """Maximizar soma de 16 bits: ótimo (todos 1) alcançável."""
    cfg = GAConfig(tamanho_populacao=30, tamanho_cromossomo=8,
                   max_geracoes=200, sem_melhoria_limite=200, seed_aleatorio=1)
    r = executar_ag(cfg, _fitness_soma, fitness_objetivo=16.0)
    assert isinstance(r, ResultadoAG)
    assert r.melhor_fitness == 16.0
    assert r.criterio_parada == "fitness_objetivo"
    assert sum(r.melhor_cromossomo) == 16


def test_engine_para_por_max_geracoes() -> None:
    """Objetivo inalcançável + estagnação alta → para por max_geracoes."""
    cfg = GAConfig(tamanho_populacao=10, tamanho_cromossomo=4,
                   max_geracoes=5, sem_melhoria_limite=999, seed_aleatorio=0)
    r = executar_ag(cfg, _fitness_soma, fitness_objetivo=1e9)
    assert r.criterio_parada == "max_geracoes"
    assert len(r.historico) == 5
    assert r.geracoes_executadas == 5


def test_engine_para_por_estagnacao() -> None:
    """Fitness constante → para por estagnação."""
    cfg = GAConfig(tamanho_populacao=10, tamanho_cromossomo=4,
                   max_geracoes=1000, sem_melhoria_limite=3, seed_aleatorio=0)
    r = executar_ag(cfg, lambda c: 1.0, fitness_objetivo=1e9)
    assert r.criterio_parada == "estagnacao"
    assert len(r.historico) <= 5


def test_engine_historico_estrutura() -> None:
    """Histórico: 1 entrada/geração, campos coerentes, melhor monotônico."""
    cfg = GAConfig(tamanho_populacao=12, tamanho_cromossomo=6,
                   max_geracoes=4, sem_melhoria_limite=999, seed_aleatorio=2)
    r = executar_ag(cfg, _fitness_soma, fitness_objetivo=1e9)
    assert len(r.historico) == 4
    for h in r.historico:
        assert isinstance(h, HistoricoGeracao)
        assert h.diversidade >= 0.0
        assert h.melhor_fitness >= h.fitness_medio - 1e-9
        assert len(h.melhor_cromossomo) == 12
    melhores = [h.melhor_fitness for h in r.historico]
    assert all(melhores[i] <= melhores[i + 1] for i in range(len(melhores) - 1))


def test_engine_populacao_seguinte_tamanho_exato() -> None:
    """População ímpar (caso de borda): roda muitas gerações sem estourar."""
    cfg = GAConfig(tamanho_populacao=21, tamanho_cromossomo=5,
                   tamanho_elite=3, max_geracoes=50, seed_aleatorio=7)
    r = executar_ag(cfg, _fitness_soma, fitness_objetivo=10.0)
    assert r.criterio_parada in ("fitness_objetivo", "max_geracoes")
    assert len(r.historico) >= 1
