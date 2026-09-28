---
tipo: tarefa-referencia
agente: FILE
contexto: "list"
keywords: listar conteudo pasta liste arquivos documentos
tags: [referencia, file]
cssclasses: [ref-note]
---
# Listar conteúdo de pasta

> [!route] Pedido exemplo
> liste os arquivos da pasta documentos

**Agente:** [[File Agent]] · **Contexto:** list

## Caminho
1. list_files ~/Documents
2. nome, tamanho, data

## Forma alternativa
Abrir no Explorer (DESKTOP)

## Critério de aceite
Lista exibida

## Armadilha
—

## Subagentes
- [[PathResolver]] — 1 · Entender
- [[OperationPlanner]] — 2 · Montar
- [[SafetyAuditor]] — 3 · Conferir
