---
tipo: tarefa-referencia
agente: WEB
contexto: "Busca dentro de loja"
keywords: buscar produto marketplace procure fone bluetooth mercado livre
tags: [referencia, web]
cssclasses: [ref-note]
---
# Buscar produto em marketplace

> [!route] Pedido exemplo
> procure fone bluetooth no mercado livre

**Agente:** [[Web Agent]] · **Contexto:** Busca dentro de loja

## Caminho
1. web_goto lista.mercadolivre.com.br/fone-bluetooth
2. wait 2

## Forma alternativa
Busca Google com site:mercadolivre.com.br

## Critério de aceite
Lista de produtos aberta

## Armadilha
Não adicionar ao carrinho sem pedido explícito

## Subagentes
- [[QueryBuilder]] — 1 · Entender
- [[Navigator]] — 2 · Montar
- [[ContentGuard]] — 3 · Conferir
