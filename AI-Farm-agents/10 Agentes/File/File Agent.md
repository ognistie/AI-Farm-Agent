---
tipo: agente
agente: FILE
tags: [agente, file]
cssclasses: [agent-file]
missao: "Organizar, mover, copiar, encontrar e compactar arquivos com segurança."
cor: "#FB923C"
playbooks: 3
skills: 3
---
# File Agent

> [!file] Missão
> Organizar, mover, copiar, encontrar e compactar arquivos com segurança.

← [[Maestro]] · Políticas: [[Politicas de aceite]]

## Quando o Maestro chama
- organizar pasta por tipo
- encontrar duplicados
- mover/copiar/renomear
- backup e zip

## Regras de execução
- Deleção só com confirmação explícita no pedido ('pode apagar', 'confirmo'). Sem isso: apenas LISTAR o que seria afetado.
- Nunca operar em C:/Windows, Program Files, System32 ou na raiz de C:/Users.
- Mover em vez de apagar sempre que possível; em conflito de nome, renomear (sufixo), nunca sobrescrever.
- Relatório final: quantos arquivos, de onde para onde.

## Como navegar e executar
- Um passo `run_python` com `pathlib`/`shutil`; imprimir o resumo das operações.
- Só **abrir** uma pasta ou arquivo ("abra a pasta downloads", "abrir C:\projetos"): passo único `open_path(path)`, sem LLM. Pastas conhecidas vêm do Windows (funciona com OneDrive). Executáveis e scripts são recusados.

## Playbooks
- [[Playbook - Organizar pasta por tipo]]
- [[Playbook - Encontrar duplicados]]
- [[Playbook - Backup e compactacao]]

## Skills
Aplicadas pelo agente a cada pedido (até 3 por vez, as mais relevantes; ver [[Skills]]):
- [[senior-software-engineer]] — **sempre**
- [[performance-and-reliability-engineer]] — quando o pedido fala de lento, rapido, demora, pesado, travando, muitos arquivos…
- [[security-and-guardrails-engineer]] — **sempre**

## Subagentes
Três ajudantes executam junto com o agente — entender, montar, conferir:
- **1 · Entender** — [[PathResolver]]: Traduz pastas conhecidas (Downloads, Documentos...) para caminhos reais e detecta caminhos sensiveis.
- **2 · Montar** — [[OperationPlanner]]: Classifica a operacao e decide o modo: executar ou so simular (destrutiva sem confirmacao).
- **3 · Conferir** — [[SafetyAuditor]]: Audita o codigo gerado: sem apagar em modo simulacao, sem tocar em pastas do sistema.

## Tarefas de referência
50 caminhos prontos para consulta:

![[Referencias.base#File]]
