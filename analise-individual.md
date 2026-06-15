# Analise Individual - Seguranca Presente

> Documento cumulativo de analise por noticia, conforme
> `seguranca-presente/workflow-classificacao-seguranca-presente.md`.
>
> Cada bloco deve corresponder a uma noticia. O ID deve usar o formato
-> `a-{articleId}`, rastreavel ao snapshot `database/dados_recortes.json` e, quando houver
-> texto bruto, a chave `article-{articleId}` em `database/textos_recortes.json`.

## Status do loop

- **Fonte de dados ativa:** pendente. Preferir
  `seguranca-presente/database/dados_recortes.json` e
  `seguranca-presente/database/textos_recortes.json` quando existirem;
  caso contrario, os helpers tentam usar `assets/`.
- **Referencia da interface do site:** 363 cards/stories.
- **Total canonico para analise individual:** 604 artigos strict no snapshot
  live de 12/06/2026 21:13 UTC.
- **Alvos usados para a lista canonica:** `seguranca_presente`,
  `programa_seguranca_presente`, `operacao_seguranca_presente` em
  `article.targetKeys`.
- **Artigos concluidos:** 5.
- **Artigos em andamento:** 0.

## Notas de execucao

- Antes de analisar um artigo, registrar um bloco `EM ANDAMENTO`.
- Ao concluir, substituir o bloco pelo formato completo de analise.
- Artigos fora de escopo devem ser registrados como `n/a`, nunca omitidos
  silenciosamente.

---
## a-1041 - Prefeitura da Cidade do Rio de Janeiro - Prefeitura da Cidade do Rio de Janeiro

**Fonte:** Google News (rio.rj.gov.br)
**Data:** 31/05/2016 07:00 UTC
**URL:** http://www.rio.rj.gov.br/web/guest/exibeconteudo?id=6167059

### Resumo Narrativo

O texto da Prefeitura do Rio anuncia a Operacao Centro Presente como uma expansao da Operacao Seguranca Presente para os principais corredores do Centro, entre a Regiao Portuaria, Praca Maua, Avenida Rio Branco, Praca 15, Cinelandia, MAM e entorno do Aeroporto Santos Dumont. A cobertura e institucional e apresenta a iniciativa como resposta a indices elevados de violencia na regiao central, com patrulhamento ostensivo de 528 agentes, viaturas, motos, bicicletas, monitoramento por GPS e cameras para registrar abordagens.

O enquadramento e fortemente favoravel ao programa. A materia enfatiza parceria entre prefeitura, governo estadual e Fecomercio, investimento anual de R$ 47 milhoes, permanencia da operacao e integracao com diferentes orgaos municipais e estaduais. Tambem apresenta resultados positivos das operacoes ja existentes, citando prisões, capturas de foragidos e ausencia de troca de tiros como evidencias de eficacia e de um modelo de seguranca mais proximo do cidadao.

### Temas Identificados

| Tema | Como e tratado | Classificacao |
|------|---------------|---------------|
| Expansao territorial para o Centro | Apresentada como resposta necessaria a uma area com indices de violencia acima da media da cidade. | positivo |
| Patrulhamento ostensivo e desenho operacional | Detalha efetivo, horarios, areas de cobertura, viaturas, bicicletas, motos e patrulhamento a pe como estrutura robusta. | muito positivo |
| Parceria publico-privada | Prefeitura, estado e Fecomercio aparecem como financiadores e operadores de uma politica permanente. | positivo |
| Monitoramento e controle das abordagens | Cameras e GPS sao apresentados como instrumentos de transparencia e controle operacional. | positivo |
| Resultados anteriores da Seguranca Presente | Prisões, capturas de foragidos e ausencia de tiroteios sao usados para legitimar a expansao. | muito positivo |

### Classificacao Geral

**Sentimento geral do artigo:** muito positivo

---
## a-1570 - Tijuca Presente começa em 3 de Janeiro

**Fonte:** Diario do Rio (diariodorio.com)
**Data:** 24/12/2018 13:50 UTC
**URL:** https://diariodorio.com/tijuca-presente-comeca-em-3-de-janeiro

### Resumo Narrativo

