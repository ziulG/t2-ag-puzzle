"""Gera as 7 figuras matplotlib do RELATORIO.md.

Lê o batch mais recente de ``results/`` (ou o passado via ``--batch``) e os
dados de ``results/astar/comparativo.json``, produzindo PNGs em
``docs/figuras/``. As funções são autocontidas para facilitar regenerar
uma figura específica sem rodar tudo.

Estilo: matplotlib puro (sem seaborn), DPI 150, paleta consistente:
``#2c3e50`` (escuro), ``#3498db`` (azul), ``#e74c3c`` (vermelho), ``#2ecc71``
(verde). Labels em português, legenda discreta.

Uso::

    python -m scripts.gerar_figuras_relatorio                # auto-discover batch
    python -m scripts.gerar_figuras_relatorio --batch results/2026-05-21_16-39-05
"""

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Estilo
# ---------------------------------------------------------------------------

COR_ESCURO = "#2c3e50"
COR_AZUL = "#3498db"
COR_VERMELHO = "#e74c3c"
COR_VERDE = "#2ecc71"
COR_LARANJA = "#e67e22"

ORDEM_CASOS = ["facil", "medio", "dificil"]
LABEL_CASOS = {"facil": "Fácil (d*=5)", "medio": "Médio (d*=15)", "dificil": "Difícil (d*=25)"}

plt.rcParams.update({
    "figure.dpi": 150,
    "savefig.dpi": 150,
    "savefig.bbox": "tight",
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
    "axes.labelsize": 10,
    "axes.edgecolor": COR_ESCURO,
    "axes.linewidth": 0.8,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "grid.linewidth": 0.5,
    "legend.frameon": False,
})


# ---------------------------------------------------------------------------
# Carregamento dos dados
# ---------------------------------------------------------------------------

def descobrir_batch_mais_recente(raiz: Path = Path("results")) -> Path:
    """Pega a pasta mais recente em ``results/`` que tem ``runs.csv``."""
    candidatas = sorted(
        [p for p in raiz.glob("*") if p.is_dir() and (p / "runs.csv").exists()],
        reverse=True,
    )
    if not candidatas:
        raise FileNotFoundError(f"Nenhum batch encontrado em {raiz}/")
    return candidatas[0]


def carregar_runs(pasta_batch: Path) -> pd.DataFrame:
    df = pd.read_csv(pasta_batch / "runs.csv")
    df["resolveu"] = df["resolveu"].map({"True": True, "False": False, True: True, False: False})
    return df


def carregar_historicos(pasta_batch: Path) -> pd.DataFrame:
    return pd.read_csv(pasta_batch / "historicos.csv")


