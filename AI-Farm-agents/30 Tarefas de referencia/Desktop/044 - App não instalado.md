---
tipo: tarefa-referencia
agente: DESKTOP
contexto: "Falha provável"
keywords: app nao instalado abra photoshop
tags: [referencia, desktop]
cssclasses: [ref-note]
---
# App não instalado

> [!route] Pedido exemplo
> abra o photoshop

**Agente:** [[Desktop Agent]] · **Contexto:** Falha provável

## Caminho
1. app_search → sem resultado → falha reportada

## Forma alternativa
Sugerir alternativa (web)

## Critério de aceite
Usuário informado

## Armadilha
Não instalar software sem pedido

## Subagentes
- [[AppResolver]] — 1 · Entender
- [[ContentComposer]] — 2 · Montar
- [[ScreenGuard]] — 3 · Conferir
