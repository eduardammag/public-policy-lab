from __future__ import annotations

import argparse
import csv
import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd

from src.configuracoes.config import CONSOLIDA, SENTIMENT_ORDER, TABLES_DIR


DEFAULT_LABELS = TABLES_DIR / "noticias_classificadas.csv"
EVENTS_BY_ARTICLE = TABLES_DIR / "eventos_por_noticia.csv"

SCORE_MAP = {
    "muito negativo": -2,
    "negativo": -1,
    "neutro": 0,
    "positivo": 1,
    "muito positivo": 2,
    "n/a": pd.NA,
}

EVENT_COLUMNS = [
    "evento",
    "evento_chave",
    "evento_id",
    "tipo_evento",
    "local",
    "data_evento",
    "descricao_curta",
]

ARTICLE_FIELDS = [
    "articleId",
    "recordKey",
    "publishedAt",
    "sourceName",
    "sourceHost",
    "title",
    "label",
    "sentiment_score",
    *EVENT_COLUMNS,
    "model",
]


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", str(text or ""))
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return re.sub(r"-+", "-", text) or "evento-sem-chave"


def normalize_label(label: str) -> str:
    label = str(label or "").strip().lower()
    return label if label in SENTIMENT_ORDER else "n/a"


def load_unified_labels(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"input CSV not found: {path}")
    df = pd.read_csv(path, encoding="utf-8-sig", keep_default_na=False)
    missing = [col for col in ["articleId", "recordKey", "title", "label", "evento_chave"] if col not in df.columns]
    if missing:
        raise SystemExit(
            "CSV does not contain unified prompt event fields. "
            "Rerun `python -m src.pipeline.classificar_noticias --all --workers 6 --no-resume` "
            f"and then regenerate rankings. Missing: {', '.join(missing)}"
        )
    df["articleId"] = pd.to_numeric(df["articleId"], errors="coerce")
    df = df.dropna(subset=["articleId"]).copy()
    df["articleId"] = df["articleId"].astype(int)
    df["publishedAtSort"] = pd.to_datetime(df.get("publishedAt"), errors="coerce", utc=True)
    df["label"] = df["label"].map(normalize_label)
    if "sentiment_score" in df.columns:
        df["sentiment_score"] = pd.to_numeric(df["sentiment_score"], errors="coerce")
    else:
        df["sentiment_score"] = pd.NA
    fallback_score = df["label"].map(SCORE_MAP)
    df["sentiment_score"] = df["sentiment_score"].fillna(fallback_score)
    df["evento"] = df["evento"].where(df["evento"].astype(str).str.len() > 0, df["evento_chave"])
    df["evento_id"] = df["evento_id"].where(df["evento_id"].astype(str).str.len() > 0, df["evento_chave"].map(slugify))
    return (
        df.sort_values(["articleId", "publishedAtSort", "recordKey"])
        .drop_duplicates(subset=["articleId"], keep="first")
        .sort_values(["publishedAtSort", "articleId"])
        .reset_index(drop=True)
    )