O artigo informa que o projeto Seguranca Presente chegaria a Tijuca em 3 de janeiro de 2019, com base na Praca Saens Pena e patrulhamento inicial ate a Praca Varnhagen. A materia descreve cerca de 30 agentes, incluindo policiais militares da ativa, da reserva e agentes civis egressos das Forcas Armadas, atuando das 8h as 20h, a pe, em bicicletas e viaturas. A expansao e apresentada como gradual, com novos modulos ate que o Tijuca Presente cubra todo o bairro.

O enquadramento e celebratorio e favoravel. O texto recupera a origem do modelo na Lapa Presente, cita a expansao para Meier, Lagoa, Aterro, Centro, Leblon e Ipanema, e enfatiza carater permanente, filmagem de abordagens, monitoramento por GPS e articulacao entre multiplos orgaos. O fechamento explicita uma defesa editorial do programa, afirmando que quem ve um bairro antes e depois do Seguranca Presente percebe a diferenca.

### Temas Identificados

| Tema | Como e tratado | Classificacao |
|------|---------------|---------------|
| Expansao para a Tijuca | Tratada como boa noticia para o bairro e como inicio de cobertura progressiva. | muito positivo |
| Modelo operacional do patrulhamento | Efetivo, base, horario e meios de deslocamento sao apresentados como estrutura concreta de seguranca. | positivo |
| Transparencia operacional | Filmagem de abordagens e GPS sao destacados como elementos de controle e acompanhamento. | positivo |
| Continuidade e expansao do programa | A materia situa a Tijuca dentro de uma trajetoria de crescimento do modelo em varios bairros. | positivo |
| Avaliacao editorial do impacto | O texto afirma explicitamente que o programa faz diferenca nos bairros atendidos. | muito positivo |

### Classificacao Geral

**Sentimento geral do artigo:** muito positivo

---
## a-1569 - Vias Expressas do Rio ganharão seu “Segurança Presente”

**Fonte:** Diario do Rio (diariodorio.com)
**Data:** 18/01/2019 16:14 UTC
**URL:** https://diariodorio.com/vias-expressas-do-rio-ganharao-seu-seguranca-presente

### Resumo Narrativo

O artigo apresenta a possibilidade de criar, nas vias expressas do Rio, um programa inspirado no Seguranca Presente. A justificativa parte de um diagnostico negativo da Linha Vermelha, Arco Metropolitano e Linha Amarela, descritos como areas vulneraveis a crimes em determinados horarios, com o BPVE recebendo dezenas de chamadas mensais de vitimas ou testemunhas apenas na Linha Vermelha.

Apesar do diagnostico de inseguranca ser duro, o tratamento dado ao modelo Seguranca Presente e positivo. A proposta associada ao governo Wilson Witzel e descrita como reforco ao BPVE, com policiais de folga, reserva e egressos das Forcas Armadas, alem de viaturas, efetivo e planejamento. O texto conclui desejando que a iniciativa tenha o mesmo sucesso do Seguranca Presente, reforcando o programa como referencia a ser replicada.

### Temas Identificados

| Tema | Como e tratado | Classificacao |
|------|---------------|---------------|
| Inseguranca nas vias expressas | As vias sao retratadas como areas de risco, com ocorrencias frequentes e necessidade de resposta. | negativo |
| Replicacao do modelo Seguranca Presente | O programa aparece como referencia positiva para enfrentar crimes nas vias expressas. | positivo |
| Reforco ao policiamento especializado | A proposta e apresentada como complemento planejado ao BPVE, com viaturas e efetivo adicional. | positivo |
| Participacao de policiais de folga e reserva | O arranjo de pessoal e tratado como componente operacional do modelo, sem problematizacao. | neutro |
| Expectativa de eficacia | O texto expressa desejo de que a nova versao repita o sucesso do Seguranca Presente. | positivo |

### Classificacao Geral

**Sentimento geral do artigo:** positivo

---
## a-1060 - Programa Segurança Presente cresce custeado por comerciantes

**Fonte:** Google News (oglobo.globo.com)
**Data:** 21/01/2019 08:00 UTC
**URL:** https://oglobo.globo.com/rio/programa-seguranca-presente-cresce-custeado-por-comerciantes-23387986

