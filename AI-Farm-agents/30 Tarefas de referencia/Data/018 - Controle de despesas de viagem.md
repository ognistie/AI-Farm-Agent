---
tipo: tarefa-referencia
agente: DATA
contexto: "rateio"
keywords: controle despesas viagem planilha grupo
tags: [referencia, data]
cssclasses: [ref-note]
---
# Controle de despesas de viagem

> [!route] Pedido exemplo
> planilha de despesas de uma viagem em grupo

**Agente:** [[Data Agent]] · **Contexto:** rateio

## Caminho
1. Despesa, Pagador, Valor, Rateio por pessoa, Saldo de cada um

## Forma alternativa
Aba 'quem deve a quem'

## Critério de aceite
Saldos zeram no total

## Armadilha
Arredondamento de centavos

## Subagentes
- [[SchemaDesigner]] — 1 · Entender
- [[FormulaChartDesigner]] — 2 · Montar
- [[SheetReviewer]] — 3 · Conferir
