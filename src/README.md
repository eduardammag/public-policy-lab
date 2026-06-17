# Organizacao do `src`

Este diretorio esta separado por responsabilidade:

- `configuracoes/`: caminhos, parametros da pipeline e listas compartilhadas.
- `dados_entrada/`: arquivos brutos de entrada, como o JSON de noticias.
- `prompts/`: prompts usados pelo LLM.
- `pipeline/`: scripts executaveis da analise principal.
  - `classificar_noticias.py`: classifica sentimento e extrai evento/tema em uma unica chamada LLM.
  - `gerar_graficos.py`: gera tabelas finais e graficos de sentimento.
  - `ranquear_eventos.py`: agrega eventos e gera rankings de mais amados/odiados.
- `utilitarios/`: funcoes auxiliares para ler e preparar noticias.

A entrada principal do projeto continua sendo:

```powershell
python main.py
```

## Chaves de API

O arquivo `.env` deve ter:

```text
OPENAI_API_KEY=...
```

## Saidas

Ao rodar `python main.py`, a pipeline gera:

```text
tabelas/
  llm_labels.csv
  noticias_classificadas.csv
  eventos_por_noticia.csv
  ranking-eventos.md
  *.csv de apoio
graficos/
  *.png
```

A classificacao e a separacao de eventos/temas sao feitas em uma unica chamada ao modelo OpenAI configurado em `src/configuracoes/config.py`.
