---
tipo: tarefa-referencia
agente: DESKTOP
contexto: "Mensagem ditada"
keywords: mensagem teams mande bom dia time carlos
tags: [referencia, desktop]
cssclasses: [ref-note]
---
# Mensagem no Teams

> [!route] Pedido exemplo
> mande 'bom dia, time' no teams para o carlos

**Agente:** [[Desktop Agent]] · **Contexto:** Mensagem ditada

## Caminho
1. AppResolver teams
2. rotina: app_search
3. wait_for_window
4. uia_click Chat
5. uia_click Carlos
6. uia_type
7. enter

## Forma alternativa
vision_click se UIA falhar

## Critério de aceite
Mensagem enviada ao Carlos

## Armadilha
Sem destinatário claro: perguntar

## Subagentes
- [[AppResolver]] — 1 · Entender
- [[ContentComposer]] — 2 · Montar
- [[ScreenGuard]] — 3 · Conferir
