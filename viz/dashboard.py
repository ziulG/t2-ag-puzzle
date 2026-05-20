"""Dashboard Streamlit do 8-Puzzle AG.

Roda com: streamlit run viz/dashboard.py
Consome: results/<timestamp>/{runs.csv, historicos.csv, detalhes/*.json}
"""

from __future__ import annotations

import sys
from pathlib import Path

# Streamlit roda este arquivo como script — adiciona a raiz do projeto no sys.path
# para que `from viz._io ...` (e demais pacotes do projeto) funcione.
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from viz._io import (  # noqa: E402
    carregar_detalhe_json,
    carregar_historicos_csv,
    carregar_runs_csv,
    listar_execucoes,
)

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"


@st.cache_data(show_spinner=False)
def _carregar_pasta(pasta_str: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    pasta = Path(pasta_str)
    runs = carregar_runs_csv(pasta / "runs.csv")
    historicos = carregar_historicos_csv(pasta / "historicos.csv")
    return runs, historicos


def _sidebar() -> tuple[Path, pd.DataFrame, pd.DataFrame]:
    st.sidebar.title("8-Puzzle AG — Dashboard")
    pastas = listar_execucoes(RESULTS_DIR)
    if not pastas:
        st.sidebar.error(
            f"Nenhuma execução em {RESULTS_DIR}. Rode `python main.py run` primeiro."
        )
        st.stop()

    rotulo = {p.name: p for p in pastas}
    nome = st.sidebar.selectbox("Execução", list(rotulo.keys()))
    pasta = rotulo[nome]
    runs, historicos = _carregar_pasta(str(pasta))

    casos = sorted(runs["caso_nome"].unique())
    selecoes = sorted(runs["tipo_selecao"].unique())
    crossovers = sorted(runs["tipo_crossover"].unique())
    mutacoes = sorted(runs["taxa_mutacao"].unique())

    f_casos = st.sidebar.multiselect("Casos", casos, default=casos)
    f_selecoes = st.sidebar.multiselect("Seleção", selecoes, default=selecoes)
    f_crossovers = st.sidebar.multiselect("Crossover", crossovers, default=crossovers)
    f_mutacoes = st.sidebar.multiselect("Taxa mutação", mutacoes, default=mutacoes)

    mask = (
        runs["caso_nome"].isin(f_casos)
        & runs["tipo_selecao"].isin(f_selecoes)
        & runs["tipo_crossover"].isin(f_crossovers)
        & runs["taxa_mutacao"].isin(f_mutacoes)
    )
    runs_f = runs[mask].copy()
    historicos_f = historicos[historicos["run_id"].isin(runs_f["run_id"])].copy()

    if st.sidebar.button("Recarregar"):
        st.cache_data.clear()
        st.rerun()

    return pasta, runs_f, historicos_f


def _secao_visao_geral(runs: pd.DataFrame) -> None:
    st.header("1. Visão Geral")
    if runs.empty:
        st.info("Sem dados para os filtros atuais.")
        return
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Execuções", len(runs))
    c2.metric("Taxa de sucesso", f"{runs['resolveu'].mean() * 100:.1f}%")
    c3.metric("Tempo médio (s)", f"{runs['tempo_total_s'].mean():.2f}")
    c4.metric("Gerações médias", f"{runs['geracoes_executadas'].mean():.0f}")

    resumo = (
        runs.groupby(["caso_nome", "tipo_selecao", "taxa_mutacao"], as_index=False)
        .agg(
            n=("run_id", "count"),
            taxa_sucesso=("resolveu", "mean"),
            geracoes_media=("geracoes_executadas", "mean"),
            tempo_medio_s=("tempo_total_s", "mean"),
            manhattan_final_medio=("manhattan_final", "mean"),
        )
        .sort_values(["caso_nome", "tipo_selecao", "taxa_mutacao"])
    )
    st.dataframe(resumo, use_container_width=True)


def _secao_convergencia(runs: pd.DataFrame, historicos: pd.DataFrame) -> None:
    st.header("2. Convergência")
    if historicos.empty:
        st.info("Sem dados para a seleção atual.")
        return

    meta = runs[["run_id", "caso_nome", "tipo_selecao", "taxa_mutacao"]]
    df = historicos.merge(meta, on="run_id", how="inner")
    df["config"] = (
        df["caso_nome"] + " | " + df["tipo_selecao"] + " | pm=" + df["taxa_mutacao"].astype(str)
    )

    configs = sorted(df["config"].unique())
    escolhidas = st.multiselect(
        "Configs no gráfico", configs, default=configs[: min(4, len(configs))]
    )
    df = df[df["config"].isin(escolhidas)]
    if df.empty:
        st.info("Selecione ao menos uma config.")
        return

    fig, ax = plt.subplots(figsize=(10, 5))
    for cfg, grupo in df.groupby("config"):
        agg = grupo.groupby("geracao")["melhor_fitness"].agg(["mean", "std"]).reset_index()
        ax.plot(agg["geracao"], agg["mean"], label=cfg)
        ax.fill_between(
            agg["geracao"],
            agg["mean"] - agg["std"].fillna(0),
            agg["mean"] + agg["std"].fillna(0),
            alpha=0.15,
        )
    ax.set_xlabel("Geração")
    ax.set_ylabel("Melhor fitness (média ± desvio)")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    st.pyplot(fig)


def _secao_comparacao(runs: pd.DataFrame) -> None:
    st.header("3. Comparação de Configurações")
    if runs.empty:
        st.info("Sem dados.")
        return

    agg = (
        runs.groupby(["tipo_selecao", "taxa_mutacao"], as_index=False)
        .agg(taxa_sucesso=("resolveu", "mean"))
        .sort_values(["tipo_selecao", "taxa_mutacao"])
    )
    agg["config"] = agg["tipo_selecao"] + " | pm=" + agg["taxa_mutacao"].astype(str)

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(agg["config"], agg["taxa_sucesso"] * 100)
    ax.set_ylabel("Taxa de sucesso (%)")
    ax.set_xticks(range(len(agg["config"])))
    ax.set_xticklabels(agg["config"], rotation=30, ha="right")
    ax.grid(axis="y", alpha=0.3)
    st.pyplot(fig)

    resolvidos = runs[runs["resolveu"]]
    if not resolvidos.empty:
        fig2, ax2 = plt.subplots(figsize=(10, 4))
        labels = sorted(resolvidos["tipo_selecao"].unique())
        grupos = [
            resolvidos[resolvidos["tipo_selecao"] == s]["geracoes_executadas"].values
            for s in labels
        ]
        ax2.boxplot(grupos, tick_labels=labels)
        ax2.set_ylabel("Gerações até resolver")
        ax2.set_xlabel("Tipo de seleção")
        st.pyplot(fig2)
    else:
        st.info("Nenhuma execução filtrada resolveu — boxplot omitido.")


def _secao_heatmap(runs: pd.DataFrame) -> None:
    st.header("4. Heatmap de Parâmetros")
    if runs.empty:
        st.info("Sem dados.")
        return

    pivot = (
        runs.pivot_table(
            index="taxa_mutacao",
            columns="tipo_crossover",
            values="resolveu",
            aggfunc="mean",
        )
        * 100
    )
    if pivot.empty:
        st.info("Sem dados para o heatmap.")
        return

    fig, ax = plt.subplots(figsize=(6, 4))
    im = ax.imshow(pivot.values, cmap="viridis", aspect="auto")
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    ax.set_xlabel("Tipo de crossover")
    ax.set_ylabel("Taxa de mutação")
    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]):
            valor = pivot.values[i, j]
            ax.text(j, i, f"{valor:.0f}%", ha="center", va="center", color="white")
    fig.colorbar(im, ax=ax, label="Taxa de sucesso (%)")
    st.pyplot(fig)


