---
tipo: tarefa-referencia
agente: WEB
contexto: "Site conhecido"
keywords: abrir rede social abra linkedin
tags: [referencia, web]
cssclasses: [ref-note]
---
# Abrir rede social

> [!route] Pedido exemplo
> abra o linkedin

**Agente:** [[Web Agent]] · **Contexto:** Site conhecido

## Caminho
1. SITES['linkedin'] → web_goto
2. wait 2

## Forma alternativa
Busca 'linkedin' se o catálogo mudar

## Critério de aceite
LinkedIn aberto

## Armadilha
Nunca postar nada sem pedido explícito

## Subagentes
- [[QueryBuilder]] — 1 · Entender
- [[Navigator]] — 2 · Montar
- [[ContentGuard]] — 3 · Conferir
