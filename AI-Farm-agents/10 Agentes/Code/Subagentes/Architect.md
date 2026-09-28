---
tipo: subagente
agente: CODE
papel: entender
tags: [subagente, code]
cssclasses: [agent-code]
---
# Architect

> [!code] 1 · Entender — subagente do [[Code Agent]]
> Classifica o projeto (tipo, complexidade, stack, tema) e, se multi-arquivo, desenha o esqueleto.

| | |
|---|---|
| **Entrada** | Pedido original do usuário |
| **Saída** | Tipo de projeto, complexidade, tema e esqueleto multi-arquivo |
| **Regra** | Tema sempre da tarefa atual |
| **Custo** | zero tokens (determinístico) |
| **Código** | `ai-farm-agent/agents/subagents.py` → `Architect` |

O rastro de cada execução aparece no plano em `40 Execucoes/Planos` (bloco **Subagentes**).
