---
tipo: playbook
agente: WEB
estado: curado
verificado: nao
keywords: abrir site url acessar nova aba
revisado_em: 2026-10-31
tags: [playbook, web]
---
# Abrir site ou URL

Agente: [[Web Agent]]

## Caminho
open_url ou web_goto conforme o backend, com HTTP/HTTPS e URL sem credenciais; confirmar destino quando houver leitura disponivel.

## Limites e aceite
Abertura solicitada nao e pagina observada. Nao usar Python, protocolos arbitrarios, seletor fixo ou sessao/aba de identidade desconhecida.
