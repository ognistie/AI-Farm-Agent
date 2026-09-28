---
tipo: tarefa-referencia
agente: DESKTOP
contexto: "Encerrar"
keywords: fechar aplicativo feche bloco notas
tags: [referencia, desktop]
cssclasses: [ref-note]
---
# Fechar aplicativo

> [!route] Pedido exemplo
> feche o bloco de notas

**Agente:** [[Desktop Agent]] · **Contexto:** Encerrar

## Caminho
1. close_app 'notepad'

## Forma alternativa
alt+f4 com a janela focada

## Critério de aceite
Processo encerrado

## Armadilha
Texto não salvo é perdido: avisar

## Subagentes
- [[AppResolver]] — 1 · Entender
- [[ContentComposer]] — 2 · Montar
- [[ScreenGuard]] — 3 · Conferir
