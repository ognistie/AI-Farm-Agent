---
tipo: skill
origem: AIWorkbench
agentes: [MAESTRO]
sempre_para: []
ativa_quando: e depois, em seguida, depois, projeto, sistema completo, varias, varios, etapas, passo a passo, planeja, organiza tudo, primeiro
tags: [skill]
cssclasses: [skill-note]
atualizado: 2026-10-05
---
# tech-lead

> [!skill] O que faz
> Plano de entrega com escopo, dependências, riscos e evidência visíveis.

**Usada por:** [[Maestro]]

## Quando usar
- Pedidos com várias etapas ou vários agentes

Ativa sozinha quando o pedido fala de: e depois, em seguida, depois, projeto, sistema completo, varias, varios, etapas, passo a passo, planeja, organiza tudo, primeiro.

## Como o agente aplica
- **Maestro:** Pedido com várias partes: subtarefas na ORDEM certa, cada uma com depends_on quando usa o resultado da anterior.
- **Maestro:** Cada subtarefa com critério de pronto verificável; nada de subtarefa 'genérica'.
- **Maestro:** Se uma parte depende de algo que falta (login, arquivo, escolha do usuário), pergunte antes de planejar o resto.

## Regras
- Não estimar sem premissas
- Não esconder dependências no texto
- Separar decisões de produto, técnicas e de implementação

## Conferir antes de concluir
- A ordem respeita as dependências
- Cada parte tem um 'pronto' verificável

## Fluxo (catálogo)
1. Definir resultado, fora de escopo e evidência
2. Inspecionar o estado atual
3. Dividir em marcos verticais de valor
4. Mapear dependências e caminho crítico
5. Planejar rollout e rollback

Fonte: [AIWorkbench](https://github.com/BielmFranco/AIWorkbench/tree/main/skills/tech-lead) · como os agentes usam: [[Skills]]
