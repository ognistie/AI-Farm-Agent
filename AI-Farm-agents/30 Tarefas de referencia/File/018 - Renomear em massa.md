---
tipo: tarefa-referencia
agente: FILE
contexto: "rename"
keywords: renomear massa renomeie fotos pasta viagem 001 002
tags: [referencia, file]
cssclasses: [ref-note]
---
# Renomear em massa

> [!route] Pedido exemplo
> renomeie as fotos da pasta viagem para viagem_001, viagem_002

**Agente:** [[File Agent]] · **Contexto:** rename

## Caminho
1. Ordenar por data
2. renomear com padrão
3. evitar colisão

## Forma alternativa
Simular primeiro e mostrar prévia

## Critério de aceite
Nomes sequenciais

## Armadilha
Extensões preservadas

## Subagentes
- [[PathResolver]] — 1 · Entender
- [[OperationPlanner]] — 2 · Montar
- [[SafetyAuditor]] — 3 · Conferir
