---
tipo: tarefa-referencia
agente: FILE
contexto: "search"
keywords: encontrar extensao liste todas planilhas excel pasta documentos
tags: [referencia, file]
cssclasses: [ref-note]
---
# Encontrar por extensão

> [!route] Pedido exemplo
> liste todas as planilhas excel da pasta documentos

**Agente:** [[File Agent]] · **Contexto:** search

## Caminho
1. glob **/*.xlsx em Documents
2. lista com tamanho e data

## Forma alternativa
—

## Critério de aceite
Lista gerada

## Armadilha
—

## Subagentes
- [[PathResolver]] — 1 · Entender
- [[OperationPlanner]] — 2 · Montar
- [[SafetyAuditor]] — 3 · Conferir
