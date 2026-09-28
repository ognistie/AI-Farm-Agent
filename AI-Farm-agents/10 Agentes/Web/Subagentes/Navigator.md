---
tipo: subagente
agente: WEB
papel: montar
tags: [subagente, web]
cssclasses: [agent-web]
---
# Navigator

> [!web] 2 · Montar — subagente do [[Web Agent]]
> Monta a rota: URL de resultados, site conhecido ou fallback nativo sem Playwright.

| | |
|---|---|
| **Entrada** | Saída do QueryBuilder + Playwright disponível? |
| **Saída** | Passos prontos (URL de busca, site conhecido) ou nada → LLM |
| **Regra** | Sem Playwright converte para navegador padrão |
| **Custo** | zero tokens (determinístico) |
| **Código** | `ai-farm-agent/agents/subagents.py` → `Navigator` |

O rastro de cada execução aparece no plano em `40 Execucoes/Planos` (bloco **Subagentes**).
