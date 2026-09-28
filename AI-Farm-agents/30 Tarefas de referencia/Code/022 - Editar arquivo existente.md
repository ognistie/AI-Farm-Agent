---
tipo: tarefa-referencia
agente: CODE
contexto: "edit_existing"
keywords: editar arquivo existente app projeto adicione rota health
tags: [referencia, code]
cssclasses: [ref-note]
---
# Editar arquivo existente

> [!route] Pedido exemplo
> no app.py do meu projeto adicione uma rota /health

**Agente:** [[Code Agent]] · **Contexto:** edit_existing

## Caminho
1. Ler arquivo
2. inserir rota mantendo estilo
3. Reviewer
4. abrir no VS Code

## Forma alternativa
Mostrar o diff antes de salvar

## Critério de aceite
Rota adicionada sem quebrar o resto

## Armadilha
Não reescrever o arquivo inteiro

## Subagentes
- [[Architect]] — 1 · Entender
- [[Builder]] — 2 · Montar
- [[Reviewer]] — 3 · Conferir
