---
tipo: tarefa-referencia
agente: DATA
contexto: "limpeza"
keywords: limpar dados duplicados remova linhas duplicadas planilha clientes xlsx
tags: [referencia, data]
cssclasses: [ref-note]
---
# Limpar dados duplicados

> [!route] Pedido exemplo
> remova linhas duplicadas da planilha clientes.xlsx

**Agente:** [[Data Agent]] · **Contexto:** limpeza

## Caminho
1. pandas drop_duplicates → salvar como clientes_limpo.xlsx (não sobrescrever)

## Forma alternativa
Destacar duplicados sem remover

## Critério de aceite
Arquivo novo sem duplicados

## Armadilha
Nunca sobrescrever o original

## Subagentes
- [[SchemaDesigner]] — 1 · Entender
- [[FormulaChartDesigner]] — 2 · Montar
- [[SheetReviewer]] — 3 · Conferir
