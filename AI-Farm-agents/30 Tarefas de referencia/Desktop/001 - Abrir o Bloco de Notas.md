---
tipo: tarefa-referencia
agente: DESKTOP
contexto: "Abrir app vazio"
keywords: abrir bloco notas abra
tags: [referencia, desktop]
cssclasses: [ref-note]
---
# Abrir o Bloco de Notas

> [!route] Pedido exemplo
> abra o bloco de notas

**Agente:** [[Desktop Agent]] · **Contexto:** Abrir app vazio

## Caminho
1. AppResolver: notepad
2. rotina: app_search 'Bloco de Notas'
3. wait 3
4. ScreenGuard ok

## Forma alternativa
Win+R 'notepad'

## Critério de aceite
Janela do Bloco de Notas aberta

## Armadilha
Não escrever nada que não foi pedido

## Subagentes
- [[AppResolver]] — 1 · Entender
- [[ContentComposer]] — 2 · Montar
- [[ScreenGuard]] — 3 · Conferir
