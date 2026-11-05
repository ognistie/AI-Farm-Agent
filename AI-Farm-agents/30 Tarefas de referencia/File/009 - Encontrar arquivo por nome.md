---
tipo: tarefa-referencia
agente: FILE
keywords: encontrar buscar arquivo nome extensao listar ler pasta
estado: curado
verificado: nao
revisado_em: 2026-10-31
tags: [referencia, file]
cssclasses: [ref-note]
---
# Encontrar arquivo por nome

Procedimento revisado contra o codigo atual. Exige validacao desta versao antes de ser
promovido a caminho comprovado; contagens historicas nao validam um procedimento modificado.

## Caminho
FILE -> find_files(path, pattern) ou list_files(path) na raiz autorizada -> listar caminhos observados; read_file somente no escopo.

## Aceite e limites
- Solicitar a pasta quando faltar alvo suficiente. Nao varrer o disco inteiro.
- Distinguir nenhum resultado, acesso negado e limite de busca.
- Nao chamar busca por nome de deteccao de duplicatas: identidade por hash exige ferramenta propria.
