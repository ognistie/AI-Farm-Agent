---
tipo: tarefa-referencia
agente: DESKTOP
contexto: "Pedido incompleto"
keywords: texto vazio pedido abra bloco notas escreva
tags: [referencia, desktop]
cssclasses: [ref-note]
---
# Texto vazio pedido

> [!route] Pedido exemplo
> abra o bloco de notas e escreva

**Agente:** [[Desktop Agent]] · **Contexto:** Pedido incompleto

## Caminho
1. POL-001 reprova plano sem texto → Maestro pergunta o que escrever

## Forma alternativa
—

## Critério de aceite
Pergunta feita, nada digitado

## Armadilha
Não abrir o app vazio fingindo sucesso

## Subagentes
- [[AppResolver]] — 1 · Entender
- [[ContentComposer]] — 2 · Montar
- [[ScreenGuard]] — 3 · Conferir
