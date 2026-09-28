---
tipo: tarefa-referencia
agente: DESKTOP
contexto: "App Office"
keywords: abrir excel branco abra
tags: [referencia, desktop]
cssclasses: [ref-note]
---
# Abrir Excel em branco

> [!route] Pedido exemplo
> abra o excel

**Agente:** [[Desktop Agent]] · **Contexto:** App Office

## Caminho
1. rotina: app_search Excel
2. wait 5
3. vision_click 'Pasta de trabalho em branco'

## Forma alternativa
DATA se houver dados

## Critério de aceite
Pasta em branco aberta

## Armadilha
Planilha com dados é do Data Agent

## Subagentes
- [[AppResolver]] — 1 · Entender
- [[ContentComposer]] — 2 · Montar
- [[ScreenGuard]] — 3 · Conferir
