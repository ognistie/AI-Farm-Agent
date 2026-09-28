---
tipo: guia
tags: [guia]
cssclasses: [agent-maestro]
---
# Como usar o cérebro

## Estrutura
| Pasta | Conteúdo | Quem escreve |
|---|---|---|
| `00 Maestro` | orquestração, validação, roteamento | humano |
| `10 Agentes` | nota de cada agente + playbooks | humano |
| `20 Politicas` | políticas de aceite (espelham o código) | humano |
| `30 Skills` | skills do catálogo AIWorkbench por agente | humano |
| `30 Tarefas de referencia` | caminhos prontos para consulta | humano |
| `40 Execucoes` | planos, sucessos e falhas | **o app** |
| `90 Sistema` | templates | humano |

## Como os agentes usam
- A seção **Regras de execução** da nota de cada agente entra no prompt quando o agente precisa do modelo.
- As [[Tarefas de referencia]] e as execuções com sucesso parecidas com o pedido entram no prompt do [[Maestro]] como pista (seção **Caminho**).
- Cada execução cria um plano em `40 Execucoes/Planos` e uma nota em `Sucesso` ou `Falhas`.

## Para ensinar algo novo
1. Crie uma nota em `30 Tarefas de referencia` com o template [[Template - Tarefa de referencia]].
2. Preencha `keywords` no topo e a seção **Caminho**.
3. Pronto: pedidos parecidos passam a receber esse caminho como referência.

> Não coloque senhas, chaves ou dados pessoais nas notas.
