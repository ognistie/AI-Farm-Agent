---
tipo: playbook
agente: WEB
keywords: abrir site url github gmail acessar
tags: [playbook, web]
cssclasses: [agent-web]
---
# Abrir site ou URL

Agente: [[Web Agent]]

## Exemplo de pedido
> Abra o GitHub

## Caminho
1. Site conhecido (github, gmail, linkedin...) ou URL no texto → `web_goto(url)`
2. `wait` 2s

## Armadilhas
- Não confundir 'abrir o google' (abrir) com 'pesquisar no google' (buscar).
