---
tipo: tarefa-referencia
agente: FILE
contexto: "info"
keywords: espaco disco quanto livre tenho
tags: [referencia, file]
cssclasses: [ref-note]
---
# Espaço em disco

> [!route] Pedido exemplo
> quanto espaço livre tenho no disco c

**Agente:** [[File Agent]] · **Contexto:** info

## Caminho
1. shutil.disk_usage('C:/')
2. GB livres/total

## Forma alternativa
—

## Critério de aceite
Valores exibidos

## Armadilha
Só leitura

## Subagentes
- [[PathResolver]] — 1 · Entender
- [[OperationPlanner]] — 2 · Montar
- [[SafetyAuditor]] — 3 · Conferir
