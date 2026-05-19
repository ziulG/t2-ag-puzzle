"""Configuração do Algoritmo Genético (Fase 3 do roadmap).

Módulo neutro: não importa ``puzzle/`` nem ``ga/``. ``GAConfig`` é o contrato
de parâmetros do motor; os defaults são exatamente os do roadmap.
"""

from dataclasses import dataclass
from enum import Enum


class TipoSelecao(Enum):
    """Operador de seleção a usar no AG."""

    TORNEIO = "torneio"
    ROLETA = "roleta"


class TipoCrossover(Enum):
    """Operador de crossover a usar no AG."""

    UM_PONTO = "um_ponto"
    UNIFORME = "uniforme"


@dataclass
class GAConfig:
    """Todos os parâmetros do AG, tipados e versionáveis."""

    # População
    tamanho_populacao: int = 200
    tamanho_cromossomo: int = 80          # número de movimentos (2 bits cada)

    # Operadores
    tipo_selecao: TipoSelecao = TipoSelecao.TORNEIO
    tipo_crossover: TipoCrossover = TipoCrossover.UM_PONTO
    tamanho_torneio: int = 3
    taxa_crossover: float = 0.85
    taxa_mutacao: float = 0.02
    tamanho_elite: int = 3

    # Fitness (alfa/beta/bonus só usados na Fase 3; presentes já por contrato)
    max_score: float = 100.0
    alfa_invalidos: float = 2.0
    beta_comprimento: float = 0.5
    bonus_resolveu: float = 1000.0

    # Parada
    max_geracoes: int = 1000
    sem_melhoria_limite: int = 200

    # Reprodutibilidade
    seed_aleatorio: int | None = None
