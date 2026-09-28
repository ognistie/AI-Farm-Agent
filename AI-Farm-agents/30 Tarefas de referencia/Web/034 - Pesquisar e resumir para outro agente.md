---
tipo: tarefa-referencia
agente: WEB
contexto: "Cadeia de dados"
keywords: pesquisar resumir outro agente pesquise palmeiras resumo
tags: [referencia, web]
cssclasses: [ref-note]
---
# Pesquisar e resumir para outro agente

> [!route] Pedido exemplo
> pesquise sobre o palmeiras e me dê um resumo

**Agente:** [[Web Agent]] · **Contexto:** Cadeia de dados

## Caminho
1. Busca por URL
2. web_read
3. Maestro usa {output_summary_1}

## Forma alternativa
Wikipedia como fonte estável

## Critério de aceite
Resumo curto disponível na próxima subtask

## Armadilha
ContentGuard marca injection antes de repassar

## Subagentes
- [[QueryBuilder]] — 1 · Entender
- [[Navigator]] — 2 · Montar
- [[ContentGuard]] — 3 · Conferir
