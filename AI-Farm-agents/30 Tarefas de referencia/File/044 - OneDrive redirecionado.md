---
tipo: tarefa-referencia
agente: FILE
contexto: "caminho especial"
keywords: onedrive redirecionado organize area trabalho
tags: [referencia, file]
cssclasses: [ref-note]
---
# OneDrive redirecionado

> [!route] Pedido exemplo
> organize minha área de trabalho do onedrive

**Agente:** [[File Agent]] · **Contexto:** caminho especial

## Caminho
1. Detectar ~/OneDrive/Desktop se existir
2. organizar lá

## Forma alternativa
Pedir o caminho

## Critério de aceite
Pasta certa organizada

## Armadilha
Arquivos só na nuvem (placeholder) não baixados

## Subagentes
- [[PathResolver]] — 1 · Entender
- [[OperationPlanner]] — 2 · Montar
- [[SafetyAuditor]] — 3 · Conferir
