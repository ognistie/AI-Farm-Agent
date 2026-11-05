---
tipo: tarefa-referencia
agente: DATA
keywords: planilha excel gastos vendas fluxo caixa cadastro grafico despesas orcamento
estado: curado
verificado: nao
revisado_em: 2026-10-31
tags: [referencia, data]
cssclasses: [ref-note]
---
# Criar planilha de gastos com grafico

Procedimento revisado contra o codigo atual. Exige validacao desta versao antes de ser
promovido a caminho comprovado; contagens historicas nao validam um procedimento modificado.

## Caminho
DATA -> create_workbook(manifest: name, sheets[title, rows, charts]) -> novo XLSX -> reabrir e conferir abas, celulas, formulas e graficos.

## Aceite e limites
- Cabecalho na primeira linha; dados fornecidos pelo usuario ou exemplos identificados.
- Ate 6 abas, 5000 linhas/aba, 100 colunas, 1 MiB. Graficos bar/line; categorias na primeira coluna.
- Formulas locais permitidas em ingles; sem macros, referencias externas ou entre abas.
- O builder nao recalcula formulas nem comprova a renderizacao no Excel. Ver [[Playbook - Fluxo de caixa]] e [[Playbook - Lista e cadastro]].
