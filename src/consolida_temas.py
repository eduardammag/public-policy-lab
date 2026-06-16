#!/usr/bin/env python3
"""Consolidate themes from classified news using deterministic clustering."""
from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer

from config import CONSOLIDA, SENTIMENT_ORDER, TABLES_DIR
from iter_helper import article_records, load_data


DEFAULT_LABELS = TABLES_DIR / "noticias_classificadas.csv"
THEME_ARTICLES_CSV = "noticias_com_temas.csv"
THEME_SUMMARY_CSV = "resumo-temas-clusterizados.csv"
DEDUPED_LABELS_CSV = "noticias_classificadas_sem_duplicatas.csv"

PORTUGUESE_STOPWORDS = {
    "a", "ao", "aos", "aquela", "aquele", "aqueles", "as", "ate", "com", "como",
    "da", "das", "de", "do", "dos", "e", "em", "entre", "era", "essa", "esse",
    "esta", "este", "foi", "foram", "ha", "isso", "ja", "mais", "mas", "na",
    "nas", "no", "nos", "o", "os", "ou", "para", "pela", "pelas", "pelo",
    "pelos", "por", "que", "se", "sem", "ser", "sua", "suas", "seu", "seus",
    "tambem", "um", "uma", "umas", "uns", "vai", "sao", "rio", "janeiro",
    "seguranca", "presente", "programa", "operacao", "noticia", "noticias",
    "whatsapp", "facebook", "linkedin", "email", "telegram", "instagram", "youtube",
    "compartilhar", "compartilhe", "publicidade", "continua", "apos", "search",
    "redacao", "jornalista", "editor", "diretor", "tags", "receba", "gratuitamente",
    "newsletter", "cadastro", "sucesso", "google", "news", "clique", "aqui",
    "acessar", "fonte", "anterior", "proximo", "comentario", "responder",
    "altair", "alves", "raphael", "fernandes", "felipe", "lucena", "quintino",
    "freire", "mario", "marques", "tribuna", "serra", "destaque",
    "abre", "janela", "tempo", "artigo", "leitura", "min", "real", "contraste",
    "ciencia", "texto", "conosco", "ferramentas", "feira", "maio", "nao",
    "negar", "nega", "video",
}


def fold_text(text: str) -> str:
    text = unicodedata.normalize("NFKD", str(text or ""))
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", " ", text).lower()
    return re.sub(r"\s+", " ", text).strip()


def normalize_label(label: str) -> str:
    label = str(label or "").strip().lower()
    return label if label in SENTIMENT_ORDER else "n/a"


def load_classified(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"classified CSV not found: {path}")
    df = pd.read_csv(path, encoding="utf-8-sig", keep_default_na=False)
    required = {"recordKey", "articleId", "title", "label"}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"classified CSV missing columns: {', '.join(sorted(missing))}")
    df["articleId"] = pd.to_numeric(df["articleId"], errors="coerce")
    df = df.dropna(subset=["articleId"]).copy()
    df["articleId"] = df["articleId"].astype(int)
    df["jsonIndex"] = pd.to_numeric(df.get("jsonIndex"), errors="coerce").fillna(0).astype(int)
    df["publishedAtSort"] = pd.to_datetime(df.get("publishedAt"), errors="coerce", utc=True)
    df["label"] = df["label"].map(normalize_label)
    return df


