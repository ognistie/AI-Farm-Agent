---
tipo: tarefa-referencia
agente: CODE
contexto: "edit_existing / bugfix"
keywords: corrigir bug corrija erro divisao zero calculo
tags: [referencia, code]
cssclasses: [ref-note]
---
# Corrigir bug

> [!route] Pedido exemplo
> corrija o erro de divisão por zero no calculo.py

**Agente:** [[Code Agent]] · **Contexto:** edit_existing / bugfix

## Caminho
1. Ler
2. tratar o caso
3. adicionar teste
4. Reviewer

## Forma alternativa
Explicar o bug antes

## Critério de aceite
Erro não ocorre mais

## Armadilha
Não mascarar erro com except genérico

## Subagentes
- [[Architect]] — 1 · Entender
- [[Builder]] — 2 · Montar
- [[Reviewer]] — 3 · Conferir
