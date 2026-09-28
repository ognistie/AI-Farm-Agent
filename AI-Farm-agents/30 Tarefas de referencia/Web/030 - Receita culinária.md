---
tipo: tarefa-referencia
agente: WEB
contexto: "Culinária"
keywords: receita culinaria procure lasanha berinjela
tags: [referencia, web]
cssclasses: [ref-note]
---
# Receita culinária

> [!route] Pedido exemplo
> procure uma receita de lasanha de berinjela

**Agente:** [[Web Agent]] · **Contexto:** Culinária

## Caminho
1. Query 'receita lasanha de berinjela'
2. web_goto
3. web_click h3
4. web_read

## Forma alternativa
YouTube se o usuário preferir vídeo

## Critério de aceite
Receita aberta

## Armadilha
Resumo com palavras próprias

## Subagentes
- [[QueryBuilder]] — 1 · Entender
- [[Navigator]] — 2 · Montar
- [[ContentGuard]] — 3 · Conferir
