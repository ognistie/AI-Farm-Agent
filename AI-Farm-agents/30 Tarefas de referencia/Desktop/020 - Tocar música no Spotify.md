---
tipo: tarefa-referencia
agente: DESKTOP
contexto: "Mídia"
keywords: tocar musica spotify abra toque musicas estudar
tags: [referencia, desktop]
cssclasses: [ref-note]
---
# Tocar música no Spotify

> [!route] Pedido exemplo
> abra o spotify e toque músicas para estudar

**Agente:** [[Desktop Agent]] · **Contexto:** Mídia

## Caminho
1. LLM fallback: app_search Spotify
2. wait 5
3. vision_click Pesquisar
4. type_text
5. enter
6. vision_click playlist

## Forma alternativa
Spotify Web (WEB)

## Critério de aceite
Música tocando

## Armadilha
Conta premium/anúncios variam

## Subagentes
- [[AppResolver]] — 1 · Entender
- [[ContentComposer]] — 2 · Montar
- [[ScreenGuard]] — 3 · Conferir
