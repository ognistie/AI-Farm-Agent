---
tipo: tarefa-referencia
agente: WEB
contexto: "Busca restrita a um domínio"
keywords: pesquisa filtro site procure receita federal como declarar imposto renda
tags: [referencia, web]
cssclasses: [ref-note]
---
# Pesquisa com filtro de site

> [!route] Pedido exemplo
> procure no site da receita federal como declarar imposto de renda

**Agente:** [[Web Agent]] · **Contexto:** Busca restrita a um domínio

## Caminho
1. Query: 'declarar imposto de renda site:gov.br'
2. web_goto busca
3. web_read

## Forma alternativa
Abrir o site oficial e usar a busca interna

## Critério de aceite
Resultados só do domínio gov.br

## Armadilha
Não inventar a URL interna do site

## Subagentes
- [[QueryBuilder]] — 1 · Entender
- [[Navigator]] — 2 · Montar
- [[ContentGuard]] — 3 · Conferir
