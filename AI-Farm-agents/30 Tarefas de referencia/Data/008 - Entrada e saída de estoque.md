---
tipo: tarefa-referencia
agente: DATA
contexto: "inventario"
keywords: entrada saida estoque crie planilha movimentacao
tags: [referencia, data]
cssclasses: [ref-note]
---
# Entrada e saída de estoque

> [!route] Pedido exemplo
> crie planilha de movimentação de estoque

**Agente:** [[Data Agent]] · **Contexto:** inventario

## Caminho
1. Aba Movimentos (entrada/saída) + aba Saldo com SUMIFS

## Forma alternativa
Uma aba só com saldo manual

## Critério de aceite
Saldo por produto correto

## Armadilha
Sinal da saída (negativo)

## Subagentes
- [[SchemaDesigner]] — 1 · Entender
- [[FormulaChartDesigner]] — 2 · Montar
- [[SheetReviewer]] — 3 · Conferir
