---
tipo: tarefa-referencia
agente: DESKTOP
contexto: "Chamada de voz"
keywords: ligacao teams ligue mariana
tags: [referencia, desktop]
cssclasses: [ref-note]
---
# Ligação no Teams

> [!route] Pedido exemplo
> ligue para a mariana no teams

**Agente:** [[Desktop Agent]] · **Contexto:** Chamada de voz

## Caminho
1. rotina Teams action_type=call
2. vision_click ícone telefone

## Forma alternativa
Chamada de vídeo se pedido

## Critério de aceite
Chamada iniciada

## Armadilha
Ação externa: só com pessoa explícita

## Subagentes
- [[AppResolver]] — 1 · Entender
- [[ContentComposer]] — 2 · Montar
- [[ScreenGuard]] — 3 · Conferir
