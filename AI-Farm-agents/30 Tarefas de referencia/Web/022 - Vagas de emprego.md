---
tipo: tarefa-referencia
agente: WEB
contexto: "Busca de carreira"
keywords: vagas emprego pesquise desenvolvedor python remoto
tags: [referencia, web]
cssclasses: [ref-note]
---
# Vagas de emprego

> [!route] Pedido exemplo
> pesquise vagas de desenvolvedor python remoto

**Agente:** [[Web Agent]] · **Contexto:** Busca de carreira

## Caminho
1. Query 'vagas desenvolvedor python remoto'
2. web_goto
3. web_read

## Forma alternativa
LinkedIn Jobs: linkedin.com/jobs/search/?keywords=

## Critério de aceite
Lista de vagas

## Armadilha
Não candidatar-se automaticamente

## Subagentes
- [[QueryBuilder]] — 1 · Entender
- [[Navigator]] — 2 · Montar
- [[ContentGuard]] — 3 · Conferir
