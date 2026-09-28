---
tipo: tarefa-referencia
agente: WEB
contexto: "Local + data"
keywords: horario filme cinema pesquise filmes cartaz hoje campinas
tags: [referencia, web]
cssclasses: [ref-note]
---
# Horário de filme no cinema

> [!route] Pedido exemplo
> pesquise os filmes em cartaz hoje em campinas

**Agente:** [[Web Agent]] · **Contexto:** Local + data

## Caminho
1. Query 'filmes em cartaz campinas hoje'
2. web_goto
3. web_read

## Forma alternativa
Site do cinema/ingresso.com

## Critério de aceite
Lista de filmes

## Armadilha
Não comprar ingresso

## Subagentes
- [[QueryBuilder]] — 1 · Entender
- [[Navigator]] — 2 · Montar
- [[ContentGuard]] — 3 · Conferir
