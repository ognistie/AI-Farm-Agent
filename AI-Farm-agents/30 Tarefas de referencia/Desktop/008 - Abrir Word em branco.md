---
tipo: tarefa-referencia
agente: DESKTOP
contexto: "App Office"
keywords: abrir word branco abra
tags: [referencia, desktop]
cssclasses: [ref-note]
---
# Abrir Word em branco

> [!route] Pedido exemplo
> abra o word

**Agente:** [[Desktop Agent]] · **Contexto:** App Office

## Caminho
1. rotina: app_search Word
2. wait 5
3. vision_click 'Documento em branco'

## Forma alternativa
Win+R 'winword'

## Critério de aceite
Documento em branco aberto

## Armadilha
Tela inicial muda por versão do Office

## Subagentes
- [[AppResolver]] — 1 · Entender
- [[ContentComposer]] — 2 · Montar
- [[ScreenGuard]] — 3 · Conferir
