---
tipo: tarefa-referencia
agente: WEB
keywords: pesquisar pesquise google busca termo internet
tags: [referencia]
cssclasses: [ref-note]
---
# Pesquisar no Google

**Agentes:** [[Web Agent]]

## Pedido exemplo
> abra o google e pesquise por eleições 2026 brasil

## Caminho
WEB(search) com params.query='eleições 2026 brasil' → web_goto https://www.google.com/search?q=... → wait → web_read

## Armadilha
Não abrir só a página inicial. Termo vai em params.query.
