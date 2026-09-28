---
tipo: tarefa-referencia
agente: DESKTOP
contexto: "Transferência"
keywords: copiar colar texto copie bloco notas cole word
tags: [referencia, desktop]
cssclasses: [ref-note]
---
# Copiar e colar texto

> [!route] Pedido exemplo
> copie o texto do bloco de notas e cole no word

**Agente:** [[Desktop Agent]] · **Contexto:** Transferência

## Caminho
1. focus_window Notas
2. ctrl+a
3. ctrl+c
4. rotina Word
5. ctrl+v

## Forma alternativa
run_python lendo o .txt e escrevendo no .docx

## Critério de aceite
Texto no Word

## Armadilha
Área de transferência sobrescrita

## Subagentes
- [[AppResolver]] — 1 · Entender
- [[ContentComposer]] — 2 · Montar
- [[ScreenGuard]] — 3 · Conferir
