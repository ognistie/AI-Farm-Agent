---
tipo: tarefa-referencia
agente: WEB
keywords: youtube video pesquisar primeiro assistir
tags: [referencia]
cssclasses: [ref-note]
---
# Pesquisar no YouTube e abrir o primeiro

**Agentes:** [[Web Agent]]

## Pedido exemplo
> abra o youtube, pesquise lofi e abra o primeiro vídeo

## Caminho
WEB(search, url youtube) → web_goto results?search_query=lofi → wait → web_click primeiro vídeo

## Armadilha
Sem Playwright: abrir os resultados já conta como busca.
