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
EVENTS_SUMMARY = TABLES_DIR / "eventos_resumo.csv"
LOVED_EVENTS = TABLES_DIR / "eventos_mais_amados.csv"
HATED_EVENTS = TABLES_DIR / "eventos_mais_odiados.csv"

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
    "event_confidence",
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
    "grau_ambiguidade",
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


def normalize_ambiguity(value: str) -> str:
    value = str(value or "").strip().lower().replace("médio", "medio")
    return value if value in {"baixo", "medio", "alto"} else ""


def load_unified_labels(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"input CSV not found: {path}")
    df = pd.read_csv(path, encoding="utf-8-sig", keep_default_na=False)
    missing = [col for col in ["articleId", "recordKey", "title", "label", "evento_chave"] if col not in df.columns]
    if missing:
        raise SystemExit(
            "CSV does not contain unified prompt event fields. "
            "Rerun `python -m src.pipeline.classificar_noticias --all --workers 6 --no-resume` "
            f"and then regenerate charts. Missing: {', '.join(missing)}"
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
    if "grau_ambiguidade" in df.columns:
        df["grau_ambiguidade"] = df["grau_ambiguidade"].map(normalize_ambiguity)
    else:
        df["grau_ambiguidade"] = ""
    if "event_confidence" in df.columns:
        df["event_confidence"] = pd.to_numeric(df["event_confidence"], errors="coerce")
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
        positive_weight = counts.get("positivo", 0) + 2 * counts.get("muito positivo", 0)
        negative_weight = counts.get("negativo", 0) + 2 * counts.get("muito negativo", 0)
        score_series = pd.to_numeric(group["sentiment_score"], errors="coerce")
        score_mean = score_series.mean()
        classified_n = int(score_series.notna().sum())
        ambiguity_counts = (
            group["grau_ambiguidade"].value_counts().to_dict()
            if "grau_ambiguidade" in group
            else {}
        )
        event_confidence_mean = (
            pd.to_numeric(group.get("event_confidence"), errors="coerce").mean()
            if "event_confidence" in group
            else pd.NA
        )
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
                "muito_negativo": counts.get("muito negativo", 0),
                "negativo": counts.get("negativo", 0),
                "neutro": counts.get("neutro", 0),
                "positivo": counts.get("positivo", 0),
                "muito_positivo": counts.get("muito positivo", 0),
                "n/a": counts.get("n/a", 0),
                "n_positivas": positive_n,
                "n_negativas": negative_n,
                "share_positivo": round(positive_n / n, 4),
                "share_negativo": round(negative_n / n, 4),
                "proporcao_positivas": round(positive_n / n, 4),
                "proporcao_negativas": round(negative_n / n, 4),
                "ambiguidade_baixa": ambiguity_counts.get("baixo", 0),
                "ambiguidade_media": ambiguity_counts.get("medio", 0),
                "ambiguidade_alta": ambiguity_counts.get("alto", 0),
                "proporcao_ambiguidade_alta": round(ambiguity_counts.get("alto", 0) / n, 4),
                "confianca_evento_media": round(event_confidence_mean, 4) if pd.notna(event_confidence_mean) else pd.NA,
                "peso_positivo": positive_weight,
                "peso_negativo": negative_weight,
                "titulos_exemplo": " | ".join(group["title"].head(5).astype(str)),
            }
        )
    summary = pd.DataFrame(rows)
    if min_articles > 1:
        summary = summary[summary["n_artigos"] >= min_articles].copy()
    return summary.sort_values(["n_artigos", "score_medio"], ascending=[False, False])


