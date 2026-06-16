from __future__ import annotations
import json
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
import subprocess

from src.configuracoes.config import ANALISE, DATA_PATHS, EXPECTED_SITE_STORIES, ROOT, TARGET_KEYS, TEXT_PHRASES


def ascii_fold(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", " ", text).lower()
    return re.sub(r"\s+", " ", text).strip()


def load_data() -> tuple[dict, dict, Path]:
    for data_path, raw_path in DATA_PATHS:
        if data_path.exists():
            with data_path.open(encoding="utf-8") as f:
                data = json.load(f)
            raw = {}
            if raw_path and raw_path.exists():
                with raw_path.open(encoding="utf-8") as f:
                    raw = json.load(f)
            return data, raw, data_path
    raise SystemExit(
        "No article data found. Expected src/dados_entrada/seguranca_presente_artigos.json "
        "or snapshots under database/."
    )


def selection_stats(data: dict, raw: dict) -> dict[str, int]:
    if "articles" in data and "stories" not in data:
        articles = data.get("articles", []) or []
        article_ids = {int(a.get("articleId") or 0) for a in articles if a.get("articleId")}
        return {
            "site_stories": len({int(a.get("storyId") or 0) for a in articles if a.get("storyId")}),
            "strict_articles": len(articles),
            "unique_article_ids": len(article_ids),
            "duplicate_article_rows": len(articles) - len(article_ids),
            "story_inherited_articles": len(articles),
            "text_phrase_articles": len(articles),
            "strict_or_text_articles": len(articles),
            "broad_articles": len(articles),
        }

    folded_phrases = {ascii_fold(p) for p in TEXT_PHRASES}
    site_story_ids: set[int] = set()
    story_inherited_article_ids: set[int] = set()
    strict_article_ids: set[int] = set()
    text_article_ids: set[int] = set()

    for story in data.get("stories", []):
        story_keys = set(story.get("targetKeys") or [])
        story_in_scope = bool(TARGET_KEYS & story_keys)
        if story_in_scope and story.get("storyIdInt") is not None:
            site_story_ids.add(int(story["storyIdInt"]))
        for art in story.get("articles") or []:
            aid = int(art.get("articleId") or 0)
            if not aid:
                continue
            if story_in_scope:
                story_inherited_article_ids.add(aid)
            article_keys = set(art.get("targetKeys") or [])
            if TARGET_KEYS & article_keys:
                strict_article_ids.add(aid)
            rkey = art.get("rawTextKey") or ""
            rtext = raw.get(rkey, "") if rkey else ""
            haystack = ascii_fold(
                " ".join(
                    [
                        str(art.get("title") or ""),
                        str(art.get("summaryPreview") or ""),
                        rtext,
                    ]
                )
            )
            if any(p in haystack for p in folded_phrases):
                text_article_ids.add(aid)

    return {
        "site_stories": len(site_story_ids),
        "strict_articles": len(strict_article_ids),
        "story_inherited_articles": len(story_inherited_article_ids),
        "text_phrase_articles": len(text_article_ids),
        "strict_or_text_articles": len(strict_article_ids | text_article_ids),
        "broad_articles": len(story_inherited_article_ids | text_article_ids),
    }


def article_records(data: dict, raw: dict) -> list[dict]:
    """Return one record per strict individual article for Seguranca Presente."""
    if "articles" in data and "stories" not in data:
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
            out.append({
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
                "storyTargetKeys": [],
                "storyInScope": True,
                "articleInScope": True,
                "mentionOnlyInText": False,
            })
        return sorted(out, key=lambda r: (r["publishedAt"], r["articleId"], r["jsonIndex"]))

    out: dict[int, dict] = {}
    folded_phrases = {ascii_fold(p) for p in TEXT_PHRASES}

    for story in data.get("stories", []):
        story_keys = set(story.get("targetKeys") or [])
        story_in_scope = bool(TARGET_KEYS & story_keys)
        for art in story.get("articles") or []:
            aid = int(art.get("articleId") or 0)
            if not aid or aid in out:
                continue

            article_keys = set(art.get("targetKeys") or [])
            article_in_scope = bool(TARGET_KEYS & article_keys)
            rkey = art.get("rawTextKey") or ""
            rtext = raw.get(rkey, "") if rkey else ""
            haystack = ascii_fold(
                " ".join(
                    [
                        str(art.get("title") or ""),
                        str(art.get("summaryPreview") or ""),
                        rtext,
                    ]
                )
            )
            mention_in_text = any(p in haystack for p in folded_phrases)
            if not article_in_scope:
                continue

            out[aid] = {
                "id": f"a-{aid}",
                "articleId": aid,
                "title": art.get("title") or "",
                "url": art.get("url") or "",
                "sourceName": art.get("sourceName") or "",
                "sourceHost": art.get("sourceHost") or "",
                "publishedAt": art.get("publishedAt") or "",
                "publishedDisplay": art.get("publishedDisplay") or "",
                "rawTextKey": rkey,
                "rawText": rtext,
                "summaryPreview": art.get("summaryPreview") or "",
                "summaryLabel": art.get("summaryLabel") or "",
                "targetKeys": sorted(article_keys),
                "storyTitle": story.get("title") or "",
                "storyId": story.get("storyIdInt"),
                "storyTargetKeys": sorted(story_keys),
                "storyInScope": story_in_scope,
                "articleInScope": article_in_scope,
                "mentionOnlyInText": mention_in_text
                and not (article_in_scope or story_in_scope),
            }

    return sorted(out.values(), key=lambda r: (r["publishedAt"], r["articleId"]))


def already_seen(text: str) -> set[str]:
    return set(re.findall(r"^## (a-\d+)\b", text, re.MULTILINE))


def in_progress(text: str) -> set[str]:
    return set(re.findall(r"^## (a-\d+)\s+[-—]\s+EM ANDAMENTO", text, re.MULTILINE))


def print_count_note(data: dict, raw: dict, total: int) -> None:
    stats = selection_stats(data, raw)
    story_delta = stats["site_stories"] - EXPECTED_SITE_STORIES
    print(f"site card/story reference: {EXPECTED_SITE_STORIES}")
    print(f"extracted site stories: {stats['site_stories']}")
    print(f"canonical individual articles: {total}")
    print(f"story-inherited broad articles: {stats['story_inherited_articles']}")
    print(f"text-phrase articles: {stats['text_phrase_articles']}")
    print(f"broad articles (story or text): {stats['broad_articles']}")
    if story_delta == 0:
        print("site story count check: OK")
    else:
        sign = "+" if story_delta > 0 else ""
        print(
            "site story count check: DIFFERENCE "
            f"({sign}{story_delta}). Verify snapshot freshness before "
            "starting the full loop."
        )


def emit_stub(aid: str, agent: str = "Codex") -> str:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return (
        f"\n---\n## {aid} - EM ANDAMENTO\n"
        f"**Subagente:** {agent}\n"
        f"**Inicio:** {ts}\n"
    )


def emit_template(rec: dict) -> str:
    return f"""\n---\n## {rec['id']} - {rec['title']}\n
**Fonte:** {rec['sourceName']} ({rec['sourceHost']})
**Data:** {rec['publishedDisplay']}
**URL:** {rec['url']}

### Resumo Narrativo

[FILL: 1 a 3 paragrafos em prosa contextualizada descrevendo o enquadramento,
os pontos centrais e a historia que o artigo conta. Se estiver fora de escopo,
comecar com "Artigo fora de escopo - nao trata do programa Seguranca Presente"
e explicar brevemente.]

### Temas Identificados

| Tema | Como e tratado | Classificacao |
|------|---------------|---------------|
| [tema 1] | [posicionamento] | [muito negativo / negativo / neutro / positivo / muito positivo / n/a] |

### Classificacao Geral

**Sentimento geral do artigo:** [muito negativo / negativo / neutro / positivo / muito positivo / n/a]
"""


def cmd_list(data: dict, raw: dict) -> int:
    arts = article_records(data, raw)
    print_count_note(data, raw, len(arts))
    for r in arts:
        flag = ""
        if r["mentionOnlyInText"]:
            flag = " [text-only]"
        elif r["storyInScope"] and not r["articleInScope"]:
            flag = " [story-only]"
        print(
            f"  {r['id']:>8s}  {r['publishedDisplay']:<22s}  "
            f"{r['sourceName'][:30]:<30s}  {r['title'][:90]}{flag}"
        )
    return 0


def cmd_show(data: dict, raw: dict, aid: str) -> int:
    aid = aid if aid.startswith("a-") else f"a-{aid}"
    rec = next((r for r in article_records(data, raw) if r["id"] == aid), None)
    if not rec:
        print(f"not found: {aid}", file=sys.stderr)
        return 1
    out = dict(rec)
    out["rawTextLen"] = len(rec["rawText"])
    out["rawTextPreview"] = rec["rawText"][:600]
    out.pop("rawText", None)
    print(json.dumps(out, indent=2, ensure_ascii=False))
    print("\n--- raw text (full) ---\n")
    print(rec["rawText"])
    return 0


def cmd_todo(data: dict, raw: dict) -> int:
    arts = article_records(data, raw)
    if ANALISE.exists():
        text = ANALISE.read_text(encoding="utf-8")
        seen = already_seen(text)
        wip = in_progress(text)
    else:
        seen = set()
        wip = set()
    todo = [r for r in arts if r["id"] not in seen]
    print_count_note(data, raw, len(arts))
    print(f"already in analise-individual.md (any state): {len(seen)}")
    print(f"in EM ANDAMENTO state: {len(wip)}")
    print(f"todo: {len(todo)}")
    for r in todo:
        print(f"  {r['id']}  {r['publishedDisplay']}  {r['title'][:100]}")
    return 0


def cmd_stats(data: dict, raw: dict) -> int:
    print(json.dumps(selection_stats(data, raw), indent=2, ensure_ascii=False))
    return 0


def cmd_stub(aid: str) -> int:
    aid = aid if aid.startswith("a-") else f"a-{aid}"
    print(emit_stub(aid))
    return 0


def cmd_template(data: dict, raw: dict, aid: str) -> int:
    aid = aid if aid.startswith("a-") else f"a-{aid}"
    rec = next((r for r in article_records(data, raw) if r["id"] == aid), None)
    if not rec:
        print(f"not found: {aid}", file=sys.stderr)
        return 1
    print(emit_template(rec))
    return 0


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    cmd = argv[1]
    if cmd == "stub" and len(argv) >= 3:
        return cmd_stub(argv[2])

    data, raw, src = load_data()
    generated = (data.get("meta") or {}).get("generatedAt")
    try:
        src_display = src.relative_to(ROOT)
    except ValueError:
        src_display = src
    print(f"# data source: {src_display} (generated {generated})", file=sys.stderr)

    if cmd == "list":
        return cmd_list(data, raw)
    if cmd == "stats":
        return cmd_stats(data, raw)
    if cmd == "show" and len(argv) >= 3:
        return cmd_show(data, raw, argv[2])
    if cmd == "todo":
        return cmd_todo(data, raw)
    if cmd == "classify":
        # Invoke the external LLM helper script to avoid circular imports.
        proc = subprocess.run([sys.executable, "-m", "src.pipeline.classificar_noticias"] + argv[2:], cwd=ROOT)
        return proc.returncode
    if cmd == "template" and len(argv) >= 3:
        return cmd_template(data, raw, argv[2])
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
