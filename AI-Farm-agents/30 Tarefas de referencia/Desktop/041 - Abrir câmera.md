---
tipo: tarefa-referencia
agente: DESKTOP
contexto: "App do Windows"
keywords: abrir camera abra
tags: [referencia, desktop]
cssclasses: [ref-note]
---
# Abrir câmera

> [!route] Pedido exemplo
> abra a câmera

**Agente:** [[Desktop Agent]] · **Contexto:** App do Windows

## Caminho
1. app_search 'Câmera'
2. wait 3

## Forma alternativa
—

## Critério de aceite
Câmera aberta

## Armadilha
Privacidade: não gravar sem pedido

## Subagentes
- [[AppResolver]] — 1 · Entender
- [[ContentComposer]] — 2 · Montar
- [[ScreenGuard]] — 3 · Conferir