def dedupe_articles(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    before = len(df)
    deduped = (
        df.sort_values(["articleId", "publishedAtSort", "jsonIndex", "recordKey"])
        .drop_duplicates(subset=["articleId"], keep="first")
        .sort_values(["publishedAtSort", "articleId"])
        .reset_index(drop=True)
    )
    return deduped, before - len(deduped)


def records_by_article_id() -> dict[int, dict]:
    data, raw, _src = load_data()
    return {int(rec["articleId"]): rec for rec in article_records(data, raw)}


def build_corpus(df: pd.DataFrame, source_records: dict[int, dict]) -> list[str]:
    corpus = []
    for row in df.itertuples(index=False):
        rec = source_records.get(int(row.articleId), {})
        parts = [
            getattr(row, "title", ""),
            getattr(row, "storyTitle", ""),
            getattr(row, "reason", ""),
            rec.get("summaryPreview", ""),
            rec.get("rawText", "")[:6000],
        ]
        corpus.append(fold_text(" ".join(str(part or "") for part in parts)))
    return corpus


def choose_cluster_count(n_docs: int, requested: int | None) -> int:
    if requested:
        return max(2, min(requested, n_docs))
    if n_docs < 80:
        return max(2, min(6, n_docs))
    if n_docs < 300:
        return 8
    return 12


def fit_theme_clusters(corpus: list[str], n_clusters: int) -> tuple[TfidfVectorizer, KMeans, list[int]]:
    min_df = 2 if len(corpus) >= 30 else 1
    vectorizer = TfidfVectorizer(
        min_df=min_df,
        max_df=0.88,
        max_features=4000,
        ngram_range=(1, 2),
        stop_words=list(PORTUGUESE_STOPWORDS),
        token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z]{2,}\b",
    )
    matrix = vectorizer.fit_transform(corpus)
    model = KMeans(n_clusters=n_clusters, random_state=42, n_init=20)
    labels = model.fit_predict(matrix)
    return vectorizer, model, labels.tolist()


def theme_terms(vectorizer: TfidfVectorizer, model: KMeans, n_terms: int = 8) -> dict[int, list[str]]:
    terms = vectorizer.get_feature_names_out()
    out: dict[int, list[str]] = {}
    for cluster_id, centroid in enumerate(model.cluster_centers_):
        top = centroid.argsort()[::-1][:n_terms]
        out[cluster_id] = [terms[idx] for idx in top]
    return out


def theme_name(terms: list[str]) -> str:
    return " / ".join(terms[:4])


def sentiment_distribution(labels: pd.Series) -> dict[str, int]:
    counts = Counter(labels)
    return {label: counts.get(label, 0) for label in SENTIMENT_ORDER}


def write_outputs(df: pd.DataFrame, terms_by_cluster: dict[int, list[str]], tables_dir: Path) -> pd.DataFrame:
    tables_dir.mkdir(parents=True, exist_ok=True)

    article_rows = df.copy()
    article_rows["tema_id"] = article_rows["cluster"].map(lambda value: f"tema-{int(value) + 1:02d}")
    article_rows["tema"] = article_rows["cluster"].map(lambda value: theme_name(terms_by_cluster[int(value)]))
    article_rows["termos_do_cluster"] = article_rows["cluster"].map(lambda value: "; ".join(terms_by_cluster[int(value)]))

    article_cols = [
        "recordKey", "id", "articleId", "publishedAt", "publishedDisplay", "sourceName",
        "sourceHost", "title", "label", "sentiment_score", "confidence", "tema_id",
        "tema", "termos_do_cluster", "reason",
    ]
    article_rows[article_cols].to_csv(tables_dir / THEME_ARTICLES_CSV, index=False, encoding="utf-8-sig")

    summary_rows = []
    for cluster_id, group in article_rows.groupby("cluster"):
        dist = sentiment_distribution(group["label"])
        examples = " | ".join(group.sort_values("publishedAtSort")["title"].head(5).astype(str))
        summary_rows.append(
            {
                "tema_id": f"tema-{int(cluster_id) + 1:02d}",
                "tema": theme_name(terms_by_cluster[int(cluster_id)]),
                "termos_do_cluster": "; ".join(terms_by_cluster[int(cluster_id)]),
                "n_artigos": len(group),
                "percentual": round(len(group) / len(article_rows) * 100, 4),
                **dist,
                "exemplos_titulos": examples,
            }
        )
    summary = pd.DataFrame(summary_rows).sort_values("n_artigos", ascending=False)
    summary.to_csv(tables_dir / THEME_SUMMARY_CSV, index=False, encoding="utf-8-sig")
    return summary