def write_article_events(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cols = [col for col in ARTICLE_FIELDS if col in df.columns]
    df[cols].to_csv(path, index=False, encoding="utf-8-sig", quoting=csv.QUOTE_MINIMAL)


def aggregate_events(events: pd.DataFrame, min_articles: int) -> pd.DataFrame:
    rows = []
    for event_id, group in events.groupby("evento_id"):
        counts = group["label"].value_counts().to_dict()
        n = len(group)
        positive_n = counts.get("positivo", 0) + counts.get("muito positivo", 0)
        negative_n = counts.get("negativo", 0) + counts.get("muito negativo", 0)
        very_positive_n = counts.get("muito positivo", 0)
        very_negative_n = counts.get("muito negativo", 0)
        positive_weight = counts.get("positivo", 0) + 2 * very_positive_n
        negative_weight = counts.get("negativo", 0) + 2 * very_negative_n
        score_series = pd.to_numeric(group["sentiment_score"], errors="coerce")
        score_mean = score_series.mean()
        classified_n = int(score_series.notna().sum())
        valid_denominator = classified_n if classified_n else n
        rows.append(
            {
                "evento_id": event_id,
                "evento": group["evento_chave"].mode().iloc[0],
                "evento_exemplo": group["evento"].mode().iloc[0],
                "tipo_evento": group["tipo_evento"].mode().iloc[0] if "tipo_evento" in group else "",
                "local": group["local"].mode().iloc[0] if "local" in group else "",
                "n_artigos": n,
                "n_classificados": classified_n,
                "score_medio": round(score_mean, 4) if pd.notna(score_mean) else pd.NA,
                "media_sentimento": round(score_mean, 4) if pd.notna(score_mean) else pd.NA,
                "muito_negativo": very_negative_n,
                "negativo": counts.get("negativo", 0),
                "neutro": counts.get("neutro", 0),
                "positivo": counts.get("positivo", 0),
                "muito_positivo": very_positive_n,
                "n/a": counts.get("n/a", 0),
                "n_positivas": positive_n,
                "n_negativas": negative_n,
                "n_muito_positivas": very_positive_n,
                "n_muito_negativas": very_negative_n,
                "share_positivo": round(positive_n / n, 4),
                "share_negativo": round(negative_n / n, 4),
                "share_muito_positivo": round(very_positive_n / valid_denominator, 4) if valid_denominator else 0,
                "share_muito_negativo": round(very_negative_n / valid_denominator, 4) if valid_denominator else 0,
                "peso_positivo": positive_weight,
                "peso_negativo": negative_weight,
                "titulos_exemplo": " | ".join(group["title"].drop_duplicates().head(5).astype(str)),
            }
        )
    summary = pd.DataFrame(rows)
    if min_articles > 1:
        summary = summary[summary["n_artigos"] >= min_articles].copy()
    return summary.sort_values(["n_artigos", "score_medio"], ascending=[False, False])


def write_rankings(
    events: pd.DataFrame,
    min_articles: int,
    min_classified: int,
    tables_dir: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    summary = aggregate_events(events, min_articles=1)
    ranked = aggregate_events(events, min_articles=min_articles)
    ranked = ranked[ranked["score_medio"].notna()].copy()
    ranked = ranked[ranked["n_classificados"] >= min_classified].copy()

    very_positive = ranked.sort_values(
        ["score_medio", "share_positivo", "share_muito_positivo", "peso_positivo", "n_artigos"],
        ascending=[False, False, False, False, False],
    )
    very_positive = very_positive[
        (very_positive["score_medio"] > 0)
        & (very_positive["n_positivas"] > very_positive["n_negativas"])
    ].copy()

    very_negative = ranked.sort_values(
        ["score_medio", "share_negativo", "share_muito_negativo", "peso_negativo", "n_artigos"],
        ascending=[True, False, False, False, False],
    )
    very_negative = very_negative[
        (very_negative["score_medio"] < 0)
        & (very_negative["n_negativas"] > very_negative["n_positivas"])
    ].copy()

    summary.to_csv(tables_dir / "eventos_resumo.csv", index=False, encoding="utf-8-sig")
    very_positive.to_csv(tables_dir / "eventos_muito_positivos.csv", index=False, encoding="utf-8-sig")
    very_negative.to_csv(tables_dir / "eventos_muito_negativos.csv", index=False, encoding="utf-8-sig")
    return summary, very_positive, very_negative


def build_markdown(
    events: pd.DataFrame,
    very_positive: pd.DataFrame,
    very_negative: pd.DataFrame,
    min_articles: int,
    min_classified: int,
) -> str:
    event_counts = events["evento_id"].value_counts()
    lines = [
        "# Eventos Muito Positivos e Muito Negativos - Seguranca Presente",
        "",
        "Os eventos foram agrupados exclusivamente por `evento_chave`/`evento_id`, conforme retornado pelo prompt de classificacao.",
        "Este script nao aplica consolidacao por similaridade, tema agregado ou heuristica textual posterior.",
        "",
        f"- Noticias unicas analisadas: **{len(events)}**",
        f"- `evento_id` distintos: **{len(event_counts)}**.",
        f"- Criterio do ranking: eventos com pelo menos **{min_articles}** noticia(s) e **{min_classified}** escore(s) valido(s).",
        "- `score_medio` usa: muito negativo=-2, negativo=-1, neutro=0, positivo=1, muito positivo=2; n/a fica fora da media.",
        "- O ranking positivo prioriza score medio alto, proporcao positiva e peso de `muito positivo`.",
        "- O ranking negativo prioriza score medio baixo, proporcao negativa e peso de `muito negativo`.",
        "",
        "## Eventos com Cobertura Mais Positiva",
        "",
    ]
    for idx, row in enumerate(very_positive.head(25).itertuples(index=False), 1):
        lines.append(
            f"{idx}. **{row.evento_exemplo}** - score medio {row.score_medio}; "
            f"{row.n_artigos} noticia(s); positivos={row.positivo + row.muito_positivo}; "
            f"muito positivos={row.muito_positivo}; negativos={row.negativo + row.muito_negativo}. "
            f"Exemplos: {row.titulos_exemplo}"
        )
    lines.extend(["", "## Eventos com Cobertura Mais Negativa", ""])
    for idx, row in enumerate(very_negative.head(25).itertuples(index=False), 1):
        lines.append(
            f"{idx}. **{row.evento_exemplo}** - score medio {row.score_medio}; "
            f"{row.n_artigos} noticia(s); negativos={row.negativo + row.muito_negativo}; "
            f"muito negativos={row.muito_negativo}; positivos={row.positivo + row.muito_positivo}. "
            f"Exemplos: {row.titulos_exemplo}"
        )
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABELS)
    parser.add_argument("--out", type=Path, default=EVENTS_BY_ARTICLE)
    parser.add_argument("--tables-dir", type=Path, default=TABLES_DIR)
    parser.add_argument("--min-articles", type=int, default=1)
    parser.add_argument("--min-classified", type=int, default=None)
    parser.add_argument("--markdown", type=Path, default=TABLES_DIR / "ranking-eventos.md")
    parser.add_argument("--update-consolidacao", action="store_true")
    args = parser.parse_args(argv[1:])
    args.tables_dir.mkdir(parents=True, exist_ok=True)
    min_classified = args.min_articles if args.min_classified is None else args.min_classified

    events = load_unified_labels(args.labels)
    write_article_events(events, args.out)
    _summary, very_positive, very_negative = write_rankings(
        events,
        args.min_articles,
        min_classified,
        args.tables_dir,
    )
    markdown = build_markdown(events, very_positive, very_negative, args.min_articles, min_classified)
    args.markdown.write_text(markdown, encoding="utf-8")
    if args.update_consolidacao:
        existing = CONSOLIDA.read_text(encoding="utf-8") if CONSOLIDA.exists() else ""
        markers = [
            "\n\n# Eventos Muito Positivos e Muito Negativos - Seguranca Presente\n",
            "\n\n# Temas Mais Amados e Odiados - Seguranca Presente\n",
            "\n\n# Eventos Mais Amados e Odiados - Seguranca Presente\n",
        ]
        base = existing.rstrip()
        for marker in markers:
            if marker in existing:
                base = existing.split(marker)[0].rstrip()
                break
        CONSOLIDA.write_text(base + "\n\n" + markdown, encoding="utf-8")
    print(f"# wrote {args.out}", file=sys.stderr)
    print(f"# wrote {args.tables_dir / 'eventos_resumo.csv'}", file=sys.stderr)
    print(f"# wrote {args.tables_dir / 'eventos_muito_positivos.csv'}", file=sys.stderr)
    print(f"# wrote {args.tables_dir / 'eventos_muito_negativos.csv'}", file=sys.stderr)
    print(f"# wrote {args.markdown}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
