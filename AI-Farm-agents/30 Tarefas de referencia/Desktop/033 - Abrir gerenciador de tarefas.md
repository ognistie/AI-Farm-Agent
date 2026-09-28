---
tipo: tarefa-referencia
agente: DESKTOP
contexto: "Diagnóstico"
keywords: abrir gerenciador tarefas abra
tags: [referencia, desktop]
cssclasses: [ref-note]
---
# Abrir gerenciador de tarefas

> [!route] Pedido exemplo
> abra o gerenciador de tarefas

**Agente:** [[Desktop Agent]] · **Contexto:** Diagnóstico

## Caminho
1. hotkey ctrl+shift+esc

## Forma alternativa
run_command taskmgr

## Critério de aceite
Gerenciador aberto

## Armadilha
Não finalizar processos sem pedido

## Subagentes
- [[AppResolver]] — 1 · Entender
- [[ContentComposer]] — 2 · Montar
- [[ScreenGuard]] — 3 · Conferir
