---
tipo: tarefa-referencia
agente: DESKTOP
contexto: "E-mail"
keywords: mail outlook envie ana empresa assunto relatorio
tags: [referencia, desktop]
cssclasses: [ref-note]
---
# E-mail no Outlook

> [!route] Pedido exemplo
> envie um e-mail para ana@empresa.com com o assunto relatório

**Agente:** [[Desktop Agent]] · **Contexto:** E-mail

## Caminho
1. rotina Outlook: ctrl+n
2. type_text destinatário
3. tab
4. assunto
5. corpo
6. ctrl+enter

## Forma alternativa
Abrir rascunho sem enviar se o corpo não foi dado

## Critério de aceite
E-mail enviado

## Armadilha
E-mail é redigido no log (PII)

## Subagentes
- [[AppResolver]] — 1 · Entender
- [[ContentComposer]] — 2 · Montar
- [[ScreenGuard]] — 3 · Conferir
