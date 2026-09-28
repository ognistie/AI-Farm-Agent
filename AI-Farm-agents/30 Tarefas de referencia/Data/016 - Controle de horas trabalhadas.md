---
tipo: tarefa-referencia
agente: DATA
contexto: "horas"
keywords: controle horas trabalhadas planilha banco
tags: [referencia, data]
cssclasses: [ref-note]
---
# Controle de horas trabalhadas

> [!route] Pedido exemplo
> planilha de banco de horas

**Agente:** [[Data Agent]] · **Contexto:** horas

## Caminho
1. Entrada, Saída, Intervalo, Total (=Saída-Entrada-Intervalo) formato [h]:mm

## Forma alternativa
Resumo semanal

## Critério de aceite
Totais em horas corretos

## Armadilha
Formato [h]:mm para passar de 24h

## Subagentes
- [[SchemaDesigner]] — 1 · Entender
- [[FormulaChartDesigner]] — 2 · Montar
- [[SheetReviewer]] — 3 · Conferir
