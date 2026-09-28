---
tipo: tarefa-referencia
agente: WEB
contexto: "Site no catálogo SITES"
keywords: abrir site conhecido pelo nome abra github
tags: [referencia, web]
cssclasses: [ref-note]
---
# Abrir site conhecido pelo nome

> [!route] Pedido exemplo
> abra o github

**Agente:** [[Web Agent]] · **Contexto:** Site no catálogo SITES

## Caminho
1. Navigator: SITES['github'] → web_goto https://github.com
2. wait 2

## Forma alternativa
Se não estiver no catálogo: busca pelo nome e abrir o primeiro resultado

## Critério de aceite
github.com aberto

## Armadilha
Não pesquisar quando o site é conhecido

## Subagentes
- [[QueryBuilder]] — 1 · Entender
- [[Navigator]] — 2 · Montar
- [[ContentGuard]] — 3 · Conferir
