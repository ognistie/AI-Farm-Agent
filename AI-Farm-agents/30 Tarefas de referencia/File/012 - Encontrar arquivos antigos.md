---
tipo: tarefa-referencia
agente: FILE
contexto: "search / idade"
keywords: encontrar arquivos antigos liste pasta downloads mais meses
tags: [referencia, file]
cssclasses: [ref-note]
---
# Encontrar arquivos antigos

> [!route] Pedido exemplo
> liste arquivos da pasta downloads com mais de 6 meses

**Agente:** [[File Agent]] · **Contexto:** search / idade

## Caminho
1. mtime < hoje-180d
2. lista

## Forma alternativa
Oferecer mover para 'Antigos'

## Critério de aceite
Lista gerada

## Armadilha
Só listar

## Subagentes
- [[PathResolver]] — 1 · Entender
- [[OperationPlanner]] — 2 · Montar
- [[SafetyAuditor]] — 3 · Conferir
