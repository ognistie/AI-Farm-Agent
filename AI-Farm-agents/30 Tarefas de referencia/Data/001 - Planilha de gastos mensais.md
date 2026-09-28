---
tipo: tarefa-referencia
agente: DATA
contexto: "gastos"
keywords: planilha gastos mensais crie mes
tags: [referencia, data]
cssclasses: [ref-note]
---
# Planilha de gastos mensais

> [!route] Pedido exemplo
> crie uma planilha de gastos do mês

**Agente:** [[Data Agent]] · **Contexto:** gastos

## Caminho
1. SchemaDesigner: gastos (Data, Categoria, Descrição, Valor, Forma)
2. FormulaChart: SUM
3. SheetReviewer
4. abrir Excel

## Forma alternativa
Aba por mês se pedir o ano

## Critério de aceite
Planilha com total por fórmula

## Armadilha
Formato monetário R$

## Subagentes
- [[SchemaDesigner]] — 1 · Entender
- [[FormulaChartDesigner]] — 2 · Montar
- [[SheetReviewer]] — 3 · Conferir
