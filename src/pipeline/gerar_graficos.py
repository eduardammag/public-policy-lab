from __future__ import annotations
import argparse
from pathlib import Path
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
from src.configuracoes.config import GRAPHS_DIR, SENTIMENT_ORDER, TABLES_DIR

TIME_PLOT_START = pd.Timestamp("2018-01-01")

PALETTE = {
    "muito negativo": "#8b0000",
    "negativo": "#d1495b",
    "neutro": "#7f8c8d",
    "positivo": "#2a9d8f",
    "muito positivo": "#1d6f42",
    "n/a": "#c8c8c8",
}

LINE_PALETTE = {
    "muito negativo": "#d00022",
    "negativo": "#ff7f2a",
    "positivo": "#42b6ff",
    "muito positivo": "#2ca62d",
}

LABELS_PT = {
    "muito negativo": "Muito negativo",
    "negativo": "Negativo",
    "neutro": "Neutro",
    "positivo": "Positivo",
    "muito positivo": "Muito positivo",
    "n/a": "Não aplicável",
}


def apply_plot_style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": "#333333",
            "axes.labelcolor": "#222222",
            "axes.titlecolor": "#111111",
            "axes.titlesize": 22,
            "axes.labelsize": 18,
            "xtick.labelsize": 15,
            "ytick.labelsize": 15,
            "legend.fontsize": 15,
            "legend.title_fontsize": 15,
            "font.size": 16,
            "grid.color": "#d8d8d8",
            "grid.linewidth": 0.8,
            "savefig.facecolor": "white",
            "savefig.bbox": "tight",
        }
    )


