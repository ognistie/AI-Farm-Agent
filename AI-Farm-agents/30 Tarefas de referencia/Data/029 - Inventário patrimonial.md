---
tipo: tarefa-referencia
agente: DATA
contexto: "inventario / contábil"
keywords: inventario patrimonial planilha patrimonio empresa depreciacao
tags: [referencia, data]
cssclasses: [ref-note]
---
# Inventário patrimonial

> [!route] Pedido exemplo
> planilha de patrimônio da empresa com depreciação

**Agente:** [[Data Agent]] · **Contexto:** inventario / contábil

## Caminho
1. Bem, Aquisição, Valor, Vida útil, Depreciação anual (=Valor/Vida)

## Forma alternativa
Depreciação mensal

## Critério de aceite
Valores por fórmula

## Armadilha
Regra contábil: avisar que é simplificada

## Subagentes
- [[SchemaDesigner]] — 1 · Entender
- [[FormulaChartDesigner]] — 2 · Montar
- [[SheetReviewer]] — 3 · Conferir
