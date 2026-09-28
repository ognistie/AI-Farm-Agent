---
tipo: tarefa-referencia
agente: WEB
contexto: "Conteúdo muda todo dia"
keywords: pesquisa noticias recentes busque ultimas copa mundo
tags: [referencia, web]
cssclasses: [ref-note]
---
# Pesquisa de notícias recentes

> [!route] Pedido exemplo
> busque as últimas notícias sobre a copa do mundo

**Agente:** [[Web Agent]] · **Contexto:** Conteúdo muda todo dia

## Caminho
1. Query + &tbm=nws (aba Notícias)
2. web_goto
3. web_read

## Forma alternativa
Google News direto: news.google.com/search?q=

## Critério de aceite
Aba de notícias aberta

## Armadilha
Não resumir notícias de memória: ler a página

## Subagentes
- [[QueryBuilder]] — 1 · Entender
- [[Navigator]] — 2 · Montar
- [[ContentGuard]] — 3 · Conferir
