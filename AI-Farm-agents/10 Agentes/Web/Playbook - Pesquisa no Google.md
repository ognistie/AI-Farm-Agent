---
tipo: playbook
agente: WEB
estado: curado
verificado: nao
keywords: pesquisar google termo busca noticias aspas filtro cotacao dolar clima
revisado_em: 2026-10-31
tags: [playbook, web]
---
# Pesquisa no Google

Agente: [[Web Agent]]

## Caminho
Codificar o termo completo na URL de resultados -> open_url/web_goto -> ler o resultado quando o pedido exigir resposta.

## Limites e aceite
Sem termo, perguntar. Aspas e filtros devem sobreviver. Clima, preco e cotacao exigem fonte atual; nao guardar o valor como conhecimento duravel.
