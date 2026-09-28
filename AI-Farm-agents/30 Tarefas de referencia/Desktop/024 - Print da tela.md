---
tipo: tarefa-referencia
agente: DESKTOP
contexto: "Captura"
keywords: print tela tire
tags: [referencia, desktop]
cssclasses: [ref-note]
---
# Print da tela

> [!route] Pedido exemplo
> tire um print da tela

**Agente:** [[Desktop Agent]] · **Contexto:** Captura

## Caminho
1. utilitário: run_python pyautogui.screenshot → Desktop/screenshot_HHMMSS.png
2. abre no Explorer

## Forma alternativa
Win+Shift+S (manual)

## Critério de aceite
PNG salvo na área de trabalho

## Armadilha
App do agente pode aparecer no print

## Subagentes
- [[AppResolver]] — 1 · Entender
- [[ContentComposer]] — 2 · Montar
- [[ScreenGuard]] — 3 · Conferir
