---
tipo: tarefa-referencia
agente: DESKTOP
contexto: "Texto literal"
keywords: escrever frase ditada abra bloco notas escreva reuniao 15h
tags: [referencia, desktop]
cssclasses: [ref-note]
---
# Escrever frase ditada

> [!route] Pedido exemplo
> abra o bloco de notas e escreva "reunião às 15h"

**Agente:** [[Desktop Agent]] · **Contexto:** Texto literal

## Caminho
1. ContentComposer: text literal
2. app_search
3. wait 3
4. app_type 'Notas'

## Forma alternativa
type_text com janela focada

## Critério de aceite
Texto exato na janela

## Armadilha
Aspas: copiar exatamente

## Subagentes
- [[AppResolver]] — 1 · Entender
- [[ContentComposer]] — 2 · Montar
- [[ScreenGuard]] — 3 · Conferir
