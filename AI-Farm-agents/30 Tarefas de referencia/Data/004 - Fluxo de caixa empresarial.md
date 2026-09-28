---
tipo: tarefa-referencia
agente: DATA
contexto: "fluxo de caixa"
keywords: fluxo caixa empresarial crie planilha empresa
tags: [referencia, data]
cssclasses: [ref-note]
---
# Fluxo de caixa empresarial

> [!route] Pedido exemplo
> crie uma planilha de fluxo de caixa para uma empresa

**Agente:** [[Data Agent]] · **Contexto:** fluxo de caixa

## Caminho
1. Abas Lançamentos + Resumo
2. entradas, saídas, saldo acumulado
3. formatação R$

## Forma alternativa
DRE simplificada junto

## Critério de aceite
Saldo = anterior + entradas − saídas

## Armadilha
Não misturar competência e caixa sem avisar

## Subagentes
- [[SchemaDesigner]] — 1 · Entender
- [[FormulaChartDesigner]] — 2 · Montar
- [[SheetReviewer]] — 3 · Conferir
