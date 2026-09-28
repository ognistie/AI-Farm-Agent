---
tipo: tarefa-referencia
agente: WEB
contexto: "URL explícita no pedido"
keywords: abrir url digitada acesse https www python org downloads
tags: [referencia, web]
cssclasses: [ref-note]
---
# Abrir URL digitada

> [!route] Pedido exemplo
> acesse https://www.python.org/downloads/

**Agente:** [[Web Agent]] · **Contexto:** URL explícita no pedido

## Caminho
1. URL do texto → web_goto
2. wait 2

## Forma alternativa
Adicionar https:// se vier só www.

## Critério de aceite
Página exata aberta

## Armadilha
Não trocar a URL por outra 'parecida'

## Subagentes
- [[QueryBuilder]] — 1 · Entender
- [[Navigator]] — 2 · Montar
- [[ContentGuard]] — 3 · Conferir
