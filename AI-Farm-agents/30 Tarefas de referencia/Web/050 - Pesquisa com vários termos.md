---
tipo: tarefa-referencia
agente: WEB
contexto: "Termo composto"
keywords: pesquisa varios termos pesquise receitas vegetarianas rapidas baratas
tags: [referencia, web]
cssclasses: [ref-note]
---
# Pesquisa com vários termos

> [!route] Pedido exemplo
> pesquise receitas vegetarianas rápidas e baratas

**Agente:** [[Web Agent]] · **Contexto:** Termo composto

## Caminho
1. Query completa (todas as palavras)
2. web_goto
3. web_read

## Forma alternativa
Dividir em buscas se ficar amplo demais

## Critério de aceite
Resultados relevantes

## Armadilha
Não cortar a query no primeiro 'e'

## Subagentes
- [[QueryBuilder]] — 1 · Entender
- [[Navigator]] — 2 · Montar
- [[ContentGuard]] — 3 · Conferir
