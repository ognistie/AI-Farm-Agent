---
tipo: indice-politicas
tags: [politica, indice]
cssclasses: [policy-note]
---
# Políticas de aceite

← [[Início]]

O [[Maestro]] valida todo plano antes de executar. Violação → replanejamento com o motivo; se persistir, a tarefa não executa e o motivo aparece na tela e em [[Tarefas com falha]].

| ID | Política | Aplicação |
|---|---|---|
| [[POL-000]] | Plano não vazio | bloqueia |
| [[POL-001]] | Conteúdo pedido presente | bloqueia + replaneja |
| [[POL-002]] | Sem eco nem substituto | bloqueia + replaneja |
| [[POL-003]] | Pesquisa com termo | bloqueia + replaneja |
| [[POL-004]] | Variáveis de contexto válidas | bloqueia + replaneja |
| [[POL-005]] | Agente conhecido | bloqueia |
| [[POL-006]] | Plano enxuto | bloqueia |
| [[POL-007]] | Toda ação pedida está no plano | bloqueia |
| [[SEC-001]] | Segredos e dados pessoais | aplicada no código |
| [[AGT-001]] | Ações destrutivas e externas | orientação + FileAgent em simulação |
| [[AGT-002]] | Conteúdo não confiável | orientação |
| [[AUD-001]] | Evidência de conclusão | aplicada no código |

Princípios herdados do Maestro do hackathon: menor privilégio, negação por padrão, rastreabilidade, conteúdo externo como dado não confiável, falha segura, **declarado ≠ verificado**.
