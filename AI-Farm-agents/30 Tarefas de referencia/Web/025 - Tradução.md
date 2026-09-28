---
tipo: tarefa-referencia
agente: WEB
contexto: "Tradução rápida"
keywords: traducao traduza ingles frase bom dia todos
tags: [referencia, web]
cssclasses: [ref-note]
---
# Tradução

> [!route] Pedido exemplo
> traduza para inglês a frase bom dia a todos

**Agente:** [[Web Agent]] · **Contexto:** Tradução rápida

## Caminho
1. web_goto translate.google.com/?sl=pt&tl=en&text=bom+dia+a+todos

## Forma alternativa
O próprio Maestro traduz se não precisar do site

## Critério de aceite
Tradução exibida

## Armadilha
Textos longos: dividir

## Subagentes
- [[QueryBuilder]] — 1 · Entender
- [[Navigator]] — 2 · Montar
- [[ContentGuard]] — 3 · Conferir
