---
tipo: tarefa-referencia
agente: WEB
contexto: "Compra — só pesquisa"
keywords: comparar precos pesquise preco iphone lojas diferentes
tags: [referencia, web]
cssclasses: [ref-note]
---
# Comparar preços

> [!route] Pedido exemplo
> pesquise o preço de um iphone 16 em lojas diferentes

**Agente:** [[Web Agent]] · **Contexto:** Compra — só pesquisa

## Caminho
1. Query 'preço iphone 16' &tbm=shop
2. web_goto
3. web_read

## Forma alternativa
Sites de comparação (zoom, buscapé)

## Critério de aceite
Lista de preços por loja

## Armadilha
Nunca finalizar compra nem inserir cartão

## Subagentes
- [[QueryBuilder]] — 1 · Entender
- [[Navigator]] — 2 · Montar
- [[ContentGuard]] — 3 · Conferir
