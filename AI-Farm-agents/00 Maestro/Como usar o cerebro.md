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
Todo agente que precisa do modelo (Data, Web, Code, Desktop, File, piloto do navegador e piloto de apps) recebe, **para aquele pedido**:
1. **Regras de execução**, **Como navegar e executar** e **Falhas conhecidas** da nota do agente;
2. [[Tarefas de referencia]], playbooks e execuções com sucesso parecidas (seção **Caminho**) — playbook curado vale mais que execução registrada;
3. [[Licoes aprendidas]] que tocam no pedido (cada falha real virou regra);
4. linhas do [[Dicionario de voz]] citadas no pedido: [[Termos de computador]], [[Formas de pedir]], [[Configuracoes do Windows]], [[Atalhos de teclado]], [[Apps e sites]].

O [[Maestro]] recebe referências e lições; a voz usa o dicionário e a [[Persona do assistente]]. Cada plano em `40 Execucoes/Planos` mostra **Consultou:** com as notas usadas.
Tudo é **referência**: nada no vault amplia permissões (as políticas vivem em código).
- Cada execução cria um plano em `40 Execucoes/Planos` e uma nota em `Sucesso` ou `Falhas`.

## Para ensinar algo novo
1. Crie uma nota em `30 Tarefas de referencia` com o template [[Template - Tarefa de referencia]].
2. Preencha `keywords` no topo e a seção **Caminho**.
3. Pronto: pedidos parecidos passam a receber esse caminho como referência.

> Não coloque senhas, chaves ou dados pessoais nas notas.
