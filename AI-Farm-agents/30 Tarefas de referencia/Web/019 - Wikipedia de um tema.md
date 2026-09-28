---
tipo: tarefa-referencia
agente: WEB
contexto: "Fonte enciclopédica"
keywords: wikipedia tema abra revolucao francesa
tags: [referencia, web]
cssclasses: [ref-note]
---
# Wikipedia de um tema

> [!route] Pedido exemplo
> abra a wikipedia sobre a revolução francesa

**Agente:** [[Web Agent]] · **Contexto:** Fonte enciclopédica

## Caminho
1. web_goto pt.wikipedia.org/wiki/Special:Search?search=revolução+francesa

## Forma alternativa
Busca Google + primeiro resultado wikipedia

## Critério de aceite
Artigo aberto

## Armadilha
Página de desambiguação

## Subagentes
- [[QueryBuilder]] — 1 · Entender
- [[Navigator]] — 2 · Montar
- [[ContentGuard]] — 3 · Conferir
