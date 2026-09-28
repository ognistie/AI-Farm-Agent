---
tipo: tarefa-referencia
agente: DESKTOP
contexto: "Calendário"
keywords: agendar lembrete crie calendario amanha
tags: [referencia, desktop]
cssclasses: [ref-note]
---
# Agendar lembrete

> [!route] Pedido exemplo
> crie um lembrete no calendário para amanhã às 9h

**Agente:** [[Desktop Agent]] · **Contexto:** Calendário

## Caminho
1. LLM fallback: app_search Calendário/Outlook
2. ctrl+n
3. preencher título e horário

## Forma alternativa
Arquivo .ics gerado e aberto

## Critério de aceite
Evento criado

## Armadilha
Fuso horário e data relativa: confirmar a data absoluta

## Subagentes
- [[AppResolver]] — 1 · Entender
- [[ContentComposer]] — 2 · Montar
- [[ScreenGuard]] — 3 · Conferir