### Resumo Narrativo

O artigo de O Globo enquadra o Seguranca Presente como principal projeto de seguranca publica do governo Wilson Witzel e informa planos de expansao para Jacarepagua, Maracana e Baixada Fluminense. O foco da materia esta no modelo de financiamento: o secretario de Governo, Gutemberg Fonseca, afirma que a expansao dependeria de recursos de parceiros privados ou prefeituras, evitando aumento de gasto direto do governo estadual.

A cobertura e majoritariamente positiva, mas com uma camada institucional mais analitica do que celebratoria. O texto destaca interesse de associacoes comerciais, concessionaria do Maracana e prefeitura de Nova Iguacu, alem de mencionar a tentativa de recompor repasses da Fecomercio bloqueados pelo TCU por desvio de finalidade. Tambem registra que a expansao usaria a mancha criminal como criterio e que o governo pretendia ampliar vagas para policiais em folga sem aumentar o numero de PMs cedidos exclusivamente ao projeto.

### Temas Identificados

| Tema | Como e tratado | Classificacao |
|------|---------------|---------------|
| Expansao territorial do programa | A ampliacao para novas regioes e apresentada como prioridade do governo e demanda de parceiros locais. | positivo |
| Financiamento por comerciantes e parceiros | Tratado como solucao para expandir sem aumentar gasto estadual direto. | positivo |
| Dependencia de recursos privados e municipais | A expansao fica condicionada a parceiros, o que introduz limite operacional ao crescimento. | neutro |
| Bloqueio de repasses da Fecomercio pelo TCU | Menciona questionamento institucional sobre desvio de finalidade, sem transformar isso no foco da materia. | negativo |
| Criterio de mancha criminal | O secretario apresenta a escolha de areas por aumento de crimes como racional tecnico de expansao. | positivo |
| Uso de policiais em folga | O texto descreve o aumento de vagas de bico oficial como mecanismo para ampliar o programa. | neutro |

### Classificacao Geral

**Sentimento geral do artigo:** positivo

---
## a-1568 - Jacarepaguá e Maracanã podem ter Segurança Presente

**Fonte:** Diario do Rio (diariodorio.com)
**Data:** 21/01/2019 11:53 UTC
**URL:** https://diariodorio.com/jacarepagua-e-maracana-podem-ter-seguranca-presente

### Resumo Narrativo

O artigo informa que Maracana e Jacarepagua poderiam receber unidades do Seguranca Presente, a partir de interesse da Associacao Comercial da Tijuca, da concessionaria que administra o Maracana e da Associacao Comercial e Industrial de Jacarepagua. A materia se apoia em informacao do Extra e resume a estrategia do secretario Gutemberg Fonseca de evitar aporte direto de dinheiro do contribuinte, buscando financiamento por atores locais.

O enquadramento e favoravel e bastante sintetico. O texto apresenta o projeto como um sucesso nas regioes onde ja opera e cita o Leblon Presente como exemplo, com reducao de 81% dos crimes registrados na 14a DP no horario de atuacao do programa. Tambem conecta a possivel expansao para Maracana e Jacarepagua a uma agenda mais ampla de replicacao, mencionando projeto semelhante para vias expressas.

### Temas Identificados

| Tema | Como e tratado | Classificacao |
|------|---------------|---------------|
| Expansao para Maracana e Jacarepagua | Tratada como possibilidade positiva de levar o modelo a novas areas. | positivo |
| Financiamento local privado | Associacoes comerciais e concessionaria aparecem como possiveis financiadoras, evitando aporte do contribuinte. | positivo |
| Resultados no Leblon Presente | A reducao de 81% dos crimes e usada como evidencia forte de sucesso do modelo. | muito positivo |
| Replicabilidade do programa | A materia associa novas unidades a um movimento maior de expansao, inclusive para vias expressas. | positivo |
| Ausencia de contraponto | O texto nao apresenta criticas, riscos ou custos alternativos do modelo. | neutro |

### Classificacao Geral

**Sentimento geral do artigo:** positivo
