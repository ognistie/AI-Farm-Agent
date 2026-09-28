---
tipo: tarefa-referencia
agente: FILE
contexto: "organize"
keywords: organizar downloads tipo organize pasta arquivo
tags: [referencia, file]
cssclasses: [ref-note]
---
# Organizar Downloads por tipo

> [!route] Pedido exemplo
> organize a pasta downloads por tipo de arquivo

**Agente:** [[File Agent]] · **Contexto:** organize

## Caminho
1. PathResolver: ~/Downloads
2. OperationPlanner: organize/executar
3. move por categoria
4. SafetyAuditor
5. resumo

## Forma alternativa
Só listar o plano (simulação)

## Critério de aceite
Arquivos movidos para subpastas

## Armadilha
Não mexer em subpastas existentes

## Subagentes
- [[PathResolver]] — 1 · Entender
- [[OperationPlanner]] — 2 · Montar
- [[SafetyAuditor]] — 3 · Conferir
