#!/usr/bin/env python3
"""Generate summary CSVs and charts from article-level LLM labels."""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from config import GRAPHS_DIR, SENTIMENT_ORDER, TABLES_DIR


PALETTE = {
    "muito negativo": "#8b1e3f",
    "negativo": "#d1495b",
    "neutro": "#7f8c8d",
    "positivo": "#2a9d8f",
    "muito positivo": "#1d6f42",
    "n/a": "#c8c8c8",
}


def load_labels(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"labels CSV not found: {path}")
    df = pd.read_csv(path, encoding="utf-8-sig")
    if "id" not in df.columns or "label" not in df.columns:
        raise SystemExit("labels CSV must include id and label columns")
    df["label"] = df["label"].fillna("n/a").str.strip().str.lower()
    df.loc[~df["label"].isin(SENTIMENT_ORDER), "label"] = "n/a"
    df["publishedAt"] = pd.to_datetime(df.get("publishedAt"), errors="coerce", utc=True)
    df["date"] = df["publishedAt"].dt.date
    df["month"] = df["publishedAt"].dt.to_period("M").astype(str)
    df["confidence"] = pd.to_numeric(df.get("confidence"), errors="coerce")
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
    fig, ax = plt.subplots(figsize=(14, 7))
    x = pd.to_datetime(monthly_pct.index)
    for label in SENTIMENT_ORDER:
        ax.plot(x, monthly_pct[label], marker="o", linewidth=2, label=label, color=PALETTE[label])
    ax.set_title("Percentual mensal de noticias por sentimento")
    ax.set_xlabel("Mes")
    ax.set_ylabel("% das noticias")
    ax.set_ylim(0, 100)
    ax.grid(True, alpha=0.25)
    ax.legend(ncol=3)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(graphs_dir / "linha_percentual_mensal_sentimentos.png", dpi=180)
    plt.close(fig)


def stacked_area(monthly_pct: pd.DataFrame, graphs_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(14, 7))
    x = pd.to_datetime(monthly_pct.index)
    ax.stackplot(
        x,
        [monthly_pct[label] for label in SENTIMENT_ORDER],
        labels=SENTIMENT_ORDER,
        colors=[PALETTE[label] for label in SENTIMENT_ORDER],
        alpha=0.85,
    )
    ax.set_title("Composicao mensal dos sentimentos")
    ax.set_xlabel("Mes")
    ax.set_ylabel("% das noticias")
    ax.set_ylim(0, 100)
    ax.legend(ncol=3, loc="upper left")
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(graphs_dir / "area_empilhada_percentual_mensal.png", dpi=180)
    plt.close(fig)


def bar_counts(counts: pd.DataFrame, graphs_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(counts["label"], counts["n_articles"], color=[PALETTE[label] for label in counts["label"]])
    ax.set_title("Quantidade de noticias por sentimento")
    ax.set_xlabel("Sentimento")
    ax.set_ylabel("Noticias")
    ax.tick_params(axis="x", rotation=25)
    fig.tight_layout()
    fig.savefig(graphs_dir / "barras_quantidade_por_sentimento.png", dpi=180)
    plt.close(fig)


def confidence_histogram(df: pd.DataFrame, graphs_dir: Path) -> None:
    valid = df.dropna(subset=["confidence"])
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(valid["confidence"], bins=20, color="#457b9d", edgecolor="white")
    ax.set_title("Histograma de confianca da classificacao")
    ax.set_xlabel("Confianca")
    ax.set_ylabel("Noticias")
    fig.tight_layout()
    fig.savefig(graphs_dir / "histograma_confianca.png", dpi=180)
    plt.close(fig)


def score_histogram(df: pd.DataFrame, graphs_dir: Path) -> None:
    valid = df.dropna(subset=["sentiment_score"]).copy()
    valid["sentiment_score"] = pd.to_numeric(valid["sentiment_score"], errors="coerce")
    valid = valid.dropna(subset=["sentiment_score"])
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(valid["sentiment_score"], bins=[-2.5, -1.5, -0.5, 0.5, 1.5, 2.5], color="#6c757d", edgecolor="white")
    ax.set_title("Histograma do escore de sentimento")
    ax.set_xlabel("Escore (-2 a 2)")
    ax.set_ylabel("Noticias")
    ax.set_xticks([-2, -1, 0, 1, 2])
    fig.tight_layout()
    fig.savefig(graphs_dir / "histograma_escore_sentimento.png", dpi=180)
    plt.close(fig)


def volume_line(df: pd.DataFrame, graphs_dir: Path) -> None:
    monthly_volume = df.dropna(subset=["publishedAt"]).groupby("month").size().sort_index()
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(pd.to_datetime(monthly_volume.index), monthly_volume.values, marker="o", color="#264653")
    ax.set_title("Volume mensal de noticias classificadas")
    ax.set_xlabel("Mes")
    ax.set_ylabel("Noticias")
    ax.grid(True, alpha=0.25)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(graphs_dir / "linha_volume_mensal_noticias.png", dpi=180)
    plt.close(fig)


def source_chart(df: pd.DataFrame, graphs_dir: Path, tables_dir: Path) -> None:
    source_counts = df.groupby(["sourceHost", "label"]).size().unstack(fill_value=0).reindex(columns=SENTIMENT_ORDER, fill_value=0)
    source_counts["total"] = source_counts.sum(axis=1)
    top = source_counts.sort_values("total", ascending=False).head(12).drop(columns=["total"])
    top.to_csv(tables_dir / "top_sources_sentiment_counts.csv", encoding="utf-8-sig")
    fig, ax = plt.subplots(figsize=(13, 7))
    top.plot(kind="bar", stacked=True, ax=ax, color=[PALETTE[label] for label in SENTIMENT_ORDER])
    ax.set_title("Sentimentos por fonte - top 12")
    ax.set_xlabel("Fonte")
    ax.set_ylabel("Noticias")
    ax.tick_params(axis="x", rotation=35)
    ax.legend(ncol=3)
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

    df = load_labels(args.labels)
    df.to_csv(args.tables_dir / "noticias_classificadas.csv", index=False, encoding="utf-8-sig")
    counts, monthly_pct = save_label_counts(df, args.tables_dir)

    line_percent(monthly_pct, args.graphs_dir)
    stacked_area(monthly_pct, args.graphs_dir)
    bar_counts(counts, args.graphs_dir)
    confidence_histogram(df, args.graphs_dir)
    score_histogram(df, args.graphs_dir)
    volume_line(df, args.graphs_dir)
    source_chart(df, args.graphs_dir, args.tables_dir)

    print(f"Wrote article CSV and summary tables to {args.tables_dir}")
    print(f"Wrote charts to {args.graphs_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
