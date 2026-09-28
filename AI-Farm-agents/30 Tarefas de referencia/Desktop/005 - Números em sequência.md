---
tipo: tarefa-referencia
agente: DESKTOP
contexto: "Conteúdo derivado"
keywords: numeros sequencia abra notepad escreva ate
tags: [referencia, desktop]
cssclasses: [ref-note]
---
# Números em sequência

> [!route] Pedido exemplo
> abra o notepad e escreva de 1 até 20

**Agente:** [[Desktop Agent]] · **Contexto:** Conteúdo derivado

## Caminho
1. Maestro monta 1..20 com \n
2. ContentComposer converte quebras
3. app_type

## Forma alternativa
run_python gerando o texto

## Critério de aceite
20 linhas numeradas

## Armadilha
Quebra de linha literal '\n' aparecendo

## Subagentes
- [[AppResolver]] — 1 · Entender
- [[ContentComposer]] — 2 · Montar
- [[ScreenGuard]] — 3 · Conferir
