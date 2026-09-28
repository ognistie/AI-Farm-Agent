---
tipo: tarefa-referencia
agente: FILE
contexto: "search / análise"
keywords: encontrar arquivos grandes mostre maiores pasta downloads
tags: [referencia, file]
cssclasses: [ref-note]
---
# Encontrar arquivos grandes

> [!route] Pedido exemplo
> mostre os 10 maiores arquivos da pasta downloads

**Agente:** [[File Agent]] · **Contexto:** search / análise

## Caminho
1. os.walk + sort por tamanho
2. top 10 legível (MB)

## Forma alternativa
—

## Critério de aceite
Lista dos maiores

## Armadilha
Não apagar nada

## Subagentes
- [[PathResolver]] — 1 · Entender
- [[OperationPlanner]] — 2 · Montar
- [[SafetyAuditor]] — 3 · Conferir
