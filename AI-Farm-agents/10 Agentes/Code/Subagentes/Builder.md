---
tipo: subagente
agente: CODE
papel: montar
tags: [subagente, code]
cssclasses: [agent-code]
---
# Builder

> [!code] 2 · Montar — subagente do [[Code Agent]]
> Gera o codigo completo com o modelo (unico subagente que usa LLM).

| | |
|---|---|
| **Entrada** | Esqueleto + regras do projeto |
| **Saída** | Código completo (única chamada ao modelo) |
| **Regra** | Até 3 tentativas com o motivo do Reviewer |
| **Custo** | chamada ao modelo |
| **Código** | `ai-farm-agent/agents/subagents.py` → `Builder` |

O rastro de cada execução aparece no plano em `40 Execucoes/Planos` (bloco **Subagentes**).
