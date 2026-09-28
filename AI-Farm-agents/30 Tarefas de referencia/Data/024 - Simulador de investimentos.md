---
tipo: tarefa-referencia
agente: DATA
contexto: "financeiro"
keywords: simulador investimentos planilha juros compostos aportes mensais
tags: [referencia, data]
cssclasses: [ref-note]
---
# Simulador de investimentos

> [!route] Pedido exemplo
> planilha de juros compostos com aportes mensais

**Agente:** [[Data Agent]] · **Contexto:** financeiro

## Caminho
1. Mês, Aporte, Juros, Saldo (=anterior*(1+taxa)+aporte) + LineChart

## Forma alternativa
—

## Critério de aceite
Evolução correta

## Armadilha
Não é recomendação de investimento: avisar

## Subagentes
- [[SchemaDesigner]] — 1 · Entender
- [[FormulaChartDesigner]] — 2 · Montar
- [[SheetReviewer]] — 3 · Conferir
