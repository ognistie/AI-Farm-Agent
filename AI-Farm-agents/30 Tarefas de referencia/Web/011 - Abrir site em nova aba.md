---
tipo: tarefa-referencia
agente: WEB
contexto: "Preservar a aba atual"
keywords: abrir site nova aba abra gmail
tags: [referencia, web]
cssclasses: [ref-note]
---
# Abrir site em nova aba

> [!route] Pedido exemplo
> abra o gmail em uma nova aba

**Agente:** [[Web Agent]] · **Contexto:** Preservar a aba atual

## Caminho
1. web_new_tab https://mail.google.com
2. wait 2

## Forma alternativa
Sem Playwright: navegador padrão já abre nova aba

## Critério de aceite
Gmail em aba nova

## Armadilha
Login é do usuário: nunca digitar senha

## Subagentes
- [[QueryBuilder]] — 1 · Entender
- [[Navigator]] — 2 · Montar
- [[ContentGuard]] — 3 · Conferir
