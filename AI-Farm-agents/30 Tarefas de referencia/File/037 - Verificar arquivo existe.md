---
tipo: tarefa-referencia
agente: FILE
contexto: "check"
keywords: verificar arquivo existe orcamento xlsx esta area trabalho
tags: [referencia, file]
cssclasses: [ref-note]
---
# Verificar arquivo existe

> [!route] Pedido exemplo
> o arquivo orcamento.xlsx está na área de trabalho?

**Agente:** [[File Agent]] · **Contexto:** check

## Caminho
1. os.path.exists Desktop/orcamento.xlsx → sim/não + caminho

## Forma alternativa
Buscar em outras pastas se não estiver

## Critério de aceite
Resposta objetiva

## Armadilha
—

## Subagentes
- [[PathResolver]] — 1 · Entender
- [[OperationPlanner]] — 2 · Montar
- [[SafetyAuditor]] — 3 · Conferir
