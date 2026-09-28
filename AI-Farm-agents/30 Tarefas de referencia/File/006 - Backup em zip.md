---
tipo: tarefa-referencia
agente: FILE
contexto: "archive"
keywords: backup zip faca pasta documentos area trabalho
tags: [referencia, file]
cssclasses: [ref-note]
---
# Backup em zip

> [!route] Pedido exemplo
> faça backup da pasta documentos em zip na área de trabalho

**Agente:** [[File Agent]] · **Contexto:** archive

## Caminho
1. make_archive Documentos_backup_AAAAMMDD.zip → Desktop

## Forma alternativa
Copiar para outro drive

## Critério de aceite
Zip criado com data

## Armadilha
Espaço em disco

## Subagentes
- [[PathResolver]] — 1 · Entender
- [[OperationPlanner]] — 2 · Montar
- [[SafetyAuditor]] — 3 · Conferir
