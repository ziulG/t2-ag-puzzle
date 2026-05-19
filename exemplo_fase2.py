"""Demo da Fase 2: roda o AG num puzzle de exemplo e imprime, em texto, a
curva de convergência (gráfico fica para a Fase 4) e a solução decodificada.

Uso:
    python3 exemplo_fase2.py
"""

from config import GAConfig
from fitness import cria_fitness, decodifica_solucao
from ga.engine import executar_ag

# Puzzle solúvel a exatamente 5 movimentos do GOAL (verificado por BFS).
ESTADO_INICIAL = (1, 2, 3, 0, 8, 5, 4, 7, 6)


def main() -> None:
    cfg = GAConfig(tamanho_populacao=20, tamanho_cromossomo=10,
                   max_geracoes=200, sem_melhoria_limite=200, seed_aleatorio=2)
    resultado = executar_ag(
        cfg, cria_fitness(ESTADO_INICIAL, cfg), fitness_objetivo=cfg.max_score
    )

    print(f"estado inicial : {ESTADO_INICIAL}")
    print(f"criterio parada: {resultado.criterio_parada}")
    print(f"geracoes       : {resultado.geracoes_executadas}")
    print("--- curva de convergencia (gen: melhor | media | diversidade) ---")
    for h in resultado.historico:
        print(f"{h.geracao:3d}: {h.melhor_fitness:6.1f} | "
              f"{h.fitness_medio:6.2f} | {h.diversidade:5.2f}")

    sol = decodifica_solucao(ESTADO_INICIAL, resultado.melhor_cromossomo, cfg)
    print("--- solucao ---")
    print(f"resolveu          : {sol.resolveu}")
    print(f"melhor manhattan  : {sol.melhor_manhattan}")
    print(f"passos ate melhor : {sol.passos_ate_melhor}")
    print("movimentos        :",
          [d.name for d in sol.movimentos[: sol.passos_ate_melhor]])


if __name__ == "__main__":
    main()
