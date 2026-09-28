---
tipo: tarefa-referencia
agente: DESKTOP
contexto: "Sistema"
keywords: abrir configuracoes windows abra bluetooth
tags: [referencia, desktop]
cssclasses: [ref-note]
---
# Abrir configurações do Windows

> [!route] Pedido exemplo
> abra as configurações de bluetooth

**Agente:** [[Desktop Agent]] · **Contexto:** Sistema

## Caminho
1. run_command 'start ms-settings:bluetooth'

## Forma alternativa
Win+I e navegar

## Critério de aceite
Tela de Bluetooth aberta

## Armadilha
Não alterar configurações sem pedido

## Subagentes
- [[AppResolver]] — 1 · Entender
- [[ContentComposer]] — 2 · Montar
- [[ScreenGuard]] — 3 · Conferir