def _secao_por_caso(runs: pd.DataFrame) -> None:
    st.header("5. Análise por Caso")
    if runs.empty:
        st.info("Sem dados.")
        return
    por_caso = runs.groupby("caso_nome", as_index=False).agg(
        n=("run_id", "count"),
        taxa_sucesso=("resolveu", "mean"),
        geracoes_media=("geracoes_executadas", "mean"),
        manhattan_final_medio=("manhattan_final", "mean"),
        tempo_medio_s=("tempo_total_s", "mean"),
    )
    st.dataframe(por_caso, use_container_width=True)

    # Bar chart de taxa de sucesso por caso
    fig, ax = plt.subplots(figsize=(8, 3))
    ax.bar(por_caso["caso_nome"], por_caso["taxa_sucesso"] * 100, color="#3498db")
    ax.set_ylabel("Taxa de sucesso (%)")
    ax.set_xlabel("Caso")
    ax.grid(axis="y", alpha=0.3)
    st.pyplot(fig)


def _secao_inspecao(pasta: Path, runs: pd.DataFrame, historicos: pd.DataFrame) -> None:
    st.header("6. Inspeção Individual")
    if runs.empty:
        st.info("Sem dados.")
        return
    run_id = st.selectbox("Run", sorted(runs["run_id"].tolist()))
    h = historicos[historicos["run_id"] == run_id]
    if not h.empty:
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(h["geracao"], h["melhor_fitness"], label="melhor")
        ax.plot(h["geracao"], h["fitness_medio"], label="médio", alpha=0.7)
        ax.set_xlabel("Geração")
        ax.set_ylabel("Fitness")
        ax.legend()
        ax.grid(alpha=0.3)
        st.pyplot(fig)

    json_path = pasta / "detalhes" / f"{run_id}.json"
    if json_path.exists():
        detalhe = carregar_detalhe_json(json_path)
        st.json({k: v for k, v in detalhe.items() if k not in {"melhor_cromossomo", "historico"}})
        st.code(f"python main.py animate {json_path}", language="bash")


def main() -> None:
    st.set_page_config(page_title="8-Puzzle AG Dashboard", layout="wide")
    pasta, runs, historicos = _sidebar()
    _secao_visao_geral(runs)
    _secao_convergencia(runs, historicos)
    _secao_comparacao(runs)
    _secao_heatmap(runs)
    _secao_por_caso(runs)
    _secao_inspecao(pasta, runs, historicos)


if __name__ == "__main__":
    main()
