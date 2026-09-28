---
tipo: subagente
agente: DATA
papel: entender
tags: [subagente, data]
cssclasses: [agent-data]
---
# SchemaDesigner

> [!data] 1 · Entender — subagente do [[Data Agent]]
> Descobre o tipo de planilha e sugere colunas iniciais.

| | |
|---|---|
| **Entrada** | Pedido |
| **Saída** | Tipo de planilha e colunas sugeridas |
| **Regra** | Colunas são ponto de partida |
| **Custo** | zero tokens (determinístico) |
| **Código** | `ai-farm-agent/agents/subagents.py` → `SchemaDesigner` |

O rastro de cada execução aparece no plano em `40 Execucoes/Planos` (bloco **Subagentes**).
