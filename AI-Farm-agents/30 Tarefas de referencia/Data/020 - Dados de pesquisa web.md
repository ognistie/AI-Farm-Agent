---
tipo: tarefa-referencia
agente: DATA
contexto: "cadeia WEB → DATA"
keywords: dados pesquisa web coloque numa planilha agente pesquisou
tags: [referencia, data]
cssclasses: [ref-note]
---
# Dados de pesquisa web

> [!route] Pedido exemplo
> coloque numa planilha os dados que o agente web pesquisou

**Agente:** [[Data Agent]] · **Contexto:** cadeia WEB → DATA

## Caminho
1. Usar {output_text_N} como fonte
2. parse para linhas
3. planilha

## Forma alternativa
Pedir confirmação se o texto vier sem estrutura

## Critério de aceite
Dados lidos viram tabela

## Armadilha
Não inventar dados que a pesquisa não trouxe

## Subagentes
- [[SchemaDesigner]] — 1 · Entender
- [[FormulaChartDesigner]] — 2 · Montar
- [[SheetReviewer]] — 3 · Conferir
