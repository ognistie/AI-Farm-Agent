---
tipo: tarefa-referencia
agente: DESKTOP
keywords: abrir app aplicativo bloco notas calculadora paint
tags: [referencia]
cssclasses: [ref-note]
---
# Abrir aplicativo

**Agentes:** [[Desktop Agent]]

## Pedido exemplo
> abra a calculadora

## Caminho
DESKTOP(calculadora/open) → app_search → wait 3

## Armadilha
Não escrever nada se não foi pedido.
