---
tipo: tarefa-referencia
agente: DATA
contexto: "financeiro"
keywords: controle notas fiscais planilha emitidas
tags: [referencia, data]
cssclasses: [ref-note]
---
# Controle de notas fiscais

> [!route] Pedido exemplo
> planilha de notas fiscais emitidas

**Agente:** [[Data Agent]] · **Contexto:** financeiro

## Caminho
1. Número, Data, Cliente, Valor, Imposto + totais mensais

## Forma alternativa
—

## Critério de aceite
Totais por mês

## Armadilha
Dados fictícios

## Subagentes
- [[SchemaDesigner]] — 1 · Entender
- [[FormulaChartDesigner]] — 2 · Montar
- [[SheetReviewer]] — 3 · Conferir