def format_time_axis(ax) -> None:
    ax.xaxis.set_major_locator(mdates.YearLocator(base=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.tick_params(axis="x", rotation=0)
    ax.margins(x=0.01)


def filter_time_index_from_2018(data: pd.DataFrame | pd.Series) -> pd.DataFrame | pd.Series:
    dates = pd.to_datetime(data.index, errors="coerce")
    return data.loc[dates >= TIME_PLOT_START]


def add_bar_labels(ax, padding: int = 3) -> None:
    for container in ax.containers:
        ax.bar_label(container, padding=padding, fontsize=14, color="#222222")


def load_labels(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"labels CSV not found: {path}")
    df = pd.read_csv(path, encoding="utf-8-sig")
    if "id" not in df.columns or "label" not in df.columns:
        raise SystemExit("labels CSV must include id and label columns")
    df["label"] = df["label"].fillna("n/a").str.strip().str.lower()
    df.loc[~df["label"].isin(SENTIMENT_ORDER), "label"] = "n/a"
    df["publishedAt"] = pd.to_datetime(df.get("publishedAt"), errors="coerce", utc=True)
    df["month"] = df["publishedAt"].dt.tz_convert(None).dt.to_period("M").astype(str)
    if "articleId" in df.columns:
        df["articleId"] = pd.to_numeric(df["articleId"], errors="coerce")
        df = (
            df.dropna(subset=["articleId"])
            .sort_values(["articleId", "publishedAt", "recordKey"])
            .drop_duplicates(subset=["articleId"], keep="first")
            .sort_values(["publishedAt", "articleId"])
            .reset_index(drop=True)
        )
    return df


def save_label_counts(df: pd.DataFrame, tables_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    counts = (
        df["label"]
        .value_counts()
        .reindex(SENTIMENT_ORDER, fill_value=0)
        .rename_axis("label")
        .reset_index(name="n_articles")
    )
    counts["percent"] = (counts["n_articles"] / len(df) * 100).round(4)
    counts.to_csv(tables_dir / "sentiment_counts.csv", index=False, encoding="utf-8-sig")

    monthly_counts = (
        df.dropna(subset=["publishedAt"])
        .groupby(["month", "label"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=SENTIMENT_ORDER, fill_value=0)
        .sort_index()
    )
    monthly_pct = monthly_counts.div(monthly_counts.sum(axis=1), axis=0).fillna(0) * 100
    monthly_pct.round(4).to_csv(tables_dir / "monthly_sentiment_percent.csv", encoding="utf-8-sig")
    monthly_counts.to_csv(tables_dir / "monthly_sentiment_counts.csv", encoding="utf-8-sig")
    return counts, monthly_pct


def line_percent(monthly_pct: pd.DataFrame, graphs_dir: Path) -> None:
    monthly_pct = filter_time_index_from_2018(monthly_pct)
    fig, ax = plt.subplots(figsize=(15, 8))
    x = pd.to_datetime(monthly_pct.index)
    line_labels = [label for label in SENTIMENT_ORDER if label not in {"neutro", "n/a"}]
    for label in line_labels:
        ax.plot(
            x,
            monthly_pct[label],
            linewidth=2.4,
            label=LABELS_PT[label],
            color=LINE_PALETTE[label],
        )
    ax.set_title("Evolução mensal da distribuição de sentimentos", pad=16, fontweight="bold")
    ax.set_xlabel("Ano de publicação")
    ax.set_ylabel("Participação nas notícias (%)")
    ax.set_ylim(0, 100)
    ax.spines[["top", "right"]].set_visible(False)
    format_time_axis(ax)
    ax.legend(
        ncol=2,
        frameon=True,
        facecolor="white",
        edgecolor="#dddddd",
        framealpha=0.94,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.16),
    )
    fig.tight_layout()
    fig.savefig(graphs_dir / "linha_percentual_mensal_sentimentos.png", dpi=180)
    plt.close(fig)


def stacked_area(monthly_pct: pd.DataFrame, graphs_dir: Path) -> None:
    monthly_pct = filter_time_index_from_2018(monthly_pct)
    fig, ax = plt.subplots(figsize=(15, 8))
    x = pd.to_datetime(monthly_pct.index)
    ax.stackplot(
        x,
        [monthly_pct[label] for label in SENTIMENT_ORDER],
        labels=[LABELS_PT[label] for label in SENTIMENT_ORDER],
        colors=[PALETTE[label] for label in SENTIMENT_ORDER],
        alpha=0.9,
    )
    ax.set_title("Composição mensal da cobertura por sentimento", pad=16, fontweight="bold")
    ax.set_xlabel("Ano de publicação")
    ax.set_ylabel("Participação nas notícias (%)")
    ax.set_ylim(0, 100)
    ax.spines[["top", "right"]].set_visible(False)
    format_time_axis(ax)
    ax.legend(
        ncol=3,
        frameon=True,
        facecolor="white",
        edgecolor="#dddddd",
        framealpha=0.94,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.16),
    )
    fig.tight_layout()
    fig.savefig(graphs_dir / "area_empilhada_percentual_mensal.png", dpi=180)
    plt.close(fig)


def bar_counts(counts: pd.DataFrame, graphs_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(12, 7))
    labels = [LABELS_PT[label] for label in counts["label"]]
    ax.bar(labels, counts["n_articles"], color=[PALETTE[label] for label in counts["label"]], width=0.68)
    ax.set_title("Distribuição geral das notícias por sentimento", pad=16, fontweight="bold")
    ax.set_xlabel("Sentimento")
    ax.set_ylabel("Número de notícias")
    ax.tick_params(axis="x", rotation=0)
    ax.spines[["top", "right"]].set_visible(False)
    add_bar_labels(ax)
    fig.tight_layout()
    fig.savefig(graphs_dir / "barras_quantidade_por_sentimento.png", dpi=180)
    plt.close(fig)


def score_histogram(df: pd.DataFrame, graphs_dir: Path) -> None:
    valid = df.dropna(subset=["sentiment_score"]).copy()
    valid["sentiment_score"] = pd.to_numeric(valid["sentiment_score"], errors="coerce")
    valid = valid.dropna(subset=["sentiment_score"])
    fig, ax = plt.subplots(figsize=(11, 6.5))
    ax.hist(valid["sentiment_score"], bins=[-2.5, -1.5, -0.5, 0.5, 1.5, 2.5], color="#6c757d", edgecolor="white")
    ax.set_title("Distribuição do escore de sentimento", pad=16, fontweight="bold")
    ax.set_xlabel("Escore de sentimento")
    ax.set_ylabel("Número de notícias")
    ax.set_xticks([-2, -1, 0, 1, 2])
    ax.set_xticklabels(["-2\nMuito negativo", "-1\nNegativo", "0\nNeutro", "1\nPositivo", "2\nMuito positivo"])
    ax.tick_params(axis="x", rotation=0)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(graphs_dir / "histograma_escore_sentimento.png", dpi=180)
    plt.close(fig)


def volume_line(df: pd.DataFrame, graphs_dir: Path) -> None:
    monthly_volume = df.dropna(subset=["publishedAt"]).groupby("month").size().sort_index()
    monthly_volume = filter_time_index_from_2018(monthly_volume)
    fig, ax = plt.subplots(figsize=(15, 7))
    ax.plot(pd.to_datetime(monthly_volume.index), monthly_volume.values, marker="o", markersize=4.5, linewidth=2.4, color="#264653")
    ax.set_title("Volume mensal de notícias analisadas", pad=16, fontweight="bold")
    ax.set_xlabel("Ano de publicação")
    ax.set_ylabel("Número de notícias")
    ax.spines[["top", "right"]].set_visible(False)
    format_time_axis(ax)
    fig.tight_layout()
    fig.savefig(graphs_dir / "linha_volume_mensal_noticias.png", dpi=180)
    plt.close(fig)


def source_chart(df: pd.DataFrame, graphs_dir: Path, tables_dir: Path) -> None:
    source_counts = df.groupby(["sourceHost", "label"]).size().unstack(fill_value=0).reindex(columns=SENTIMENT_ORDER, fill_value=0)
    source_counts["total"] = source_counts.sum(axis=1)
    top = source_counts.sort_values("total", ascending=False).head(12).drop(columns=["total"])
    top.to_csv(tables_dir / "top_sources_sentiment_counts.csv", encoding="utf-8-sig")
    fig, ax = plt.subplots(figsize=(13, 8))
    top = top.iloc[::-1]
    top.rename(columns=LABELS_PT).plot(kind="barh", stacked=True, ax=ax, color=[PALETTE[label] for label in SENTIMENT_ORDER], width=0.72)
    ax.set_title("Distribuição de sentimentos nas principais fontes", pad=16, fontweight="bold")
    ax.set_xlabel("Número de notícias")
    ax.set_ylabel("Fonte de publicação")
    ax.tick_params(axis="y", rotation=0)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(
        ncol=3,
        frameon=False,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.10),
        title="Sentimento",
    )
    fig.tight_layout()
    fig.savefig(graphs_dir / "barras_empilhadas_top_fontes.png", dpi=180)
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--labels", type=Path, default=TABLES_DIR / "llm_labels.csv")
    parser.add_argument("--tables-dir", type=Path, default=TABLES_DIR)
    parser.add_argument("--graphs-dir", type=Path, default=GRAPHS_DIR)
    args = parser.parse_args()

    args.tables_dir.mkdir(parents=True, exist_ok=True)
    args.graphs_dir.mkdir(parents=True, exist_ok=True)

    apply_plot_style()

    df = load_labels(args.labels)
    article_columns = [
        "recordKey",
        "jsonIndex",
        "id",
        "articleId",
        "publishedAt",
        "publishedDisplay",
        "sourceName",
        "sourceHost",
        "title",
        "storyId",
        "storyTitle",
        "targetKeys",
        "label",
        "sentiment_score",
        "reason",
        "evidencia_sentimento",
        "evento",
        "evento_chave",
        "evento_id",
        "tipo_evento",
        "local",
        "data_evento",
        "descricao_curta",
        "evidencia_evento",
        "model",
        "month",
    ]
    df[[col for col in article_columns if col in df.columns]].to_csv(
        args.tables_dir / "noticias_classificadas.csv",
        index=False,
        encoding="utf-8-sig",
    )
    counts, monthly_pct = save_label_counts(df, args.tables_dir)

    line_percent(monthly_pct, args.graphs_dir)
    stacked_area(monthly_pct, args.graphs_dir)
    bar_counts(counts, args.graphs_dir)
    score_histogram(df, args.graphs_dir)
    volume_line(df, args.graphs_dir)
    source_chart(df, args.graphs_dir, args.tables_dir)

    print(f"Wrote article CSV and summary tables to {args.tables_dir}")
    print(f"Wrote charts to {args.graphs_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
