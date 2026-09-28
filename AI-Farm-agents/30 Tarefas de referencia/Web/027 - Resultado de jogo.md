---
tipo: tarefa-referencia
agente: WEB
contexto: "Esporte"
keywords: resultado jogo pesquise ultimo flamengo
tags: [referencia, web]
cssclasses: [ref-note]
---
# Resultado de jogo

> [!route] Pedido exemplo
> pesquise o resultado do último jogo do flamengo

**Agente:** [[Web Agent]] · **Contexto:** Esporte

## Caminho
1. Query 'resultado último jogo flamengo'
2. web_goto
3. web_read

## Forma alternativa
ge.globo.com

## Critério de aceite
Placar lido

## Armadilha
Resultado de memória está desatualizado

## Subagentes
- [[QueryBuilder]] — 1 · Entender
- [[Navigator]] — 2 · Montar
- [[ContentGuard]] — 3 · Conferir
