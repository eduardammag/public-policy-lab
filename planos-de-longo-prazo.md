# Planos de Longo Prazo - Seguranca Presente

## 1. Objetivo do projeto

Este projeto tem como objetivo analisar as noticias relacionadas ao programa
Seguranca Presente no clipping do Laboratorio de Politicas Publicas.

O universo inicial visto na interface do site e composto por **363 cards/stories**
que passaram pelo filtro de nomes acompanhados do termo **"Seguranca Presente"**:

- https://clipping-project.onrender.com/

O acesso ao site pode exigir a senha administrativa ja registrada no prompt do
projeto. Como esse dado e sensivel, este documento nao deve repetir a senha; ela
deve ser consultada em `seguranca-presente/prompt.txt` apenas quando a etapa de
coleta ou verificacao exigir acesso ao site.

O objetivo final e replicar, para `seguranca-presente/`, a pipeline de
classificacao usada no projeto `Show da Shakira`, preservando a granularidade
por **artigo individual**. No snapshot live de 12/06/2026 21:13 UTC, os 363
cards/stories correspondem a **604 artigos individuais strict** com
`article.targetKeys` de Seguranca Presente.

## 2. Principios de trabalho

1. **Qualidade acima de velocidade.** O projeto deve ser feito em etapas
   verificaveis, sem pular direto para scripts ou classificacoes antes de
   entender a pipeline original.
2. **Replicacao fiel antes de adaptacao.** A pasta `Show da Shakira` e a fonte
   de referencia. Primeiro se entende o fluxo, depois se decide como adaptar.
3. **Documento evolutivo.** Este arquivo e o plano mestre inicial, mas deve ser
   atualizado conforme novas descobertas forem feitas.
4. **Rastreabilidade.** Cada entrega em `seguranca-presente/` deve ter relacao
   clara com uma etapa ou artefato equivalente do projeto `Show da Shakira`.
5. **Cobertura completa.** Ao final, deve existir uma forma simples de conferir
   quantos artigos individuais foram processados, quantos ficaram pendentes e
   quais outputs foram produzidos.

## 3. Estado inicial

Pasta do projeto:

- `seguranca-presente/`

Arquivos iniciais:

- `prompt.txt`: registra o pedido original, o escopo, o site de origem, a senha
  de acesso e as instrucoes de planejamento.
- `planos-de-longo-prazo.md`: este documento.

Referencia externa dentro do repositorio:

- `Show da Shakira/`: projeto-modelo cuja pipeline deve ser estudada e
  replicada.

## 4. Fase 1 - Documento de longo prazo

### Objetivo

Criar um roteiro operacional completo, mas evolutivo, para guiar o projeto
Seguranca Presente.

### Entregavel

- `seguranca-presente/planos-de-longo-prazo.md`

### Criterios de aceite

- O documento menciona explicitamente os **363 cards/stories** vistos no site.
- O documento menciona explicitamente o filtro **"Seguranca Presente"**.
- O documento registra que a pipeline da Shakira deve ser entendida antes de
  qualquer replicacao.
- O documento separa as etapas de entendimento, planejamento, replicacao e
  validacao.

### Status

Em andamento neste arquivo.

## 5. Fase 2 - Entender a pipeline da Shakira

### Objetivo

Mapear como a pipeline do projeto `Show da Shakira` funciona antes de qualquer
adaptacao para Seguranca Presente.

### Fontes iniciais a examinar

Os seguintes arquivos e diretorios devem ser lidos e resumidos em uma secao
futura deste documento ou em um documento auxiliar:

- `Show da Shakira/workflow-classificacao-shakira.md`
- `Show da Shakira/SOBRE-O-WORKFLOW-GITHUB-ACTIONS.md`
- `Show da Shakira/revisao passos 2 e 3.md`
- `Show da Shakira/analise-individual.md`
- `Show da Shakira/consolidacao-temas.md`
- `Show da Shakira/categorias-temas.md`
- `Show da Shakira/relatorios/`
- `Show da Shakira/tools/`
- `Show da Shakira/penelope-fetched/`

Observacao: alguns nomes de arquivo podem conter acentos no disco. Se houver
diferenca entre este plano e o nome real, o nome real do repositorio prevalece.

### Perguntas a responder

1. Qual e a sequencia real da pipeline?
2. Quais arquivos sao entradas, quais sao intermediarios e quais sao outputs?
3. Como os artigos sao identificados, contados e marcados como processados?
4. Como a analise individual e estruturada?
5. Como temas sao consolidados a partir das analises individuais?
6. Como os relatorios finais sao gerados?
7. Quais scripts sao essenciais e quais sao auxiliares?
8. Que postura editorial a pipeline efetivamente usa?

### Saida esperada

Um mapeamento operacional da pipeline da Shakira, suficiente para que outra
pessoa ou agente consiga reproduzir a logica sem depender de intuicao.

### Status

Concluida como entendimento operacional inicial. A pipeline da Shakira foi
mapeada como quatro camadas:

1. obter snapshot do clipping;
2. iterar noticia por noticia;
3. consolidar temas mecanicamente;
4. produzir categorias e relatorios com revisao editorial.

O resultado esta registrado em
`seguranca-presente/workflow-classificacao-seguranca-presente.md`.

## 6. Fase 3 - Planejar a replicacao para Seguranca Presente

### Objetivo

Transformar o entendimento da pipeline da Shakira em uma estrutura equivalente
para `seguranca-presente/`.

