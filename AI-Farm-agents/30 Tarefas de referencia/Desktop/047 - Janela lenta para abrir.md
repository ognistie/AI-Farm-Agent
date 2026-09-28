---
tipo: tarefa-referencia
agente: DESKTOP
contexto: "App pesado"
keywords: janela lenta abrir abra teams
tags: [referencia, desktop]
cssclasses: [ref-note]
---
# Janela lenta para abrir

> [!route] Pedido exemplo
> abra o teams

**Agente:** [[Desktop Agent]] · **Contexto:** App pesado

## Caminho
1. rotina com wait_for_window (até 15s) em vez de wait fixo

## Forma alternativa
Aumentar espera e tentar focar

## Critério de aceite
Teams pronto antes do próximo passo

## Armadilha
ScreenGuard garante espera após abrir

## Subagentes
- [[AppResolver]] — 1 · Entender
- [[ContentComposer]] — 2 · Montar
- [[ScreenGuard]] — 3 · Conferir
