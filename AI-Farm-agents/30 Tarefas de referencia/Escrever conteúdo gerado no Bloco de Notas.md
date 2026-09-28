---
tipo: tarefa-referencia
agente: DESKTOP
keywords: bloco notas escrever poema texto lista criar conteudo
tags: [referencia]
cssclasses: [ref-note]
---
# Escrever conteúdo gerado no Bloco de Notas

**Agentes:** [[Desktop Agent]]

## Pedido exemplo
> abra o bloco de notas e escreva um poema sobre o mar

## Caminho
Maestro ESCREVE o poema completo em params.text → DESKTOP(notepad/write_text) → app_type

## Armadilha
Reprovado por POL-002 se o texto for só 'poema sobre o mar'.
