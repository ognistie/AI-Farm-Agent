---
tipo: tarefa-referencia
agente: DATA
keywords: planilha excel gastos grafico despesas orcamento
tags: [referencia]
cssclasses: [ref-note]
---
# Criar planilha de gastos com grafico

**Agentes:** [[Data Agent]]

## Pedido exemplo
> crie uma planilha de gastos do mês com gráfico

## Caminho
DATA → run_python openpyxl (categorias, =SUM, BarChart) → salva .xlsx na Área de Trabalho → abre no Excel

## Armadilha
Nome do arquivo do tema; não sobrescrever.
