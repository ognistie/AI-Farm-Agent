---
tipo: tarefa-referencia
agente: DESKTOP
contexto: "Desenho"
keywords: desenhar paint abra desenhe circulo
tags: [referencia, desktop]
cssclasses: [ref-note]
---
# Desenhar no Paint

> [!route] Pedido exemplo
> abra o paint e desenhe um círculo

**Agente:** [[Desktop Agent]] · **Contexto:** Desenho

## Caminho
1. LLM fallback: app_search Paint
2. wait 4
3. vision_click ferramenta elipse
4. click + drag

## Forma alternativa
Gerar imagem com Python (PIL) e abrir

## Critério de aceite
Círculo desenhado

## Armadilha
Coordenadas dependem da resolução

## Subagentes
- [[AppResolver]] — 1 · Entender
- [[ContentComposer]] — 2 · Montar
- [[ScreenGuard]] — 3 · Conferir
