"""Estado objetivo do 8-puzzle e checagem de objetivo.

Mantido sem dependências de outros módulos de ``puzzle/`` para servir de folha
no grafo de imports (``heuristicas`` depende deste, não o contrário).
"""

GOAL: tuple[int, ...] = (1, 2, 3, 4, 5, 6, 7, 8, 0)


def eh_objetivo(estado: tuple[int, ...]) -> bool:
    """Retorna True se o estado é exatamente o estado objetivo (GOAL)."""
    return estado == GOAL
