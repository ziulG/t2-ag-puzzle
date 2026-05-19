# Roadmap — 8-Puzzle com Algoritmo Genético

> Implementação **na munheca** (sem bibliotecas de GA). Trabalho de Inteligência Artificial.
> Stack: Python + Pygame + Streamlit/Matplotlib + pytest.

---

## Sumário

- [Stack Sugerida](#stack-sugerida)
- [Fase 0 — Arquitetura](#fase-0--arquitetura)
- [Fase 1 — Domínio do Puzzle](#fase-1--domínio-do-puzzle)
- [Fase 2 — Motor do AG](#fase-2--motor-do-ag)
- [Fase 3 — Configuração](#fase-3--configuração)
- [Fase 4 — Experimentação](#fase-4--experimentação)
- [Fase 5 — Visualizações](#fase-5--visualizações)
- [Fase 6 — Testes Unitários](#fase-6--testes-unitários)
- [Fase 7 — Definindo os Parâmetros](#fase-7--definindo-os-parâmetros)
- [Ordem Prática de Execução](#ordem-prática-de-execução)
- [Checklist Final](#checklist-final)

---

## Stack Sugerida

| Camada | Ferramenta | Justificativa |
|---|---|---|
| Core do AG | **Python puro** | Zero libs de GA — implementação manual exigida |
| Domínio do puzzle | Python puro | Lógica do tabuleiro, movimentos, heurísticas |
| Visualização animada | **Pygame** | Anima o puzzle resolvendo passo a passo |
| Dashboard analítico | **Streamlit** (ou Matplotlib) | Gráficos de convergência, comparações, métricas |
| Testes | **pytest** | Cobertura de unidade e integração |
| Configuração | `@dataclass` | Parâmetros tipados e versionáveis |

**Por que Streamlit?** Dá uma página web interativa onde dá pra mexer nos parâmetros e ver os gráficos atualizando. Rende ótimas screenshots pro relatório e é o toque "diferentão" sem te ferrar de complexidade.

---

## Fase 0 — Arquitetura

Separa em módulos desde o começo. A estrutura proposta:

```
8puzzle-ag/
├── puzzle/             # Domínio do 8-puzzle
│   ├── __init__.py
│   ├── estado.py       # Representação e operações do tabuleiro
│   ├── movimentos.py   # Direções, validação, aplicação
│   ├── heuristicas.py  # Manhattan, Hamming, solvabilidade
│   └── goal.py         # Estado objetivo e checagem
│
├── ga/                 # Motor do Algoritmo Genético
│   ├── __init__.py
│   ├── cromossomo.py   # Encode/decode binário
│   ├── populacao.py    # Inicialização e gerenciamento
│   ├── selecao.py      # Torneio, Roleta, Rank
│   ├── crossover.py    # Um-ponto, dois-pontos, uniforme
│   ├── mutacao.py      # Bit flip
│   ├── elitismo.py     # Preservação dos melhores
│   └── engine.py       # Loop principal do AG
│
├── experiment/         # Execução de experimentos
│   ├── __init__.py
│   ├── runner.py       # Roda uma execução
│   ├── batch.py        # Roda múltiplas configurações
│   └── metricas.py     # Coleta e agrega métricas
│
├── viz/                # Visualizações
│   ├── __init__.py
│   ├── pygame_anim.py  # Animação do puzzle resolvendo
│   └── dashboard.py    # Streamlit ou Matplotlib
│
├── tests/              # Testes unitários
│   ├── test_puzzle.py
│   ├── test_ga.py
│   └── test_integration.py
│
├── config.py           # GAConfig dataclass
├── main.py             # Entry points (run, animate, dashboard)
├── requirements.txt
└── README.md
```

**Regra de ouro:** o módulo `ga/` **não pode importar nada de `puzzle/` diretamente**. Recebe funções de fitness e decode como parâmetros. Isso permite reaproveitar o motor pra outros problemas (Mochila, Caixeiro Viajante) depois — e é argumento forte pro relatório.

---

## Fase 1 — Domínio do Puzzle

Implementa primeiro, **sem AG nenhum**. Roda em REPL, valida na mão.

### Representação do Estado

Use `tuple[int, ...]` de 9 elementos, com `0` representando o espaço vazio.

```python
# Goal state
GOAL = (1, 2, 3, 4, 5, 6, 7, 8, 0)

# Exemplo de estado
estado = (2, 5, 1, 0, 7, 4, 3, 6, 8)
```

**Por que tupla e não lista?** Imutável, hasheável (útil pra detectar ciclos e cachear), e impede bugs sutis de mutação acidental.

### Operações Mínimas

| Função | Entrada | Saída |
|---|---|---|
| `posicao_vazio(estado)` | tupla | índice do `0` (0-8) |
| `movimentos_validos(estado)` | tupla | lista de direções possíveis |
| `aplicar_movimento(estado, direcao)` | tupla, enum | nova tupla (ou mesma se inválido) |
| `eh_objetivo(estado)` | tupla | bool |
| `distancia_manhattan(estado)` | tupla | int |
| `distancia_hamming(estado)` | tupla | int |
| `eh_soluvel(estado)` | tupla | bool |

### Direções

```python
from enum import IntEnum

class Direcao(IntEnum):
    CIMA = 0      # 00
    BAIXO = 1     # 01
    ESQUERDA = 2  # 10
    DIREITA = 3   # 11
```

Cada direção move o **espaço vazio** naquela direção (e a peça vizinha vai pro lugar do vazio).

### Validade de Movimentos

Mapeamento de qual direção é inválida em cada posição do vazio:

| Posição do vazio | Inválidos |
|---|---|
| 0 (topo-esq) | CIMA, ESQUERDA |
| 1 (topo-meio) | CIMA |
| 2 (topo-dir) | CIMA, DIREITA |
| 3 (meio-esq) | ESQUERDA |
| 4 (centro) | nenhum |
| 5 (meio-dir) | DIREITA |
| 6 (base-esq) | BAIXO, ESQUERDA |
| 7 (base-meio) | BAIXO |
| 8 (base-dir) | BAIXO, DIREITA |

### Solvabilidade — CRÍTICO

Só metade das permutações do 8-puzzle são solucionáveis. Critério: contar **inversões** ignorando o `0`. Se o número de inversões for **par**, é solúvel.

```python
def eh_soluvel(estado: tuple[int, ...]) -> bool:
    pecas = [p for p in estado if p != 0]
    inversoes = sum(
        1 for i in range(len(pecas))
        for j in range(i + 1, len(pecas))
        if pecas[i] > pecas[j]
    )
    return inversoes % 2 == 0
```

**Se rodar AG em puzzle insolúvel, é loop infinito.** Sempre valide antes.

### Antes de Seguir

Escreva testes pra cada operação acima. Se essa camada tiver bug, todo o resto vai parecer que o AG está quebrado quando o problema é o puzzle.

---

## Fase 2 — Motor do AG

Aqui é a parte "na munheca". Constrói nessa ordem.

### Cromossomo

Sequência fixa de movimentos, cada movimento codificado em 2 bits.

- **Comprimento sugerido:** 80-100 movimentos (o ótimo do 8-puzzle nunca passa de 31, então 80 dá folga sobrando)
- **Armazenamento:** `list[int]` de 0/1, ou `bytearray` (mais econômico)
- **Funções:** `encode(direcoes) -> bits`, `decode(bits) -> direcoes`

```python
# Exemplo conceitual (não implementação)
cromossomo = [0, 1, 1, 0, 1, 0, 0, 1, ...]  # 160 bits = 80 movimentos
# Decodificado: [BAIXO, ESQUERDA, BAIXO, DIREITA, ...]
```

### Inicialização da População

População inicial = N cromossomos com bits aleatórios. **Não** tenta ser esperto aqui — o AG precisa de diversidade pra funcionar.

### Fitness — A Alma do Trabalho

Função composta com punições:

```
fitness(cromossomo) = MAX_SCORE
                    - manhattan_no_melhor_estado_alcancado
                    - α × movimentos_invalidos
                    - β × passos_ate_o_melhor_estado
                    + BONUS_RESOLVEU (se chegou no goal)
```

**Detalhe crítico:** ao decodificar e simular, **guarda o melhor estado intermediário** (menor Manhattan), não só o final. Se o cromossomo resolveu no movimento 30 e os 50 restantes bagunçaram tudo, você quer premiar o cromossomo, não punir.

**Valores iniciais sugeridos:**
- `MAX_SCORE = 100`
- `α = 2` (penalidade por movimento inválido)
- `β = 0.5` (penalidade por usar mais movimentos)
- `BONUS_RESOLVEU = 1000`

Manhattan no 8-puzzle vai de 0 a ~30, então o range fica saudável.

### Operadores de Seleção

Implementa **dois** pra comparar no relatório:

**Torneio (recomendado como default):**
1. Sorteia `k` indivíduos da população (k=3)
2. Retorna o de maior fitness
3. Repete pra cada vaga necessária

Simples, robusto, e não sofre com fitness negativo.

**Roleta (como na aula):**
1. Calcula soma total de fitness
2. Sorteia número aleatório em `[0, soma_total]`
3. Percorre acumulando até passar do sorteado

Cuidado: se algum fitness for negativo, **normaliza** antes (`f_norm = f - min_fitness + 1`).

### Operadores de Crossover

Implementa pelo menos dois:

**Um-ponto:**
- Sorteia índice `p` em `[1, L-1]`
- Filho 1 = pai1[:p] + pai2[p:]
- Filho 2 = pai2[:p] + pai1[p:]

**Uniforme:**
- Pra cada bit, sorteia 50/50 qual pai vem
- Mais "agressivo" na recombinação

**Aplicação:** só executa crossover com probabilidade `Pc` (default 0.85). Caso contrário, filhos = cópias dos pais.

### Mutação

Bit flip simples: pra cada bit, com probabilidade `Pm` (default 0.02), inverte (`0 → 1` ou `1 → 0`).

### Elitismo

Copia os `N` melhores indivíduos direto pra próxima geração, **antes** de aplicar crossover/mutação no resto. Default: `N = 3`.

**Sem elitismo, o AG perde solução boa por azar de sorteio.** Não negocia isso.

### Loop Principal

Pseudo-código (como na aula, mas com elitismo):

```
inicializa_populacao()
melhor_global = nenhum
geracoes_sem_melhoria = 0

enquanto nao parar:
    avalia_populacao()
    atualiza melhor_global

    elite = top_N(populacao)

    pais = selecao(populacao)
    filhos = crossover(pais)
    filhos = mutacao(filhos)

    populacao = elite + filhos[:tamanho - N]

    se nao houve melhoria:
        geracoes_sem_melhoria += 1
```

### Critério de Parada (Composto)

Para quando **qualquer** das condições for verdadeira:
- `geracao >= max_geracoes`
- `melhor_fitness >= FITNESS_OBJETIVO` (puzzle resolvido)
- `geracoes_sem_melhoria >= LIMITE_ESTAGNACAO`

---

## Fase 3 — Configuração

Cria uma `@dataclass GAConfig` com **todos** os parâmetros. Nunca hardcoda nada no motor.

```python
from dataclasses import dataclass
from enum import Enum

class TipoSelecao(Enum):
    TORNEIO = "torneio"
    ROLETA = "roleta"

class TipoCrossover(Enum):
    UM_PONTO = "um_ponto"
    UNIFORME = "uniforme"

@dataclass
class GAConfig:
    # População
    tamanho_populacao: int = 200
    tamanho_cromossomo: int = 80  # número de movimentos
    
    # Operadores
    tipo_selecao: TipoSelecao = TipoSelecao.TORNEIO
    tipo_crossover: TipoCrossover = TipoCrossover.UM_PONTO
    tamanho_torneio: int = 3
    taxa_crossover: float = 0.85
    taxa_mutacao: float = 0.02
    tamanho_elite: int = 3
    
    # Fitness
    max_score: float = 100.0
    alfa_invalidos: float = 2.0
    beta_comprimento: float = 0.5
    bonus_resolveu: float = 1000.0
    
    # Parada
    max_geracoes: int = 1000
    sem_melhoria_limite: int = 200
    
    # Reprodutibilidade
    seed_aleatorio: int | None = None
```

A `seed` é o que vai te salvar nos testes — execução reprodutível.

---

## Fase 4 — Experimentação

Aqui o trabalho deixa de ser código e vira ciência. **É onde os pontos do relatório moram.**

### Runner

Recebe `GAConfig` + estado inicial do puzzle:

- Roda **múltiplas execuções** (10-30) com seeds diferentes
- Coleta **por geração:** melhor fitness, fitness médio, diversidade (desvio padrão dos fitness), tempo decorrido
- Coleta **por execução:** gerações até resolver, taxa de sucesso, tamanho da solução final, resolveu ou não

### Batch Runner

Roda vários `GAConfig` diferentes pra comparação. Estrutura sugerida:

```python
casos = [
    estado_facil_5_movimentos,
    estado_medio_15_movimentos,
    estado_dificil_25_movimentos,
]

configs_selecao = [TipoSelecao.TORNEIO, TipoSelecao.ROLETA]
taxas_mutacao = [0.01, 0.05, 0.10]

resultados = []
for caso in casos:
    for selecao in configs_selecao:
        for pm in taxas_mutacao:
            cfg = GAConfig(tipo_selecao=selecao, taxa_mutacao=pm)
            for seed in range(10):
                cfg.seed_aleatorio = seed
                resultado = Runner(cfg, caso).run()
                resultados.append(resultado)
```

Salva tudo em **CSV/JSON**. O dashboard só lê esses arquivos. Separação clara entre executar e visualizar.

### Métricas Importantes Pro Relatório

| Métrica | Importância | Como apresentar |
|---|---|---|
| Taxa de sucesso | Alta | Barra por config |
| Gerações até resolver (médio) | Alta | Linha de convergência |
| Tempo médio de execução | Média | Tabela |
| Tamanho da solução encontrada | Média | Histograma |
| Manhattan final (quando não resolveu) | Alta | Boxplot |
| Diversidade ao longo das gerações | Diferencial | Linha sobreposta à convergência |

---

## Fase 5 — Visualizações

### Pygame — Animação da Solução

- Renderiza tabuleiro 3x3 com Pygame
- Recebe a sequência de movimentos do melhor cromossomo
- Anima passo a passo com delay configurável (~300ms entre movimentos)
- Mostra na tela: contador de movimentos, fitness atual, estado inicial e objetivo

Sugestão de layout: tabuleiro central, painel lateral com infos, botões de play/pause/reset.

### Dashboard — Streamlit (Recomendado)

Tela única com:

- **Sidebar:** seletor de configuração inicial, dropdowns dos parâmetros
- **Gráfico de convergência:** melhor fitness × geração (média ± desvio sobre N execuções)
- **Comparação entre configs:** barras de taxa de sucesso, boxplot de gerações até resolver
- **Heatmap:** taxa de mutação × taxa de crossover → sucesso
- **Tabela:** config inicial + solução encontrada + nº movimentos

Se Streamlit parecer overkill, **matplotlib salvando PNGs** também resolve pro relatório.

---

## Fase 6 — Testes Unitários

Não precisa cobertura 100%. Foca no que **te dá confiança**.

### Puzzle (essencial)

```python
def test_movimento_cima_em_centro():
    # Vazio no centro (índice 4), move pra cima → vazio vai pro índice 1
    estado = (1, 2, 3, 4, 0, 5, 6, 7, 8)
    novo = aplicar_movimento(estado, Direcao.CIMA)
    assert novo == (1, 0, 3, 4, 2, 5, 6, 7, 8)

def test_movimento_invalido_nao_altera():
    # Vazio na borda superior, tentar mover pra cima → sem alteração
    estado = (0, 1, 2, 3, 4, 5, 6, 7, 8)
    novo = aplicar_movimento(estado, Direcao.CIMA)
    assert novo == estado

def test_solvabilidade():
    assert eh_soluvel((1, 2, 3, 4, 5, 6, 7, 8, 0)) == True
    assert eh_soluvel((1, 2, 3, 4, 5, 6, 8, 7, 0)) == False  # inversão única

def test_manhattan_no_goal_eh_zero():
    assert distancia_manhattan((1, 2, 3, 4, 5, 6, 7, 8, 0)) == 0
```

### GA (importante)

```python
def test_crossover_preserva_comprimento():
    pai1 = [random.randint(0, 1) for _ in range(160)]
    pai2 = [random.randint(0, 1) for _ in range(160)]
    filho1, filho2 = crossover_um_ponto(pai1, pai2)
    assert len(filho1) == 160 and len(filho2) == 160

def test_mutacao_zero_nao_altera():
    cromo = [0, 1, 0, 1, 0, 1]
    resultado = mutacao(cromo.copy(), taxa=0.0)
    assert resultado == cromo

def test_torneio_seleciona_melhor_majoritariamente():
    # Roda 1000 vezes, o melhor deve ser escolhido na esmagadora maioria
    populacao_com_fitness = [(c1, 10), (c2, 50), (c3, 30)]
    vezes_c2 = sum(1 for _ in range(1000) 
                   if torneio(populacao_com_fitness, k=3) == c2)
    assert vezes_c2 > 900

def test_elitismo_preserva_melhor():
    # Após uma geração, o melhor da anterior deve estar presente
    ...
```

### Integração

```python
def test_ag_curto_executa_sem_erro():
    cfg = GAConfig(tamanho_populacao=20, max_geracoes=10)
    estado_inicial = (1, 2, 3, 4, 5, 6, 0, 7, 8)  # 2 movimentos do goal
    resultado = Runner(cfg, estado_inicial).run()
    assert resultado.melhor_fitness is not None
```

Roda os testes com `pytest -v` e **tira screenshot pro anexo do relatório**. Professor adora ver isso.

---

## Fase 7 — Definindo os Parâmetros

A pergunta "qual o melhor valor" é exatamente o que o relatório responde. Pra começar (baseline):

| Parâmetro | Valor inicial | Faixa pra testar |
|---|---|---|
| População | 200 | 100, 200, 500 |
| Cromossomo (movimentos) | 80 | 50, 80, 150 |
| Taxa crossover | 0.85 | 0.7, 0.85, 0.95 |
| Taxa mutação | 0.03 | 0.01, 0.03, 0.05, 0.10 |
| Tam. torneio | 3 | 2, 3, 5 |
| Elite | 3 | 1, 3, 10 |
| Max gerações | 1000 | fixo |
| Estagnação limite | 200 | fixo |

### Sobre Punições

- **α (movimentos inválidos):** começa em 2. Se o AG está produzindo muito movimento inválido, sobe pra 5. Se está sendo restritivo demais (perdendo diversidade), abaixa pra 1.
- **β (comprimento da solução):** começa em 0.5. Esse parâmetro é fino — alto demais e o AG vira "minimização de movimentos" antes de resolver.
- **Bonus resolveu:** alto (1000+). Quando aparece um cromossomo que resolve, ele tem que dominar a seleção.

A discussão **"como cheguei nesses valores"** no relatório é o que diferencia trabalho 7 de trabalho 10. Mostra curvas de convergência pra diferentes valores e argumenta com dados.

---

## Ordem Prática de Execução

1. **Puzzle + testes do puzzle** (1 dia)
2. **Motor GA bem básico com fitness simples** + testes (1-2 dias)
3. **Roda manual**, valida convergência num puzzle fácil
4. **Refina fitness** (Manhattan + penalidades)
5. **Adiciona seleção alternativa, crossover alternativo**
6. **Runner + batch + métricas** (1 dia)
7. **Pygame animando** (1 dia, opcional mas vale ponto)
8. **Dashboard com gráficos** (1 dia)
9. **Roda todos os experimentos pro relatório** (deixa rodando, vai dormir)
10. **Escreve o relatório**

Total realista: **7-10 dias** se tocar com calma.

---

## Checklist Final

### Código
- [ ] Módulos separados (`puzzle/`, `ga/`, `experiment/`, `viz/`, `tests/`)
- [ ] `GAConfig` com todos os parâmetros tipados
- [ ] Solvabilidade verificada antes de rodar
- [ ] Fitness composto (Manhattan + penalidades + bônus)
- [ ] Dois operadores de seleção implementados
- [ ] Dois operadores de crossover implementados
- [ ] Elitismo implementado
- [ ] Critério de parada composto
- [ ] Seed reprodutível

### Testes
- [ ] Testes do puzzle (movimentos, validade, solvabilidade, heurísticas)
- [ ] Testes do GA (operadores preservam invariantes)
- [ ] Teste de integração (AG curto executa)
- [ ] Screenshot do `pytest -v` verde

### Visualização
- [ ] Pygame animando a solução
- [ ] Dashboard com gráfico de convergência
- [ ] Gráfico comparativo entre configurações
- [ ] Heatmap ou similar pra parâmetros

### Experimentação
- [ ] 3+ configurações iniciais do puzzle testadas
- [ ] Torneio vs Roleta comparados estatisticamente
- [ ] Pelo menos 3 valores de taxa de mutação testados
- [ ] 10+ execuções por config (com seeds diferentes)
- [ ] Resultados salvos em CSV/JSON

### Relatório
- [ ] Fundamentação teórica (representação, fitness, operadores, parada)
- [ ] Justificativa da codificação por movimentos (não por estado)
- [ ] Justificativa da Manhattan sobre Hamming
- [ ] Análise dos parâmetros com base nos dados
- [ ] Comparação honesta com A\* (AG não é o ótimo aqui, e tudo bem)
- [ ] Conclusão sobre quando usar AG faz sentido (problemas genéricos, sem heurística admissível conhecida, etc.)

---

> Última atualização: Maio/2026
