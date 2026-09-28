---
tipo: subagente
agente: DATA
papel: montar
tags: [subagente, data]
cssclasses: [agent-data]
---
# FormulaChartDesigner

> [!data] 2 · Montar — subagente do [[Data Agent]]
> Decide formulas (SUM, AVERAGE...) e grafico conforme o pedido e o tipo.

| | |
|---|---|
| **Entrada** | Pedido + tipo |
| **Saída** | Fórmulas (SUM, AVERAGE, IF...) e se há gráfico |
| **Regra** | Fórmulas em inglês no openpyxl |
| **Custo** | zero tokens (determinístico) |
| **Código** | `ai-farm-agent/agents/subagents.py` → `FormulaChartDesigner` |

O rastro de cada execução aparece no plano em `40 Execucoes/Planos` (bloco **Subagentes**).
