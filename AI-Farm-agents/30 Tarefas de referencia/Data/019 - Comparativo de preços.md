---
tipo: tarefa-referencia
agente: DATA
contexto: "comparativo"
keywords: comparativo precos planilha comparando fornecedores
tags: [referencia, data]
cssclasses: [ref-note]
---
# Comparativo de preços

> [!route] Pedido exemplo
> planilha comparando preços de 3 fornecedores

**Agente:** [[Data Agent]] · **Contexto:** comparativo

## Caminho
1. Produto x Fornecedor + MIN + fornecedor mais barato (INDEX/MATCH)

## Forma alternativa
Destaque condicional do menor

## Critério de aceite
Menor preço identificado

## Armadilha
Empates

## Subagentes
- [[SchemaDesigner]] — 1 · Entender
- [[FormulaChartDesigner]] — 2 · Montar
- [[SheetReviewer]] — 3 · Conferir
