---
tipo: indice
tags: [subagente, indice]
cssclasses: [agent-maestro]
---
# Subagentes

← [[Maestro]] · [[Início]]

> [!maestro] 3 ajudantes por agente
> **Entender** o pedido → **Montar** o insumo da execução → **Conferir** antes de agir.
> 14 dos 15 são determinísticos (custo zero). Só o [[Builder]] do Code Agent usa o modelo.

![[Subagentes.base]]

```mermaid
flowchart LR
  P[Subtask do Maestro] --> E[1 · Entender]
  E --> M[2 · Montar]
  M --> C{3 · Conferir}
  C -- ok --> X[Execução]
  C -- reprovado --> F[Falha com motivo]
  X --> R[Revisão pós-passo<br/>ex.: ContentGuard]
```
