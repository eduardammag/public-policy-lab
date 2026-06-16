# Eventos Mais Amados e Odiados - Seguranca Presente

Os eventos e sentimentos foram extraidos pelo mesmo prompt unico em `src/llm_classifier.py`.
Este script apenas agrega e ranqueia os campos ja retornados pelo LLM.

- Noticias unicas analisadas: **2**
- Criterio do ranking principal: eventos com pelo menos **1** noticia(s).
- `score_medio` usa: muito negativo=-2, negativo=-1, neutro=0, positivo=1, muito positivo=2, n/a=0.

## Eventos Mais Amados

1. **Operacao_Centro_Presente_Centro_Rio_2016** - score medio 1.0; 1 noticia(s); positivos=1; negativos=0. Exemplos: O que é a operação Centro Presente
2. **Operacao_Centro_Presente_Rio_de_Janeiro_2016** - score medio 1.0; 1 noticia(s); positivos=1; negativos=0. Exemplos: Prefeitura da Cidade do Rio de Janeiro - Prefeitura da Cidade do Rio de Janeiro

## Eventos Mais Odiados

1. **Operacao_Centro_Presente_Centro_Rio_2016** - score medio 1.0; 1 noticia(s); negativos=0; positivos=1. Exemplos: O que é a operação Centro Presente
2. **Operacao_Centro_Presente_Rio_de_Janeiro_2016** - score medio 1.0; 1 noticia(s); negativos=0; positivos=1. Exemplos: Prefeitura da Cidade do Rio de Janeiro - Prefeitura da Cidade do Rio de Janeiro