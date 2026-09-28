---
tipo: processo
tags: [maestro, validacao]
cssclasses: [agent-maestro]
---
# Ciclo de validação de planos

Inspirado no fluxo do Maestro do hackathon: **quem propõe não aprova o próprio plano**.

```mermaid
flowchart LR
  P[Pedido] --> M[Maestro propõe subtasks]
  M --> V1{Políticas de aceite}
  V1 -- reprovado --> R[Replaneja 1x com o motivo] --> V1
  V1 -- aprovado --> N[Plano salvo em 40 Execucoes/Planos]
  N --> A[Agente propõe passos]
  A --> V2{Políticas dos passos}
  V2 -- reprovado --> F[Subtask falha, motivo registrado]
  V2 -- aprovado --> E[Executa no computador]
  E --> S{Todos os passos ok?}
  S -- sim --> OK[Tarefas com sucesso]
  S -- não --> KO[Tarefas com falha]
```

## Estados de uma ação
| Estado | Significado |
|---|---|
| `proposto` | sugerido pelo Maestro/agente, ainda não validado |
| `aprovado` | passou nas políticas; pode executar |
| `executado` | todos os passos rodaram sem falha |
| `falhou` | algum passo falhou ou foi reprovado |
| `bloqueado` | política impediu (ex.: `cannot_do`) |

> [!warning] Validação é código
> As políticas que bloqueiam vivem em `ai-farm-agent/core/plan_validator.py`. As notas do cérebro orientam os agentes, mas **não concedem permissão** — editar uma nota não libera uma ação bloqueada.

Relacionado: [[Maestro]] · [[Politicas de aceite]]
