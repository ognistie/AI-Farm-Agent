---
tipo: tarefa-referencia
agente: FILE
contexto: "undo"
keywords: desfazer organizacao desfaca voce fez pasta downloads
tags: [referencia, file]
cssclasses: [ref-note]
---
# Desfazer organização

> [!route] Pedido exemplo
> desfaça a organização que você fez na pasta downloads

**Agente:** [[File Agent]] · **Contexto:** undo

## Caminho
1. Ler organizacao_log.txt
2. mover de volta

## Forma alternativa
Se não houver log: explicar que não é possível

## Critério de aceite
Arquivos de volta

## Armadilha
Sem log não há desfazer seguro

## Subagentes
- [[PathResolver]] — 1 · Entender
- [[OperationPlanner]] — 2 · Montar
- [[SafetyAuditor]] — 3 · Conferir
