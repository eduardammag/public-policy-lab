# Consolidacao Tematica - Seguranca Presente

Documento gerado automaticamente a partir de `tabelas/noticias_classificadas.csv`.

## Como a classificacao foi feita

- Cada noticia foi enviada ao LLM pelo script `src/llm_classifier.py`.
- O prompt pede um unico rotulo: `muito negativo`, `negativo`, `neutro`, `positivo`, `muito positivo` ou `n/a`.
- O modelo tambem retorna `confidence` e `reason`; esses campos ficam no CSV de saida.
- A classificacao mede o enquadramento/percepcao retratada pela noticia sobre o programa, nao uma pesquisa direta de opiniao publica.

## Como os temas foram definidos

- Primeiro, noticias duplicadas foram removidas por `articleId`.
- Depois, o texto de cada noticia foi montado com titulo, titulo da historia, justificativa do LLM, resumo e texto bruto.
- Os textos foram vetorizados com TF-IDF, removendo palavras muito comuns.
- Em seguida, KMeans agrupou as noticias em **12 clusters**.
- O nome de cada tema vem dos termos com maior peso no centroide do cluster.
- Portanto, os temas sao exploratorios: eles nascem dos dados, mas devem ser revisados editorialmente antes de conclusoes finais.

## Controle de duplicatas

- Linhas no CSV classificado original: **863**
- Noticias duplicadas removidas por `articleId`: **11**
- Noticias unicas usadas na analise tematica: **852**

## Distribuicao de sentimento

| Muito Negativo | Negativo | Neutro | Positivo | Muito Positivo | N/A |
|---|---|---|---|---|---|
| 52 | 187 | 40 | 518 | 8 | 47 |

## Temas Clusterizados

### tema-06 - rua / cidade / tijuca / centro

- Noticias: **191** (22.4178%)
- Termos definidores: rua; cidade; tijuca; centro; prefeitura; agentes; municipal; homem
- Sentimentos: MN=11, N=56, Ne=11, P=96, MP=0, NA=17
- Exemplos: Prefeitura da Cidade do Rio de Janeiro - Prefeitura da Cidade do Rio de Janeiro | Vias Expressas do Rio ganharão seu “Segurança Presente” | Jacarepaguá e Maracanã podem ter Segurança Presente | Prefeitura fará ações de ordenamento urbano no Centro | Editorial: Witzel está certo, usuário de droga na rua é para internar ou prender

### tema-05 - nova / mulher / homem / preso

- Noticias: **98** (11.5023%)
- Termos definidores: nova; mulher; homem; preso; agenda poder; pinterest nova; pinterest; nova nova
- Sentimentos: MN=6, N=30, Ne=2, P=60, MP=0, NA=0
- Exemplos: Casal é preso após assaltar motorista de aplicativo no Centro do Rio | Polícia investiga se secretário de Governo era alvo de quadrilha que invadiu prédio no Flamengo | Homem invade igreja com foice, assusta fiéis e é preso em Campo Grande | Carlos Minc denuncia PMs por oração em serviço no Largo do Machado | Homem é preso no Aterro do Flamengo após escalar poste para roubar cabos de energia; vídeo

### tema-12 - governo / estado / vagas / agentes

- Noticias: **93** (10.9155%)
- Termos definidores: governo; estado; vagas; agentes; governo estado; civil; castro; projeto
- Sentimentos: MN=6, N=14, Ne=8, P=60, MP=0, NA=5
- Exemplos: Tijuca Presente começa em 3 de Janeiro | Programa Segurança Presente cresce custeado por comerciantes | ‘Sou situação, mas posso virar oposição’, diz Witzel a Paulo Guedes | Segurança Presente chega a novas áreas a partir de agosto | Segurança Presente diminui número de PMs em unidades para expandir áreas

### tema-02 - base / nova / iguacu / nova iguacu

- Noticias: **89** (10.446%)
- Termos definidores: base; nova; iguacu; nova iguacu; governador; barra; castro; inauguracao
- Sentimentos: MN=1, N=1, Ne=1, P=85, MP=1, NA=0
- Exemplos: Segurança Presente será expandido para 5 bairros do Rio | Inaugurada base do Segurança Presente em Nova Iguaçu - Prefeitura de Nova Iguaçu | Segurança Presente começa em Bangu nesta sexta-feira | Botafogo ganha Segurança Presente | Segurança Presente inaugura sua segunda base em Nova Iguaçu - Prefeitura de Nova Iguaçu

### tema-08 - politica / alerj / castro / niteroi

- Noticias: **86** (10.0939%)
- Termos definidores: politica; alerj; castro; niteroi; tse; chama; jairinho agressoes; agressoes namoradas
- Sentimentos: MN=14, N=32, Ne=3, P=32, MP=0, NA=5
- Exemplos: Argentino foragido é capturado em Copacabana graças a sistema de câmeras | Taxistas piratas, tremei: hoje tem mega operação no Galeão | Empregada doméstica é presa em flagrante por dopar e roubar idosa em Copacabana | Morte de porteiro provoca guerra política em Niterói | Major da PM descumpre estatuto e lei ao fazer postagens de apoio a pré-candidato

