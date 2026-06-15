#!/usr/bin/env python3
"""Generate econometrics-ready CSVs from collected articles and LLM labels.

Outputs (in `tabelas/`):
- `daily_sentiment_index.csv`  : date, n_articles, n_with_label, mean_sentiment, sd_sentiment, log_return
- `topic_prevalence.csv`      : date, tema, n_articles, prevalence, mean_sentiment
- `source_metrics.csv`        : date, sourceName, n_articles, share, mean_sentiment
- `panel_articles.csv`        : article-level panel with sentiment_score and metadata

Requires that `tools/iter_helper.py` is present and that `tabelas/llm_labels.csv`
or `tabelas/artigos-analisados.csv` exist to provide labels/themes.
"""
from __future__ import annotations

import csv
import math
import statistics
from collections import defaultdict
from datetime import datetime
import sys

from config import TABLES_DIR as TABLES


def parse_date(dt: str) -> str:
    if not dt:
        return "1970-01-01"
    try:
        # handle Z suffix
        if dt.endswith("Z"):
            dt = dt.replace("Z", "+00:00")
        d = datetime.fromisoformat(dt)
        return d.date().isoformat()
    except Exception:
        # try short YYYY-MM-DD
        try:
            return datetime.strptime(dt[:10], "%Y-%m-%d").date().isoformat()
        except Exception:
            return dt[:10]


def load_llm_labels(path: Path) -> dict:
    out = {}
    if not path.exists():
        return out
    with path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            key = r.get("id")
            if not key:
                # skip malformed rows
                continue
            out[key] = r
    return out


def load_artigos_analisados(path: Path) -> dict:
    out = {}
    if not path.exists():
        return out
    with path.open(encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for r in reader:
            out[r["id_artigo"]] = r
    return out


SCORE_MAP = {
    "muito positivo": 2,
    "positivo": 1,
    "neutro": 0,
    "negativo": -1,
    "muito negativo": -2,
    "n/a": None,
    "unknown": None,
    "error": None,
}

LLM_MAP = {"positivo": 1, "neutro": 0, "negativo": -1, "n/a": None}


def sentiment_score_from_label(label: str) -> tuple[float | None, str]:
    if label is None:
        return None, "none"
    lab = label.strip().lower()
    if lab in LLM_MAP:
        return LLM_MAP[lab], lab
    if lab in SCORE_MAP:
        return SCORE_MAP[lab], lab
    return None, lab


def main(argv: list[str]) -> int:
    try:
        from iter_helper import load_data, article_records  # type: ignore
    except Exception as e:
        print("iter_helper not available:", e, file=sys.stderr)
        return 1

    data, raw, src = load_data()
    arts = article_records(data, raw)

    llm_labels = load_llm_labels(TABLES / "llm_labels.csv")
    analisados = load_artigos_analisados(TABLES / "artigos-analisados.csv")

    # panel articles
    panel_rows = []

    # aggregates
    daily_scores = defaultdict(list)
    daily_counts = defaultdict(int)
    topic_date_counts = defaultdict(lambda: defaultdict(int))
    topic_date_scores = defaultdict(lambda: defaultdict(list))
    source_date_counts = defaultdict(lambda: defaultdict(int))
    source_date_scores = defaultdict(lambda: defaultdict(list))

    for rec in arts:
        aid = rec.get("id")
        date = parse_date(rec.get("publishedAt") or rec.get("publishedDisplay") or "")
        title = rec.get("title", "")
        source = rec.get("sourceName") or rec.get("sourceHost") or ""

        # get label from llm if present, else from analisados
        label = None
        confidence = ""
        if aid in llm_labels:
            label = llm_labels[aid].get("label")
            confidence = llm_labels[aid].get("confidence", "")
        elif aid in analisados:
            label = analisados[aid].get("sentimento_geral")

        score, lab_norm = sentiment_score_from_label(label)

        temas = ""
        if aid in analisados:
            temas = analisados[aid].get("temas", "")

        panel_rows.append(
            {
                "id": aid,
                "date": date,
                "title": title,
                "sourceName": source,
                "label": label or "",
                "label_norm": lab_norm,
                "sentiment_score": "" if score is None else float(score),
                "confidence": confidence,
                "temas": temas,
            }
        )

        daily_counts[date] += 1
        if score is not None:
            daily_scores[date].append(score)
            source_date_scores[date][source].append(score)
            source_date_counts[date][source] += 1

        # topics
        if temas:
            for tema in [t.strip() for t in temas.split(";") if t.strip()]:
                topic_date_counts[tema][date] += 1
                if score is not None:
                    topic_date_scores[tema][date].append(score)

    # write panel
    TABLES.mkdir(parents=True, exist_ok=True)
    panel_path = TABLES / "panel_articles.csv"
    with panel_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["id", "date", "title", "sourceName", "label", "label_norm", "sentiment_score", "confidence", "temas"],
        )
        writer.writeheader()
        for r in panel_rows:
            writer.writerow(r)

    # daily sentiment index
    daily_path = TABLES / "daily_sentiment_index.csv"
    dates = sorted(daily_counts.keys())
    prev_mean = None
    with daily_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "n_articles", "n_with_label", "mean_sentiment", "sd_sentiment", "log_return"])
        writer.writeheader()
        for d in dates:
            n = daily_counts[d]
            scores = daily_scores.get(d, [])
            n_lab = len(scores)
            mean = "" if not scores else round(statistics.mean(scores), 4)
            sd = "" if len(scores) < 2 else round(statistics.pstdev(scores), 4)
            log_return = ""
            if prev_mean is not None and isinstance(mean, (int, float)) and prev_mean not in (0, ""):
                try:
                    log_return = round(math.log((mean + 3) / (prev_mean + 3)), 6)
                except Exception:
                    log_return = ""
            if isinstance(mean, (int, float)):
                prev_mean = mean
            writer.writerow({
                "date": d,
                "n_articles": n,
                "n_with_label": n_lab,
                "mean_sentiment": mean,
                "sd_sentiment": sd,
                "log_return": log_return,
            })

    # topic prevalence (long format)
    topic_path = TABLES / "topic_prevalence.csv"
    with topic_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "tema", "n_articles", "prevalence", "mean_sentiment"])
        writer.writeheader()
        for tema, dates_map in topic_date_counts.items():
            for d, cnt in sorted(dates_map.items()):
                total = daily_counts.get(d, 0) or 1
                scores = topic_date_scores[tema].get(d, [])
                mean = "" if not scores else round(statistics.mean(scores), 4)
                writer.writerow({
                    "date": d,
                    "tema": tema,
                    "n_articles": cnt,
                    "prevalence": round(cnt / total, 6),
                    "mean_sentiment": mean,
                })

    # source metrics
    source_path = TABLES / "source_metrics.csv"
    with source_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "sourceName", "n_articles", "share", "mean_sentiment"])
        writer.writeheader()
        for d in dates:
            total = daily_counts.get(d, 0) or 1
            for src_name, cnt in sorted(source_date_counts[d].items(), key=lambda x: -x[1]):
                scores = source_date_scores[d].get(src_name, [])
                mean = "" if not scores else round(statistics.mean(scores), 4)
                writer.writerow({
                    "date": d,
                    "sourceName": src_name,
                    "n_articles": cnt,
                    "share": round(cnt / total, 6),
                    "mean_sentiment": mean,
                })

    print(f"Wrote: {panel_path}, {daily_path}, {topic_path}, {source_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
