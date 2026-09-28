---
tipo: playbook
agente: DESKTOP
keywords: teams mensagem enviar chat conversa
tags: [playbook, desktop]
cssclasses: [agent-desktop]
---
# Teams

Agente: [[Desktop Agent]]

## Exemplo de pedido
> Envie 'bom dia' para João no Teams

## Caminho
1. `app_search` Microsoft Teams
2. `wait_for_window` Teams
3. `uia_click` Chat
4. `uia_click` conversa com a pessoa
5. `uia_type` mensagem
6. `hotkey` Enter

## Armadilhas
- Sem destinatário ou sem mensagem → pedir esclarecimento.
- Nome ambíguo (dois 'João') → parar e perguntar.
