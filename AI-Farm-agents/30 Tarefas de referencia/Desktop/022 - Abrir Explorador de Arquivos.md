---
tipo: tarefa-referencia
agente: DESKTOP
contexto: "Sistema"
keywords: abrir explorador arquivos abra
tags: [referencia, desktop]
cssclasses: [ref-note]
---
# Abrir Explorador de Arquivos

> [!route] Pedido exemplo
> abra o explorador de arquivos

**Agente:** [[Desktop Agent]] · **Contexto:** Sistema

## Caminho
1. rotina: hotkey win+e
2. wait 2

## Forma alternativa
explorer.exe via run_command

## Critério de aceite
Explorador aberto

## Armadilha
—

## Subagentes
- [[AppResolver]] — 1 · Entender
- [[ContentComposer]] — 2 · Montar
- [[ScreenGuard]] — 3 · Conferir
