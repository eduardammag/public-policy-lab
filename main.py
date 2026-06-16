#!/usr/bin/env python3
"""Run the full Seguranca Presente analysis pipeline."""
from __future__ import annotations

import subprocess
import sys

from src.configuracoes.config import (
    CLASSIFIED_NEWS,
    EVENTS_BY_ARTICLE,
    EVENT_RANKING_MD,
    GRAPHS_DIR,
    LLM_LABELS,
    MIN_ARTICLES_PER_EVENT,
    PIPELINE_WORKERS,
    ROOT,
    TABLES_DIR,
)

def run_step(name: str, command: list[str]) -> None:
    print(f"\n[INICIO] {name}", flush=True)
    print(f"[COMANDO] {' '.join(command)}", flush=True)
    subprocess.run(command, cwd=ROOT, check=True)
    print(f"[OK] {name}", flush=True)


def main() -> int:
    print("Pipeline Seguranca Presente iniciada.", flush=True)
    print(f"Raiz do projeto: {ROOT}", flush=True)
    print(f"Tabelas: {TABLES_DIR}", flush=True)
    print(f"Graficos: {GRAPHS_DIR}", flush=True)
    print(f"Workers LLM: {PIPELINE_WORKERS}", flush=True)
    print(f"Minimo de noticias por evento: {MIN_ARTICLES_PER_EVENT}", flush=True)

    print("\nPreparando pastas de saida...", flush=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    GRAPHS_DIR.mkdir(parents=True, exist_ok=True)
    print("Pastas prontas.", flush=True)

    run_step(
        "Fase 1/3 - Classificacao LLM unificada",
        [
            sys.executable,
            "-m",
            "src.pipeline.classificar_noticias",
            "--all",
            "--out",
            str(LLM_LABELS),
            "--workers",
            str(PIPELINE_WORKERS),
        ],
    )
    print(f"CSV bruto do LLM gerado em: {LLM_LABELS}", flush=True)

    run_step(
        "Fase 2/3 - Graficos e tabelas de sentimento",
        [
            sys.executable,
            "-m",
            "src.pipeline.gerar_graficos",
            "--labels",
            str(LLM_LABELS),
            "--tables-dir",
            str(TABLES_DIR),
            "--graphs-dir",
            str(GRAPHS_DIR),
        ],
    )
    print(f"CSV final de noticias gerado em: {CLASSIFIED_NEWS}", flush=True)
    print(f"Graficos gerados em: {GRAPHS_DIR}", flush=True)

    run_step(
        "Fase 3/3 - Ranking de eventos",
        [
            sys.executable,
            "-m",
            "src.pipeline.ranquear_eventos",
            "--labels",
            str(CLASSIFIED_NEWS),
            "--out",
            str(EVENTS_BY_ARTICLE),
            "--markdown",
            str(EVENT_RANKING_MD),
            "--min-articles",
            str(MIN_ARTICLES_PER_EVENT),
            "--update-consolidacao",
        ],
    )
    print(f"Eventos por noticia gerados em: {EVENTS_BY_ARTICLE}", flush=True)
    print(f"Ranking markdown gerado em: {EVENT_RANKING_MD}", flush=True)

    print("\nPipeline concluida.")
    print(f"- CSV classificado: {CLASSIFIED_NEWS}")
    print(f"- Eventos por noticia: {EVENTS_BY_ARTICLE}")
    print(f"- Ranking de eventos: {EVENT_RANKING_MD}")
    print(f"- Tabelas: {TABLES_DIR}")
    print(f"- Graficos: {GRAPHS_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
