---
tipo: skill
origem: AIWorkbench
agentes: [WEB, MEMORY, MAESTRO]
sempre_para: []
ativa_quando: pesquisa, procura, busca, le, ler, resume, resumo, qual, quanto, preco, cotacao, noticia, informacao, compara, melhor, review, avaliacao, fonte
tags: [skill]
cssclasses: [skill-note]
atualizado: 2026-10-05
---
# rag-knowledge-engineer

> [!skill] O que faz
> Responder com base na menor evidência suficiente, citando só o que foi realmente lido e assumindo quando não há evidência.

**Usada por:** [[Web Agent]] · [[Memory Agent]] · [[Maestro]]

## Quando usar
- Pesquisas, leituras, resumos e comparações

Ativa sozinha quando o pedido fala de: pesquisa, procura, busca, le, ler, resume, resumo, qual, quanto, preco, cotacao, noticia, informacao, compara, melhor, review, avaliacao, fonte.

## Como o agente aplica
- **Web Agent:** Responda só com o que está na página lida; cite o site/título de onde veio o dado.
- **Web Agent:** Se a página não tem a informação, diga que não encontrou — não complete de cabeça.
- **Web Agent:** Comparação: leia pelo menos 2 resultados reais antes de concluir 'o mais barato/melhor'.
- **Maestro:** Pergunta sobre dado do momento (preço, notícia, clima) vai para o Web Agent ler; nunca responda de memória.

## Regras
- Nunca cruzar fronteira de permissão
- Não citar fonte não vista
- Falta de evidência é dita explicitamente

## Conferir antes de concluir
- Cada dado tem origem lida
- 'Não encontrei' quando não há evidência
- Nada inventado

## Fluxo (catálogo)
1. Definir tarefa e política para falta de evidência
2. Ingestão com origem e identificação
3. Recorte do conteúdo pela estrutura da pergunta
4. Comparar busca lexical e semântica
5. Controlar acesso antes do modelo
6. Avaliar busca e resposta separadamente

Fonte: [AIWorkbench](https://github.com/BielmFranco/AIWorkbench/tree/main/skills/rag-knowledge-engineer) · como os agentes usam: [[Skills]]
