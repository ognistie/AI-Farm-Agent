---
tipo: tarefa-referencia
agente: DATA
contexto: "gastos + chart"
keywords: gastos grafico planilha categoria pizza
tags: [referencia, data]
cssclasses: [ref-note]
---
# Gastos com gráfico

> [!route] Pedido exemplo
> planilha de gastos por categoria com gráfico de pizza

**Agente:** [[Data Agent]] · **Contexto:** gastos + chart

## Caminho
1. Tabela + resumo por categoria (SUMIF) + PieChart

## Forma alternativa
BarChart se muitas categorias

## Critério de aceite
Gráfico reflete o resumo

## Armadilha
Gráfico apontando para a faixa errada

## Subagentes
- [[SchemaDesigner]] — 1 · Entender
- [[FormulaChartDesigner]] — 2 · Montar
- [[SheetReviewer]] — 3 · Conferir
