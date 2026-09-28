---
tipo: tarefa-referencia
agente: DESKTOP
contexto: "Interação visual"
keywords: calcular calculadora abra calcule 150
tags: [referencia, desktop]
cssclasses: [ref-note]
---
# Calcular na calculadora

> [!route] Pedido exemplo
> abra a calculadora e calcule 150 x 12

**Agente:** [[Desktop Agent]] · **Contexto:** Interação visual

## Caminho
1. LLM fallback: app_search
2. wait
3. vision_click botões ou type_text '150*12' + enter

## Forma alternativa
Maestro calcula e mostra o resultado direto

## Critério de aceite
Resultado 1800 na tela

## Armadilha
Digitar é mais estável que clicar botão a botão

## Subagentes
- [[AppResolver]] — 1 · Entender
- [[ContentComposer]] — 2 · Montar
- [[ScreenGuard]] — 3 · Conferir
