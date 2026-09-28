---
tipo: tarefa-referencia
agente: DATA
contexto: "lista"
keywords: lista compras precos crie total estimado
tags: [referencia, data]
cssclasses: [ref-note]
---
# Lista de compras com preços

> [!route] Pedido exemplo
> crie uma lista de compras com total estimado

**Agente:** [[Data Agent]] · **Contexto:** lista

## Caminho
1. Item, Qtd, Preço unit., Total (=Qtd*Preço) + SUM

## Forma alternativa
Bloco de Notas se não precisar de valores

## Critério de aceite
Total por fórmula

## Armadilha
—

## Subagentes
- [[SchemaDesigner]] — 1 · Entender
- [[FormulaChartDesigner]] — 2 · Montar
- [[SheetReviewer]] — 3 · Conferir
