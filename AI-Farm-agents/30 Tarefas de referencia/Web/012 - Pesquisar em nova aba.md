---
tipo: tarefa-referencia
agente: WEB
contexto: "Busca sem perder a página atual"
keywords: pesquisar nova aba guia pesquise clima sao paulo
tags: [referencia, web]
cssclasses: [ref-note]
---
# Pesquisar em nova aba

> [!route] Pedido exemplo
> em uma nova guia pesquise sobre o clima em são paulo

**Agente:** [[Web Agent]] · **Contexto:** Busca sem perder a página atual

## Caminho
1. QueryBuilder new_tab=true
2. web_new_tab URL de busca

## Forma alternativa
Busca normal se a aba não importar

## Critério de aceite
Resultados em nova aba

## Armadilha
Termo 'em uma nova guia' não entra na query

## Subagentes
- [[QueryBuilder]] — 1 · Entender
- [[Navigator]] — 2 · Montar
- [[ContentGuard]] — 3 · Conferir
