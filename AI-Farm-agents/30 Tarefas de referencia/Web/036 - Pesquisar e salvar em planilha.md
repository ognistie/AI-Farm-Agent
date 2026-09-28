---
tipo: tarefa-referencia
agente: WEB
contexto: "Web → Data"
keywords: pesquisar salvar planilha pesquise maiores paises area coloque numa
tags: [referencia, web]
cssclasses: [ref-note]
---
# Pesquisar e salvar em planilha

> [!route] Pedido exemplo
> pesquise os 10 maiores países em área e coloque numa planilha

**Agente:** [[Web Agent]] · **Contexto:** Web → Data

## Caminho
1. 1) WEB busca + web_read 2) DATA planilha com {output_text_1}

## Forma alternativa
DATA com dados conhecidos se não precisar de fonte

## Critério de aceite
Planilha com os dados lidos

## Armadilha
Conferir se a leitura trouxe a lista

## Subagentes
- [[QueryBuilder]] — 1 · Entender
- [[Navigator]] — 2 · Montar
- [[ContentGuard]] — 3 · Conferir
