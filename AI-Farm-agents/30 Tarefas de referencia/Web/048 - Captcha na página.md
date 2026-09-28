---
tipo: tarefa-referencia
agente: WEB
contexto: "Bloqueio anti-bot"
keywords: captcha pagina pesquise site traga dados
tags: [referencia, web]
cssclasses: [ref-note]
---
# Captcha na página

> [!route] Pedido exemplo
> pesquise no site y e me traga os dados

**Agente:** [[Web Agent]] · **Contexto:** Bloqueio anti-bot

## Caminho
1. Detectar captcha no web_read → parar e pedir ação humana

## Forma alternativa
Outra fonte sem captcha

## Critério de aceite
Usuário informado

## Armadilha
Nunca tentar resolver captcha

## Subagentes
- [[QueryBuilder]] — 1 · Entender
- [[Navigator]] — 2 · Montar
- [[ContentGuard]] — 3 · Conferir
