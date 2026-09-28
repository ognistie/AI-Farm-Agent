---
tipo: tarefa-referencia
agente: WEB
contexto: "Usuário quer reproduzir"
keywords: abrir primeiro video youtube abra toque lofi
tags: [referencia, web]
cssclasses: [ref-note]
---
# Abrir primeiro vídeo do YouTube

> [!route] Pedido exemplo
> abra o youtube e toque o primeiro vídeo de lofi

**Agente:** [[Web Agent]] · **Contexto:** Usuário quer reproduzir

## Caminho
1. Busca por URL
2. wait 3
3. web_click 'ytd-video-renderer a#video-title'

## Forma alternativa
Sem Playwright: abrir resultados e avisar que o clique precisa ser manual

## Critério de aceite
Vídeo abre na página de reprodução

## Armadilha
Anúncios podem ocupar o primeiro lugar

## Subagentes
- [[QueryBuilder]] — 1 · Entender
- [[Navigator]] — 2 · Montar
- [[ContentGuard]] — 3 · Conferir
