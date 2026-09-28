---
tipo: tarefa-referencia
agente: WEB
contexto: "Autenticação"
keywords: pagina login abra outlook
tags: [referencia, web]
cssclasses: [ref-note]
---
# Página de login

> [!route] Pedido exemplo
> abra a página de login do outlook

**Agente:** [[Web Agent]] · **Contexto:** Autenticação

## Caminho
1. web_goto https://outlook.live.com
2. wait 2

## Forma alternativa
Abrir o app Outlook (DESKTOP)

## Critério de aceite
Tela de login exibida

## Armadilha
NUNCA digitar senha ou código 2FA

## Subagentes
- [[QueryBuilder]] — 1 · Entender
- [[Navigator]] — 2 · Montar
- [[ContentGuard]] — 3 · Conferir