def write_rankings(events: pd.DataFrame, min_articles: int) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    summary_all = aggregate_events(events, min_articles=1)
    summary_ranked = aggregate_events(events, min_articles=min_articles)
    summary_ranked = summary_ranked[summary_ranked["score_medio"].notna()].copy()
    loved = summary_ranked.sort_values(
        ["score_medio", "share_positivo", "peso_positivo", "n_artigos"],
        ascending=[False, False, False, False],
    )
    hated = summary_ranked.sort_values(
        ["score_medio", "share_negativo", "peso_negativo", "n_artigos"],
        ascending=[True, False, False, False],
    )
    summary_all.to_csv(EVENTS_SUMMARY, index=False, encoding="utf-8-sig")
    loved.to_csv(LOVED_EVENTS, index=False, encoding="utf-8-sig")
    hated.to_csv(HATED_EVENTS, index=False, encoding="utf-8-sig")
    return summary_all, loved, hated


def build_markdown(events: pd.DataFrame, loved: pd.DataFrame, hated: pd.DataFrame, min_articles: int) -> str:
    lines = [
        "# Eventos Mais Amados e Odiados - Seguranca Presente",
        "",
        "Os eventos e sentimentos foram extraidos pelo mesmo prompt unico em `src/pipeline/classificar_noticias.py`.",
        "Este script apenas agrega e ranqueia os campos ja retornados pelo LLM.",
        "",
        f"- Noticias unicas analisadas: **{len(events)}**",
        f"- Criterio do ranking principal: eventos com pelo menos **{min_articles}** noticia(s).",
        "- `score_medio` usa: muito negativo=-2, negativo=-1, neutro=0, positivo=1, muito positivo=2; n/a fica fora da media.",
        "- `grau_ambiguidade` resume a incerteza da classificacao como baixo, medio ou alto.",
        "- Desempates usam proporcao de positivas/negativas, peso dos extremos e quantidade de noticias.",
        "",
        "## Eventos Mais Amados",
        "",
    ]
    for idx, row in enumerate(loved.head(25).itertuples(index=False), 1):
        lines.append(
            f"{idx}. **{row.evento}** - score medio {row.score_medio}; "
            f"{row.n_artigos} noticia(s); positivos={row.positivo + row.muito_positivo}; "
            f"negativos={row.negativo + row.muito_negativo}. Exemplos: {row.titulos_exemplo}"
        )
    lines.extend(["", "## Eventos Mais Odiados", ""])
    for idx, row in enumerate(hated.head(25).itertuples(index=False), 1):
        lines.append(
            f"{idx}. **{row.evento}** - score medio {row.score_medio}; "
            f"{row.n_artigos} noticia(s); negativos={row.negativo + row.muito_negativo}; "
            f"positivos={row.positivo + row.muito_positivo}. Exemplos: {row.titulos_exemplo}"
        )
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABELS)
    parser.add_argument("--out", type=Path, default=EVENTS_BY_ARTICLE)
    parser.add_argument("--min-articles", type=int, default=3)
    parser.add_argument("--markdown", type=Path, default=TABLES_DIR / "ranking-eventos.md")
    parser.add_argument("--update-consolidacao", action="store_true")
    args = parser.parse_args(argv[1:])

    events = load_unified_labels(args.labels)
    write_article_events(events, args.out)
    _summary, loved, hated = write_rankings(events, args.min_articles)
    markdown = build_markdown(events, loved, hated, args.min_articles)
    args.markdown.write_text(markdown, encoding="utf-8")
    if args.update_consolidacao:
        existing = CONSOLIDA.read_text(encoding="utf-8") if CONSOLIDA.exists() else ""
        marker = "\n\n# Eventos Mais Amados e Odiados - Seguranca Presente\n"
        base = existing.split(marker)[0].rstrip()
        CONSOLIDA.write_text(base + "\n\n" + markdown, encoding="utf-8")
    print(f"# wrote {args.out}", file=sys.stderr)
    print(f"# wrote {EVENTS_SUMMARY}", file=sys.stderr)
    print(f"# wrote {LOVED_EVENTS}", file=sys.stderr)
    print(f"# wrote {HATED_EVENTS}", file=sys.stderr)
    print(f"# wrote {args.markdown}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
