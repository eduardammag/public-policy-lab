#!/usr/bin/env python3
"""Mechanical theme consolidation for Seguranca Presente analyses (renamed).

Same behavior as the original; renamed to reflect primary function.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict

from config import ALIAS_PATH, ANALISE, CONSOLIDA, TABLES_DIR, SENTIMENT_ORDER



ARTICLE_BLOCK_RE = re.compile(
    r"^## (a-\d+)\s+[-—]\s+(?!EM ANDAMENTO)(.+?)$(?P<body>.*?)(?=\n## |\Z)",
    re.MULTILINE | re.DOTALL,
)

GERAL_RE = re.compile(
    r"\*\*Sentimento geral do artigo:\*\*\s*([^\n]+)", re.IGNORECASE
)


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9 ]+", " ", text).lower().strip()
    return re.sub(r"\s+", " ", text)


def normalize_tema(text: str, aliases: dict[str, str]) -> str:
    raw = text.strip().strip('"').strip("'").strip()
    return aliases.get(slugify(raw), raw)


def normalize_sentiment(text: str) -> str:
    folded = slugify(text)
    folded = folded.replace("muitonegativo", "muito negativo")
    folded = folded.replace("muitopositivo", "muito positivo")
    if not folded or folded in {"na", "n a"}:
        return "n/a"
    for value in sorted(SENTIMENT_ORDER, key=len, reverse=True):
        if value != "n/a" and value in folded:
            return value
    if "n/a" in (text or "").lower():
        return "n/a"
    return folded


def extract_theme_rows(body: str, aliases: dict[str, str]) -> list[dict]:
    lines = body.splitlines()
    rows: list[dict] = []
    in_table = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|") and "Tema" in stripped and "Classifica" in stripped:
            in_table = True
            continue
        if not in_table:
            continue
        if not stripped.startswith("|"):
            if rows:
                break
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if len(cells) < 3 or set(cells[0]) <= {"-"}:
            continue
        rows.append(
            {
                "tema": normalize_tema(cells[0], aliases),
                "tratamento": cells[1],
                "sentiment": normalize_sentiment(cells[2]),
            }
        )
    return rows


def parse_blocks(markdown: str, aliases: dict[str, str]) -> list[dict]:
    blocks = []
    for match in ARTICLE_BLOCK_RE.finditer(markdown):
        aid = match.group(1)
        title = match.group(2).strip()
        body = match.group("body")
        geral_match = GERAL_RE.search(body)
        geral = normalize_sentiment(geral_match.group(1)) if geral_match else "n/a"
        blocks.append(
            {
                "id": aid,
                "title": title,
                "temas": extract_theme_rows(body, aliases),
                "geral": geral,
            }
        )
    return blocks


def build_consolidacao(blocks: list[dict]) -> str:
    total = len(blocks)
    off_scope = sum(1 for block in blocks if block["geral"] == "n/a")
    in_scope = total - off_scope
    geral_dist = Counter(block["geral"] for block in blocks)

    tema_articles: dict[str, set[str]] = defaultdict(set)
    tema_sentiments: dict[str, Counter] = defaultdict(Counter)
    for block in blocks:
        for tema in block["temas"]:
            tema_articles[tema["tema"]].add(block["id"])
            tema_sentiments[tema["tema"]][tema["sentiment"]] += 1

    lines = [
        "# Consolidacao Tematica - Seguranca Presente",
        "",
        "> Documento gerado mecanicamente a partir de `analise-individual.md`.",
        "> As contagens sao base de revisao; a sintese narrativa e o agrupamento",
        "> editorial final devem ser preenchidos depois.",
        "",
        "## Sumario Quantitativo",
        "",
        f"- Total de blocos analisados: **{total}**",
        f"- Artigos em escopo: **{in_scope}**",
        f"- Artigos fora de escopo ou n/a: **{off_scope}**",
        "",
        "| Muito Negativo | Negativo | Neutro | Positivo | Muito Positivo | N/A |",
        "|---|---|---|---|---|---|",
        "| {} | {} | {} | {} | {} | {} |".format(
            geral_dist["muito negativo"],
            geral_dist["negativo"],
            geral_dist["neutro"],
            geral_dist["positivo"],
            geral_dist["muito positivo"],
            geral_dist["n/a"],
        ),
        "",
        "## Temas Brutos",
        "",
    ]

    sorted_temas = sorted(tema_articles.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    for tema, articles in sorted_temas:
        dist = tema_sentiments[tema]
        dist_text = "/".join(str(dist[s]) for s in SENTIMENT_ORDER if s != "n/a")
        lines.append(
            f"- **{tema}** - {len(articles)} artigo(s); sentimentos "
            f"(MN/N/Ne/P/MP): {dist_text}; IDs: {', '.join(sorted(articles))}"
        )

    def rank(metric_fn, limit: int = 10) -> list[str]:
        return sorted(tema_articles.keys(), key=metric_fn, reverse=True)[:limit]

    most_freq = rank(lambda t: len(tema_articles[t]))
    most_pos = rank(lambda t: tema_sentiments[t]["muito positivo"] * 2 + tema_sentiments[t]["positivo"])
    most_neg = rank(lambda t: tema_sentiments[t]["muito negativo"] * 2 + tema_sentiments[t]["negativo"])

    lines.extend(["", "## Rankings", "", "### Temas mais frequentes", ""])
    for idx, tema in enumerate(most_freq, 1):
        lines.append(f"{idx}. {tema} ({len(tema_articles[tema])} artigos)")

    lines.extend(["", "### Temas mais elogiados", ""])
    for idx, tema in enumerate(most_pos, 1):
        dist = tema_sentiments[tema]
        lines.append(f"{idx}. {tema} (MP={dist['muito positivo']}, P={dist['positivo']})")

    lines.extend(["", "### Temas mais criticados", ""])
    for idx, tema in enumerate(most_neg, 1):
        dist = tema_sentiments[tema]
        lines.append(f"{idx}. {tema} (MN={dist['muito negativo']}, N={dist['negativo']})")

    lines.extend(
        [
            "",
            "## Categorias Tematicas",
            "",
            "> Placeholder. Agrupar os temas brutos acima em categorias editoriais",
            "> antes de produzir relatorios finais.",
            "",
            "### [Categoria - preencher]",
            "",
            "**Temas agrupados:** [...]",
            "",
            "**Frequencia:** N artigos (X%)",
            "",
            "**Distribuicao de sentimento:** [...]",
            "",
            "**Sintese narrativa:** [...]",
            "",
        ]
    )
    return "\n".join(lines)


def write_csv_outputs(blocks: list[dict], tables_dir: Path) -> list[Path]:
    tables_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    total = len(blocks)
    geral_dist = Counter(block["geral"] for block in blocks)
    off_scope = geral_dist["n/a"]
    in_scope = total - off_scope

    resumo_path = tables_dir / "resumo-sentimentos.csv"
    with resumo_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "total_analisado",
                "em_escopo",
                "fora_de_escopo_ou_na",
                "muito_negativo",
                "negativo",
                "neutro",
                "positivo",
                "muito_positivo",
                "na",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "total_analisado": total,
                "em_escopo": in_scope,
                "fora_de_escopo_ou_na": off_scope,
                "muito_negativo": geral_dist["muito negativo"],
                "negativo": geral_dist["negativo"],
                "neutro": geral_dist["neutro"],
                "positivo": geral_dist["positivo"],
                "muito_positivo": geral_dist["muito positivo"],
                "na": geral_dist["n/a"],
            }
        )
    written.append(resumo_path)

    artigos_path = tables_dir / "artigos-analisados.csv"
    with artigos_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "id_artigo",
                "titulo",
                "sentimento_geral",
                "n_temas",
                "temas",
            ],
        )
        writer.writeheader()
        for block in blocks:
            writer.writerow(
                {
                    "id_artigo": block["id"],
                    "titulo": block["title"],
                    "sentimento_geral": block["geral"],
                    "n_temas": len(block["temas"]),
                    "temas": "; ".join(t["tema"] for t in block["temas"]),
                }
            )
    written.append(artigos_path)

    temas_path = tables_dir / "temas-identificados.csv"
    with temas_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "id_artigo",
                "titulo",
                "tema",
                "como_e_tratado",
                "classificacao",
                "sentimento_geral_artigo",
            ],
        )
        writer.writeheader()
        for block in blocks:
            for tema in block["temas"]:
                writer.writerow(
                    {
                        "id_artigo": block["id"],
                        "titulo": block["title"],
                        "tema": tema["tema"],
                        "como_e_tratado": tema["tratamento"],
                        "classificacao": tema["sentiment"],
                        "sentimento_geral_artigo": block["geral"],
                    }
                )
    written.append(temas_path)

    tema_articles: dict[str, set[str]] = defaultdict(set)
    tema_sentiments: dict[str, Counter] = defaultdict(Counter)
    for block in blocks:
        for tema in block["temas"]:
            tema_articles[tema["tema"]].add(block["id"])
            tema_sentiments[tema["tema"]][tema["sentiment"]] += 1

    temas_resumo_path = tables_dir / "resumo-temas.csv"
    with temas_resumo_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "tema",
                "n_artigos",
                "muito_negativo",
                "negativo",
                "neutro",
                "positivo",
                "muito_positivo",
                "na",
                "ids_artigos",
            ],
        )
        writer.writeheader()
        for tema, articles in sorted(tema_articles.items(), key=lambda kv: (-len(kv[1]), kv[0])):
            dist = tema_sentiments[tema]
            writer.writerow(
                {
                    "tema": tema,
                    "n_artigos": len(articles),
                    "muito_negativo": dist["muito negativo"],
                    "negativo": dist["negativo"],
                    "neutro": dist["neutro"],
                    "positivo": dist["positivo"],
                    "muito_positivo": dist["muito positivo"],
                    "na": dist["n/a"],
                    "ids_artigos": "; ".join(sorted(articles)),
                }
            )
    written.append(temas_resumo_path)

    return written


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="print instead of writing")
    parser.add_argument("--input", type=Path, default=ANALISE)
    parser.add_argument("--output", type=Path, default=CONSOLIDA)
    parser.add_argument("--tables-dir", type=Path, default=TABLES_DIR)
    parser.add_argument("--aliases", type=Path, default=ALIAS_PATH)
    args = parser.parse_args(argv[1:])

    if not args.input.exists():
        print(f"input not found: {args.input}", file=sys.stderr)
        return 1

    aliases = {}
    if args.aliases.exists():
        with args.aliases.open(encoding="utf-8") as f:
            aliases = json.load(f)

    markdown = args.input.read_text(encoding="utf-8")
    blocks = parse_blocks(markdown, aliases)
    print(f"# parsed {len(blocks)} finished article blocks", file=sys.stderr)
    if not blocks:
        print("no finished blocks parsed; nothing to consolidate", file=sys.stderr)
        return 1

    output = build_consolidacao(blocks)
    if args.dry_run:
        print(output)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
        print(f"# wrote {args.output}", file=sys.stderr)
        for path in write_csv_outputs(blocks, args.tables_dir):
            print(f"# wrote {path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
