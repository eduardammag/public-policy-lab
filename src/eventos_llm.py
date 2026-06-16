#!/usr/bin/env python3
"""Extract canonical events from classified news with an LLM and rank them."""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

from config import CONSOLIDA, SENTIMENT_ORDER, TABLES_DIR
from iter_helper import article_records, load_data
from llm_classifier import DEFAULT_MODEL, ensure_openai_available

try:
    import openai
except Exception:
    openai = None


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
    "n/a": 0,
}

ARTICLE_FIELDS = [
    "articleId",
    "recordKey",
    "publishedAt",
    "sourceName",
    "sourceHost",
    "title",
    "label",
    "sentiment_score",
    "evento",
    "evento_chave",
    "evento_id",
    "tipo_evento",
    "local",
    "data_evento",
    "descricao_curta",
    "event_confidence",
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


def load_classified(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8-sig", keep_default_na=False)
    df["articleId"] = pd.to_numeric(df["articleId"], errors="coerce")
    df = df.dropna(subset=["articleId"]).copy()
    df["articleId"] = df["articleId"].astype(int)
    df["publishedAtSort"] = pd.to_datetime(df.get("publishedAt"), errors="coerce", utc=True)
    df["label"] = df["label"].map(normalize_label)
    df["sentiment_score"] = df["label"].map(SCORE_MAP)
    return (
        df.sort_values(["articleId", "publishedAtSort", "recordKey"])
        .drop_duplicates(subset=["articleId"], keep="first")
        .sort_values(["publishedAtSort", "articleId"])
        .reset_index(drop=True)
    )


def source_records() -> dict[int, dict]:
    data, raw, _src = load_data()
    return {int(rec["articleId"]): rec for rec in article_records(data, raw)}


def article_text(row: pd.Series, rec: dict) -> str:
    parts = [
        f"Titulo: {row.get('title', '')}",
        f"Titulo agrupador: {row.get('storyTitle', '')}",
        f"Fonte: {row.get('sourceName', '')} ({row.get('sourceHost', '')})",
        f"Data publicada: {row.get('publishedDisplay', '') or row.get('publishedAt', '')}",
        f"Classificacao ja atribuida: {row.get('label', '')}",
        f"Justificativa da classificacao: {row.get('reason', '')}",
        f"Resumo: {rec.get('summaryPreview', '')}",
        f"Texto bruto: {rec.get('rawText', '')[:7000]}",
    ]
    return "\n".join(str(part or "") for part in parts)


def extract_event(text: str, model: str, retries: int = 3) -> dict:
    ensure_openai_available()
    if openai is None:
        raise SystemExit("Missing dependency 'openai'. Install requirements.txt")

    prompt = (
        "Identifique o evento especifico central desta noticia sobre Seguranca Presente.\n"
        "Aqui, evento significa um acontecimento concreto ou pauta factual da noticia, "
        "nao uma categoria generica. Exemplos de bons eventos: "
        "'Show da Shakira em Copacabana', 'Show da Lady Gaga em Copacabana', "
        "'Auditoria aponta escalas fantasmas no Seguranca Presente', "
        "'Transferencia do Seguranca Presente para a Policia Militar', "
        "'Inauguracao da base do Seguranca Presente em Buzios'.\n\n"
        "Regras importantes:\n"
        "- Nao junte eventos diferentes so porque usam palavras parecidas.\n"
        "- Show da Shakira e Show da Lady Gaga sao eventos distintos.\n"
        "- Inclua local, pessoa/instituicao e ano quando isso ajudar a distinguir.\n"
        "- Se a noticia for sobre uma prisao, salvamento, auditoria, inauguracao, concurso, "
        "evento politico ou grande show, use esse acontecimento como evento.\n"
        "- Use `evento_chave` como nome canonico curto e estavel para agrupar noticias sobre o mesmo evento.\n\n"
        "Responda somente JSON com: evento, evento_chave, tipo_evento, local, "
        "data_evento, descricao_curta, confidence.\n\n"
        "Noticia:\n"
        f"{text}"
    )
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            client = openai.OpenAI()
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "Voce extrai eventos jornalisticos especificos em portugues brasileiro.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0,
                max_tokens=350,
                response_format={"type": "json_object"},
            )
            content = (resp.choices[0].message.content or "").strip()
            parsed = json.loads(content)
            return parsed
        except Exception as exc:
            last_error = exc
            if attempt == retries:
                return {
                    "evento": "Evento nao extraido",
                    "evento_chave": "evento-nao-extraido",
                    "tipo_evento": "erro",
                    "local": "",
                    "data_evento": "",
                    "descricao_curta": f"API/parsing error: {exc}",
                    "confidence": 0,
                }
            time.sleep(2 * attempt)
    raise RuntimeError(last_error)


def read_existing(path: Path) -> dict[int, dict]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8-sig", newline="") as f:
        rows = {}
        for row in csv.DictReader(f):
            if row.get("articleId"):
                rows[int(row["articleId"])] = row
        return rows


def write_article_rows(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ARTICLE_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def article_event_row(row: pd.Series, event: dict, model: str) -> dict:
    event_name = str(event.get("evento") or event.get("evento_chave") or "Evento sem nome").strip()
    event_key = str(event.get("evento_chave") or event_name).strip()
    label = normalize_label(row.get("label", ""))
    return {
        "articleId": int(row["articleId"]),
        "recordKey": row.get("recordKey", ""),
        "publishedAt": row.get("publishedAt", ""),
        "sourceName": row.get("sourceName", ""),
        "sourceHost": row.get("sourceHost", ""),
        "title": row.get("title", ""),
        "label": label,
        "sentiment_score": SCORE_MAP[label],
        "evento": event_name,
        "evento_chave": event_key,
        "evento_id": slugify(event_key),
        "tipo_evento": event.get("tipo_evento", ""),
        "local": event.get("local", ""),
        "data_evento": event.get("data_evento", ""),
        "descricao_curta": event.get("descricao_curta", ""),
        "event_confidence": event.get("confidence", ""),
        "model": model,
    }


def extract_events_for_articles(df: pd.DataFrame, records: dict[int, dict], args: argparse.Namespace) -> pd.DataFrame:
    existing = {} if args.no_resume else read_existing(args.out)
    rows_by_article = dict(existing)
    pending = [row for _, row in df.iterrows() if int(row["articleId"]) not in rows_by_article]

    def work(row: pd.Series) -> tuple[int, dict]:
        aid = int(row["articleId"])
        rec = records.get(aid, {})
        event = extract_event(article_text(row, rec), args.model)
        return aid, article_event_row(row, event, args.model)

    done = 0
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        futures = [executor.submit(work, row) for row in pending]
        for future in as_completed(futures):
            aid, out = future.result()
            rows_by_article[aid] = out
            done += 1
            ordered = [rows_by_article[int(row.articleId)] for row in df.itertuples() if int(row.articleId) in rows_by_article]
            write_article_rows(ordered, args.out)
            print(f"# extracted event {done}/{len(pending)} articleId={aid}: {out['evento_chave']}", file=sys.stderr)

    ordered = [rows_by_article[int(row.articleId)] for row in df.itertuples() if int(row.articleId) in rows_by_article]
    write_article_rows(ordered, args.out)
    return pd.DataFrame(ordered)


def aggregate_events(events: pd.DataFrame, min_articles: int) -> pd.DataFrame:
    rows = []
    for event_id, group in events.groupby("evento_id"):
        counts = group["label"].value_counts().to_dict()
        n = len(group)
        positive_n = counts.get("positivo", 0) + counts.get("muito positivo", 0)
        negative_n = counts.get("negativo", 0) + counts.get("muito negativo", 0)
        positive_weight = counts.get("positivo", 0) + 2 * counts.get("muito positivo", 0)
        negative_weight = counts.get("negativo", 0) + 2 * counts.get("muito negativo", 0)
        score_mean = pd.to_numeric(group["sentiment_score"], errors="coerce").fillna(0).mean()
        rows.append(
            {
                "evento_id": event_id,
                "evento": group["evento_chave"].mode().iloc[0],
                "evento_exemplo": group["evento"].mode().iloc[0],
                "tipo_evento": group["tipo_evento"].mode().iloc[0] if not group["tipo_evento"].mode().empty else "",
                "local": group["local"].mode().iloc[0] if not group["local"].mode().empty else "",
                "n_artigos": n,
                "score_medio": round(score_mean, 4),
                "muito_negativo": counts.get("muito negativo", 0),
                "negativo": counts.get("negativo", 0),
                "neutro": counts.get("neutro", 0),
                "positivo": counts.get("positivo", 0),
                "muito_positivo": counts.get("muito positivo", 0),
                "n/a": counts.get("n/a", 0),
                "share_positivo": round(positive_n / n, 4),
                "share_negativo": round(negative_n / n, 4),
                "peso_positivo": positive_weight,
                "peso_negativo": negative_weight,
                "titulos_exemplo": " | ".join(group["title"].head(5).astype(str)),
            }
        )
    summary = pd.DataFrame(rows)
    if min_articles > 1:
        summary = summary[summary["n_artigos"] >= min_articles].copy()
    return summary.sort_values(["n_artigos", "score_medio"], ascending=[False, False])


def write_rankings(events: pd.DataFrame, min_articles: int, tables_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    summary_all = aggregate_events(events, min_articles=1)
    summary_ranked = aggregate_events(events, min_articles=min_articles)
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
        "Cada evento foi extraido por LLM a partir de uma noticia unica por `articleId`.",
        "Eventos parecidos mas factualmente distintos sao mantidos separados; por exemplo, Show da Shakira e Show da Lady Gaga nao sao fundidos.",
        "",
        f"- Noticias unicas analisadas: **{len(events)}**",
        f"- Criterio do ranking principal: eventos com pelo menos **{min_articles}** noticia(s).",
        "- `score_medio` usa: muito negativo=-2, negativo=-1, neutro=0, positivo=1, muito positivo=2, n/a=0.",
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
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--sample", type=int, help="process only the first N deduplicated articles")
    parser.add_argument("--min-articles", type=int, default=2)
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument("--markdown", type=Path, default=TABLES_DIR / "ranking-eventos.md")
    parser.add_argument("--update-consolidacao", action="store_true")
    args = parser.parse_args(argv[1:])

    classified = load_classified(args.labels)
    if args.sample:
        classified = classified.head(args.sample).copy()
    records = source_records()
    events = extract_events_for_articles(classified, records, args)
    _summary, loved, hated = write_rankings(events, args.min_articles, TABLES_DIR)
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
