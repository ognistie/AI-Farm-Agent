---
tipo: agente
agente: CODE
tags: [agente, code]
cssclasses: [agent-code]
missao: "Criar projetos de software completos (sites, scripts, APIs, apps desktop, jogos) e abrir no VS Code."
cor: "#34D399"
playbooks: 4
skills: 6
---
# Code Agent

> [!code] Missão
> Criar projetos de software completos (sites, scripts, APIs, apps desktop, jogos) e abrir no VS Code.

← [[Maestro]] · Políticas: [[Politicas de aceite]]

## Quando o Maestro chama
- criar site/sistema/script/API
- editar arquivo de código existente
- abrir o VS Code apontando para uma pasta

## Regras de execução
- Pasta do projeto na Área de Trabalho com nome derivado do TEMA da tarefa atual (nunca de tarefas anteriores).
- Identidade visual própria por tema: paleta e fontes coerentes com o assunto; não repetir o mesmo visual entre projetos.
- Código completo e executável; nada de placeholders 'TODO' ou 'lorem ipsum'.
- Multi-arquivo: imports coerentes com o esqueleto do planner; sem ciclos.
- Programas com interface (Tkinter, Flask) nunca rodam inline no processo do agente: gravar arquivos e abrir com o executável certo.
- Toda entrega abre no VS Code ou no navegador ao final para o usuário verificar.

## Como navegar e executar
- Um passo `run_python` grava todos os arquivos (`os.makedirs` + `open(...).write`).
- Abrir resultado: `subprocess.Popen(['code', pasta])` ou `webbrowser.open(index.html)`.
- Validadores rodam antes da execução: sintaxe, estrutura, qualidade e tema. Até 3 tentativas com o motivo literal.

## Playbooks
- [[Playbook - Site estatico]]
- [[Playbook - Script Python]]
- [[Playbook - API REST]]
- [[Playbook - App desktop Python]]

## Skills
- [[senior-software-engineer]] — Código de produção com design coerente com o repositório, testes e erros explícitos.
- [[full-stack-architect]] — Fronteiras entre cliente, API, serviços, dados, filas, cache e entrega.
- [[frontend-experience-engineer]] — Interfaces acessíveis, responsivas e performáticas com todos os estados de interação.
- [[code-review-and-refactoring-expert]] — Revisão de defeitos concretos e refatoração preservando comportamento.
- [[premium-ui-designer]] — Direção visual refinada: composição, tipografia, hierarquia e movimento deliberado.
- [[design-system-architect]] — Tokens, componentes, temas, acessibilidade e versionamento reutilizáveis.

## Falhas conhecidas (e correção)
- Tema de uma tarefa antiga vazava na nova (pasta SITE_BUDISMO em pedido de Muay Thai). Corrigido com `original_task` e memória só de rotas.
- Tkinter inline travava o app. Validador bloqueia programa inline.

## Subagentes
Três ajudantes executam junto com o agente — entender, montar, conferir:
- **1 · Entender** — [[Architect]]: Classifica o projeto (tipo, complexidade, stack, tema) e, se multi-arquivo, desenha o esqueleto.
- **2 · Montar** — [[Builder]]: Gera o codigo completo com o modelo (unico subagente que usa LLM).
- **3 · Conferir** — [[Reviewer]]: Valida sintaxe, estrutura, qualidade e tema do codigo antes de executar.

## Tarefas de referência
50 caminhos prontos para consulta:

![[Referencias.base#Code]]
