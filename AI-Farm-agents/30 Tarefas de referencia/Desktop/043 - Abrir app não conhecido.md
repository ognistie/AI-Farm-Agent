---
tipo: tarefa-referencia
agente: DESKTOP
contexto: "App sem rotina"
keywords: abrir app nao conhecido abra obsidian
tags: [referencia, desktop]
cssclasses: [ref-note]
---
# Abrir app não conhecido

> [!route] Pedido exemplo
> abra o obsidian

**Agente:** [[Desktop Agent]] · **Contexto:** App sem rotina

## Caminho
1. AppResolver sem rotina
2. LLM fallback: app_search 'Obsidian'
3. wait 4

## Forma alternativa
Pedir o nome exato se não abrir

## Critério de aceite
App aberto

## Armadilha
Nome do atalho diferente do nome do app

## Subagentes
- [[AppResolver]] — 1 · Entender
- [[ContentComposer]] — 2 · Montar
- [[ScreenGuard]] — 3 · Conferir
