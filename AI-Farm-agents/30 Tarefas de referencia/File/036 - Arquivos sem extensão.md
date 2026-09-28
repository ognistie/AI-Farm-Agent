---
tipo: tarefa-referencia
agente: FILE
contexto: "search"
keywords: arquivos sem extensao encontre pasta downloads
tags: [referencia, file]
cssclasses: [ref-note]
---
# Arquivos sem extensão

> [!route] Pedido exemplo
> encontre arquivos sem extensão na pasta downloads

**Agente:** [[File Agent]] · **Contexto:** search

## Caminho
1. Filtrar Path.suffix == ''
2. listar

## Forma alternativa
—

## Critério de aceite
Lista exibida

## Armadilha
—

## Subagentes
- [[PathResolver]] — 1 · Entender
- [[OperationPlanner]] — 2 · Montar
- [[SafetyAuditor]] — 3 · Conferir
