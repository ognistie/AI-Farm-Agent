---
tipo: tarefa-referencia
agente: FILE
contexto: "create"
keywords: criar estrutura pastas crie clientes contratos notas dentro documentos empresa
tags: [referencia, file]
cssclasses: [ref-note]
---
# Criar estrutura de pastas

> [!route] Pedido exemplo
> crie as pastas clientes, contratos e notas dentro de documentos/empresa

**Agente:** [[File Agent]] · **Contexto:** create

## Caminho
1. makedirs(exist_ok=True) para cada
2. abrir Explorer

## Forma alternativa
—

## Critério de aceite
Pastas criadas

## Armadilha
Idempotente

## Subagentes
- [[PathResolver]] — 1 · Entender
- [[OperationPlanner]] — 2 · Montar
- [[SafetyAuditor]] — 3 · Conferir
