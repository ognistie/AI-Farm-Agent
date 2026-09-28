---
tipo: subagente
agente: FILE
papel: montar
tags: [subagente, file]
cssclasses: [agent-file]
---
# OperationPlanner

> [!file] 2 · Montar — subagente do [[File Agent]]
> Classifica a operacao e decide o modo: executar ou so simular (destrutiva sem confirmacao).

| | |
|---|---|
| **Entrada** | Pedido + caminho sensível |
| **Saída** | Operação e modo: executar, simular ou bloqueado |
| **Regra** | Destrutivo sem 'pode apagar' → simular |
| **Custo** | zero tokens (determinístico) |
| **Código** | `ai-farm-agent/agents/subagents.py` → `OperationPlanner` |

O rastro de cada execução aparece no plano em `40 Execucoes/Planos` (bloco **Subagentes**).
