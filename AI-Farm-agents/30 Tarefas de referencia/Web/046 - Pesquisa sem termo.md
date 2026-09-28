---
tipo: tarefa-referencia
agente: WEB
contexto: "Pedido incompleto"
keywords: pesquisa sem termo abra google pesquise
tags: [referencia, web]
cssclasses: [ref-note]
---
# Pesquisa sem termo

> [!route] Pedido exemplo
> abra o google e pesquise

**Agente:** [[Web Agent]] · **Contexto:** Pedido incompleto

## Caminho
1. QueryBuilder: intenção=search sem termo → erro 'diga o que pesquisar' (POL-003)

## Forma alternativa
Maestro pede esclarecimento

## Critério de aceite
Nada executado; pergunta feita

## Armadilha
Nunca pesquisar 'pesquisa'

## Subagentes
- [[QueryBuilder]] — 1 · Entender
- [[Navigator]] — 2 · Montar
- [[ContentGuard]] — 3 · Conferir
