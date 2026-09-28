---
tipo: tarefa-referencia
agente: WEB
contexto: "Resultado visual"
keywords: pesquisa imagens pesquise casas madeira
tags: [referencia, web]
cssclasses: [ref-note]
---
# Pesquisa de imagens

> [!route] Pedido exemplo
> pesquise imagens de casas de madeira

**Agente:** [[Web Agent]] · **Contexto:** Resultado visual

## Caminho
1. web_goto google.com/search?q=casas+de+madeira&tbm=isch
2. wait

## Forma alternativa
Bing Imagens como alternativa

## Critério de aceite
Aba de imagens com o termo

## Armadilha
web_read não descreve imagens

## Subagentes
- [[QueryBuilder]] — 1 · Entender
- [[Navigator]] — 2 · Montar
- [[ContentGuard]] — 3 · Conferir
