---
tipo: tarefa-referencia
agente: FILE
contexto: "move"
keywords: mover arquivos palavra nome mova tudo tem nota fiscal pasta
tags: [referencia, file]
cssclasses: [ref-note]
---
# Mover arquivos por palavra no nome

> [!route] Pedido exemplo
> mova tudo que tem 'nota fiscal' no nome para a pasta fiscal

**Agente:** [[File Agent]] · **Contexto:** move

## Caminho
1. Filtro por nome (sem acento/case)
2. move
3. resumo

## Forma alternativa
—

## Critério de aceite
Arquivos movidos

## Armadilha
Falsos positivos: listar antes se muitos

## Subagentes
- [[PathResolver]] — 1 · Entender
- [[OperationPlanner]] — 2 · Montar
- [[SafetyAuditor]] — 3 · Conferir
