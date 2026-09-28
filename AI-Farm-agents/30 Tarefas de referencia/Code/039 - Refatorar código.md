---
tipo: tarefa-referencia
agente: CODE
contexto: "edit_existing / refactor"
keywords: refatorar codigo refatore arquivo utils ficar mais legivel
tags: [referencia, code]
cssclasses: [ref-note]
---
# Refatorar código

> [!route] Pedido exemplo
> refatore o arquivo utils.py para ficar mais legível

**Agente:** [[Code Agent]] · **Contexto:** edit_existing / refactor

## Caminho
1. Ler
2. extrair funções
3. manter comportamento
4. Reviewer

## Forma alternativa
Só sugerir mudanças

## Critério de aceite
Mesmo comportamento, código mais claro

## Armadilha
Não mudar API pública

## Subagentes
- [[Architect]] — 1 · Entender
- [[Builder]] — 2 · Montar
- [[Reviewer]] — 3 · Conferir
