---
tipo: tarefa-referencia
agente: DATA
contexto: "entrada do usuário"
keywords: planilha partir texto transforme essa lista nomes idades
tags: [referencia, data]
cssclasses: [ref-note]
---
# Planilha a partir de texto

> [!route] Pedido exemplo
> transforme essa lista de nomes e idades em planilha

**Agente:** [[Data Agent]] · **Contexto:** entrada do usuário

## Caminho
1. Parse do texto do pedido → linhas
2. planilha

## Forma alternativa
Pedir o texto se não veio

## Critério de aceite
Todas as linhas presentes

## Armadilha
Não inventar linhas

## Subagentes
- [[SchemaDesigner]] — 1 · Entender
- [[FormulaChartDesigner]] — 2 · Montar
- [[SheetReviewer]] — 3 · Conferir
