---
tipo: tarefa-referencia
agente: DATA
contexto: "análise"
keywords: tabela dinamica faca resumo regiao produto vendas
tags: [referencia, data]
cssclasses: [ref-note]
---
# Tabela dinâmica

> [!route] Pedido exemplo
> faça um resumo por região e produto das vendas

**Agente:** [[Data Agent]] · **Contexto:** análise

## Caminho
1. pandas pivot_table → aba Resumo (openpyxl não cria pivot nativa)

## Forma alternativa
Instruções para criar a tabela dinâmica no Excel

## Critério de aceite
Resumo correto

## Armadilha
Explicar que é um resumo estático

## Subagentes
- [[SchemaDesigner]] — 1 · Entender
- [[FormulaChartDesigner]] — 2 · Montar
- [[SheetReviewer]] — 3 · Conferir