def carregar_astar(arquivo: Path) -> dict:
    return json.loads(arquivo.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Figuras
# ---------------------------------------------------------------------------

def figura_01_taxa_sucesso_por_caso(df: pd.DataFrame, destino: Path) -> Path:
    """Barras: taxa de sucesso (%) por caso, agrupando por (seleção × crossover)."""
    grupos = (
        df.groupby(["caso_nome", "tipo_selecao", "tipo_crossover"])["resolveu"]
        .mean()
        .reset_index()
    )

    fig, ax = plt.subplots(figsize=(8, 4.5))
    largura = 0.2
    casos = ORDEM_CASOS
    x = np.arange(len(casos))

    combinacoes = [
        ("torneio", "um_ponto", COR_AZUL, "Torneio + 1-ponto"),
        ("torneio", "uniforme", COR_VERDE, "Torneio + Uniforme"),
        ("roleta", "um_ponto", COR_VERMELHO, "Roleta + 1-ponto"),
        ("roleta", "uniforme", COR_LARANJA, "Roleta + Uniforme"),
    ]

    for i, (sel, cx, cor, label) in enumerate(combinacoes):
        valores = [
            grupos.query(
                "caso_nome == @c and tipo_selecao == @sel and tipo_crossover == @cx"
            )["resolveu"].mean() * 100
            for c in casos
        ]
        ax.bar(x + (i - 1.5) * largura, valores, largura, color=cor, label=label, edgecolor="white")

    ax.set_xticks(x)
    ax.set_xticklabels([LABEL_CASOS[c] for c in casos])
    ax.set_ylabel("Taxa de sucesso (%)")
    ax.set_title("Taxa de sucesso por caso e configuração")
    ax.set_ylim(0, 105)
    ax.legend(loc="upper right", fontsize=8)

    arquivo = destino / "fig_01_taxa_sucesso_caso.png"
    fig.savefig(arquivo)
    plt.close(fig)
    return arquivo


def figura_02_convergencia(
    df_runs: pd.DataFrame, df_hist: pd.DataFrame, destino: Path
) -> Path:
    """Curvas de convergência: melhor fitness médio ± IC95% bootstrap.

    Compara torneio vs roleta no caso médio, agregando todas as taxas de
    mutação e crossovers (para olhar o efeito da seleção).
    """
    ids_medio = set(df_runs[df_runs["caso_nome"] == "medio"]["run_id"])
    hist = df_hist[df_hist["run_id"].isin(ids_medio)].merge(
        df_runs[["run_id", "tipo_selecao"]], on="run_id"
    )

    fig, ax = plt.subplots(figsize=(8, 4.5))
    cores = {"torneio": COR_AZUL, "roleta": COR_VERMELHO}
    max_g = 100                          # zoom nas primeiras 100 gerações

    for selecao, cor in cores.items():
        sub = hist[hist["tipo_selecao"] == selecao]
        agreg = sub.groupby("geracao")["melhor_fitness"].agg(["mean", "std", "count"])
        agreg = agreg[agreg.index <= max_g]
        ic = 1.96 * agreg["std"] / np.sqrt(agreg["count"].clip(lower=1))
        ax.plot(agreg.index, agreg["mean"], color=cor, label=f"{selecao}", linewidth=1.8)
        ax.fill_between(agreg.index, agreg["mean"] - ic, agreg["mean"] + ic, color=cor, alpha=0.15)

    ax.set_xlabel("Geração")
    ax.set_ylabel("Melhor fitness (média ± IC95%)")
    ax.set_title("Convergência por seleção — caso médio")
    ax.legend(loc="lower right")

    arquivo = destino / "fig_02_convergencia.png"
    fig.savefig(arquivo)
    plt.close(fig)
    return arquivo


def figura_03_mutacao_sensibilidade(df: pd.DataFrame, destino: Path) -> Path:
    """Boxplot: gerações até resolver por taxa de mutação (caso médio + difícil)."""
    sub = df[(df["caso_nome"].isin(["medio", "dificil"])) & (df["resolveu"] == True)].copy()
    if sub.empty:
        sub = df[df["resolveu"] == True].copy()

    fig, ax = plt.subplots(figsize=(8, 4.5))
    taxas = sorted(sub["taxa_mutacao"].unique())
    dados_por_caso = {
        caso: [sub[(sub["taxa_mutacao"] == t) & (sub["caso_nome"] == caso)]["geracoes_executadas"].tolist()
               for t in taxas]
        for caso in ["medio", "dificil"]
        if caso in sub["caso_nome"].values
    }

    largura = 0.35
    x = np.arange(len(taxas))
    cores = {"medio": COR_AZUL, "dificil": COR_VERMELHO}
    deslocamento = {"medio": -largura / 2, "dificil": largura / 2}

    for caso, dados in dados_por_caso.items():
        positions = x + deslocamento[caso]
        bp = ax.boxplot(
            dados, positions=positions, widths=largura * 0.85,
            patch_artist=True, manage_ticks=False,
            boxprops=dict(facecolor=cores[caso], alpha=0.6, edgecolor=cores[caso]),
            medianprops=dict(color=COR_ESCURO, linewidth=1.4),
            whiskerprops=dict(color=cores[caso]),
            capprops=dict(color=cores[caso]),
            flierprops=dict(marker="o", markersize=3, markerfacecolor=cores[caso], markeredgecolor="none"),
        )
        # legenda manual
        ax.plot([], [], color=cores[caso], linewidth=8, alpha=0.6, label=LABEL_CASOS[caso])

    ax.set_xticks(x)
    ax.set_xticklabels([f"{t:.2f}" for t in taxas])
    ax.set_xlabel("Taxa de mutação (Pm)")
    ax.set_ylabel("Gerações até resolver (apenas runs que resolveram)")
    ax.set_title("Sensibilidade à taxa de mutação")
    ax.legend(loc="upper right")

    arquivo = destino / "fig_03_mutacao_sensibilidade.png"
    fig.savefig(arquivo)
    plt.close(fig)
    return arquivo


def figura_04_crossover_comparacao(df: pd.DataFrame, destino: Path) -> Path:
    """Barras pareadas: taxa de sucesso de um-ponto vs uniforme, por caso."""
    grupos = (
        df.groupby(["caso_nome", "tipo_crossover"])["resolveu"]
        .mean()
        .reset_index()
    )

    fig, ax = plt.subplots(figsize=(7, 4.2))
    largura = 0.35
    casos = ORDEM_CASOS
    x = np.arange(len(casos))

    vals_um = [grupos.query("caso_nome == @c and tipo_crossover == 'um_ponto'")["resolveu"].values[0] * 100
               if len(grupos.query("caso_nome == @c and tipo_crossover == 'um_ponto'")) else 0
               for c in casos]
    vals_uni = [grupos.query("caso_nome == @c and tipo_crossover == 'uniforme'")["resolveu"].values[0] * 100
                if len(grupos.query("caso_nome == @c and tipo_crossover == 'uniforme'")) else 0
                for c in casos]

    ax.bar(x - largura / 2, vals_um, largura, color=COR_AZUL, label="1-ponto", edgecolor="white")
    ax.bar(x + largura / 2, vals_uni, largura, color=COR_VERDE, label="Uniforme", edgecolor="white")

    ax.set_xticks(x)
    ax.set_xticklabels([LABEL_CASOS[c] for c in casos])
    ax.set_ylabel("Taxa de sucesso (%)")
    ax.set_title("Comparação de operadores de crossover")
    ax.set_ylim(0, 105)
    ax.legend(loc="upper right")

    # Anotar valores em cima das barras
    for i, (vu, vn) in enumerate(zip(vals_um, vals_uni)):
        ax.text(i - largura / 2, vu + 2, f"{vu:.0f}%", ha="center", fontsize=9, color=COR_ESCURO)
        ax.text(i + largura / 2, vn + 2, f"{vn:.0f}%", ha="center", fontsize=9, color=COR_ESCURO)

    arquivo = destino / "fig_04_crossover_comparacao.png"
    fig.savefig(arquivo)
    plt.close(fig)
    return arquivo


def figura_05_heatmap_pm_caso(df: pd.DataFrame, destino: Path) -> Path:
    """Heatmap: taxa de sucesso (%) em função de (caso × taxa de mutação)."""
    matriz = (
        df.groupby(["caso_nome", "taxa_mutacao"])["resolveu"].mean()
        .unstack("taxa_mutacao")
        .reindex(ORDEM_CASOS)
        * 100
    )

    fig, ax = plt.subplots(figsize=(6.5, 3.6))
    im = ax.imshow(matriz.values, aspect="auto", cmap="RdYlGn", vmin=0, vmax=100)

    ax.set_xticks(range(len(matriz.columns)))
    ax.set_xticklabels([f"{c:.2f}" for c in matriz.columns])
    ax.set_yticks(range(len(matriz.index)))
    ax.set_yticklabels([LABEL_CASOS[c] for c in matriz.index])
    ax.set_xlabel("Taxa de mutação")
    ax.set_title("Taxa de sucesso (%) — caso × mutação")

    for i in range(matriz.shape[0]):
        for j in range(matriz.shape[1]):
            valor = matriz.values[i, j]
            cor_texto = "white" if valor < 30 or valor > 70 else COR_ESCURO
            ax.text(j, i, f"{valor:.0f}%", ha="center", va="center",
                    color=cor_texto, fontweight="bold")

    cbar = fig.colorbar(im, ax=ax, shrink=0.85)
    cbar.set_label("Sucesso (%)")

    arquivo = destino / "fig_05_heatmap_pm_caso.png"
    fig.savefig(arquivo)
    plt.close(fig)
    return arquivo


def figura_06_ag_vs_astar(df: pd.DataFrame, astar: dict, destino: Path) -> Path:
    """Comparação AG vs A*: tempo (s, log) e passos da solução, por caso."""
    melhor_por_caso = {}
    for caso in ORDEM_CASOS:
        sub = df[(df["caso_nome"] == caso) & (df["resolveu"] == True)]
        if sub.empty:
            melhor_por_caso[caso] = {"tempo_s": np.nan, "passos": np.nan, "n": 0}
            continue
        melhor_por_caso[caso] = {
            "tempo_s": sub["tempo_total_s"].mean(),
            "passos": sub["tamanho_solucao_ag"].astype(float).mean(),
            "n": len(sub),
        }

    fig, (ax_t, ax_p) = plt.subplots(1, 2, figsize=(10, 4))
    casos = ORDEM_CASOS
    x = np.arange(len(casos))
    largura = 0.35

    # Tempo
    tempos_ag = [melhor_por_caso[c]["tempo_s"] for c in casos]
    tempos_astar = [astar[c]["tempo_s"] for c in casos]

    ax_t.bar(x - largura / 2, tempos_ag, largura, color=COR_AZUL, label="AG (média)", edgecolor="white")
    ax_t.bar(x + largura / 2, tempos_astar, largura, color=COR_VERMELHO, label="A* (ótimo)", edgecolor="white")
    ax_t.set_yscale("log")
    ax_t.set_xticks(x)
    ax_t.set_xticklabels([LABEL_CASOS[c] for c in casos])
    ax_t.set_ylabel("Tempo (s, escala log)")
    ax_t.set_title("Tempo de execução")
    ax_t.legend(loc="upper left", fontsize=9)

    # Passos
    passos_ag = [melhor_por_caso[c]["passos"] for c in casos]
    passos_astar = [astar[c]["passos_otimos"] for c in casos]

    ax_p.bar(x - largura / 2, passos_ag, largura, color=COR_AZUL, label="AG (média)", edgecolor="white")
    ax_p.bar(x + largura / 2, passos_astar, largura, color=COR_VERMELHO, label="A* (ótimo)", edgecolor="white")
    ax_p.set_xticks(x)
    ax_p.set_xticklabels([LABEL_CASOS[c] for c in casos])
    ax_p.set_ylabel("Tamanho da solução (movimentos)")
    ax_p.set_title("Qualidade da solução")
    ax_p.legend(loc="upper left", fontsize=9)

    # Anotar contagem N do AG
    for i, c in enumerate(casos):
        n = melhor_por_caso[c]["n"]
        ax_p.text(i - largura / 2, (passos_ag[i] or 0) + 1.5, f"n={n}",
                  ha="center", fontsize=8, color=COR_ESCURO)

    fig.suptitle("AG vs A* — tempo e qualidade", fontsize=13, fontweight="bold", y=1.02)

    arquivo = destino / "fig_06_ag_vs_astar.png"
    fig.savefig(arquivo)
    plt.close(fig)
    return arquivo


def figura_07_diversidade(
    df_runs: pd.DataFrame, df_hist: pd.DataFrame, destino: Path
) -> Path:
    """Diversidade (desvio padrão do fitness) ao longo das gerações, por taxa de mutação.

    Foca no caso médio para curvas serem interpretáveis.
    """
    ids_medio = df_runs[df_runs["caso_nome"] == "medio"][["run_id", "taxa_mutacao"]]
    hist = df_hist.merge(ids_medio, on="run_id")

    fig, ax = plt.subplots(figsize=(8, 4.5))
    cores = {0.01: COR_VERMELHO, 0.05: COR_AZUL, 0.10: COR_VERDE}
    max_g = 100

    for taxa in sorted(hist["taxa_mutacao"].unique()):
        sub = hist[hist["taxa_mutacao"] == taxa]
        agreg = sub.groupby("geracao")["diversidade"].mean()
        agreg = agreg[agreg.index <= max_g]
        ax.plot(agreg.index, agreg.values, color=cores.get(taxa, COR_ESCURO),
                linewidth=1.8, label=f"Pm = {taxa:.2f}")

    ax.set_xlabel("Geração")
    ax.set_ylabel("Diversidade (desvio padrão do fitness)")
    ax.set_title("Diversidade da população — caso médio")
    ax.legend(loc="upper right")

    arquivo = destino / "fig_07_diversidade.png"
    fig.savefig(arquivo)
    plt.close(fig)
    return arquivo


# ---------------------------------------------------------------------------
# Orquestração
# ---------------------------------------------------------------------------

def gerar_todas(pasta_batch: Path, arquivo_astar: Path, destino: Path) -> list[Path]:
    """Gera as 7 figuras e devolve a lista de arquivos criados."""
    destino.mkdir(parents=True, exist_ok=True)
    df_runs = carregar_runs(pasta_batch)
    df_hist = carregar_historicos(pasta_batch)
    astar = carregar_astar(arquivo_astar)

    arquivos = [
        figura_01_taxa_sucesso_por_caso(df_runs, destino),
        figura_02_convergencia(df_runs, df_hist, destino),
        figura_03_mutacao_sensibilidade(df_runs, destino),
        figura_04_crossover_comparacao(df_runs, destino),
        figura_05_heatmap_pm_caso(df_runs, destino),
        figura_06_ag_vs_astar(df_runs, astar, destino),
        figura_07_diversidade(df_runs, df_hist, destino),
    ]
    return arquivos


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gera figuras do RELATORIO.md.")
    parser.add_argument("--batch", type=Path, default=None,
                        help="Pasta do batch (default: mais recente em results/).")
    parser.add_argument("--astar", type=Path, default=Path("results/astar/comparativo.json"),
                        help="JSON do comparativo A*.")
    parser.add_argument("--destino", type=Path, default=Path("docs/figuras"),
                        help="Pasta de saída das PNGs.")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    pasta_batch = args.batch or descobrir_batch_mais_recente()
    print(f"Batch: {pasta_batch}")
    print(f"A*:    {args.astar}")
    print(f"Saída: {args.destino}\n")

    arquivos = gerar_todas(pasta_batch, args.astar, args.destino)
    for arq in arquivos:
        print(f"  ✓ {arq}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
