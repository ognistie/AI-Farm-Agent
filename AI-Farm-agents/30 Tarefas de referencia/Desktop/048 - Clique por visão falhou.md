---
tipo: tarefa-referencia
agente: DESKTOP
contexto: "Baixa confiança"
keywords: clique visao falhou enviar aplicativo
tags: [referencia, desktop]
cssclasses: [ref-note]
---
# Clique por visão falhou

> [!route] Pedido exemplo
> clique em enviar no aplicativo

**Agente:** [[Desktop Agent]] · **Contexto:** Baixa confiança

## Caminho
1. vision_click falha (⚠️ confiança) → retry 1x → falha registrada

## Forma alternativa
Atalho de teclado equivalente (enter)

## Critério de aceite
Falha reportada, sem clique aleatório

## Armadilha
Clique na barra de tarefas é reprovado

## Subagentes
- [[AppResolver]] — 1 · Entender
- [[ContentComposer]] — 2 · Montar
- [[ScreenGuard]] — 3 · Conferir
