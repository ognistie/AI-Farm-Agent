---
tipo: tarefa-referencia
agente: DATA
contexto: "financeiro / RH"
keywords: folha pagamento simplificada crie descontos
tags: [referencia, data]
cssclasses: [ref-note]
---
# Folha de pagamento simplificada

> [!route] Pedido exemplo
> crie uma folha de pagamento com descontos

**Agente:** [[Data Agent]] · **Contexto:** financeiro / RH

## Caminho
1. Salário, INSS, IRRF (tabelas de exemplo), Líquido

## Forma alternativa
Avisar que alíquotas mudam por ano

## Critério de aceite
Líquido por fórmula

## Armadilha
Não afirmar alíquota oficial sem fonte

## Subagentes
- [[SchemaDesigner]] — 1 · Entender
- [[FormulaChartDesigner]] — 2 · Montar
- [[SheetReviewer]] — 3 · Conferir
