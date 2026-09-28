---
tipo: tarefa-referencia
agente: FILE
contexto: "rename"
keywords: renomear trocando texto troque rascunho final nomes arquivos pasta relatorios
tags: [referencia, file]
cssclasses: [ref-note]
---
# Renomear trocando texto

> [!route] Pedido exemplo
> troque 'rascunho' por 'final' nos nomes dos arquivos da pasta relatorios

**Agente:** [[File Agent]] · **Contexto:** rename

## Caminho
1. Filtrar nomes com 'rascunho'
2. replace
3. colisão

## Forma alternativa
—

## Critério de aceite
Nomes atualizados

## Armadilha
Case sensitive

## Subagentes
- [[PathResolver]] — 1 · Entender
- [[OperationPlanner]] — 2 · Montar
- [[SafetyAuditor]] — 3 · Conferir
