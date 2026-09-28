---
tipo: tarefa-referencia
agente: DESKTOP
contexto: "Conteúdo gerado pelo Maestro"
keywords: escrever lista gerada abra bloco notas escreva compras churrasco
tags: [referencia, desktop]
cssclasses: [ref-note]
---
# Escrever lista gerada

> [!route] Pedido exemplo
> abra o bloco de notas e escreva uma lista de compras para churrasco

**Agente:** [[Desktop Agent]] · **Contexto:** Conteúdo gerado pelo Maestro

## Caminho
1. Maestro gera lista completa em text
2. ContentComposer ajusta quebras
3. app_type

## Forma alternativa
Word se o usuário quiser formatação

## Critério de aceite
Lista com vários itens digitada

## Armadilha
POL-002: não escrever só 'lista de compras'

## Subagentes
- [[AppResolver]] — 1 · Entender
- [[ContentComposer]] — 2 · Montar
- [[ScreenGuard]] — 3 · Conferir
