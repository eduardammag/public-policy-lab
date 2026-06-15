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
import sys
from typing import Optional

from config import ANALISE, TABLES_DIR

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None

try:
    import openai
except Exception:
    openai = None

# default model (tunable via OPENAI_MODEL env var)
DEFAULT_MODEL = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")


def ensure_openai_available() -> None:
    if load_dotenv:
        load_dotenv()
    if openai is None:
        raise SystemExit("Missing dependency 'openai'. Install requirements.txt")
    key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_KEY")
    if not key:
        raise SystemExit("OpenAI API key not found in environment (OPENAI_API_KEY)")
    openai.api_key = key


def classify_text(text: str, model: str = DEFAULT_MODEL) -> dict:
    ensure_openai_available()
    prompt = (
        "Classifique a percepcao publica expressa neste trecho de noticia em: "
        "positivo, neutro, negativo ou n/a (quando nao aplicavel).\n"
        "Responda estritamente um JSON com campos: label, confidence (0-1), reason.\n"
        "Texto:\n" + text[:4000]
    )
    try:
        resp = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=256,
        )
        content = resp["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return {"label": "error", "confidence": 0.0, "reason": str(e)}

    try:
        parsed = json.loads(content)
        return parsed
    except Exception:
        return {"label": "unknown", "confidence": 0.0, "reason": content}


def load_data_for_classification() -> tuple[dict, dict, Path]:
    try:
        from iter_helper import load_data  # type: ignore

        return load_data()
    except Exception:
        raise SystemExit("Cannot import data loader from iter_helper.py")


def find_article_by_aid(arts: list[dict], aid: str) -> Optional[dict]:
    aid = aid if aid.startswith("a-") else f"a-{aid}"
    return next((r for r in arts if r["id"] == aid), None)


def write_labels_csv(rows: list[dict], outpath: Path) -> None:
    outpath.parent.mkdir(parents=True, exist_ok=True)
    with outpath.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "title", "label", "confidence", "reason"])
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--aid", type=str, help="article id (a-NNN)")
    parser.add_argument("--sample", type=int, help="classify N sample articles")
    parser.add_argument("--all", action="store_true", help="classify all articles (careful)")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL)
    args = parser.parse_args(argv[1:])

    data, raw, src = load_data_for_classification()
    arts = []
    try:
        from iter_helper import article_records  # type: ignore

        arts = article_records(data, raw)
    except Exception:
        raise SystemExit("Cannot import article_records from iter_helper.py")

    targets: list[dict] = []
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

    for rec in candidates:
        text = "\n\n".join([rec.get("title", ""), rec.get("summaryPreview", ""), rec.get("rawText", "")])
        out = classify_text(text, model=args.model)
        row = {
            "id": rec["id"],
            "title": rec.get("title", "")[:200],
            "label": out.get("label"),
            "confidence": out.get("confidence", 0),
            "reason": out.get("reason", "")[:800],
        }
        targets.append(row)

    outpath = TABLES_DIR / "llm_labels.csv"
    write_labels_csv(targets, outpath)
    print(f"Wrote {outpath}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
