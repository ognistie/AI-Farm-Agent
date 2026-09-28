---
tipo: tarefa-referencia
agente: FILE
contexto: "find_duplicates"
keywords: encontrar duplicados encontre fotos duplicadas pasta imagens
tags: [referencia, file]
cssclasses: [ref-note]
---
# Encontrar duplicados

> [!route] Pedido exemplo
> encontre fotos duplicadas na pasta imagens

**Agente:** [[File Agent]] · **Contexto:** find_duplicates

## Caminho
1. Agrupar por tamanho → hash SHA-256 → grupos

## Forma alternativa
Comparar só por nome (menos preciso)

## Critério de aceite
Grupos de duplicados listados

## Armadilha
Sem confirmação: não apagar

## Subagentes
- [[PathResolver]] — 1 · Entender
- [[OperationPlanner]] — 2 · Montar
- [[SafetyAuditor]] — 3 · Conferir
