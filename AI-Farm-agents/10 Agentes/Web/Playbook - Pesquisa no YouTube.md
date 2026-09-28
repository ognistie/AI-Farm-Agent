---
tipo: playbook
agente: WEB
keywords: youtube video pesquisar assistir primeiro
tags: [playbook, web]
cssclasses: [agent-web]
---
# Pesquisa no YouTube

Agente: [[Web Agent]]

## Exemplo de pedido
> Abra o YouTube e pesquise vídeos de skate e abra o primeiro

## Caminho
1. `web_goto` → `https://www.youtube.com/results?search_query=videos+de+skate`
2. `wait` 2s
3. `web_click` em `ytd-video-renderer a#video-title`

## Armadilhas
- Sem Playwright não é possível clicar no primeiro vídeo: abrir os resultados já cumpre a busca.
