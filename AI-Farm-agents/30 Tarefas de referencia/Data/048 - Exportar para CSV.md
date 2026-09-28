---
tipo: tarefa-referencia
agente: DATA
contexto: "exportação"
keywords: exportar csv gere tambem planilha vendas
tags: [referencia, data]
cssclasses: [ref-note]
---
# Exportar para CSV

> [!route] Pedido exemplo
> gere também um csv da planilha de vendas

**Agente:** [[Data Agent]] · **Contexto:** exportação

## Caminho
1. Salvar .xlsx e .csv (sep ;, utf-8-sig)

## Forma alternativa
—

## Critério de aceite
Dois arquivos gerados

## Armadilha
Excel BR abre CSV com ;

## Subagentes
- [[SchemaDesigner]] — 1 · Entender
- [[FormulaChartDesigner]] — 2 · Montar
- [[SheetReviewer]] — 3 · Conferir
