---
tipo: tarefa-referencia
agente: DESKTOP
contexto: "Arquivos"
keywords: abrir pasta especifica abra downloads
tags: [referencia, desktop]
cssclasses: [ref-note]
---
# Abrir pasta específica

> [!route] Pedido exemplo
> abra a pasta downloads

**Agente:** [[Desktop Agent]] · **Contexto:** Arquivos

## Caminho
1. run_command 'explorer %USERPROFILE%\Downloads'

## Forma alternativa
FILE Agent se houver operação

## Critério de aceite
Pasta aberta

## Armadilha
Caminho com OneDrive redirecionado

## Subagentes
- [[AppResolver]] — 1 · Entender
- [[ContentComposer]] — 2 · Montar
- [[ScreenGuard]] — 3 · Conferir
