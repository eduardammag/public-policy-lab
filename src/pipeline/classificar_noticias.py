#!/usr/bin/env python3
"""LLM classification helper using OpenAI (renamed).

Reads OpenAI key from environment (or .env) and provides a simple
zero-shot classifier that emits a CSV with labels.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

from src.configuracoes.config import SENTIMENT_ORDER, TABLES_DIR

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None

try:
    import openai
except Exception:
    openai = None

# default model (tunable via OPENAI_MODEL env var)
DEFAULT_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "prompt_classificacao.txt"
OUTPUT_FIELDS = [
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
    "grau_ambiguidade",
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
    "event_confidence",
    "model",
]

SCORE_MAP = {
    "muito negativo": -2,
    "negativo": -1,
    "neutro": 0,
    "positivo": 1,
    "muito positivo": 2,
    "n/a": "",
}


def slugify(text: str) -> str:
    text = str(text or "").strip().lower()
    replacements = {
        "á": "a", "à": "a", "ã": "a", "â": "a",
        "é": "e", "ê": "e",
        "í": "i",
        "ó": "o", "ô": "o", "õ": "o",
        "ú": "u",
        "ç": "c",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return re.sub(r"-+", "-", text) or "evento-sem-chave"


def ensure_openai_available() -> None:
    if load_dotenv:
        load_dotenv()
    if openai is None:
        raise SystemExit("Missing dependency 'openai'. Install requirements.txt")
    key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_KEY")
    if not key:
        raise SystemExit("OpenAI API key not found in environment (OPENAI_API_KEY)")
    os.environ["OPENAI_API_KEY"] = key


def load_prompt_template() -> str:
    try:
        return PROMPT_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise SystemExit(f"Prompt file not found: {PROMPT_PATH}")


def normalize_label(label: str | None) -> str:
    value = (label or "").strip().lower()
    value = value.replace("nao aplicavel", "n/a").replace("não aplicável", "n/a")
    value = value.replace("não se aplica", "n/a").replace("na", "n/a")
    for allowed in SENTIMENT_ORDER:
        if value == allowed:
            return allowed
    if "muito negativo" in value:
        return "muito negativo"
    if "muito positivo" in value:
        return "muito positivo"
    if "negativo" in value:
        return "negativo"
    if "positivo" in value:
        return "positivo"
    if "neutro" in value:
        return "neutro"
    if "n/a" in value:
        return "n/a"
    return "n/a"


def normalize_ambiguity(value: str | None) -> str:
    value = (value or "").strip().lower()
    value = value.replace("médio", "medio")
    if value in {"baixo", "medio", "alto"}:
        return value
    return "alto"


def classify_text(text: str, model: str = DEFAULT_MODEL, retries: int = 3) -> dict:
    ensure_openai_available()
    template = load_prompt_template()
    prompt = template.replace("{noticia}", text[:10000])
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            client = openai.OpenAI()
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Voce classifica sentimento e extrai eventos jornalisticos "
                            "especificos em portugues brasileiro."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0,
                max_tokens=520,
                response_format={"type": "json_object"},
            )
            content = (resp.choices[0].message.content or "").strip()
            break
        except Exception as e:
            last_error = e
            if attempt == retries:
                return {"label": "n/a", "grau_ambiguidade": "alto", "reason": f"API error: {e}"}
            time.sleep(2 * attempt)

    try:
        parsed = json.loads(content)
        parsed["label"] = normalize_label(parsed.get("label"))
        return parsed
    except Exception:
        return {"label": "n/a", "grau_ambiguidade": "alto", "reason": content or str(last_error or "")}


def load_data_for_classification() -> tuple[dict, dict, Path]:
    try:
        from src.utilitarios.dados_noticias import load_data

        return load_data()
    except Exception:
        raise SystemExit("Cannot import data loader from src/utilitarios/dados_noticias.py")


def find_article_by_aid(arts: list[dict], aid: str) -> Optional[dict]:
    aid = aid if aid.startswith("a-") else f"a-{aid}"
    return next((r for r in arts if r["id"] == aid or r.get("recordKey") == aid), None)


def read_existing_rows(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8-sig", newline="") as f:
        out = {}
        for row in csv.DictReader(f):
            key = row.get("recordKey") or row.get("id")
            if key:
                out[key] = row
        return out


def write_labels_csv(rows: list[dict], outpath: Path) -> None:
    outpath.parent.mkdir(parents=True, exist_ok=True)
    with outpath.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def article_to_row(rec: dict, out: dict, model: str) -> dict:
    label = normalize_label(out.get("label"))
    grau_ambiguidade = normalize_ambiguity(out.get("grau_ambiguidade"))
    event_confidence = out.get("event_confidence", "")
    try:
        event_confidence = round(float(event_confidence), 4)
    except Exception:
        event_confidence = ""
    event_name = str(out.get("evento") or out.get("evento_chave") or "").strip()
    event_key = str(out.get("evento_chave") or event_name or "").strip()
    return {
        "recordKey": rec.get("recordKey") or rec["id"],
        "jsonIndex": rec.get("jsonIndex", ""),
        "id": rec["id"],
        "articleId": rec.get("articleId", ""),
        "publishedAt": rec.get("publishedAt", ""),
        "publishedDisplay": rec.get("publishedDisplay", ""),
        "sourceName": rec.get("sourceName", ""),
        "sourceHost": rec.get("sourceHost", ""),
        "title": rec.get("title", ""),
        "storyId": rec.get("storyId", ""),
        "storyTitle": rec.get("storyTitle", ""),
        "targetKeys": "; ".join(rec.get("targetKeys") or []),
        "label": label,
        "sentiment_score": SCORE_MAP[label],
        "grau_ambiguidade": grau_ambiguidade,
        "reason": str(out.get("reason", ""))[:1200],
        "evidencia_sentimento": str(out.get("evidencia_sentimento", ""))[:1200],
        "evento": event_name,
        "evento_chave": event_key,
        "evento_id": slugify(event_key),
        "tipo_evento": str(out.get("tipo_evento", ""))[:200],
        "local": str(out.get("local", ""))[:200],
        "data_evento": str(out.get("data_evento", ""))[:100],
        "descricao_curta": str(out.get("descricao_curta", ""))[:1200],
        "evidencia_evento": str(out.get("evidencia_evento", ""))[:1200],
        "event_confidence": event_confidence,
        "model": model,
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--aid", type=str, help="article id (a-NNN)")
    parser.add_argument("--sample", type=int, help="classify N sample articles")
    parser.add_argument("--all", action="store_true", help="classify all articles (careful)")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL)
    parser.add_argument("--out", type=Path, default=TABLES_DIR / "llm_labels.csv")
    parser.add_argument("--no-resume", action="store_true", help="reclassify rows even if output already has them")
    parser.add_argument("--workers", type=int, default=1, help="parallel API calls")
    args = parser.parse_args(argv[1:])

    data, raw = load_data_for_classification()[:2]
    arts = []
    try:
        from src.utilitarios.dados_noticias import article_records

        arts = article_records(data, raw)
    except Exception:
        raise SystemExit("Cannot import article_records from src/utilitarios/dados_noticias.py")

    if args.aid:
        rec = find_article_by_aid(arts, args.aid)
        if not rec:
            print(f"not found: {args.aid}", file=sys.stderr)
            return 1
        candidates = [rec]
    elif args.sample:
        candidates = arts[: args.sample]
    elif args.all:
        candidates = arts
    else:
        parser.print_help()
        return 2

    existing = {} if args.no_resume else read_existing_rows(args.out)
    rows_by_key = dict(existing)
    pending = []
    for rec in candidates:
        key = rec.get("recordKey") or rec["id"]
        if key in rows_by_key and rows_by_key[key].get("label") and rows_by_key[key].get("evento_chave"):
            print(f"skip existing {key}", file=sys.stderr)
            continue
        pending.append(rec)

    def classify_record(rec: dict) -> tuple[str, dict]:
        key = rec.get("recordKey") or rec["id"]
        text = "\n\n".join([rec.get("title", ""), rec.get("summaryPreview", ""), rec.get("rawText", "")])
        out = classify_text(text, model=args.model)
        return key, article_to_row(rec, out, args.model)

    workers = max(1, args.workers)
    completed = 0
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(classify_record, rec) for rec in pending]
        for future in as_completed(futures):
            key, row = future.result()
            rows_by_key[key] = row
            completed += 1
            ordered_rows = [
                rows_by_key[r.get("recordKey") or r["id"]]
                for r in arts
                if (r.get("recordKey") or r["id"]) in rows_by_key
            ]
            write_labels_csv(ordered_rows, args.out)
            print(f"classified {key} as {row['label']} ({completed}/{len(pending)})", file=sys.stderr)

    if not pending:
        ordered_rows = [rows_by_key[r.get("recordKey") or r["id"]] for r in arts if (r.get("recordKey") or r["id"]) in rows_by_key]
        write_labels_csv(ordered_rows, args.out)

    final_rows = [rows_by_key[r.get("recordKey") or r["id"]] for r in arts if (r.get("recordKey") or r["id"]) in rows_by_key]
    write_labels_csv(final_rows, args.out)
    print(f"Wrote {args.out} ({len(final_rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
