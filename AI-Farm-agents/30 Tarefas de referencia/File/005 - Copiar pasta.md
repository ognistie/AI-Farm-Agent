---
tipo: tarefa-referencia
agente: FILE
contexto: "copy"
keywords: copiar pasta copie projetos pendrive
tags: [referencia, file]
cssclasses: [ref-note]
---
# Copiar pasta

> [!route] Pedido exemplo
> copie a pasta projetos para um pendrive E:

**Agente:** [[File Agent]] · **Contexto:** copy

## Caminho
1. shutil.copytree com verificação de espaço (disk_usage)

## Forma alternativa
zip e copiar o zip

## Critério de aceite
Cópia completa

## Armadilha
Drive inexistente: reportar

## Subagentes
- [[PathResolver]] — 1 · Entender
- [[OperationPlanner]] — 2 · Montar
- [[SafetyAuditor]] — 3 · Conferir
