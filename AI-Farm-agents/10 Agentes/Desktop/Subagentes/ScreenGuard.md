---
tipo: subagente
agente: DESKTOP
papel: conferir
tags: [subagente, desktop]
cssclasses: [agent-desktop]
---
# ScreenGuard

> [!desktop] 3 · Conferir — subagente do [[Desktop Agent]]
> Revisa os passos: espera apos abrir app, cliques nunca na barra de tarefas, limite de passos.

| | |
|---|---|
| **Entrada** | Passos propostos |
| **Saída** | Passos revisados (espera após abrir app) ou reprovação |
| **Regra** | Clique na barra de tarefas ou >20 passos → reprova |
| **Custo** | zero tokens (determinístico) |
| **Código** | `ai-farm-agent/agents/subagents.py` → `ScreenGuard` |

O rastro de cada execução aparece no plano em `40 Execucoes/Planos` (bloco **Subagentes**).
