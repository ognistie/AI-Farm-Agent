---
tipo: playbook
agente: DATA
estado: curado
verificado: nao
keywords: planilha excel grafico gastos vendas
revisado_em: 2026-10-31
tags: [playbook, data]
---
# Planilha com grafico

Agente: [[Data Agent]]

## Caminho
create_workbook: rows com cabecalho, dados e formulas locais; charts bar/line com column numerica; builder reabre o XLSX e confere as estruturas.

## Limites e aceite
Primeira coluna: categorias. Formulas permitidas: SUM, AVERAGE, MIN, MAX, COUNT, COUNTA, COUNTIF, SUMIF, IF, ROUND, ABS. Sem macros, vinculos externos, PieChart ou formulas entre abas. Nao afirmar recalculo.
