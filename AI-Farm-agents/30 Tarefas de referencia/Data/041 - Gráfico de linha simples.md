---
tipo: tarefa-referencia
agente: DATA
contexto: "chart"
keywords: grafico linha simples crie vendas ultimos meses
tags: [referencia, data]
cssclasses: [ref-note]
---
# Gráfico de linha simples

> [!route] Pedido exemplo
> crie um gráfico de linha com as vendas dos últimos 12 meses

**Agente:** [[Data Agent]] · **Contexto:** chart

## Caminho
1. Dados de exemplo 12 meses + LineChart

## Forma alternativa
BarChart

## Critério de aceite
Gráfico correto

## Armadilha
Eixo X com meses em ordem

## Subagentes
- [[SchemaDesigner]] — 1 · Entender
- [[FormulaChartDesigner]] — 2 · Montar
- [[SheetReviewer]] — 3 · Conferir
