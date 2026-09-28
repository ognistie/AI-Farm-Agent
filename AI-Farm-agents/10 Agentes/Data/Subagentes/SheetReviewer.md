---
tipo: subagente
agente: DATA
papel: conferir
tags: [subagente, data]
cssclasses: [agent-data]
---
# SheetReviewer

> [!data] 3 · Conferir — subagente do [[Data Agent]]
> Revisa o codigo da planilha: sintaxe, salva .xlsx, nao sobrescreve, abre no Excel.

| | |
|---|---|
| **Entrada** | Código da planilha |
| **Saída** | Aprovação: sintaxe, salva .xlsx, chama save(); avisos de sobrescrita |
| **Regra** | Sem .xlsx → reprova |
| **Custo** | zero tokens (determinístico) |
| **Código** | `ai-farm-agent/agents/subagents.py` → `SheetReviewer` |

O rastro de cada execução aparece no plano em `40 Execucoes/Planos` (bloco **Subagentes**).
