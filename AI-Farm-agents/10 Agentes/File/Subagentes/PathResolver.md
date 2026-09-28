---
tipo: subagente
agente: FILE
papel: entender
tags: [subagente, file]
cssclasses: [agent-file]
---
# PathResolver

> [!file] 1 · Entender — subagente do [[File Agent]]
> Traduz pastas conhecidas (Downloads, Documentos...) para caminhos reais e detecta caminhos sensiveis.

| | |
|---|---|
| **Entrada** | Pedido |
| **Saída** | Pastas reais (Downloads, Documentos...) e caminhos sensíveis |
| **Regra** | C:/Windows, Program Files, System32 → marcado |
| **Custo** | zero tokens (determinístico) |
| **Código** | `ai-farm-agent/agents/subagents.py` → `PathResolver` |

O rastro de cada execução aparece no plano em `40 Execucoes/Planos` (bloco **Subagentes**).
