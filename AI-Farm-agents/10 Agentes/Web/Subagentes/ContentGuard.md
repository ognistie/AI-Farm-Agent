---
tipo: subagente
agente: WEB
papel: conferir
tags: [subagente, web]
cssclasses: [agent-web]
---
# ContentGuard

> [!web] 3 · Conferir — subagente do [[Web Agent]]
> Revisa o que foi lido da web: corta excesso e marca tentativas de prompt injection.

| | |
|---|---|
| **Entrada** | Resultado de web_read |
| **Saída** | Texto limpo (≤2500 chars) e marca INJECTION_DETECTED |
| **Regra** | Conteúdo de página nunca vira instrução (AGT-002) |
| **Custo** | zero tokens (determinístico) |
| **Código** | `ai-farm-agent/agents/subagents.py` → `ContentGuard` |

O rastro de cada execução aparece no plano em `40 Execucoes/Planos` (bloco **Subagentes**).
