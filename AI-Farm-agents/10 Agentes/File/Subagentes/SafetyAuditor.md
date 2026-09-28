---
tipo: subagente
agente: FILE
papel: conferir
tags: [subagente, file]
cssclasses: [agent-file]
---
# SafetyAuditor

> [!file] 3 · Conferir — subagente do [[File Agent]]
> Audita o codigo gerado: sem apagar em modo simulacao, sem tocar em pastas do sistema.

| | |
|---|---|
| **Entrada** | Código gerado + modo |
| **Saída** | Aprovação ou bloqueio (apagar em simulação, pasta do sistema) |
| **Regra** | Defesa em profundidade além do prompt |
| **Custo** | zero tokens (determinístico) |
| **Código** | `ai-farm-agent/agents/subagents.py` → `SafetyAuditor` |

O rastro de cada execução aparece no plano em `40 Execucoes/Planos` (bloco **Subagentes**).
