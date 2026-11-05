---
tipo: agente
agente: FILE
tags: [agente, file]
cssclasses: [agent-file]
missao: "Inspecionar e operar arquivos com ferramentas declarativas e escopo validado."
cor: "#FB923C"
playbooks: 3
skills: 3
---
# File Agent

> [!file] Missão
> Inspecionar e operar arquivos com ferramentas declarativas e escopo validado.

← [[Maestro]] · Políticas: [[Politicas de aceite]]

## Quando o Maestro chama
- organizar pasta por tipo
- encontrar duplicados
- mover/copiar/renomear
- backup e zip

## Regras de execução
- Ferramentas declarativas apenas; nenhuma geracao de Python ou shell.
- Raizes devem vir do pedido original; pastas conhecidas resolvidas pelo Windows, inclusive OneDrive.
- Nao sobrescrever destinos. Exclusao somente com confirmacao explicita e lixeira; nunca exclusao permanente.
- Falha e simulacao nao podem produzir efeitos silenciosos.

## Como navegar e executar
- list_files/find_files/read_file para inspecao; create_folder, write_file, copy_file e move_file com escopo validado.
- Organizar exige inventario e destinos; colisao interrompe a operacao afetada.
- ZIP, conversao, hash de duplicatas e desfazer organizacao ainda precisam de ferramentas proprias.

## Playbooks
- [[Playbook - Organizar pasta por tipo]]
- [[Playbook - Encontrar duplicados]]
- [[Playbook - Backup e compactacao]]

## Skills
Aplicadas pelo agente a cada pedido (até 3 por vez, as mais relevantes; ver [[Skills]]):
- [[senior-software-engineer]] — **sempre**
- [[performance-and-reliability-engineer]] — quando o pedido fala de lento, rapido, demora, pesado, travando, muitos arquivos…
- [[security-and-guardrails-engineer]] — **sempre**

## Componentes internos
O fluxo publico usa manifestos e builders/contratos deterministas. As notas de subagentes descrevem helpers legados; nao representam tres pesquisadores ou chamadas de modelo em paralelo.


## Tarefas de referência
Procedimentos consolidados em [[Tarefas de referencia]]:

[[Tarefas de referencia]]

## Falhas conhecidas (e correção)
- Nome igual nao prova conteudo duplicado. Nao apagar por suposicao.
- Sem permissao, arquivo em uso, escopo vago ou limite atingido: informar e pedir o dado necessario; nao ampliar acesso.
