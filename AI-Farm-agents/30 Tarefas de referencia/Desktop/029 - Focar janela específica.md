---
tipo: tarefa-referencia
agente: DESKTOP
contexto: "Foco"
keywords: focar janela especifica traga excel frente
tags: [referencia, desktop]
cssclasses: [ref-note]
---
# Focar janela específica

> [!route] Pedido exemplo
> traga a janela do excel para frente

**Agente:** [[Desktop Agent]] · **Contexto:** Foco

## Caminho
1. focus_window title='Excel'
2. wait 1

## Forma alternativa
alt+tab repetido

## Critério de aceite
Excel em primeiro plano

## Armadilha
Várias janelas com 'Excel' no título

## Subagentes
- [[AppResolver]] — 1 · Entender
- [[ContentComposer]] — 2 · Montar
- [[ScreenGuard]] — 3 · Conferir
