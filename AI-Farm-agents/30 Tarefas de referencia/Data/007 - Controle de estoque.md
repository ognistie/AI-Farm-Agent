---
tipo: tarefa-referencia
agente: DATA
contexto: "inventario"
keywords: controle estoque planilha alerta minimo
tags: [referencia, data]
cssclasses: [ref-note]
---
# Controle de estoque

> [!route] Pedido exemplo
> planilha de controle de estoque com alerta de mínimo

**Agente:** [[Data Agent]] · **Contexto:** inventario

## Caminho
1. Código, Produto, Qtd, Mínimo, Status (=SE(Qtd<Mínimo;"Repor";"OK"))

## Forma alternativa
Formatação condicional vermelha

## Critério de aceite
Status atualiza sozinho

## Armadilha
Fórmula em PT vs EN: openpyxl usa nomes em inglês (IF)

## Subagentes
- [[SchemaDesigner]] — 1 · Entender
- [[FormulaChartDesigner]] — 2 · Montar
- [[SheetReviewer]] — 3 · Conferir
