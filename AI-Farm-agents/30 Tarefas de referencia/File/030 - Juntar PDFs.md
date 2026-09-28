---
tipo: tarefa-referencia
agente: FILE
contexto: "merge"
keywords: juntar pdfs junte pasta contratos
tags: [referencia, file]
cssclasses: [ref-note]
---
# Juntar PDFs

> [!route] Pedido exemplo
> junte os pdfs da pasta contratos em um só

**Agente:** [[File Agent]] · **Contexto:** merge

## Caminho
1. pypdf PdfWriter em ordem alfabética → contratos_unidos.pdf

## Forma alternativa
—

## Critério de aceite
PDF único gerado

## Armadilha
Ordem: confirmar se importa

## Subagentes
- [[PathResolver]] — 1 · Entender
- [[OperationPlanner]] — 2 · Montar
- [[SafetyAuditor]] — 3 · Conferir
