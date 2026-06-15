# Workflow - Classificacao Seguranca Presente

## Objetivo

Classificar artigos sobre o programa Seguranca Presente, manter uma analise
individual rastreavel por `articleId` e consolidar temas/sentimentos para uso
posterior em categorias, relatorios e metricas.

## Estado atual

- Codigo em `src/`.
- Arquivos de trabalho na raiz: `analise-individual.md`,
  `consolidacao-temas.md`, `categorias-temas.md` e
  `planos-de-longo-prazo.md`.
- `analise-individual.md` tem 5 artigos concluidos.
- `consolidacao-temas.md` ja foi gerado para esses 5 artigos.
- `categorias-temas.md` ainda e placeholder.
- `src/seguranca_presente_artigos.json` contem uma listagem auxiliar por
  mencao textual a "seguranca presente".

## Ponto de atencao

Antes de rodar a pipeline em escala, normalizar os caminhos em `src/config.py`.
Hoje ele ainda define:

```python
PROJECT = ROOT / "seguranca-presente"
```

Como este workspace ja e a pasta `seguranca-presente/`, o recomendado e usar a
raiz atual como projeto (`PROJECT = ROOT`) e manter as saidas em:

- `analise-individual.md`
- `consolidacao-temas.md`
- `tabelas/`
- `database/` quando houver snapshots completos

## Dados

Escopo canonico:

- `seguranca_presente`
- `programa_seguranca_presente`
- `operacao_seguranca_presente`

A lista principal deve usar `article.targetKeys`. Mencoes textuais a
"seguranca presente" servem para auditoria e recuperacao de possiveis faltantes,
nao para substituir automaticamente o escopo canonico.

Referencias atuais:

- 363 cards/stories vistos na interface do clipping.
- 604 artigos individuais strict no snapshot live citado no plano.
- 863 artigos na listagem auxiliar por frase em
  `src/seguranca_presente_artigos.json`.

## Comandos principais

Depois de corrigir os caminhos e confirmar a fonte de dados:

```powershell
python src/iter_helper.py stats
python src/iter_helper.py todo
python src/iter_helper.py show a-1041
python src/iter_helper.py template a-1041
python src/consolida_temas.py
```

Helpers adicionais:

```powershell
python src/llm_classifier.py --sample 10
python src/generate_econ_metrics.py
```

Usar os dois ultimos apenas depois de gerar/confirmar as tabelas base.

## Analise individual

Cada artigo em `analise-individual.md` deve seguir este formato:

```markdown
---
## a-123 - Titulo da noticia

**Fonte:** Veiculo (host)
**Data:** Data publicada
**URL:** URL original

### Resumo Narrativo

Texto em prosa, de um a tres paragrafos.

### Temas Identificados

| Tema | Como e tratado | Classificacao |
|------|---------------|---------------|
| tema curto | descricao do enquadramento | positivo |

### Classificacao Geral

**Sentimento geral do artigo:** positivo
```

Sentimentos permitidos:

- `muito negativo`
- `negativo`
- `neutro`
- `positivo`
- `muito positivo`
- `n/a`

Artigos fora de escopo, quando analisados, devem receber `n/a`; nao devem ser
omitidos sem registro.

## Consolidacao

`src/consolida_temas.py` deve:

- ler blocos finalizados de `analise-individual.md`;
- ignorar blocos `EM ANDAMENTO`;
- extrair temas e sentimentos;
- atualizar `consolidacao-temas.md`;
- gerar CSVs em `tabelas/`.

A consolidacao mecanica e base de revisao. Categorias finais so devem ser
definidas depois de haver volume suficiente de artigos analisados.

## Proxima ordem de trabalho

1. Corrigir `src/config.py`.
2. Confirmar snapshots em `database/` ou decidir fonte alternativa.
3. Rodar `iter_helper.py stats` e registrar a contagem real.
4. Usar `iter_helper.py todo` para montar a fila.
5. Analisar novos artigos em lotes.
6. Rodar `consolida_temas.py` ao fim de cada lote.
7. Preencher categorias e relatorios somente a partir dos temas observados.

## Postura editorial

A sintese deve ser critica e ancorada nos dados. Nao inverter o sinal da
cobertura por principio: se os artigos forem majoritariamente positivos,
negativos ou mistos, o texto final deve refletir isso.
