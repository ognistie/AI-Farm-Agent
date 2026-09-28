---
tipo: tarefa-referencia
agente: DATA
contexto: "vendas / KPI"
keywords: metas vendas crie planilha realizado mes
tags: [referencia, data]
cssclasses: [ref-note]
---
# Metas de vendas

> [!route] Pedido exemplo
> crie uma planilha de metas x realizado por mês

**Agente:** [[Data Agent]] · **Contexto:** vendas / KPI

## Caminho
1. Meta, Realizado, % atingido (=Real/Meta)
2. formatação condicional

## Forma alternativa
Gráfico de colunas meta x real

## Critério de aceite
% calculado por fórmula

## Armadilha
Divisão por zero quando meta vazia

## Subagentes
- [[SchemaDesigner]] — 1 · Entender
- [[FormulaChartDesigner]] — 2 · Montar
- [[SheetReviewer]] — 3 · Conferir
