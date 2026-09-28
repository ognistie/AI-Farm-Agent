---
tipo: tarefa-referencia
agente: FILE
contexto: "análise"
keywords: contar arquivos tipo quantos cada tenho documentos
tags: [referencia, file]
cssclasses: [ref-note]
---
# Contar arquivos por tipo

> [!route] Pedido exemplo
> quantos arquivos de cada tipo tenho em documentos

**Agente:** [[File Agent]] · **Contexto:** análise

## Caminho
1. Counter por extensão
2. tabela ordenada

## Forma alternativa
DATA gera planilha do resumo

## Critério de aceite
Contagem exibida

## Armadilha
—

## Subagentes
- [[PathResolver]] — 1 · Entender
- [[OperationPlanner]] — 2 · Montar
- [[SafetyAuditor]] — 3 · Conferir
