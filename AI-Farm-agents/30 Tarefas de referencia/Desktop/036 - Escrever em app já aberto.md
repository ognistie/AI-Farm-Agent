---
tipo: tarefa-referencia
agente: DESKTOP
contexto: "Janela atual"
keywords: escrever app aberto escreva programa esta
tags: [referencia, desktop]
cssclasses: [ref-note]
---
# Escrever em app já aberto

> [!route] Pedido exemplo
> escreva 'ok' no programa que está aberto

**Agente:** [[Desktop Agent]] · **Contexto:** Janela atual

## Caminho
1. type_text 'ok' (janela em foco)

## Forma alternativa
Perguntar qual app

## Critério de aceite
Texto digitado no app focado

## Armadilha
Janela do agente pode estar em foco

## Subagentes
- [[AppResolver]] — 1 · Entender
- [[ContentComposer]] — 2 · Montar
- [[ScreenGuard]] — 3 · Conferir
