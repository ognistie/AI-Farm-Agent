---
tipo: tarefa-referencia
agente: WEB
contexto: "Filtro temporal"
keywords: busca periodo pesquise noticias bitcoin ultima semana
tags: [referencia, web]
cssclasses: [ref-note]
---
# Busca com período

> [!route] Pedido exemplo
> pesquise notícias sobre bitcoin da última semana

**Agente:** [[Web Agent]] · **Contexto:** Filtro temporal

## Caminho
1. Query + &tbm=nws&tbs=qdr:w
2. web_goto

## Forma alternativa
Adicionar 'semana' ao termo

## Critério de aceite
Notícias da semana

## Armadilha
Mercado volátil: sempre data da fonte

## Subagentes
- [[QueryBuilder]] — 1 · Entender
- [[Navigator]] — 2 · Montar
- [[ContentGuard]] — 3 · Conferir
