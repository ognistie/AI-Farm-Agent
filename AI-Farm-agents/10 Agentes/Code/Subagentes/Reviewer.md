---
tipo: subagente
agente: CODE
papel: conferir
tags: [subagente, code]
cssclasses: [agent-code]
---
# Reviewer

> [!code] 3 · Conferir — subagente do [[Code Agent]]
> Valida sintaxe, estrutura, qualidade e tema do codigo antes de executar.

| | |
|---|---|
| **Entrada** | Código gerado |
| **Saída** | Aprovação ou motivo literal (sintaxe, estrutura, qualidade, tema) |
| **Regra** | Programa GUI inline é bloqueado |
| **Custo** | zero tokens (determinístico) |
| **Código** | `ai-farm-agent/agents/subagents.py` → `Reviewer` |

O rastro de cada execução aparece no plano em `40 Execucoes/Planos` (bloco **Subagentes**).
