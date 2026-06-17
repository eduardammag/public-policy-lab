from __future__ import annotations

import json
from pathlib import Path

from src.configuracoes.config import ARTICLES_JSON


def load_data() -> tuple[dict, Path]:
    if not ARTICLES_JSON.exists():
        raise SystemExit(f"No article data found: {ARTICLES_JSON}")
    with ARTICLES_JSON.open(encoding="utf-8") as f:
        return json.load(f), ARTICLES_JSON


def article_records(data: dict) -> list[dict]:
    """Return one normalized record per article about Seguranca Presente."""
    out: list[dict] = []
    seen_ids: dict[str, int] = {}
    for idx, art in enumerate(data.get("articles") or [], 1):
        aid = int(art.get("articleId") or 0)
        if not aid:
            continue
        original_id = art.get("id") or f"a-{aid}"
        seen_ids[original_id] = seen_ids.get(original_id, 0) + 1
        record_key = original_id if seen_ids[original_id] == 1 else f"{original_id}__dup{seen_ids[original_id]}"
        article_keys = set(art.get("targetKeys") or [])
        out.append(
            {
                "recordKey": record_key,
                "jsonIndex": idx,
                "id": original_id,
                "articleId": aid,
                "title": art.get("title") or "",
                "url": art.get("url") or "",
                "sourceName": art.get("sourceName") or "",
                "sourceHost": art.get("sourceHost") or "",
                "publishedAt": art.get("publishedAt") or "",
                "publishedDisplay": art.get("publishedDisplay") or "",
                "rawTextKey": art.get("rawTextKey") or "",
                "rawText": art.get("rawText") or "",
                "summaryPreview": art.get("summaryPreview") or "",
                "summaryLabel": art.get("summaryLabel") or "",
                "targetKeys": sorted(article_keys),
                "storyTitle": art.get("storyTitle") or "",
                "storyId": art.get("storyId"),
            }
        )
    return sorted(out, key=lambda r: (r["publishedAt"], r["articleId"], r["jsonIndex"]))
