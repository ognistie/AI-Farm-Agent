---
tipo: tarefa-referencia
agente: FILE
contexto: "create"
keywords: criar pastas mes crie pasta cada 2026 documentos financeiro
tags: [referencia, file]
cssclasses: [ref-note]
---
# Criar pastas por mês

> [!route] Pedido exemplo
> crie uma pasta para cada mês de 2026 em documentos/financeiro

**Agente:** [[File Agent]] · **Contexto:** create

## Caminho
1. 12 pastas '01 - Janeiro'...

## Forma alternativa
—

## Critério de aceite
12 pastas

## Armadilha
Ordem com prefixo numérico

## Subagentes
- [[PathResolver]] — 1 · Entender
- [[OperationPlanner]] — 2 · Montar
- [[SafetyAuditor]] — 3 · Conferir
