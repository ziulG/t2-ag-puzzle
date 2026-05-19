# 8-Puzzle com Algoritmo Genético

Resolução do 8-puzzle usando um Algoritmo Genético implementado **na munheca**
(sem bibliotecas de GA). Trabalho de Inteligência Artificial.

> Estado atual: **Fase 1 — Fundação (Domínio do Puzzle)** concluída.
> As fases seguintes (motor do AG, experimentação, visualizações) virão sobre
> esta base. O `roadmap-8puzzle-ag.md` é a fonte da verdade do projeto.

## Requisitos

- Python 3.11+ (desenvolvido e testado em 3.14)
- `pytest` (única dependência externa nesta fase)

## Setup

```bash
# 1. Criar e ativar um ambiente virtual
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Instalar dependências
pip install -r requirements.txt
```

## Rodar os testes

```bash
pytest tests/test_puzzle.py -v
```

## Estrutura do projeto

```
t2-ag-puzzle/
├── puzzle/             # Domínio do 8-puzzle (Fase 1)
│   ├── estado.py       # Representação do tabuleiro e posição do vazio
│   ├── movimentos.py   # Enum Direcao, validação e aplicação de movimentos
│   ├── goal.py         # Estado objetivo e checagem
│   └── heuristicas.py  # Manhattan, Hamming e solvabilidade
├── ga/                 # Motor do Algoritmo Genético (fases futuras)
├── experiment/         # Execução de experimentos (fases futuras)
├── viz/                # Visualizações (fases futuras)
├── tests/              # Testes unitários
│   └── test_puzzle.py  # Testes do domínio do puzzle
├── conftest.py         # Faz o pytest enxergar os pacotes (sys.path)
├── requirements.txt
└── README.md
```

## O domínio do puzzle

O estado é uma `tuple[int, ...]` de 9 elementos, com `0` representando o espaço
vazio. O estado objetivo é `(1, 2, 3, 4, 5, 6, 7, 8, 0)`. Cada direção move o
**espaço vazio** naquele sentido (a peça vizinha ocupa o lugar do vazio).

Apenas metade das permutações do 8-puzzle é solucionável; use
`puzzle.heuristicas.eh_soluvel` antes de tentar resolver um estado.
