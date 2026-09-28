---
tipo: tarefa-referencia
agente: FILE
contexto: "erro esperado"
keywords: arquivos uso mova planilha aberta outra pasta
tags: [referencia, file]
cssclasses: [ref-note]
---
# Arquivos em uso

> [!route] Pedido exemplo
> mova a planilha aberta para outra pasta

**Agente:** [[File Agent]] · **Contexto:** erro esperado

## Caminho
1. Tentar move → PermissionError → reportar arquivo em uso

## Forma alternativa
Pedir para fechar o arquivo

## Critério de aceite
Erro claro

## Armadilha
Não forçar

## Subagentes
- [[PathResolver]] — 1 · Entender
- [[OperationPlanner]] — 2 · Montar
- [[SafetyAuditor]] — 3 · Conferir
