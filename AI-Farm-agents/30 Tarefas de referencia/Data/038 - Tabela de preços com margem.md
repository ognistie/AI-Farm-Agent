---
tipo: tarefa-referencia
agente: DATA
contexto: "precificação"
keywords: tabela precos margem crie custo lucro
tags: [referencia, data]
cssclasses: [ref-note]
---
# Tabela de preços com margem

> [!route] Pedido exemplo
> crie tabela de preços com custo e margem de lucro

**Agente:** [[Data Agent]] · **Contexto:** precificação

## Caminho
1. Custo, Margem %, Preço (=Custo*(1+Margem))

## Forma alternativa
Markup vs margem explicado

## Critério de aceite
Preços por fórmula

## Armadilha
Margem ≠ markup

## Subagentes
- [[SchemaDesigner]] — 1 · Entender
- [[FormulaChartDesigner]] — 2 · Montar
- [[SheetReviewer]] — 3 · Conferir
