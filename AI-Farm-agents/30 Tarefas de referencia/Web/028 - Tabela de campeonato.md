---
tipo: tarefa-referencia
agente: WEB
contexto: "Classificação"
keywords: tabela campeonato abra brasileirao
tags: [referencia, web]
cssclasses: [ref-note]
---
# Tabela de campeonato

> [!route] Pedido exemplo
> abra a tabela do brasileirão

**Agente:** [[Web Agent]] · **Contexto:** Classificação

## Caminho
1. Query 'tabela brasileirão'
2. web_goto
3. web_read

## Forma alternativa
ge.globo.com/futebol/brasileirao-serie-a

## Critério de aceite
Tabela exibida

## Armadilha
Série A x Série B

## Subagentes
- [[QueryBuilder]] — 1 · Entender
- [[Navigator]] — 2 · Montar
- [[ContentGuard]] — 3 · Conferir
