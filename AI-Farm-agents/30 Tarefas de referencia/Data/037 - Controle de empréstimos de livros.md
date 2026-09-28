---
tipo: tarefa-referencia
agente: DATA
contexto: "cadastro"
keywords: controle emprestimos livros planilha biblioteca
tags: [referencia, data]
cssclasses: [ref-note]
---
# Controle de empréstimos de livros

> [!route] Pedido exemplo
> planilha de empréstimos da biblioteca

**Agente:** [[Data Agent]] · **Contexto:** cadastro

## Caminho
1. Livro, Leitor, Retirada, Devolução prevista, Atraso (=HOJE()-prevista)

## Forma alternativa
—

## Critério de aceite
Atrasos destacados

## Armadilha
TODAY() recalcula ao abrir

## Subagentes
- [[SchemaDesigner]] — 1 · Entender
- [[FormulaChartDesigner]] — 2 · Montar
- [[SheetReviewer]] — 3 · Conferir
