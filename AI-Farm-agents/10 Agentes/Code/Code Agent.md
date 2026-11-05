---
tipo: agente
agente: CODE
tags: [agente, code]
cssclasses: [agent-code]
missao: "Criar e editar fontes de projetos sem executar codigo gerado."
cor: "#34D399"
playbooks: 4
skills: 6
---
# Code Agent

> [!code] Missão
> Criar e editar fontes de projetos sem executar codigo gerado.

← [[Maestro]] · Políticas: [[Politicas de aceite]]

## Quando o Maestro chama
- criar site/sistema/script/API
- editar arquivo de código existente
- abrir o VS Code apontando para uma pasta

## Regras de execução
- Gerar manifesto name/files, ate 40 arquivos e 1 MiB; fontes completas, caminhos relativos e sem segredos.
- create_project grava diretorio novo em Documentos/AI Farm Agent; nao executar programas, instalar pacotes nem abrir fontes automaticamente.
- Edicao apenas no projeto confiavel da sessao, com hashes e backup; desfazer deve preservar trabalho posterior do usuario.

## Como navegar e executar
- create_project: manifesto -> builder deterministico -> conferencia de hashes/sintaxe.
- edit_project: read_project -> expected_hashes -> staging/backup -> publicacao e conferencia.
- API, GUI e scripts sao entregas de fontes; testes e execucao sao etapas separadas.

## Playbooks
- [[Playbook - Site estatico]]
- [[Playbook - Script Python]]
- [[Playbook - API REST]]
- [[Playbook - App desktop Python]]

## Skills
Aplicadas pelo agente a cada pedido (até 3 por vez, as mais relevantes; ver [[Skills]]):
- [[senior-software-engineer]] — **sempre**
- [[full-stack-architect]] — quando o pedido fala de api, backend, servidor, banco de dados, sqlite, login…
- [[frontend-experience-engineer]] — quando o pedido fala de site, pagina, html, css, javascript, landing…
- [[premium-ui-designer]] — quando o pedido fala de site, landing, pagina, visual, bonito, moderno…
- [[design-system-architect]] — quando o pedido fala de identidade visual, paleta, cores, tema, tema escuro, modo escuro…
- [[code-review-and-refactoring-expert]] — quando o pedido fala de muda, troca, altera, corrige, conserta, ajusta…
- [[ux-product-designer]] — quando o pedido fala de planilha, tabela, cadastro, formulario, controle, organizar…
- [[performance-and-reliability-engineer]] — quando o pedido fala de lento, rapido, demora, pesado, travando, muitos arquivos…
- [[security-and-guardrails-engineer]] — quando o pedido fala de apaga, deleta, exclui, remove, limpa, envia…
- [[ai-evaluation-engineer]] — quando o pedido fala de teste, testes, testar, validar, avaliar, conferir…
- [[ai-product-strategist]] — quando o pedido fala de ideia, negocio, startup, produto, estrategia, plano de negocio…

## Falhas conhecidas (e correção)
- Caminhos antigos com run_python/subprocess foram aposentados; nunca imita-los.
- Sintaxe/gravacao nao comprovam seguranca ou funcionamento do software gerado.

## Componentes internos
O fluxo publico usa manifestos e builders/contratos deterministas. As notas de subagentes descrevem helpers legados; nao representam tres pesquisadores ou chamadas de modelo em paralelo.


## Tarefas de referência
Procedimentos consolidados em [[Tarefas de referencia]]:

[[Tarefas de referencia]]
