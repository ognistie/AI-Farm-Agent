---
tipo: tarefa-referencia
agente: FILE
contexto: "delete confirmado"
keywords: remover duplicados confirmacao apague fotos duplicadas pode apagar
tags: [referencia, file]
cssclasses: [ref-note]
---
# Remover duplicados com confirmação

> [!route] Pedido exemplo
> apague as fotos duplicadas, pode apagar

**Agente:** [[File Agent]] · **Contexto:** delete confirmado

## Caminho
1. OperationPlanner: delete/executar (confirmado)
2. manter 1 por grupo
3. mover para Lixeira (send2trash)

## Forma alternativa
Mover para pasta 'Duplicados'

## Critério de aceite
Duplicados removidos, 1 cópia mantida

## Armadilha
Preferir lixeira a exclusão definitiva

## Subagentes
- [[PathResolver]] — 1 · Entender
- [[OperationPlanner]] — 2 · Montar
- [[SafetyAuditor]] — 3 · Conferir
