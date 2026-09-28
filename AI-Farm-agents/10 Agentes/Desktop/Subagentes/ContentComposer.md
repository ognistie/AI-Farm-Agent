---
tipo: subagente
agente: DESKTOP
papel: montar
tags: [subagente, desktop]
cssclasses: [agent-desktop]
---
# ContentComposer

> [!desktop] 2 · Montar — subagente do [[Desktop Agent]]
> Prepara o texto a digitar: quebras de linha reais, espacos, limite de tamanho.

| | |
|---|---|
| **Entrada** | params.text / params.message |
| **Saída** | Texto com quebras reais, sem espaços sobrando, ≤6000 chars |
| **Regra** | Texto vazio num pedido de escrita já foi barrado pela POL-001 |
| **Custo** | zero tokens (determinístico) |
| **Código** | `ai-farm-agent/agents/subagents.py` → `ContentComposer` |

O rastro de cada execução aparece no plano em `40 Execucoes/Planos` (bloco **Subagentes**).