### tema-07 - centro / niteroi / reducao / roubos

- Noticias: **60** (7.0423%)
- Termos definidores: centro; niteroi; reducao; roubos; ano; regiao; indices; criminalidade
- Sentimentos: MN=4, N=9, Ne=0, P=42, MP=5, NA=0
- Exemplos: O que é a operação Centro Presente | Cresce a procura por imóveis na Zona Sul e na Tijuca | Rio registra centésimo policial baleado este ano | Operação Niterói Presente será ampliada para a Região Oceânica | Às vésperas de completar 3 anos, Niterói Presente ultrapassa uma centena de prisões em flagrante - Prefeitura Municipal de Niterói

### tema-03 - paes / castro / eduardo / eduardo paes

- Noticias: **57** (6.6901%)
- Termos definidores: paes; castro; eduardo; eduardo paes; prefeito; governador; claudio; claudio castro
- Sentimentos: MN=4, N=27, Ne=4, P=12, MP=0, NA=10
- Exemplos: Wilson Witzel apostando em Pedro Fernandes para prefeito em 2020 | Paes elabora Plano dos 100 Dias para o próximo governo à frente da prefeitura | Em quem votar para vereador do Rio de Janeiro em 2020? | Capitão Nelson é eleito prefeito de São Gonçalo | Paes quer restaurar o campus da Gama Filho e outros projetos até abril

### tema-10 - show / copacabana / shakira / gaga

- Noticias: **52** (6.1033%)
- Termos definidores: show; copacabana; shakira; gaga; lady; lady gaga; agentes; eleicoes
- Sentimentos: MN=0, N=2, Ne=2, P=44, MP=0, NA=4
- Exemplos: Segurança Presente atuará na noite e na madrugada em Copacabana e no Leme | Agentes de segurança são treinados pelo TRE-RJ para trabalho durante as eleições | Quinze mil policiais vão trabalhar na segurança das eleições no RJ | Governo do RJ amplia horário do Segurança Presente em Copacabana e no Leme | Segurança no estado ganha reforço de 475 policiais militares

### tema-09 - couto / ricardo couto / ricardo / governo

- Noticias: **47** (5.5164%)
- Termos definidores: couto; ricardo couto; ricardo; governo; estado; educacao; governador; nova
- Sentimentos: MN=3, N=11, Ne=9, P=18, MP=1, NA=5
- Exemplos: Cláudio Castro anuncia comitê permanente para garantir segurança nas escolas | Governador Cláudio Castro anuncia comitê permanente para garantir segurança nas escolas | Governador Cláudio Castro anuncia comitê permanente para garantir segurança nas escolas | Governador Cláudio Castro anuncia comitê permanente para garantir segurança nas escolas | Governador Cláudio Castro anuncia comitê permanente para garantir segurança nas escolas

### tema-04 - carnaval / folioes / reconhecimento facial / estado

- Noticias: **31** (3.6385%)
- Termos definidores: carnaval; folioes; reconhecimento facial; estado; facial; durante carnaval; sambodromo; blocos
- Sentimentos: MN=1, N=1, Ne=0, P=28, MP=0, NA=1
- Exemplos: Segurança Presente vai reforçar policiamento no Carnaval | Pulseiras de identificação para crianças serão distribuídas no carnaval | Miguel Pereira foi a cidade mais segura do Carnaval do Rio | Governo do RJ garante segurança e tranquilidade nos ensaios técnicos na Marquês de Sapucaí | Mais de 270 pessoas foram detidas pela PM durante os primeiros dias de carnaval

### tema-11 - zona sul / sul / zona / crack

- Noticias: **27** (3.169%)
- Termos definidores: zona sul; sul; zona; crack; drogas; cracolandia; catete; armas brancas
- Sentimentos: MN=2, N=4, Ne=0, P=21, MP=0, NA=0
- Exemplos: Segurança Presente apreende mais de 50 objetos cortantes em 1 dia de operação | Laranjeiras terá Segurança Presente a partir desta sexta-feira | Laranjeiras Presente começa a circular no bairro nesta sexta | Mais uma moradora de rua é presa após agredir pedestre; fato ocorreu em Laranjeiras | Copacabana recebe operação de combate ao consumo de crack e delitos praticados por marginais

### tema-01 - redonda / volta redonda / buzios / volta

- Noticias: **21** (2.4648%)
- Termos definidores: redonda; volta redonda; buzios; volta; prefeitura; prefeitura municipal; municipio; prefeito
- Sentimentos: MN=0, N=0, Ne=0, P=20, MP=1, NA=0
- Exemplos: Prefeitura acerta implementação do programa estadual operação Segurança Presente - Prefeitura de Volta Redonda | Japeri ganha duas bases do programa Segurança Presente - Prefeitura Municipal de Japeri | Policiais do Segurança Presente já atuam nas ruas de Japeri e Engenheiro Pedreira - Prefeitura Municipal de Japeri | Volta Redonda e Barra do Piraí, no Médio Paraíba, ganham Segurança Presente do governo do Rio | Concurso Segurança Presente: Volta Redonda terá vagas para agentes civis com salário de mais de R$ 3 mil - Prefeitura de Volta Redonda
