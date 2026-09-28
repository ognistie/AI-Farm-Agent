---
tipo: tarefa-referencia
agente: WEB
contexto: "Conteúdo em vídeo"
keywords: pesquisa videos youtube procure receita pao caseiro
tags: [referencia, web]
cssclasses: [ref-note]
---
# Pesquisa de vídeos no YouTube

> [!route] Pedido exemplo
> procure vídeos de receita de pão caseiro no youtube

**Agente:** [[Web Agent]] · **Contexto:** Conteúdo em vídeo

## Caminho
1. web_goto youtube.com/results?search_query=receita+de+pao+caseiro
2. wait 2

## Forma alternativa
Google com &tbm=vid

## Critério de aceite
Lista de vídeos do YouTube aberta

## Armadilha
Não digitar no campo de busca do YouTube

## Subagentes
- [[QueryBuilder]] — 1 · Entender
- [[Navigator]] — 2 · Montar
- [[ContentGuard]] — 3 · Conferir
