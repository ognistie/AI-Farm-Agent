---
tipo: tarefa-referencia
agente: WEB
contexto: "Cálculo na SERP"
keywords: converter unidades pesquise quanto milhas
tags: [referencia, web]
cssclasses: [ref-note]
---
# Converter unidades

> [!route] Pedido exemplo
> pesquise quanto é 10 milhas em km

**Agente:** [[Web Agent]] · **Contexto:** Cálculo na SERP

## Caminho
1. Query '10 milhas em km'
2. web_goto
3. web_read

## Forma alternativa
Calcular direto sem web

## Critério de aceite
Valor convertido lido

## Armadilha
Não arredondar de forma errada

## Subagentes
- [[QueryBuilder]] — 1 · Entender
- [[Navigator]] — 2 · Montar
- [[ContentGuard]] — 3 · Conferir
