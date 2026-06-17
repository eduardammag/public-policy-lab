from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT

ARTICLES_JSON = PROJECT / "src" / "dados_entrada" / "seguranca_presente_artigos.json"

TABLES_DIR = PROJECT / "tabelas"
GRAPHS_DIR = PROJECT / "graficos"
CONSOLIDA = PROJECT / "consolidacao-temas.md"

LLM_LABELS = TABLES_DIR / "llm_labels.csv"
CLASSIFIED_NEWS = TABLES_DIR / "noticias_classificadas.csv"
EVENTS_BY_ARTICLE = TABLES_DIR / "eventos_por_noticia.csv"
EVENT_RANKING_MD = TABLES_DIR / "ranking-eventos.md"

PIPELINE_WORKERS = 6
MIN_ARTICLES_PER_EVENT = 3
OPENAI_MODEL = "gpt-4o-mini"

SENTIMENT_ORDER = ["muito negativo", "negativo", "neutro", "positivo", "muito positivo", "n/a",]
