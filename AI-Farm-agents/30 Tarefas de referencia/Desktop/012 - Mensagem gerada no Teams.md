---
tipo: tarefa-referencia
agente: DESKTOP
contexto: "Mensagem redigida"
keywords: mensagem gerada teams avise equipe reuniao foi adiada amanha
tags: [referencia, desktop]
cssclasses: [ref-note]
---
# Mensagem gerada no Teams

> [!route] Pedido exemplo
> avise a equipe no teams que a reunião foi adiada para amanhã

**Agente:** [[Desktop Agent]] · **Contexto:** Mensagem redigida

## Caminho
1. Maestro redige mensagem curta
2. rotina Teams com person=equipe

## Forma alternativa
Pedir nome do chat/canal se ambíguo

## Critério de aceite
Aviso enviado no chat certo

## Armadilha
'Equipe' pode ser vários chats

## Subagentes
- [[AppResolver]] — 1 · Entender
- [[ContentComposer]] — 2 · Montar
- [[ScreenGuard]] — 3 · Conferir
