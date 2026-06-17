# Segurança Presente - análise de notícias

Este repositório contém uma pipeline em Python para classificar notícias sobre o programa Segurança Presente, gerar gráficos de sentimento e ranquear eventos citados na cobertura jornalística.

O fluxo principal usa um modelo da OpenAI para classificar cada notícia quanto ao sentimento retratado e extrair o evento factual central. Depois, scripts locais consolidam tabelas, gráficos e rankings.

## Estrutura

- `main.py`: executa a pipeline completa.
- `src/dados_entrada/seguranca_presente_artigos.json`: base de notícias de entrada.
- `src/prompts/prompt_classificacao.txt`: prompt usado para classificar sentimento e evento.
- `src/pipeline/classificar_noticias.py`: envia as notícias ao modelo e salva os rótulos brutos.
- `src/pipeline/gerar_graficos.py`: gera tabelas e gráficos de sentimento.
- `src/pipeline/ranquear_eventos.py`: agrega notícias por `evento_chave`/`evento_id` e gera rankings.
- `tabelas/`: saídas tabulares em CSV e Markdown.
- `graficos/`: gráficos gerados pela pipeline.
- `relatorio_final_seguranca_presente.tex`: relatório final em LaTeX.
- `consolidacao-temas.md`: resumo consolidado dos rankings de eventos.

## Requisitos

- Python 3.10 ou superior.
- Chave de API da OpenAI.
- Dependências listadas em `requirements.txt`.

Instale as dependências com:

```bash
pip install -r requirements.txt
```

Se a instalação falhar por causa da última linha do `requirements.txt`, instale manualmente:

```bash
pip install openai python-dotenv pandas matplotlib requests beautifulsoup4 trafilatura feedparser tqdm python-dateutil
```

## Configuração

Crie um arquivo `.env` na raiz do projeto com:

```env
OPENAI_API_KEY=sua_chave_aqui
```

Opcionalmente, é possível definir outro modelo:

```env
OPENAI_MODEL=gpt-4o-mini
```

O modelo padrão também está definido em `src/configuracoes/config.py`.

## Como Rodar

Para executar a pipeline completa:

```bash
python main.py
```

Esse comando executa três etapas:

1. Classificação LLM das notícias.
2. Geração de tabelas e gráficos de sentimento.
3. Ranking de eventos positivos e negativos.

## Execução Por Etapa

Classificar todas as notícias:

```bash
python -m src.pipeline.classificar_noticias --all --workers 6 --out tabelas/llm_labels.csv
```

Gerar tabelas e gráficos:

```bash
python -m src.pipeline.gerar_graficos --labels tabelas/llm_labels.csv --tables-dir tabelas --graphs-dir graficos
```

Gerar ranking de eventos:

```bash
python -m src.pipeline.ranquear_eventos --labels tabelas/noticias_classificadas.csv --out tabelas/eventos_por_noticia.csv --tables-dir tabelas --markdown tabelas/ranking-eventos.md --min-articles 1 --update-consolidacao
```

## Saídas Principais

### Tabelas

- `tabelas/llm_labels.csv`: saída bruta da classificação pelo modelo.
- `tabelas/noticias_classificadas.csv`: base final de notícias classificadas.
- `tabelas/sentiment_counts.csv`: contagem total por sentimento.
- `tabelas/monthly_sentiment_counts.csv`: contagens mensais por sentimento.
- `tabelas/monthly_sentiment_percent.csv`: percentuais mensais por sentimento.
- `tabelas/top_sources_sentiment_counts.csv`: principais fontes por sentimento.
- `tabelas/eventos_por_noticia.csv`: relação notícia-evento.
- `tabelas/eventos_resumo.csv`: resumo agregado por evento.
- `tabelas/eventos_muito_positivos.csv`: eventos mais positivamente retratados.
- `tabelas/eventos_muito_negativos.csv`: eventos mais negativamente retratados.
- `tabelas/ranking-eventos.md`: ranking em Markdown.

### Gráficos

- `graficos/barras_quantidade_por_sentimento.png`
- `graficos/histograma_escore_sentimento.png`
- `graficos/linha_percentual_mensal_sentimentos.png`
- `graficos/area_empilhada_percentual_mensal.png`
- `graficos/linha_volume_mensal_noticias.png`
- `graficos/barras_empilhadas_top_fontes.png`

## Como o Ranking de Eventos Funciona

O ranking usa exclusivamente a chave `evento_chave`, criada pelo modelo no momento da classificação. Essa chave é convertida em `evento_id` e usada para agrupar notícias sobre o mesmo acontecimento factual.

O script de ranking não aplica clusterização, similaridade textual ou consolidação heurística posterior. Portanto, se duas notícias falam do mesmo acontecimento mas receberam `evento_chave` diferente, elas aparecerão como eventos separados. A correção deve ser feita melhorando o prompt e reexecutando a classificação.

Por padrão, o ranking atual considera eventos com:

- pelo menos 1 notícia;
- pelo menos 1 escore de sentimento válido.

O score de sentimento usa a escala:

- `muito negativo`: -2
- `negativo`: -1
- `neutro`: 0
- `positivo`: 1
- `muito positivo`: 2

## Relatório

O relatório final está em:

- `relatorio_final_seguranca_presente.tex`
- `relatorio_final_seguranca_presente.pdf`

Para recompilar:

```bash
pdflatex -interaction=nonstopmode relatorio_final_seguranca_presente.tex
```

## Observações Metodológicas

- A unidade de análise é a notícia, não a opinião pública diretamente.
- O sentimento representa como o Segurança Presente, seus agentes, sua gestão ou eventos relacionados são retratados na cobertura.
- Crimes não são automaticamente negativos e prisões não são automaticamente positivas; a classificação depende de como a notícia associa o fato ao programa.
- O ranking de eventos depende fortemente da consistência de `evento_chave`.