### Decisoes a tomar depois da Fase 2

1. Quais arquivos do projeto Shakira serao espelhados diretamente.
2. Quais scripts precisam ser copiados e adaptados.
3. Qual sera o nome do alvo ou filtro usado para selecionar as noticias.
4. Como os artigos individuais dentro dos 363 cards/stories serao listados e
   deduplicados.
5. Qual sera o formato do arquivo de analise individual.
6. Qual sera o formato da consolidacao tematica.
7. Como os relatorios finais serao organizados.
8. Como registrar progresso, pendencias e inconsistencias.

### Estrutura candidata

A estrutura abaixo foi confirmada como base inicial apos o estudo da pipeline da
Shakira:

```text
seguranca-presente/
├── prompt.txt
├── planos-de-longo-prazo.md
├── workflow-classificacao-seguranca-presente.md
├── analise-individual.md
├── consolidacao-temas.md
├── categorias-temas.md
├── relatorios/
├── tools/
└── recortes_brutos/
```

### Status

Implementada como scaffold operacional. A pasta agora tem documentos-base,
diretorios de saida e helpers adaptados. A analise substantiva das noticias
ainda nao foi iniciada.

### Decisoes tecnicas registradas

- O filtro principal combina as chaves `seguranca_presente`,
  `programa_seguranca_presente` e `operacao_seguranca_presente`.
- O helper usa como lista canonica os artigos cujo `article.targetKeys` contem
  `seguranca_presente`, `programa_seguranca_presente` ou
  `operacao_seguranca_presente`.
- O total de referencia da interface continua sendo **363 cards/stories**; o
  total canonico de trabalho e a quantidade de artigos individuais strict
  extraida do snapshot disponivel.
- Os scripts usam `seguranca-presente/recortes_brutos/` como fonte preferencial de
 snapshots e caem para `assets/` se a pasta `recortes_brutos/` ainda nao tiver dados.

## 7. Fase 4 - Replicar a pipeline

### Objetivo

Executar a adaptacao real da pipeline para analisar os artigos individuais
strict sobre Seguranca Presente.

### Trabalho previsto

1. Criar a estrutura final da pasta `seguranca-presente/`.
2. Preparar ou baixar os dados necessarios a partir do clipping.
3. Adaptar os scripts essenciais da Shakira para o alvo Seguranca Presente.
4. Gerar a lista controlada de artigos a processar.
5. Rodar a etapa de analise individual, artigo por artigo.
6. Consolidar temas a partir das analises individuais.
7. Produzir relatorios finais por tema e/ou relatorio geral.
8. Validar contagens, duplicidades, pendencias e consistencia dos outputs.

### Criterios de aceite

- Os 363 cards/stories esperados foram localizados e os artigos individuais
  strict foram considerados.
- O processo tem mecanismo de controle de progresso.
- Os outputs finais sao rastreaveis ate as noticias individuais.
- As adaptacoes em relacao a Shakira estao documentadas.
- Qualquer divergencia de contagem e registrada explicitamente.

### Status

Pendente. Esta fase nao deve comecar enquanto a Fase 2 nao estiver documentada.

## 8. Entregaveis finais esperados

Ao final do projeto, a pasta `seguranca-presente/` deve conter:

- Plano de longo prazo atualizado.
- Documento explicando a pipeline da Shakira e sua transferencia para Seguranca
  Presente.
- Dados ou snapshots necessarios para iterar sobre as noticias.
- Analises individuais das noticias.
- Consolidacao tematica.
- Categorias tematicas.
- Relatorios finais.
- Scripts ou helpers adaptados.
- Registro de validacao da contagem dos 363 cards/stories e dos artigos
  individuais strict.

## 9. Decisoes ja tomadas

- O arquivo de plano se chama `planos-de-longo-prazo.md`.
- O documento inicial deve ser completo, mas evolutivo.
- O sucesso principal e a classificacao completa dos artigos individuais strict
  ligados aos 363 cards/stories, com consolidacao e relatorios.
- O foco do documento e operacional.
- A postura editorial sera derivada da pipeline da Shakira, e nao decidida antes
  do estudo dessa pipeline.
- A primeira entrega apos o plano de modo plano e somente este documento
  markdown; a replicacao da pipeline vem depois.

## 10. Decisoes pendentes

- Confirmar a estrutura final da pasta `seguranca-presente/`.
- Confirmar quais scripts da Shakira serao reutilizados.
- Confirmar como os dados dos 363 cards/stories e dos artigos individuais serao
  obtidos ou versionados.
- Confirmar se sera necessario criar um workflow automatizado para buscar dados
  do site, como aconteceu no projeto Shakira.
- Confirmar o formato final dos relatorios.
- Confirmar o criterio editorial depois de estudar a pipeline original.

## 11. Proxima acao recomendada

A proxima acao e validar a **Etapa 0 - Dados** para Seguranca Presente:

1. Obter ou confirmar snapshots atualizados em `seguranca-presente/recortes_brutos/`.
2. Rodar `python seguranca-presente/tools/seguranca_presente_iter.py list`.
3. Comparar a contagem de cards/stories com os **363** esperados e registrar a
   contagem de artigos individuais strict.
4. Se houver divergencia, registrar se ela vem de snapshot antigo, chaves de
   alvo ou duplicidades.
5. So depois iniciar a Etapa 1 de analise individual.
