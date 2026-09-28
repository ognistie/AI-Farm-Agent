---
tipo: tarefa-referencia
agente: DESKTOP
contexto: "Texto extenso"
keywords: texto longo escreva bloco notas resumo paragrafos energia eolica
tags: [referencia, desktop]
cssclasses: [ref-note]
---
# Texto longo

> [!route] Pedido exemplo
> escreva no bloco de notas um resumo de 3 parágrafos sobre energia eólica

**Agente:** [[Desktop Agent]] · **Contexto:** Texto extenso

## Caminho
1. Maestro gera 3 parágrafos
2. ContentComposer limita 6000 chars
3. app_type

## Forma alternativa
Word para documentos formais

## Critério de aceite
3 parágrafos na janela

## Armadilha
Digitação lenta: preferir app_type (colar)

## Subagentes
- [[AppResolver]] — 1 · Entender
- [[ContentComposer]] — 2 · Montar
- [[ScreenGuard]] — 3 · Conferir
