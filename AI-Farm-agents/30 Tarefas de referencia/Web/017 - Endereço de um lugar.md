---
tipo: tarefa-referencia
agente: WEB
contexto: "Pergunta pontual"
keywords: endereco lugar procure museu ipiranga
tags: [referencia, web]
cssclasses: [ref-note]
---
# Endereço de um lugar

> [!route] Pedido exemplo
> procure o endereço do museu do ipiranga

**Agente:** [[Web Agent]] · **Contexto:** Pergunta pontual

## Caminho
1. Query 'endereço museu do ipiranga'
2. web_goto
3. web_read

## Forma alternativa
google.com/maps/search/museu+do+ipiranga

## Critério de aceite
Endereço lido

## Armadilha
Nomes parecidos em outras cidades

## Subagentes
- [[QueryBuilder]] — 1 · Entender
- [[Navigator]] — 2 · Montar
- [[ContentGuard]] — 3 · Conferir
