---
tipo: tarefa-referencia
agente: WEB
contexto: "Pergunta com resposta na SERP"
keywords: previsao tempo qual amanha curitiba
tags: [referencia, web]
cssclasses: [ref-note]
---
# Previsão do tempo

> [!route] Pedido exemplo
> qual a previsão do tempo para amanhã em curitiba

**Agente:** [[Web Agent]] · **Contexto:** Pergunta com resposta na SERP

## Caminho
1. Query 'previsão do tempo amanhã curitiba'
2. web_goto
3. web_read (card de clima)

## Forma alternativa
Site climatempo.com.br

## Critério de aceite
Temperatura e condição lidas

## Armadilha
Não responder sem ler a página

## Subagentes
- [[QueryBuilder]] — 1 · Entender
- [[Navigator]] — 2 · Montar
- [[ContentGuard]] — 3 · Conferir
