---
tipo: playbook
agente: DESKTOP
keywords: whatsapp zap mensagem enviar
tags: [playbook, desktop]
cssclasses: [agent-desktop]
---
# WhatsApp

Agente: [[Desktop Agent]]

## Exemplo de pedido
> Mande 'chego às 18h' para Maria no WhatsApp

## Caminho
1. `app_search` WhatsApp
2. `wait` 4s
3. `vision_click` campo de pesquisa
4. `type_text` nome
5. `vision_click` resultado
6. `type_text` mensagem
7. `hotkey` Enter

## Armadilhas
- Confirmar que a conversa aberta é a pessoa certa antes de enviar.
