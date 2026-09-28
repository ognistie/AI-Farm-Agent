---
tipo: tarefa-referencia
agente: CODE
contexto: "open_vscode_folder"
keywords: abrir projeto code abra pasta
tags: [referencia, code]
cssclasses: [ref-note]
---
# Abrir projeto no VS Code

> [!route] Pedido exemplo
> abra o vs code na pasta meu-projeto

**Agente:** [[Code Agent]] · **Contexto:** open_vscode_folder

## Caminho
1. Localizar pasta
2. subprocess code <pasta>

## Forma alternativa
DESKTOP abre VS Code vazio se não houver pasta

## Critério de aceite
VS Code na pasta certa

## Armadilha
Pasta com nome parecido

## Subagentes
- [[Architect]] — 1 · Entender
- [[Builder]] — 2 · Montar
- [[Reviewer]] — 3 · Conferir
