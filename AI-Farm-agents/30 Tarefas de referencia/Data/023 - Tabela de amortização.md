---
tipo: tarefa-referencia
agente: DATA
contexto: "financeiro"
keywords: tabela amortizacao crie simulacao financiamento price
tags: [referencia, data]
cssclasses: [ref-note]
---
# Tabela de amortização

> [!route] Pedido exemplo
> crie uma simulação de financiamento price

**Agente:** [[Data Agent]] · **Contexto:** financeiro

## Caminho
1. Parcela (=PMT), Juros, Amortização, Saldo por mês

## Forma alternativa
Tabela SAC em outra aba

## Critério de aceite
Saldo zera na última parcela

## Armadilha
Taxa mensal vs anual

## Subagentes
- [[SchemaDesigner]] — 1 · Entender
- [[FormulaChartDesigner]] — 2 · Montar
- [[SheetReviewer]] — 3 · Conferir
