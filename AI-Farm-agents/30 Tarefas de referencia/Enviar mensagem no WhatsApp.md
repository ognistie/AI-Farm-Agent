---
tipo: tarefa-referencia
agente: DESKTOP
keywords: whatsapp enviar mensagem zap
tags: [referencia]
cssclasses: [ref-note]
---
# Enviar mensagem no WhatsApp

**Agentes:** [[Desktop Agent]]

## Pedido exemplo
> mande 'chego às 18h' para Maria no WhatsApp

## Caminho
DESKTOP(whatsapp/send_message) person='Maria' message='chego às 18h' → rotina WhatsApp

## Armadilha
Sem destinatário claro → pedir esclarecimento.