def build_markdown(summary: pd.DataFrame, deduped: pd.DataFrame, duplicate_count: int, n_clusters: int) -> str:
    dist = sentiment_distribution(deduped["label"])
    lines = [
        "# Consolidacao Tematica - Seguranca Presente",
        "",
        "Documento gerado automaticamente a partir de `tabelas/noticias_classificadas.csv`.",
        "",
        "## Como a classificacao foi feita",
        "",
        "- Cada noticia foi enviada ao LLM pelo script `src/llm_classifier.py`.",
        "- O prompt pede um unico rotulo: `muito negativo`, `negativo`, `neutro`, `positivo`, `muito positivo` ou `n/a`.",
        "- O modelo tambem retorna `confidence` e `reason`; esses campos ficam no CSV de saida.",
        "- A classificacao mede o enquadramento/percepcao retratada pela noticia sobre o programa, nao uma pesquisa direta de opiniao publica.",
        "",
        "## Como os temas foram definidos",
        "",
        "- Primeiro, noticias duplicadas foram removidas por `articleId`.",
        "- Depois, o texto de cada noticia foi montado com titulo, titulo da historia, justificativa do LLM, resumo e texto bruto.",
        "- Os textos foram vetorizados com TF-IDF, removendo palavras muito comuns.",
        f"- Em seguida, KMeans agrupou as noticias em **{n_clusters} clusters**.",
        "- O nome de cada tema vem dos termos com maior peso no centroide do cluster.",
        "- Portanto, os temas sao exploratorios: eles nascem dos dados, mas devem ser revisados editorialmente antes de conclusoes finais.",
        "",
        "## Controle de duplicatas",
        "",
        f"- Linhas no CSV classificado original: **{len(deduped) + duplicate_count}**",
        f"- Noticias duplicadas removidas por `articleId`: **{duplicate_count}**",
        f"- Noticias unicas usadas na analise tematica: **{len(deduped)}**",
        "",
        "## Distribuicao de sentimento",
        "",
        "| Muito Negativo | Negativo | Neutro | Positivo | Muito Positivo | N/A |",
        "|---|---|---|---|---|---|",
        "| {} | {} | {} | {} | {} | {} |".format(
            dist["muito negativo"],
            dist["negativo"],
            dist["neutro"],
            dist["positivo"],
            dist["muito positivo"],
            dist["n/a"],
        ),
        "",
        "## Temas Clusterizados",
        "",
    ]
    for _, row in summary.iterrows():
        lines.extend(
            [
                f"### {row['tema_id']} - {row['tema']}",
                "",
                f"- Noticias: **{row['n_artigos']}** ({row['percentual']}%)",
                f"- Termos definidores: {row['termos_do_cluster']}",
                (
                    "- Sentimentos: "
                    f"MN={row['muito negativo']}, "
                    f"N={row['negativo']}, Ne={row['neutro']}, "
                    f"P={row['positivo']}, MP={row['muito positivo']}, "
                    f"NA={row['n/a']}"
                ),
                f"- Exemplos: {row['exemplos_titulos']}",
                "",
            ]
        )
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABELS)
    parser.add_argument("--output", type=Path, default=CONSOLIDA)
    parser.add_argument("--tables-dir", type=Path, default=TABLES_DIR)
    parser.add_argument("--clusters", type=int, help="number of thematic clusters")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv[1:])

    classified = load_classified(args.labels)
    deduped, duplicate_count = dedupe_articles(classified)
    records = records_by_article_id()
    corpus = build_corpus(deduped, records)
    n_clusters = choose_cluster_count(len(deduped), args.clusters)
    vectorizer, model, clusters = fit_theme_clusters(corpus, n_clusters)

    deduped = deduped.copy()
    deduped["cluster"] = clusters
    deduped.to_csv(args.tables_dir / DEDUPED_LABELS_CSV, index=False, encoding="utf-8-sig")
    terms_by_cluster = theme_terms(vectorizer, model)
    summary = write_outputs(deduped, terms_by_cluster, args.tables_dir)
    markdown = build_markdown(summary, deduped, duplicate_count, n_clusters)

    if args.dry_run:
        print(markdown)
    else:
        args.output.write_text(markdown, encoding="utf-8")
        print(f"# wrote {args.output}", file=sys.stderr)
        print(f"# wrote {args.tables_dir / DEDUPED_LABELS_CSV}", file=sys.stderr)
        print(f"# wrote {args.tables_dir / THEME_ARTICLES_CSV}", file=sys.stderr)
        print(f"# wrote {args.tables_dir / THEME_SUMMARY_CSV}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
