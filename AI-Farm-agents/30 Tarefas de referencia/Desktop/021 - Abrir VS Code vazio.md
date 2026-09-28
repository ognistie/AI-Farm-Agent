---
tipo: tarefa-referencia
agente: DESKTOP
contexto: "IDE"
keywords: abrir code vazio abra
tags: [referencia, desktop]
cssclasses: [ref-note]
---
# Abrir VS Code vazio

> [!route] Pedido exemplo
> abra o vs code

**Agente:** [[Desktop Agent]] · **Contexto:** IDE

## Caminho
1. rotina: app_search Visual Studio Code
2. wait 4

## Forma alternativa
Terminal: 'code'

## Critério de aceite
VS Code aberto

## Armadilha
Criar projeto é do Code Agent

## Subagentes
- [[AppResolver]] — 1 · Entender
- [[ContentComposer]] — 2 · Montar
- [[ScreenGuard]] — 3 · Conferir
