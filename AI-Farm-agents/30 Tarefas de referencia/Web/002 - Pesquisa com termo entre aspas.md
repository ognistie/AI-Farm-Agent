---
tipo: tarefa-referencia
agente: WEB
contexto: "Usuário quer a frase exata"
keywords: pesquisa termo entre aspas pesquise inteligencia artificial generativa google
tags: [referencia, web]
cssclasses: [ref-note]
---
# Pesquisa com termo entre aspas

> [!route] Pedido exemplo
> pesquise "inteligência artificial generativa" no google

**Agente:** [[Web Agent]] · **Contexto:** Usuário quer a frase exata

## Caminho
1. Termo mantém as aspas na URL (%22...%22)
2. web_goto
3. web_read

## Forma alternativa
Usar operador de frase exata na query

## Critério de aceite
Resultados exatos para a frase

## Armadilha
Remover aspas muda o resultado

## Subagentes
- [[QueryBuilder]] — 1 · Entender
- [[Navigator]] — 2 · Montar
- [[ContentGuard]] — 3 · Conferir
