"""Roda A* nos casos padrão (fácil, médio, difícil) e salva o comparativo.

Saída: ``results/astar/comparativo.json`` com, para cada caso:

- ``estado_inicial``     — lista [9 ints]
- ``passos_otimos``      — comprimento da solução ótima
- ``nos_expandidos``     — quantos nós o A* extraiu da fronteira
- ``nos_gerados``        — quantos nós entraram na fronteira
- ``tempo_s``            — tempo de parede da resolução
- ``sequencia_movimentos`` — lista de nomes de direção (CIMA, BAIXO, ...)

Sanity check obrigatório: ``passos_otimos == caso.optimal_depth`` (que vem
do BFS em ``analise_otima``). Se falhar, é bug — abortamos.

Uso::

    python -m experiment.run_astar
"""

import json
from dataclasses import asdict
from pathlib import Path

from experiment.astar import resolver_astar
from experiment.casos_teste import CASOS_PADRAO


def _resultado_para_dict(caso_nome: str, resultado, optimal_depth: int) -> dict:
    """Serializa AStarResult + sanity check com a profundidade do BFS."""
    assert resultado.passos_otimos == optimal_depth, (
        f"Inconsistência no caso '{caso_nome}': A* deu {resultado.passos_otimos} "
        f"passos, mas o BFS de analise_otima diz {optimal_depth}."
    )
    d = asdict(resultado)
    d["caso_nome"] = caso_nome
    d["optimal_depth_bfs"] = optimal_depth
    d["estado_inicial"] = list(resultado.estado_inicial)
    d["sequencia_movimentos"] = [m.name for m in resultado.sequencia_movimentos]
    return d


def main() -> int:
    pasta = Path("results") / "astar"
    pasta.mkdir(parents=True, exist_ok=True)

    saida: dict[str, dict] = {}
    print(f"Rodando A* em {len(CASOS_PADRAO)} casos padrão...\n")
    for caso in CASOS_PADRAO:
        resultado = resolver_astar(caso.estado_inicial)
        registro = _resultado_para_dict(caso.nome, resultado, caso.optimal_depth)
        saida[caso.nome] = registro
        print(
            f"  [{caso.nome:8s}] passos={registro['passos_otimos']:3d}  "
            f"expandidos={registro['nos_expandidos']:6d}  "
            f"gerados={registro['nos_gerados']:6d}  "
            f"tempo={registro['tempo_s']*1000:7.2f} ms"
        )

    arquivo = pasta / "comparativo.json"
    arquivo.write_text(json.dumps(saida, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSalvo: {arquivo}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
