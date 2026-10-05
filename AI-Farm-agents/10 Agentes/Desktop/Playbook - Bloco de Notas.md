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
1. `app_search` Bloco de Notas (abre `notepad.exe` direto)
2. `wait` 3s
3. `blank_document` — aba nova e vazia (o Win11 reabre o último documento)
4. `app_type` com `require_untitled` — digita só no documento novo

## Armadilhas
- Texto ditado entre aspas → literal (pontuação falada já convertida: "vírgula" → ",").
- Pedido de conteúdo (poema, lista) → o Maestro escreve o conteúdo completo em `params.text`.
- Nunca digitar num documento que o usuário já tinha aberto.

