---
tipo: tarefa-referencia
agente: DESKTOP
contexto: "Persistência"
keywords: salvar arquivo bloco notas escreva nota salve como lembrete txt area trabalho
tags: [referencia, desktop]
cssclasses: [ref-note]
---
# Salvar arquivo do Bloco de Notas

> [!route] Pedido exemplo
> escreva uma nota e salve como lembrete.txt na área de trabalho

**Agente:** [[Desktop Agent]] · **Contexto:** Persistência

## Caminho
1. app_type
2. hotkey ctrl+s
3. wait 1
4. type_text caminho
5. hotkey enter

## Forma alternativa
FILE: write_file direto em Desktop/lembrete.txt

## Critério de aceite
Arquivo existe na área de trabalho

## Armadilha
Diálogo 'substituir?' se já existir

## Subagentes
- [[AppResolver]] — 1 · Entender
- [[ContentComposer]] — 2 · Montar
- [[ScreenGuard]] — 3 · Conferir
