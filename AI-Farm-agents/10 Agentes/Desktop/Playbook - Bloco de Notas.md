---
tipo: playbook
agente: DESKTOP
keywords: bloco notas notepad escrever texto digitar
tags: [playbook, desktop]
cssclasses: [agent-desktop]
---
# Bloco de Notas

Agente: [[Desktop Agent]]

## Exemplo de pedido
> Abra o bloco de notas e escreva a frase "olá mundo"

## Caminho
1. `app_search` Bloco de Notas
2. `wait` 3s
3. `app_type` janela 'Notas' com o texto

## Armadilhas
- Texto ditado entre aspas → literal.
- Pedido de conteúdo (poema, lista) → o Maestro escreve o conteúdo completo em `params.text`.
