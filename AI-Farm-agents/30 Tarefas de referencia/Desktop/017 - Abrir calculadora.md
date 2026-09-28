---
tipo: tarefa-referencia
agente: DESKTOP
contexto: "Utilitário"
keywords: abrir calculadora abra
tags: [referencia, desktop]
cssclasses: [ref-note]
---
# Abrir calculadora

> [!route] Pedido exemplo
> abra a calculadora

**Agente:** [[Desktop Agent]] · **Contexto:** Utilitário

## Caminho
1. rotina: app_search Calculadora
2. wait 3

## Forma alternativa
Win+R 'calc'

## Critério de aceite
Calculadora aberta

## Armadilha
—

## Subagentes
- [[AppResolver]] — 1 · Entender
- [[ContentComposer]] — 2 · Montar
- [[ScreenGuard]] — 3 · Conferir
