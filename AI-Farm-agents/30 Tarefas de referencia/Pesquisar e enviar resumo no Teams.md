---
tipo: tarefa-referencia
agente: WEB, DESKTOP
keywords: pesquisar enviar teams resumo mensagem
tags: [referencia]
cssclasses: [ref-note]
---
# Pesquisar e enviar resumo no Teams

**Agentes:** [[Web Agent]], [[Desktop Agent]]

## Pedido exemplo
> pesquise sobre o Palmeiras e envie um resumo para João no Teams

## Caminho
1) WEB(search) query='Palmeiras' + web_read  2) DESKTOP(teams/send_message) person='João' message='{output_summary_1}' depends_on=1

## Armadilha
Mensagem nunca inventada: vem do resultado da pesquisa.
