---
tipo: tarefa-referencia
agente: DATA
contexto: "vendas"
keywords: controle vendas planilha trimestre total vendedor
tags: [referencia, data]
cssclasses: [ref-note]
---
# Controle de vendas

> [!route] Pedido exemplo
> planilha de vendas do trimestre com total por vendedor

**Agente:** [[Data Agent]] · **Contexto:** vendas

## Caminho
1. SchemaDesigner: vendas
2. SUMIF por vendedor
3. BarChart

## Forma alternativa
Tabela dinâmica documentada

## Critério de aceite
Totais por vendedor corretos

## Armadilha
Nomes com grafias diferentes

## Subagentes
- [[SchemaDesigner]] — 1 · Entender
- [[FormulaChartDesigner]] — 2 · Montar
- [[SheetReviewer]] — 3 · Conferir
