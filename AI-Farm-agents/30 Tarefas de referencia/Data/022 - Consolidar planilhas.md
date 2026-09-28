---
tipo: tarefa-referencia
agente: DATA
contexto: "consolidação"
keywords: consolidar planilhas junte pasta relatorios
tags: [referencia, data]
cssclasses: [ref-note]
---
# Consolidar planilhas

> [!route] Pedido exemplo
> junte as planilhas da pasta relatórios em uma só

**Agente:** [[Data Agent]] · **Contexto:** consolidação

## Caminho
1. Listar .xlsx
2. pandas concat
3. aba por origem opcional

## Forma alternativa
CODE cria script reutilizável

## Critério de aceite
Planilha única com todas as linhas

## Armadilha
Colunas com nomes diferentes

## Subagentes
- [[SchemaDesigner]] — 1 · Entender
- [[FormulaChartDesigner]] — 2 · Montar
- [[SheetReviewer]] — 3 · Conferir
