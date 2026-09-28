---
tipo: tarefa-referencia
agente: DESKTOP
contexto: "Web → Desktop"
keywords: mensagem whatsapp resultado pesquisa pesquise horario jogo brasil mande pedro
tags: [referencia, desktop]
cssclasses: [ref-note]
---
# Mensagem no WhatsApp com resultado de pesquisa

> [!route] Pedido exemplo
> pesquise o horário do jogo do brasil e mande para o pedro no whatsapp

**Agente:** [[Desktop Agent]] · **Contexto:** Web → Desktop

## Caminho
1. 1) WEB busca + web_read 2) DESKTOP whatsapp person=Pedro message={output_summary_1} depends_on=1

## Forma alternativa
Enviar só o link da busca

## Critério de aceite
Mensagem com o horário lido

## Armadilha
Conferir se a leitura trouxe o horário antes de enviar

## Subagentes
- [[AppResolver]] — 1 · Entender
- [[ContentComposer]] — 2 · Montar
- [[ScreenGuard]] — 3 · Conferir
