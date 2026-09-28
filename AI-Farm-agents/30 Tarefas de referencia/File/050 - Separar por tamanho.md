---
tipo: tarefa-referencia
agente: FILE
contexto: "organize"
keywords: separar tamanho separe videos maiores 1gb pasta
tags: [referencia, file]
cssclasses: [ref-note]
---
# Separar por tamanho

> [!route] Pedido exemplo
> separe os vídeos maiores que 1gb em uma pasta

**Agente:** [[File Agent]] · **Contexto:** organize

## Caminho
1. Filtrar vídeos > 1GB
2. mover para 'Videos grandes'

## Forma alternativa
Só listar

## Critério de aceite
Vídeos grandes separados

## Armadilha
—

## Subagentes
- [[PathResolver]] — 1 · Entender
- [[OperationPlanner]] — 2 · Montar
- [[SafetyAuditor]] — 3 · Conferir
