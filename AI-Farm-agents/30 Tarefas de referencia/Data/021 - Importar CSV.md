---
tipo: tarefa-referencia
agente: DATA
contexto: "conversão"
keywords: importar csv transforme arquivo vendas planilha formatada
tags: [referencia, data]
cssclasses: [ref-note]
---
# Importar CSV

> [!route] Pedido exemplo
> transforme o arquivo vendas.csv em uma planilha formatada

**Agente:** [[Data Agent]] · **Contexto:** conversão

## Caminho
1. pandas.read_csv → openpyxl com formatação e filtros

## Forma alternativa
Abrir CSV direto no Excel (DESKTOP)

## Critério de aceite
Planilha formatada criada

## Armadilha
Separador ; vs , e encoding

## Subagentes
- [[SchemaDesigner]] — 1 · Entender
- [[FormulaChartDesigner]] — 2 · Montar
- [[SheetReviewer]] — 3 · Conferir
