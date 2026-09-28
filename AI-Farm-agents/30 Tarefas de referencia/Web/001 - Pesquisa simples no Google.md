---
tipo: tarefa-referencia
agente: WEB
contexto: "Busca informativa geral"
keywords: pesquisa simples google pesquise energia solar
tags: [referencia, web]
cssclasses: [ref-note]
---
# Pesquisa simples no Google

> [!route] Pedido exemplo
> pesquise no google sobre energia solar

**Agente:** [[Web Agent]] · **Contexto:** Busca informativa geral

## Caminho
1. QueryBuilder: termo='energia solar'
2. Navigator: web_goto google.com/search?q=energia+solar
3. wait 2
4. web_read

## Forma alternativa
Sem Playwright: abrir a URL de busca no navegador padrão

## Critério de aceite
Página de resultados aberta com o termo exato

## Armadilha
Não abrir só google.com

## Subagentes
- [[QueryBuilder]] — 1 · Entender
- [[Navigator]] — 2 · Montar
- [[ContentGuard]] — 3 · Conferir
