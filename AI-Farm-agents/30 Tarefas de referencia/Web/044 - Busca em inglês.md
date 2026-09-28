---
tipo: tarefa-referencia
agente: WEB
contexto: "Pedido em outro idioma"
keywords: busca ingles search for best python books 2026
tags: [referencia, web]
cssclasses: [ref-note]
---
# Busca em inglês

> [!route] Pedido exemplo
> search for best python books 2026

**Agente:** [[Web Agent]] · **Contexto:** Pedido em outro idioma

## Caminho
1. Query em inglês + &hl=en
2. web_goto
3. web_read

## Forma alternativa
Manter idioma do usuário na resposta

## Critério de aceite
Resultados em inglês

## Armadilha
Não traduzir o termo sem necessidade

## Subagentes
- [[QueryBuilder]] — 1 · Entender
- [[Navigator]] — 2 · Montar
- [[ContentGuard]] — 3 · Conferir
