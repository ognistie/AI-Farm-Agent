---
tipo: tarefa-referencia
agente: WEB
contexto: "Documento oficial"
keywords: arquivo pdf especifico procure edital enem 2026
tags: [referencia, web]
cssclasses: [ref-note]
---
# Arquivo PDF específico

> [!route] Pedido exemplo
> procure o pdf do edital do enem 2026

**Agente:** [[Web Agent]] · **Contexto:** Documento oficial

## Caminho
1. Query 'edital enem 2026 filetype:pdf'
2. web_goto
3. web_read

## Forma alternativa
Site do INEP (gov.br/inep)

## Critério de aceite
PDF oficial encontrado

## Armadilha
Sites não oficiais com PDF alterado

## Subagentes
- [[QueryBuilder]] — 1 · Entender
- [[Navigator]] — 2 · Montar
- [[ContentGuard]] — 3 · Conferir
