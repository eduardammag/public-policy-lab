from __future__ import annotations
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
PROJECT = ROOT
ANALISE = PROJECT / "analise-individual.md"
EXPECTED_SITE_STORIES = 363

TARGET_KEYS = {
    "seguranca_presente",
    "programa_seguranca_presente",
    "operacao_seguranca_presente",
}

TEXT_PHRASES = {"seguranca presente"}

ARTICLES_JSON = PROJECT / "src" / "seguranca_presente_artigos.json"

DATA_PATHS = [
    (ARTICLES_JSON, None),
    (PROJECT / "database" / "dados_recortes.json", PROJECT / "database" / "textos_recortes.json"),
    (ROOT / "assets" / "clipping-data.json", ROOT / "assets" / "clipping-raw-texts.json"),
]

TABLES_DIR = PROJECT / "tabelas"
GRAPHS_DIR = PROJECT / "graficos"
CONSOLIDA = PROJECT / "consolidacao-temas.md"
ALIAS_PATH = PROJECT / "src" / "temas_aliases.json"

SENTIMENT_ORDER = ["muito negativo", "negativo", "neutro", "positivo", "muito positivo", "n/a",]
