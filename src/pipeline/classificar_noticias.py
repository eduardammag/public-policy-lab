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

from src.configuracoes.config import SENTIMENT_ORDER, TABLES_DIR

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None

try:
    import openai
except Exception:
    openai = None

DEFAULT_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
MAX_OUTPUT_TOKENS = 4000
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


def _remove_accents(s: str) -> str:
    """Return a lowercase, accent-free string for robust matching."""
    if not s:
        return ""
    s_norm = unicodedata.normalize("NFD", s)
    return "".join(ch for ch in s_norm if unicodedata.category(ch) != "Mn").lower()


def contains_exact_phrase(rec: dict, phrase: str = "seguranca presente") -> bool:
    text = "\n\n".join([rec.get("title", ""), rec.get("summaryPreview", ""), rec.get("rawText", "")])
    text_norm = _remove_accents(text)
    phrase_norm = _remove_accents(phrase)
    # word boundaries to avoid matching substrings
    return re.search(rf"\b{re.escape(phrase_norm)}\b", text_norm, flags=re.IGNORECASE) is not None


def ensure_openai_available() -> None:
    if load_dotenv:
        load_dotenv()
    if openai is None:
        raise SystemExit("Missing dependency 'openai'. Install requirements.txt")
    key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_KEY")
    if not key:
        raise SystemExit("OpenAI API key not found in environment (OPENAI_API_KEY)")
    os.environ["OPENAI_API_KEY"] = key


def openai_json(prompt: str, model: str) -> str:
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
        max_tokens=MAX_OUTPUT_TOKENS,
        response_format={"type": "json_object"},
    )
    return (resp.choices[0].message.content or "").strip()


def load_prompt_template() -> str:
    try:
        return PROMPT_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise SystemExit(f"Prompt file not found: {PROMPT_PATH}")


def parse_json_response(content: str) -> dict:
    content = (content or "").strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*", "", content, flags=re.IGNORECASE)
        content = re.sub(r"\s*```$", "", content)
    start = content.find("{")
    end = content.rfind("}")
    if start >= 0 and end > start:
        content = content[start : end + 1]
    return json.loads(content, strict=False)


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


def classify_text(
    text: str,
    model: str = DEFAULT_MODEL,
    retries: int = 3,
) -> dict:
    ensure_openai_available()
    template = load_prompt_template()
    prompt = template.replace("{noticia}", text[:10000])
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            content = openai_json(prompt, model)
            break
        except Exception as e:
            last_error = e
            if attempt == retries:
                return {
                    "label": "n/a",
                    "reason_sentimento": f"API error: {e}",
                }
            retry_seconds = re.search(r"retry in ([0-9.]+)s|seconds:\s*(\d+)", str(e), re.IGNORECASE)
            suggested_delay = 0.0
            if retry_seconds:
                suggested_delay = float(next(value for value in retry_seconds.groups() if value))
            time.sleep(max(2 * attempt, suggested_delay))

    try:
        parsed = parse_json_response(content)
        parsed["label"] = normalize_label(parsed.get("label"))
        return parsed
    except Exception:
        return {
            "label": "n/a",
            "reason_sentimento": content or str(last_error or ""),
        }


def load_data_for_classification() -> tuple[dict, Path]:
    try:
        from src.utilitarios.dados_noticias import load_data

        return load_data()
    except Exception:
        raise SystemExit("Cannot import data loader from src/utilitarios/dados_noticias.py")


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
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def article_to_row(rec: dict, out: dict, model: str) -> dict:
    label = normalize_label(out.get("label"))
    reason = out.get("reason_sentimento") or out.get("reason") or ""
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
        "reason": str(reason)[:1200],
        "evidencia_sentimento": str(out.get("evidencia_sentimento", ""))[:1200],
        "evento": event_name,
        "evento_chave": event_key,
        "evento_id": slugify(event_key),
        "tipo_evento": str(out.get("tipo_evento", ""))[:200],
        "local": str(out.get("local", ""))[:200],
        "data_evento": str(out.get("data_evento", ""))[:100],
        "descricao_curta": str(out.get("descricao_curta", ""))[:1200],
        "evidencia_evento": str(out.get("evidencia_evento", ""))[:1200],
        "model": model,
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="classify all articles")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL)
    parser.add_argument("--out", type=Path, default=TABLES_DIR / "llm_labels.csv")
    parser.add_argument("--workers", type=int, default=1, help="parallel API calls")
    args = parser.parse_args(argv[1:])

    data, _path = load_data_for_classification()
    arts = []
    try:
        from src.utilitarios.dados_noticias import article_records

        arts = article_records(data)
    except Exception:
        raise SystemExit("Cannot import article_records from src/utilitarios/dados_noticias.py")

    # Filter: keep only articles containing the exact phrase "segurança presente"
    original_count = len(arts)
    arts = [r for r in arts if contains_exact_phrase(r, "seguranca presente")]
    if len(arts) != original_count:
        print(f"Filtered articles: {original_count} -> {len(arts)} (exact phrase 'segurança presente')", file=sys.stderr)

    if args.all:
        candidates = arts
    else:
        parser.print_help()
        return 2

    existing = read_existing_rows(args.out)
    rows_by_key = dict(existing)
    pending = []
    for rec in candidates:
        key = rec.get("recordKey") or rec["id"]
        if key in rows_by_key and rows_by_key[key].get("label") and rows_by_key[key].get("evento_chave"):
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
