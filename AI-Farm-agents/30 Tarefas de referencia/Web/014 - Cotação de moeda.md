---
tipo: tarefa-referencia
agente: WEB
contexto: "Dado financeiro volátil"
keywords: cotacao moeda pesquise dolar hoje
tags: [referencia, web]
cssclasses: [ref-note]
---
# Cotação de moeda

> [!route] Pedido exemplo
> pesquise a cotação do dólar hoje

**Agente:** [[Web Agent]] · **Contexto:** Dado financeiro volátil

## Caminho
1. Query 'cotação dólar hoje'
2. web_goto
3. web_read

## Forma alternativa
Site do Banco Central (bcb.gov.br)

## Critério de aceite
Valor lido com data

## Armadilha
Nunca usar valor lembrado pelo modelo

## Subagentes
- [[QueryBuilder]] — 1 · Entender
- [[Navigator]] — 2 · Montar
- [[ContentGuard]] — 3 · Conferir
