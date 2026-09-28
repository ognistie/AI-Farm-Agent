---
tipo: playbook
agente: WEB
keywords: pesquisar google termo busca
tags: [playbook, web]
cssclasses: [agent-web]
---
# Pesquisa no Google

Agente: [[Web Agent]]

## Exemplo de pedido
> Pesquise no Google sobre eleições 2026 no Brasil

## Caminho
1. `web_goto` → `https://www.google.com/search?q=eleições+2026+brasil`
2. `wait` 2s
3. `web_read` para capturar os resultados

## Armadilhas
- Termo com acentos: use URL encoding (o código já faz).
- Pedido 'na aba de procura' não muda nada: continua sendo a URL de busca.
