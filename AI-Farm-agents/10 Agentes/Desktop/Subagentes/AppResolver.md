---
tipo: subagente
agente: DESKTOP
papel: entender
tags: [subagente, desktop]
cssclasses: [agent-desktop]
---
# AppResolver

> [!desktop] 1 · Entender — subagente do [[Desktop Agent]]
> Identifica o aplicativo (apelidos incluidos) e se existe rotina pronta para ele.

| | |
|---|---|
| **Entrada** | Pedido + params.app |
| **Saída** | App canônico (apelidos: zap→whatsapp, bloco de notas→notepad) |
| **Regra** | App desconhecido → LLM fallback |
| **Custo** | zero tokens (determinístico) |
| **Código** | `ai-farm-agent/agents/subagents.py` → `AppResolver` |

O rastro de cada execução aparece no plano em `40 Execucoes/Planos` (bloco **Subagentes**).
