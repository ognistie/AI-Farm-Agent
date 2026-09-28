---
tipo: subagente
agente: WEB
papel: entender
tags: [subagente, web]
cssclasses: [agent-web]
---
# QueryBuilder

> [!web] 1 · Entender — subagente do [[Web Agent]]
> Descobre a intencao (pesquisar, abrir, ler), o site e o termo de busca.

| | |
|---|---|
| **Entrada** | Pedido + params do Maestro |
| **Saída** | intenção (search/open/read), site, termo, clique no 1º, nova aba |
| **Regra** | Pesquisa sem termo → reprova (POL-003) |
| **Custo** | zero tokens (determinístico) |
| **Código** | `ai-farm-agent/agents/subagents.py` → `QueryBuilder` |

O rastro de cada execução aparece no plano em `40 Execucoes/Planos` (bloco **Subagentes**).
