---
tipo: tarefa-referencia
agente: DESKTOP
keywords: bloco notas escrever frase texto ditado
tags: [referencia]
cssclasses: [ref-note]
---
# Escrever texto ditado no Bloco de Notas

**Agentes:** [[Desktop Agent]]

## Pedido exemplo
> abra o bloco de notas e escreva a frase "olá mundo"

## Caminho
DESKTOP(notepad/write_text) text='olá mundo' → app_search → wait 3 → app_type

## Armadilha
Texto entre aspas é literal.
