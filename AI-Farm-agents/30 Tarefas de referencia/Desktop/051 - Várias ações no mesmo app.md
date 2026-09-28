---
tipo: tarefa-referencia
agente: DESKTOP
contexto: "Sequência"
keywords: varias acoes mesmo app abra bloco notas escreva ola salve feche
tags: [referencia, desktop]
cssclasses: [ref-note]
---
# Várias ações no mesmo app

> [!route] Pedido exemplo
> abra o bloco de notas, escreva olá, salve e feche

**Agente:** [[Desktop Agent]] · **Contexto:** Sequência

## Caminho
1. Uma subtask: app_search
2. app_type
3. ctrl+s
4. nome
5. enter
6. close_app

## Forma alternativa
Dividir em passos com confirmação

## Critério de aceite
Arquivo salvo e app fechado

## Armadilha
Um app = uma subtask (Maestro)

## Subagentes
- [[AppResolver]] — 1 · Entender
- [[ContentComposer]] — 2 · Montar
- [[ScreenGuard]] — 3 · Conferir
