---
tipo: tarefa-referencia
agente: FILE
contexto: "organize + relatório"
keywords: log operacoes organize pasta mostre relatorio foi feito
tags: [referencia, file]
cssclasses: [ref-note]
---
# Log de operações

> [!route] Pedido exemplo
> organize a pasta e me mostre um relatório do que foi feito

**Agente:** [[File Agent]] · **Contexto:** organize + relatório

## Caminho
1. Mover
2. gerar organizacao_log.txt com origem → destino

## Forma alternativa
Só print no resultado

## Critério de aceite
Log gerado

## Armadilha
—

## Subagentes
- [[PathResolver]] — 1 · Entender
- [[OperationPlanner]] — 2 · Montar
- [[SafetyAuditor]] — 3 · Conferir
