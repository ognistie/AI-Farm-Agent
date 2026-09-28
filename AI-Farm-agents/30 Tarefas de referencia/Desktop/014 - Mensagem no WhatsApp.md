---
tipo: tarefa-referencia
agente: DESKTOP
contexto: "Mensageiro"
keywords: mensagem whatsapp mande chego minutos joao
tags: [referencia, desktop]
cssclasses: [ref-note]
---
# Mensagem no WhatsApp

> [!route] Pedido exemplo
> mande 'chego em 10 minutos' para o joão no whatsapp

**Agente:** [[Desktop Agent]] · **Contexto:** Mensageiro

## Caminho
1. AppResolver whatsapp
2. rotina: app_search
3. vision_click pesquisa
4. type_text João
5. vision_click resultado
6. type_text
7. enter

## Forma alternativa
WhatsApp Web (WEB) se o app não existir

## Critério de aceite
Mensagem enviada

## Armadilha
Dois contatos com o mesmo nome

## Subagentes
- [[AppResolver]] — 1 · Entender
- [[ContentComposer]] — 2 · Montar
- [[ScreenGuard]] — 3 · Conferir
