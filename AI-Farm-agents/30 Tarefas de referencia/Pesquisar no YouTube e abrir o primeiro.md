---
tipo: tarefa-referencia
agente: WEB
keywords: youtube video pesquisar primeiro assistir tocar
estado: curado
verificado: nao
revisado_em: 2026-10-31
tags: [referencia, web]
cssclasses: [ref-note]
---
# Pesquisar no YouTube e abrir o primeiro

Procedimento revisado contra o codigo atual. Exige validacao desta versao antes de ser
promovido a caminho comprovado; contagens historicas nao validam um procedimento modificado.

## Caminho
WEB -> open_url/web_goto com results?search_query=<termo> -> browser_task para selecionar o video na janela/aba correta -> observar destino e reproducao.

## Aceite e limites
- Preservar o termo e diferenciar anuncio de resultado.
- Se apenas a busca abrir, informar resultado parcial; nao afirmar que o video tocou.
- Sem elemento identificavel, login ou CAPTCHA: parar e pedir intervencao, sem cliques por coordenadas memorizadas.
