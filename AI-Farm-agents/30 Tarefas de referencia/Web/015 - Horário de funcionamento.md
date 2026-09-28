---
tipo: tarefa-referencia
agente: WEB
contexto: "Informação local"
keywords: horario funcionamento pesquise shopping ibirapuera
tags: [referencia, web]
cssclasses: [ref-note]
---
# Horário de funcionamento

> [!route] Pedido exemplo
> pesquise o horário de funcionamento do shopping ibirapuera

**Agente:** [[Web Agent]] · **Contexto:** Informação local

## Caminho
1. Query com nome + 'horário'
2. web_goto
3. web_read (painel lateral)

## Forma alternativa
Google Maps: google.com/maps/search/

## Critério de aceite
Horário lido do painel

## Armadilha
Feriados mudam o horário

## Subagentes
- [[QueryBuilder]] — 1 · Entender
- [[Navigator]] — 2 · Montar
- [[ContentGuard]] — 3 · Conferir
