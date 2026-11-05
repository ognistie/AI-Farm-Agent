---
tipo: playbook
agente: DATA
estado: curado
verificado: nao
keywords: fluxo caixa financeiro entradas saidas saldo orcamento
revisado_em: 2026-10-31
tags: [playbook, data]
---
# Fluxo de caixa

Agente: [[Data Agent]]

## Caminho
create_workbook com Data, Descricao, Entrada, Saida e Saldo; manter formulas e referencias na propria aba.

## Limites e aceite
Saldo = anterior + entrada - saida. Separar dados reais de exemplos. Resumo em outra aba precisa de dados explicitos, sem vinculo/formula entre abas. Nao inventar juros, impostos ou saldos.
