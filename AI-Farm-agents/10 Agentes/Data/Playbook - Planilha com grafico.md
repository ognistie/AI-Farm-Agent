---
tipo: playbook
agente: DATA
keywords: planilha excel grafico gastos vendas
tags: [playbook, data]
cssclasses: [agent-data]
---
# Planilha com grafico

Agente: [[Data Agent]]

## Exemplo de pedido
> Crie uma planilha de gastos do mês com gráfico

## Caminho
1. `run_python` openpyxl: categorias, valores, total com =SUM
2. BarChart por categoria
3. Abrir no Excel

## Armadilhas
- Gráfico referencia o intervalo de dados real (Reference).
