---
tipo: tarefa-referencia
agente: WEB
contexto: "Atalho para o site certo"
keywords: abrir primeiro resultado google pesquise tabela fipe abra
tags: [referencia, web]
cssclasses: [ref-note]
---
# Abrir primeiro resultado do Google

> [!route] Pedido exemplo
> pesquise tabela fipe e abra o primeiro resultado

**Agente:** [[Web Agent]] · **Contexto:** Atalho para o site certo

## Caminho
1. Busca por URL
2. wait 2
3. web_click 'h3'
4. wait 2
5. web_read

## Forma alternativa
Abrir diretamente o site conhecido (veiculos.fipe.org.br)

## Critério de aceite
Primeiro site orgânico aberto

## Armadilha
Primeiro h3 pode ser anúncio patrocinado

## Subagentes
- [[QueryBuilder]] — 1 · Entender
- [[Navigator]] — 2 · Montar
- [[ContentGuard]] — 3 · Conferir
